"""OneDrive API service for Microsoft OneDrive operations."""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from retry import retry

from .SecretManager import SecretManager

logger = logging.getLogger(__name__)


class OneDrive:
    """OneDrive API client for file and folder operations."""

    __all__ = [
        # Connection
        "connect",
        # Folder Operations
        "get_folders",
        "get_items_by_folder_id",
        "create_folder",
        "delete_folder",
        # File Operations
        "upload_file",
    ]

    def __init__(self, secret_name: str = "AZURE_SECRET", deploy_type: str = "STAGING"):
        """Initialize OneDrive API client.

        Args:
            secret_name: The name of the secret containing Azure credentials.
            deploy_type: Deployment type - 'STAGING' or 'PRODUCTION'.
        """
        logging.info("Initializing OneDrive API client")

        # Retrieve credentials from SecretManager
        secret_manager = SecretManager(deploy_type=deploy_type)
        credentials = secret_manager.get_secret(secret_name)

        # Extract credentials
        client_id = credentials.get("client_id")
        client_secret = credentials.get("client_secret")
        refresh_token = credentials.get("refresh_token")
        tenant_id = credentials.get("tenant_id", "common")
        
        # Use custom scope if provided, otherwise use default
        scope = credentials.get("scope_decoded")
        if not scope:
            scope = "https://graph.microsoft.com/.default"
        
        # Initialize variables
        self.scope = scope
        self.token_endpoint = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

        # Get access token
        self.access_token = self.connect(client_id, client_secret, refresh_token, scope)

        # System variables
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        self.base_url = "https://graph.microsoft.com/v1.0/me/drive"

        logging.info("OneDrive API client initialized successfully")

    def connect(self, client_id: str, client_secret: str, refresh_token: str, scope: str = None) -> str:
        """Connect to OneDrive and get access token.

        Args:
            client_id: Azure application client ID.
            client_secret: Azure application client secret.
            refresh_token: OAuth refresh token.
            scope: OAuth scope (optional).

        Returns:
            Access token string.
        """
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        
        # Add scope if provided
        if scope:
            token_data["scope"] = scope

        response = requests.post(self.token_endpoint, data=token_data)
        response.raise_for_status()

        refresh_token = response.json()["refresh_token"]
        access_token = response.json()["access_token"]

        return access_token

    def get_folders(self) -> requests.Response:
        """Get all folders in root directory.

        Returns:
            Response object containing folder data.
        """
        endpoint = "/root/children"
        response = requests.get(self.base_url + endpoint, headers=self.headers)
        response.raise_for_status()
        return response

    def get_items_by_folder_id(self, folder_id: str) -> List[Dict[str, Any]]:
        """Get all items (files and folders) within a specific folder.

        Args:
            folder_id: The ID of the folder to retrieve items from.

        Returns:
            List of dictionaries containing item information.
        """
        endpoint = f"/items/{folder_id}/children"
        response = requests.get(self.base_url + endpoint, headers=self.headers)
        response.raise_for_status()
        response_json = response.json()
        value_lst = response_json["value"]

        # Initialize list to hold dictionaries
        response_list = []

        # Process the first batch of items
        for item in value_lst:
            item_dict = {
                "downloadUrl": item.get("@microsoft.graph.downloadUrl"),
                "createdAt": pd.to_datetime(item.get("createdDateTime")).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "id": item.get("id"),
                "name": item.get("name"),
                "size": item.get("size"),
                "lastModifiedAt": pd.to_datetime(item.get("lastModifiedDateTime")).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "type": "folder" if "folder" in item.keys() else "file",
            }
            response_list.append(item_dict)

        # Handle pagination if there are more items
        while True:
            next_link = response_json.get("@odata.nextLink")
            if next_link:
                response = requests.get(next_link, headers=self.headers)
                response.raise_for_status()
                response_json = response.json()
                value_response = response_json["value"]
                for next_item in value_response:
                    next_item_dict = {
                        "downloadUrl": next_item.get("@microsoft.graph.downloadUrl"),
                        "createdAt": pd.to_datetime(next_item.get("createdDateTime")).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "id": next_item.get("id"),
                        "name": next_item.get("name"),
                        "size": next_item.get("size"),
                        "lastModifiedAt": pd.to_datetime(
                            next_item.get("lastModifiedDateTime")
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                        "type": "folder" if "folder" in next_item.keys() else "file",
                    }
                    response_list.append(next_item_dict)
            else:
                break

        return response_list

    @retry(tries=2, delay=5)
    def create_folder(self, parent_folder_id: str, folder_name: str) -> tuple:
        """Create a new folder within a parent folder.

        Args:
            parent_folder_id: The ID of the parent folder.
            folder_name: Name for the new folder.

        Returns:
            Tuple of (folder_name, folder_id) if successful, response object otherwise.
        """
        endpoint = f"/items/{parent_folder_id}/children"
        payload = {"name": folder_name, "folder": {}, "@microsoft.graph.conflictBehavior": "rename"}

        response = requests.post(self.base_url + endpoint, headers=self.headers, json=payload)

        if response.status_code == 201:
            response_json = response.json()
            return response_json["name"], response_json["id"]
        else:
            response.raise_for_status()
            return response

    def delete_folder(self, folder_id: str) -> str:
        """Delete a folder by ID.

        Args:
            folder_id: The ID of the folder to delete.

        Returns:
            Success message or response object.
        """
        endpoint = f"/items/{folder_id}"
        response = requests.delete(self.base_url + endpoint, headers=self.headers)

        if response.status_code == 204:
            return "file deleted"
        else:
            response.raise_for_status()
            return response

    def upload_file(
        self,
        parent_id: str,
        file_name: str,
        file_path: Optional[str] = None,
        file_content: Optional[bytes] = None,
    ) -> requests.Response:
        """Upload a file to OneDrive.

        Args:
            parent_id: The ID of the parent folder.
            file_name: Name for the uploaded file.
            file_path: Optional path to file on disk.
            file_content: Optional file content as bytes.

        Returns:
            Response object from the upload request.
        """
        upload_headers = self.headers.copy()
        upload_headers["Content-Type"] = "application/octet-stream"

        if file_path and not file_content:
            endpoint = f'/items/{parent_id}:/{file_path.split("/")[-1]}:/content'
            with open(file_path, "rb") as file:
                file_content = file.read()
            response = requests.put(
                self.base_url + endpoint, headers=upload_headers, data=file_content
            )
            response.raise_for_status()
            return response
        elif not file_path and file_content:
            endpoint = f"/items/{parent_id}:/{file_name}:/content"
            response = requests.put(
                self.base_url + endpoint, headers=upload_headers, data=file_content
            )
            response.raise_for_status()
            return response
        else:
            raise ValueError("Either file_path or file_content must be provided, but not both")
