"""Module containing Intercom API logic."""

# General Libraries
import atexit
import logging

import requests
from requests.exceptions import HTTPError
from tqdm.auto import tqdm

from .SecretManager import SecretManager

# Configure logging at the module level
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class Intercom:
    """A class to interact with the Hubspot pre-built Library."""

    def __init__(self, secret_name: str = "INTERCOM_SECRET", deploy_type: str = "STAGING"):
        """Initialize the Intercom class with credentials from a secret manager."""
        secret = SecretManager(deploy_type=deploy_type).get_secret(secret_name=secret_name.upper())

        self.session = requests.Session()
        api_key = secret.get("api_key", "") if isinstance(secret, dict) else ""
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        )
        self._base_url = "https://api.intercom.io"
        atexit.register(self._close_session)

    def _me(self):
        """Retrieve the current user's information from the Intercom API."""
        response = self.session.get("https://api.intercom.io/me")
        self._handle_response(response)
        return response.json()

    def _close_session(self):
        """Close the session when the object is deleted or script exits."""
        self.session.close()

    def _handle_response(self, response: requests.Response):
        """Handle the HTTP response, raising an error if the status code indicates a failure."""
        try:
            response.raise_for_status()
        except HTTPError as e:
            try:
                error_message = response.json()
            except ValueError:
                error_message = response.text
            raise RuntimeError(f"HTTP error occurred: {e}, Response: {error_message}") from e

    def get_contact(self, contact_id: str):
        """Retrieve a contact's information from Intercom."""
        logger.info(f"Retrieving contact with ID: {contact_id}")
        endpoint = f"contacts/{contact_id}"
        response = self.session.get(f"{self._base_url}/{endpoint}")
        self._handle_response(response)
        logger.info(f"Contact {contact_id} retrieved")
        return response.json()

    def get_conversation(self, conversation_id: str):
        """Retrieve a conversation's information from Intercom."""
        logger.info(f"Retrieving conversation with ID: {conversation_id}")
        endpoint = f"conversations/{conversation_id}"
        response = self.session.get(f"{self._base_url}/{endpoint}")
        self._handle_response(response)
        logger.info(f"Conversation {conversation_id} retrieved")
        return response.json()
    
    def update_conversation(self, conversation_id: str, update_data: dict):
        """Update an existing conversation in Intercom."""
        logger.info(f"Updating conversation {conversation_id}")
        endpoint = f"conversations/{conversation_id}"
        # current_conversation = self.get_conversation(conversation_id)
        # conversation_data = current_conversation
        payload = {k: v for k, v in update_data.items() if v is not None}
        # merged_payload = {**conversation_data, **payload}
        response = self.session.put(f"{self._base_url}/{endpoint}", json=payload)
        self._handle_response(response)
        logger.info(f"Conversation {conversation_id} updated")
        return response.json()

    def update_conversation_state(self, conversation_id, state, admin_id):
        '''Function to update the state of a ticket'''
        logger.info(f"Updating state for conversation {conversation_id}")
        endpoint = f'conversations/{conversation_id}/reply'
        payload = {
            "admin_id": admin_id,
            "message_type": state,
            "type": "admin",
        }
        response = self.session.post(f"{self._base_url}/{endpoint}", json=payload)
        self._handle_response(response)
        logger.info(f"Update state for conversation {conversation_id} to {state}")
        return response.json()

    def note_conversation(self, conversation_id, note, admin_id):
        '''Function to apply notes to conversations'''
        logger.info(f"Updating state for conversation {conversation_id}")
        endpoint = f'conversations/{conversation_id}/reply'
        payload = {
            "admin_id": admin_id,
            "message_type": 'note',
            "body": note,
            "type": "admin",
        }
        response = self.session.put(f"{self._base_url}/{endpoint}", json=payload)
        self._handle_response(response)
        logger.info(f"Applied note to conversation {conversation_id}")
        return response.json()

    def tag_conversation(self, conversation_id, tag_name, admin_id):
        '''Function to apply tags to conversations'''
        logger.info(f"Appling tag to conversation {conversation_id}")
        endpoint = f'conversations/{conversation_id}/tags'
        _tag_list = self._list_tags()
        _tag_name_to_id = {t.get('name'): t.get('id') for t in _tag_list}
        tag_id = _tag_name_to_id.get(tag_name)
        payload = {
            'admin_id': admin_id,
            'id': tag_id,
        }
        response = self.session.post(f"{self._base_url}/{endpoint}", json=payload)
        self._handle_response(response)
        logger.info(f"Applied {tag_name} to conversation {conversation_id}")
        return response.json()

    def create_contact(
        self,
        role: str,
        email: str,
        name: str,
        external_id: str,
        phone: str | None = None,
        signed_up_at: int | None = None,
        unsubscribed_from_emails: bool | None = None,
        custom_attributes: dict | None = None,
    ):
        """Create a new contact in Intercom."""
        logger.info(f"Creating contact for email: {email}")
        endpoint = "contacts"
        payload: dict = {
            "role": role,
            "email": email,
            "phone": phone,
            "name": name,
            "external_id": external_id,
            "signed_up_at": signed_up_at,
            "unsubscribed_from_emails": unsubscribed_from_emails,
        }
        if custom_attributes is not None:
            payload["custom_attributes"] = custom_attributes
        response = self.session.post(f"{self._base_url}/{endpoint}", json=payload)
        self._handle_response(response)
        logger.info(f"Contact for email {email} created")
        return response.json()

    def delete_contact(self, contact_id: str):
        """Delete a contact in Intercom."""
        logger.info(f"Deleting contact with ID: {contact_id}")
        endpoint = f"contacts/{contact_id}"
        response = self.session.delete(f"{self._base_url}/{endpoint}")
        self._handle_response(response)
        logger.info(f"Contact {contact_id} deleted")
        return response.json()

    def update_contact(self, contact_id: str, update_data: dict):
        """Update an existing contact in Intercom."""
        logger.info(f"Updating contact {contact_id}")
        endpoint = f"contacts/{contact_id}"
        current_contact = self.get_contact(contact_id)
        contact_data = current_contact
        payload = {k: v for k, v in update_data.items() if v is not None}
        merged_payload = {**contact_data, **payload}
        response = self.session.put(f"{self._base_url}/{endpoint}", json=merged_payload)
        self._handle_response(response)
        logger.info(f"Contact {contact_id} updated")
        return response.json()

    def archive_contact(self, contact_id: str):
        """Archive a contact in Intercom."""
        logger.info(f"Archiving contact: {contact_id}")
        endpoint = f"contacts/{contact_id}/archive"
        response = self.session.post(f"{self._base_url}/{endpoint}")
        self._handle_response(response)
        logger.info(f"{contact_id} has been archived")
        return response

    def merge_contacts(self, from_contact_id: str, into_contact_id: str):
        """Merge two contacts in Intercom."""
        logger.info(f"Merging contact {from_contact_id} into {into_contact_id}")
        endpoint = "contacts/merge"
        headers = {"Intercom-Version": "2.14", "Content-Type": "application/json"}
        payload = {"from": from_contact_id, "into": into_contact_id}
        response = self.session.post(f"{self._base_url}/{endpoint}", headers=headers, json=payload)
        self._handle_response(response)
        logger.info(f"Contact {from_contact_id} merged into {into_contact_id}")
        return response.json()

    def list_contacts(self, per_page: int = 100):
        """List all contacts in Intercom with a progress bar compatible with Jupyter and console."""
        endpoint = "contacts"
        params = {"page": 1, "per_page": per_page}
        all_contacts: list = []
        next_page = True

        # First request to get total count of contacts
        response = self.session.get(f"{self._base_url}/{endpoint}", params=params)
        self._handle_response(response)
        data = response.json()
        total_contacts = data.get("total_count", 0)

        with tqdm(total=total_contacts, desc="Fetching contacts", unit="contact") as pbar:
            while next_page:
                response = self.session.get(f"{self._base_url}/{endpoint}", params=params)
                self._handle_response(response)
                data = response.json()
                contacts = data.get("data", [])
                all_contacts.extend(contacts)
                pbar.update(len(contacts))  # Update progress bar

                pages = data.get("pages", {})
                next_info = pages.get("next")
                if next_info:
                    params["page"] = next_info.get("page")
                    if "starting_after" in next_info:
                        params["starting_after"] = next_info["starting_after"]
                else:
                    next_page = False
        return all_contacts

    def list_conversations(self, per_page: int = 50):
        """List all conversations in Intercom with a tqdm progress bar, handling pagination."""
        logger.info("Starting listing conversations")
        endpoint = "conversations"
        params = {"page": 1, "per_page": per_page}
        all_conversations: list = []

        # First request to get total count or page metadata
        response = self.session.get(f"{self._base_url}/{endpoint}", params=params)
        self._handle_response(response)
        data = response.json()

        # Try to get an accurate total; fall back to estimation using pages metadata
        pages = data.get("pages", {}) or {}
        total_conversations = data.get("total_count")
        if total_conversations is None:
            total_pages = pages.get("total_pages")
            per_pg = pages.get("per_page") or per_page
            if isinstance(total_pages, int) and total_pages > 0 and isinstance(per_pg, int):
                total_conversations = total_pages * per_pg  # estimate

        # Progress bar compatible with notebooks and console
        with tqdm(
            total=total_conversations,
            desc="Fetching conversations",
            unit=" conversation",
        ) as pbar:
            while True:
                # Process current page
                conversations = data.get("conversations", [])
                all_conversations.extend(conversations)
                pbar.update(len(conversations))

                # Determine next page
                pages = data.get("pages", {}) or {}
                next_info = pages.get("next")
                if next_info:
                    # Advance pagination parameters
                    if "page" in next_info:
                        params["page"] = next_info.get("page")
                    if "starting_after" in next_info:
                        params["starting_after"] = next_info.get("starting_after")

                    # Fetch next page
                    response = self.session.get(f"{self._base_url}/{endpoint}", params=params)
                    self._handle_response(response)
                    data = response.json()
                else:
                    break
        logger.info("Completed listing conversations")
        return all_conversations

    def search_tickets(self, field: str, operator: str, value: str):
        """Search for tickets in Intercom based on a custom field, operator, and value."""
        logger.info(f"Searching tickets with {field} {operator} {value}")
        endpoint = "tickets/search"
        payload = {"query": {"field": field, "operator": operator, "value": value}}
        response = self.session.post(f"{self._base_url}/{endpoint}", json=payload)
        self._handle_response(response)
        logger.info(f"Search completed for {field} {operator} {value}")
        return response.json()

    def search_contacts(self, clauses: list, per_page: int = 100):
        """Search contacts using the Intercom Contacts Search API."""
        logger.info(f"Searching contacts with clauses: {clauses}")
        if not isinstance(clauses, (list, tuple)):
            raise ValueError("clauses must be a list or tuple of clause lists/dicts")
        normalized_clauses = []
        for item in clauses:
            if isinstance(item, dict) and {"field", "operator", "value"}.issubset(item.keys()):
                normalized_clauses.append(
                    {
                        "field": item["field"],
                        "operator": item["operator"],
                        "value": str(item["value"]),
                    }
                )
                continue
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                field, operator, value = item[0], item[1], item[2]
                normalized_clauses.append(
                    {"field": field, "operator": operator, "value": str(value)}
                )
                continue
            raise ValueError(f"Invalid clause format: {item}")
        normalized_query = {"operator": "AND", "value": normalized_clauses}
        endpoint = "contacts/search"
        payload = {"query": normalized_query, "pagination": {"per_page": per_page, "page": 1}}
        all_items: list = []
        while True:
            current_page = payload["pagination"].get("page")
            response = self.session.post(f"{self._base_url}/{endpoint}", json=payload)
            self._handle_response(response)
            data = response.json()
            items = data.get("data", [])
            all_items.extend(items)
            pages = data.get("pages") or {}
            total_pages = pages.get("total_pages")
            page_num = pages.get("page") or current_page
            next_info = pages.get("next")
            if total_pages is not None:
                if page_num >= total_pages:
                    break
                payload["pagination"]["page"] = page_num + 1
                continue
            if next_info:
                if "page" in next_info:
                    payload["pagination"]["page"] = next_info.get("page")
                if "starting_after" in next_info:
                    payload["pagination"]["starting_after"] = next_info.get("starting_after")
                continue
            break
        logger.info(f"Search completed, returning {len(all_items)} results")
        return all_items

    def search_contacts_created_after(self, created_after_timestamp: int, per_page: int = 5):
        """Convenience wrapper to search contacts created after a given UNIX timestamp."""
        logger.info(f"Searching contacts created after {created_after_timestamp}")
        clauses = [["created_at", ">", str(created_after_timestamp)]]
        result = self.search_contacts(clauses=clauses, per_page=per_page)
        logger.info(f"Search completed, returning {len(result)} results")
        return result

    def create_company(self, name: str, company_id: str, custom_attributes: dict | None = None):
        """Create a new company in Intercom."""
        logger.info(f"Creating company for name: {name}")
        endpoint = "companies"
        payload: dict = {
            "name": name,
            "company_id": company_id,
        }
        if custom_attributes is not None:
            payload["custom_attributes"] = custom_attributes
        response = self.session.post(f"{self._base_url}/{endpoint}", json=payload)
        self._handle_response(response)
        logger.info(f"Company for name {name} created")
        return response.json()

    def _ticket_states(self):
        """Retrieve the ticket attributes from Intercom."""
        logger.info("Retrieving ticket state attributes")
        endpoint = "ticket_states"
        response = self.session.get(f"{self._base_url}/{endpoint}")
        self._handle_response(response)
        logger.info("Ticket state attributes retrieved")
        return response.json()

    def _unachieve_contact(self, contact_id: str):
        """Unarchive a contact in Intercom."""
        logger.info(f"Unarchiving contact with ID: {contact_id}")
        endpoint = f"contacts/{contact_id}/unarchive"
        response = self.session.post(f"{self._base_url}/{endpoint}")
        self._handle_response(response)
        logger.info(f"Contact {contact_id} unarchived")
        return response.json()

    def _list_tags(self):
        '''Fetch all tags'''
        logger.info("Fetching all tags")
        endpoint = 'tags'
        response = self.session.get(f"{self._base_url}/{endpoint}")
        self._handle_response(response)
        logger.info("Returrning all tags")
        return response.json()['data']