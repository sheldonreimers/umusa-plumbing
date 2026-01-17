"""Module containing the logic for the SecretManager."""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import docker
import yaml

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SecretManager:
    """Initialize the SecretManager."""

    def __init__(
        self,
        deploy_type: Optional[str] = None,
        stack_file: str = "/home/.Docker/docker-stack.yml",
        stack_name: str = "mystack",
        service_names: Optional[List[str]] = None,
    ):
        """
        Initialize the SecretManager.

        Args:
            deploy_type (str, optional): Type of deployment.
                Defaults to environment variable DEPLOY_ENV or "STAGING".
            stack_file (str): Path to the stack YAML file.
            stack_name (str): Name of the Docker stack.
            service_names (list, optional): Names of the services. Defaults to ["tebi_service"].
        """
        self.deploy_type = (deploy_type or os.getenv("DEPLOY_ENV", "STAGING")).upper()
        self._cache: Dict[str, Any] = {}
        self.stack_file = stack_file
        self.stack_name = stack_name
        self.service_names = service_names or [
            "tebi_service",
        ]
        self.docker_client = docker.from_env() if self.deploy_type == "STAGING" else None

    def get_secret(
        self,
        secret_name: str,
        file_path: Optional[str] = None,
        as_json: bool = True,
        force_refresh: bool = False,
    ) -> Union[Dict[str, Any], str]:
        """
        Retrieve a secret from the cache or secret store.

        Args:
            secret_name (str): The name of the secret to retrieve.
            as_json (bool): If True, return the secret as a JSON object. Defaults to False.
            file_path (str, optional): Path to a file containing the secret. Defaults to None.
            force_refresh (bool): If True, force a refresh from the store. Defaults to False.

        Returns:
            str or dict: The secret value as a string or JSON object.

        Raises:
            FileNotFoundError: If the file_path does not exist.
            ValueError: If the secret is invalid.
            json.JSONDecodeError: If JSON decoding fails.
        """
        if not force_refresh and secret_name in self._cache:
            return self._cache[secret_name]

        try:
            if self.deploy_type == "PRODUCTION":
                env_secret = os.environ.get(secret_name.upper())
                if env_secret is None:
                    raise ValueError(f"Env variable '{secret_name.upper()}' not found.")
                secret = json.loads(env_secret) if as_json else env_secret
            elif self.deploy_type == "STAGING":
                file_path = file_path or f"/run/secrets/{secret_name}"
                if not Path(file_path).is_file():
                    raise FileNotFoundError(f"Secret file '{file_path}' not found.")
                with open(file_path, "r") as file:
                    raw = file.read()
                    secret = json.loads(raw) if as_json else raw
            elif self.deploy_type == "CLUSTER":
                secrets = self.docker_client.secrets.list()
                for s in secrets:
                    if s.name == secret_name:
                        secret = s.attrs
                        break
                else:
                    raise ValueError(f"Secret '{secret_name}' not found in Swarm.")
            else:
                raise ValueError(f"Invalid deploy_type: {self.deploy_type}")
            self._cache[secret_name] = secret
            return secret
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON secret: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading secret: {e}")
            raise

    def list_secrets(self) -> List[str]:
        """
        List all available secrets for the current deployment type.

        Returns:
            List[str]: A list of secret names.

        Raises:
            ValueError: If the deploy_type is invalid.
        """
        try:
            if self.deploy_type == "PRODUCTION":
                return [key for key in os.environ.keys() if key.isupper() and "SECRET" in key]
            elif self.deploy_type == "STAGING":
                directory = "/run/secrets/"
                if not Path(directory).is_dir():
                    logger.warning(f"Secrets directory '{directory}' not found.")
                    return []
                return [f.name for f in Path(directory).iterdir() if f.is_file()]
            elif self.deploy_type == "CLUSTER":
                return [s.name for s in self.docker_client.secrets.list()]
            else:
                raise ValueError(f"Invalid deploy_type: {self.deploy_type}")
        except Exception as e:
            logger.error(f"Error listing secrets: {e}")
            raise

    def refresh_secret(self, secret_name: str, **kwargs) -> Any:
        """
        Refresh a secret in the cache by fetching its latest value from the store.

        Args:
            secret_name (str): The name of the secret to refresh.
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        if secret_name in self._cache:
            del self._cache[secret_name]
        return self.get_secret(secret_name, force_refresh=True, **kwargs)

    def clear_cache(self) -> None:
        """
        Clear the secret cache.

        Removes all cached secret values from memory.
        """
        self._cache.clear()

    def create_or_update_secret(
        self, secret_name: str, value: Union[str, dict], verbose: bool = True
    ) -> None:
        """
        Create a new secret or update an existing one.

        Args:
            secret_name (str): The name of the secret to create or update.
            value (str or dict): The value to set for the secret.
                If a dict, it will be JSON encoded.
            verbose (bool): If True, print status messages. Defaults to True.
        """
        if isinstance(value, dict):
            value = json.dumps(value)
        client = self.docker_client
        for secret in client.secrets.list():
            if secret.name == secret_name:
                if verbose:
                    print("Existing secret found. Removing...")
                secret.remove()
        client.secrets.create(name=secret_name, data=value.encode("utf-8"))
        if verbose:
            print("A secret was created/updated.")
        self._ensure_secret_in_stack(secret_name, verbose=verbose)
        self._redeploy_stack(verbose=verbose)

    def delete_secret(
        self, secret_name: str, remove_from_stack: bool = True, verbose: bool = True
    ) -> None:
        """
        Delete a Docker Swarm secret, and optionally remove it from the stack file and redeploy.

        Args:
            secret_name (str): The name of the secret to delete.
            remove_from_stack (bool): If True, remove the secret from the stack file and
                redeploy. Defaults to True.
            verbose (bool): If True, print status messages.
                Defaults to True.

        Prints:
            Status messages about removal and redeployment when verbose is True.
        """
        client = self.docker_client
        found = False
        for secret in client.secrets.list():
            if secret.name == secret_name:
                secret.remove()
                found = True
                if verbose:
                    print("A secret was removed from Swarm.")
                break
        if not found and verbose:
            print("No matching secret found for removal.")

        if remove_from_stack:
            self._remove_secret_from_stack(secret_name, verbose=verbose)
            self._redeploy_stack(verbose=verbose)

    # ------- Private helpers for workflow --------

    def _ensure_secret_in_stack(self, secret_name: str, verbose: bool = True) -> None:
        """
        Ensure the secret is listed in the stack YAML and all associated services.

        Args:
            secret_name (str): The name of the secret to ensure in the stack.
            verbose (bool): If True, print status messages. Defaults to True.

        Prints:
            Status messages when secrets are added to the stack or services if verbose is True.
        """
        stack_file = self.stack_file
        service_names = self.service_names
        with open(stack_file, "r") as f:
            stack = yaml.safe_load(f)
        if "secrets" not in stack:
            stack["secrets"] = {}
        if secret_name not in stack["secrets"]:
            stack["secrets"][secret_name] = {"external": True}
            if verbose:
                print("A secret was added to stack-level secrets.")
        for service in service_names:
            if service in stack["services"]:
                service_def = stack["services"][service]
                if "secrets" not in service_def:
                    service_def["secrets"] = []
                if secret_name not in service_def["secrets"]:
                    service_def["secrets"].append(secret_name)
                    if verbose:
                        print(f"A secret was added to service '{service}'.")
        with open(stack_file, "w") as f:
            yaml.dump(stack, f, sort_keys=False)
        if verbose:
            print(f"Stack file '{stack_file}' updated.")

    def _redeploy_stack(self, verbose: bool = True) -> None:
        """
        Redeploy the Docker stack using the updated stack file.

        Args:
            verbose (bool): If True, print the deployment command and results. Defaults to True.

        Prints:
            The docker command, success messages, and stack deployment results if verbose is True.
        """
        cmd = ["docker", "stack", "deploy", "-c", self.stack_file, self.stack_name]
        if verbose:
            print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("Error deploying stack:", result.stderr)
        else:
            print("Stack redeployed successfully.")
            if verbose:
                print(result.stdout)

    def _remove_secret_from_stack(self, secret_name: str, verbose: bool = True) -> None:
        """
        Remove a secret from the stack YAML and all associated services.

        Args:
            secret_name (str): The name of the secret to remove.
            verbose (bool): If True, print status messages. Defaults to True.

        Prints:
            Status messages when secrets are removed from the stack or services if verbose is True.
        """
        stack_file = self.stack_file
        service_names = self.service_names
        with open(stack_file, "r") as f:
            stack = yaml.safe_load(f)

        # Remove from top-level secrets
        if "secrets" in stack and secret_name in stack["secrets"]:
            del stack["secrets"][secret_name]
            if verbose:
                print("A secret was removed from stack-level secrets.")

        # Remove from each service
        for service in service_names:
            if service in stack["services"]:
                service_def = stack["services"][service]
                if "secrets" in service_def and secret_name in service_def["secrets"]:
                    service_def["secrets"].remove(secret_name)
                    if verbose:
                        print(f"A secret was removed from service '{service}'.")

        with open(stack_file, "w") as f:
            yaml.dump(stack, f, sort_keys=False)
        if verbose:
            print(f"Stack file '{stack_file}' updated after removing secret.")
