"""Module containing Open.cx API logic."""

# General Libraries
import atexit
import sys
import requests
from requests.exceptions import HTTPError
from typing import Optional, List, Dict, Any

from .SecretManager import SecretManager


class OpenCX:
    """Client for interacting with OpenCX sessions and chat history."""

    def __init__(self, secret_name, deploy_type="STAGING"):
        """
        Initialize the open.cx class with authentication and session settings.

        Args:
            secret_name (str): The name of the secret containing authentication details.
            deploy_type (str, optional): The deployment type (default is 'stg').
        """
        secret = SecretManager(deploy_type=deploy_type).get_secret(secret_name)
        _token = secret["api_key"]
        self._baseURL = "https://api.open.cx"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {_token}",
            }
        )
        atexit.register(self._close_session)

    def _close_session(self):
        """Close the session when the object is deleted or script exits."""
        self.session.close()

    def _handle_response(self, response):
        """
        Handle the HTTP response, raising an error if the status code indicates a failure.

        Args:
            response (requests.Response): The response object returned by the API request.

        Raises:
            RuntimeError: If the response status code indicates an error.
        """
        try:
            response.raise_for_status()
        except HTTPError as e:
            try:
                error_message = response.json()
            except ValueError:
                error_message = response.text
            raise RuntimeError(f"HTTP error occurred: {e}, Response: {error_message}") from e

    def list_sessions(
        self,
        created_after: Optional[str] = None,
        ticket_status: Optional[str] = None,
        is_handed_off: Optional[str] = True,
        is_descending: Optional[str] = True,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve a list of sessions, optionally filtered by status.

        Args:
            created_after (Optional[str]): Filter sessions by the date they were created.
            ticket_status (Optional[str]): Filter sessions by their status.
            is_handed_off (Optional[bool]): Filter sessions if it was handed off to an agent.
            is_descending (Optional[bool]): Order sessions by the datetime they were created

        Returns:
            List[Dict[str, Any]]: A list of session dictionaries.
        """
        endpoint = "/chat/sessions"
        params = {}
        if created_after is not None:
            params["created_after"] = created_after
        if ticket_status is not None:
            params["status"] = ticket_status
        if is_handed_off is not None:
            params["handed_off"] = str(is_handed_off).lower()
        response = self.session.get(url=f"{self._baseURL}{endpoint}", params=params)
        self._handle_response(response)
        response_json = response.json()
        results = response_json.get("items", None)
        next_page = response_json.get("next", None)
        while next_page:
            params["cursor"] = next_page
            next_response = self.session.get(url=f"{self._baseURL}{endpoint}", params=params)
            self._handle_response(next_response)
            next_response_json = next_response.json()
            next_results = next_response_json.get("items", None)
            results.extend(next_results)
            next_page = next_response_json.get("next", None)
        sorted_results = sorted(results, key=lambda x: x["created_at"], reverse=is_descending)
        return sorted_results

    def get_chat_history(self, session_id, is_descending=False) -> List[Dict[str, Any]]:
        """
        Retrieve the chat history for a given session ID.

        Args:
            session_id (str): The ID of the session to retrieve chat history for.
            is_descending (bool): Order messages by the datetime they were sent

        Returns:
            List[Dict[str, Any]]: A list of chat message dictionaries.
        """
        params = {}
        endpoint = f"/chat/sessions/{session_id}/history"
        response = self.session.get(url=f"{self._baseURL}{endpoint}")
        self._handle_response(response)
        response_json = response.json()
        results = response_json.get("items", None)
        next_page = response_json.get("next", None)
        while next_page:
            params["cursor"] = next_page
            next_response = self.session.get(url=f"{self._baseURL}{endpoint}", params=params)
            self._handle_response(next_response)
            next_response_json = next_response.json()
            next_results = next_response_json.get("items", None)
            results.extend(next_results)
            next_page = next_response_json.get("next", None)
        sorted_results = sorted(results, key=lambda x: x["created_at"], reverse=is_descending)
        return sorted_results

    def update_session_status(self, session_id, status):
        """
        Update the status of a session to the provided status.

        Args:
            session_id (str): The ID of the session to update.
            status (str): The new status value to set.
                options include: open, closed_resolved, closed_unresolved

        Returns:
            Dict[str, Any]: The response from the API after updating the session status.
        """
        payload = {}
        endpoint = f"/chat/sessions/{session_id}"
        if status is None:
            print("Status needs to be provided")
            sys.exit(1)
        payload["status"] = status
        response = self.session.patch(url=f"{self._baseURL}{endpoint}", json=payload)
        self._handle_response(response)
        return response
