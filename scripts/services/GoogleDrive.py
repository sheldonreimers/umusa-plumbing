"""Module containing logic to interact with Google Drive."""

import logging
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

from .SecretManager import SecretManager

# Module-level logger
logger = logging.getLogger(__name__)


class GoogleDrive:
    """Public interface for Google Drive operations."""

    service: Any
    __all__ = [
        "create_file",
        "download_file",
        "delete_file",
        "rename_file",
        "create_folder",
        "share_folder_user",
        "share_folder_domain",
        "delete_folder",
        "move_file",
        "copy_file",
    ]

    def __init__(
        self,
        secret_name: str,
        deploy_type: str = "stg",
    ):
        """
        Initialize GoogleDrive with service credentials.

        Args:
            secret_name (str): Name of the secret for Google service account credentials.
            deploy_type (str): Deployment environment type (e.g., 'stg', 'prod').
        """
        self.secret_name = secret_name
        self.deploy_type = deploy_type
        self.service = None  # type: Any
        self._connect()

    def create_file(
        self,
        df: pd.DataFrame,
        file_title: str,
        file_type: str,
        folder_id: str,
        keep_local: bool = False,
        local_dir: Optional[str] = None,
    ) -> dict:
        """
        Upload a DataFrame as a file to Google Drive.

        Args:
            df (pd.DataFrame): DataFrame to upload.
            file_title (str): Base name of the file without extension.
            file_type (str): File extension including the dot (e.g., '.csv').
            folder_id (str): ID of the destination folder in Google Drive.
            keep_local (bool): If True, save a local copy to local_dir.
            local_dir (Optional[str]): Path to local directory when keep_local is True.

        Returns:
            dict: Metadata of the uploaded file, including its 'id'.

        Raises:
            ValueError: If keep_local is True and local_dir is not provided.
        """
        df_clean = df.fillna("")
        if keep_local:
            if local_dir is None:
                raise ValueError("local_dir must be provided when keep_local=True")
            dir_path = Path(local_dir)
            dir_path.mkdir(parents=True, exist_ok=True)
            file_path = dir_path / f"{file_title}{file_type}"
            df_clean.to_csv(file_path, index=False)
            media = MediaFileUpload(str(file_path), mimetype="text/csv")
            logger.info("Saved local copy to: %s", file_path)
        else:
            buffer = StringIO()
            df_clean.to_csv(buffer, index=False)
            buffer.seek(0)
            media = MediaIoBaseUpload(buffer, mimetype="text/csv", resumable=False)
            logger.debug("In-memory buffer ready for upload")
        metadata = {"name": f"{file_title}{file_type}", "parents": [folder_id]}
        result = self.service.files().create(body=metadata, media_body=media, fields="id").execute()
        logger.info("Uploaded '%s' as ID %s", file_title, result.get("id"))
        return result

    def download_file(
        self,
        file_name: Optional[str] = None,
        file_id: Optional[str] = None,
        save_to_disk: bool = False,
        local_dir: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Download a file by name or ID; return as DataFrame or save locally.

        Args:
            file_name (Optional[str]): Name of the file to download.
            file_id (Optional[str]): ID of the file to download.
            save_to_disk (bool): If True, save to local_dir instead of returning.
            local_dir (Optional[str]): Path to local directory when keep_local is True.

        Returns:
            pd.DataFrame: DataFrame of the downloaded file or empty if saved/not found.

        Raises:
            ValueError: If save_to_disk is True and local_dir is not provided.
        """
        metadata = self._find_file(file_name=file_name, file_id=file_id)
        if not metadata:
            logger.warning("File not found: %s %s", file_name, file_id)
            return pd.DataFrame()
        meta = metadata[0]
        fid = meta["id"]
        fname = meta["name"]
        data = self.service.files().get_media(fileId=fid).execute()
        if fname.lower().endswith((".xls", ".xlsx")):
            df = pd.read_excel(BytesIO(data))
        else:
            df = pd.read_csv(StringIO(data.decode("utf-8")), low_memory=False)
        if save_to_disk:
            if local_dir is None:
                raise ValueError("local_dir must be provided when save_to_disk=True")
            dir_path = Path(local_dir)
            dir_path.mkdir(parents=True, exist_ok=True)
            dest = dir_path / fname
            df.to_csv(dest, index=False)
            logger.info("Saved to disk: %s", dest)
            return pd.DataFrame()
        logger.info("Downloaded '%s' with shape %s", fname, df.shape)
        return df

    def delete_file(
        self,
        file_name: Optional[str] = None,
        file_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a file by name or ID.

        Args:
            file_name (Optional[str]): Name of the file to delete.
            file_id (Optional[str]): ID of the file to delete.

        Returns:
            bool: True if deletion succeeded, False otherwise.
        """
        metadata = self._find_file(file_name=file_name, file_id=file_id)
        if not metadata:
            logger.warning("No file to delete: %s %s", file_name, file_id)
            return False
        target_id = metadata[0]["id"]
        self.service.files().delete(fileId=target_id).execute()
        logger.info("Deleted file ID: %s", target_id)
        return True

    def rename_file(
        self,
        old_name: str,
        new_name: str,
    ) -> bool:
        """
        Rename a file given its current name.

        Args:
            old_name (str): Current name of the file.
            new_name (str): New name for the file.

        Returns:
            bool: True if rename succeeded, False otherwise.
        """
        metadata = self._find_file(file_name=old_name)
        if not metadata:
            logger.warning("File not found: %s", old_name)
            return False
        fid = metadata[0]["id"]
        self.service.files().update(fileId=fid, body={"name": new_name}).execute()
        logger.info("Renamed '%s' to '%s'", old_name, new_name)
        return True

    def create_folder(
        self,
        new_folder: str,
        parent_folder_name: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
    ) -> dict:
        """
        Create a folder under a specified parent folder name.

        Args:
            parent_folder_name (str): Name of the existing parent folder.
            parent_folder_id (str): ID of the existing parent folder.
            new_folder (str): Name of the new folder to create.

        Returns:
            dict: Metadata of the created folder, including its 'id'.

        Raises:
            ValueError: If the parent folder is not found.
        """
        if parent_folder_name:
            parent_meta = self._find_folder(folder_name=parent_folder_name)
            if not parent_meta:
                raise ValueError(f"Parent folder '{parent_folder_name}' not found")
            parent_id = parent_meta[0]["id"]
        elif parent_folder_id:
            parent_id = parent_folder_id
        else:
            raise ValueError("Parent details not provided")
        result = (
            self.service.files()
            .create(
                body={
                    "name": new_folder,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [parent_id],
                },
                fields="id",
            )
            .execute()
        )
        return result

    def share_folder_user(
        self,
        folder_name: str,
        user_email: str,
        role: str = "writer",
    ) -> dict:
        """
        Share a folder by name with a specific user.

        Args:
            folder_name (str): Name of the folder to share.
            user_email (str): Email address of the user.
            role (str): Permission role ('writer' or 'reader').

        Returns:
            dict: Permission resource metadata.

        Raises:
            ValueError: If the folder is not found.
        """
        meta = self._find_folder(folder_name=folder_name)
        if not meta:
            raise ValueError(f"Folder '{folder_name}' not found")
        fid = meta[0]["id"]
        perm = {"type": "user", "role": role, "emailAddress": user_email}
        result = self.service.permissions().create(fileId=fid, body=perm, fields="id").execute()
        logger.info("Shared folder '%s' with %s (%s)", folder_name, user_email, role)
        return result

    def share_folder_domain(
        self,
        folder_name: str,
        domain: str,
        role: str = "writer",
    ) -> dict:
        """
        Share a folder by name with an entire domain.

        Args:
            folder_name (str): Name of the folder to share.
            domain (str): Domain to share with (e.g., 'example.com').
            role (str): Permission role, defaults to 'writer'.

        Returns:
            dict: Permission resource metadata.

        Raises:
            ValueError: If the folder is not found.
        """
        meta = self._find_folder(folder_name=folder_name)
        if not meta:
            raise ValueError(f"Folder '{folder_name}' not found")
        fid = meta[0]["id"]
        perm = {"type": "domain", "role": role, "domain": domain}
        result = self.service.permissions().create(fileId=fid, body=perm, fields="id").execute()
        logger.info("Shared folder '%s' with domain %s (%s)", folder_name, domain, role)
        return result

    def delete_folder(
        self,
        folder_name: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a folder by name or ID.

        Args:
            folder_name (Optional[str]): Name of the folder to delete.
            folder_id (Optional[str]): ID of the folder to delete.

        Returns:
            bool: True if deletion succeeded, False otherwise.

        Raises:
            ValueError: If neither folder_name nor folder_id is provided.
        """
        if folder_name:
            meta = self._find_folder(folder_name=folder_name)
            if not meta:
                logger.warning("No folder to delete: %s", folder_name)
                return False
        elif folder_id:
            target_id = folder_id
        else:
            raise ValueError("folder_name or folder_id must be provided")
        self.service.files().delete(fileId=target_id).execute()
        logger.info("Deleted folder ID: %s", target_id)
        return True

    def move_file(
        self,
        file_name: Optional[str] = None,
        file_id: Optional[str] = None,
        new_folder_name: Optional[str] = None,
        new_folder_id: Optional[str] = None,
    ) -> Dict:
        """
        Move a file to a new folder, by file name or ID, into a destination by folder name or ID.

        Args:
            file_name (Optional[str]): Name of the file to move.
            file_id   (Optional[str]): ID of the file to move.
            new_folder_name (Optional[str]): Name of the destination folder.
            new_folder_id   (Optional[str]): ID of the destination folder.

        Returns:
            Dict: Metadata of the moved file, including updated parents.

        Raises:
            ValueError: If neither file_name nor file_id is provided, or if the file
                isn’t found; or if neither new_folder_name nor new_folder_id is provided,
                or the destination folder can’t be found.
        """
        # 1) Find the file metadata (handles name or ID)
        meta = self._find_file(file_name=file_name, file_id=file_id)
        if not meta:
            raise ValueError(f"File '{file_name or file_id}' not found")
        fid = meta[0]["id"]
        old_parent = meta[0]["parents"][0]

        # 2) Resolve the new parent ID
        if new_folder_id:
            parent_id = new_folder_id
        elif new_folder_name:
            folders = self._find_folder(folder_name=new_folder_name)
            if not folders:
                raise ValueError(f"Destination folder '{new_folder_name}' not found")
            parent_id = folders[0]["id"]
        else:
            raise ValueError("Either new_folder_name or new_folder_id must be provided")

        # 3) Perform the move
        result = (
            self.service.files()
            .update(
                fileId=fid,
                addParents=parent_id,
                removeParents=old_parent,
                fields="id,parents",
            )
            .execute()
        )
        logger.info(
            "Moved file %s (ID=%s) to folder ID %s",
            file_name or "<by-id>",
            fid,
            parent_id,
        )
        return result

    def copy_file(
        self,
        file_id: str,
        new_name: Optional[str] = None,
    ) -> dict:
        """
        Copy a file by ID, with optional new name.

        Args:
            file_id (str): ID of the file to copy.
            new_name (Optional[str]): New name for the copied file.

        Returns:
            dict: Metadata of the copied file, including its new 'id'.
        """
        body = {"name": new_name} if new_name else {}
        result = self.service.files().copy(fileId=file_id, body=body).execute()
        logger.info("Copied file ID %s to new ID %s", file_id, result.get("id"))
        return result

    def _connect(self) -> None:
        """Authenticate and build the Google Drive service client."""
        secret = SecretManager(deploy_type=self.deploy_type).get_secret(self.secret_name)
        creds = service_account.Credentials.from_service_account_info(secret)
        self.service = build("drive", "v3", credentials=creds, cache_discovery=False)

    def _find_file(
        self, file_name: Optional[str] = None, file_id: Optional[str] = None
    ) -> List[dict]:
        """
        Private: find file metadata by name or ID.

        Args:
            file_name (Optional[str]): Name of the file to find.
            file_id (Optional[str]): ID of the file to find.

        Returns:
            List[dict]: List of file metadata dicts (may be empty).
        """
        if file_id:
            try:
                file_meta = (
                    self.service.files()
                    .get(fileId=file_id, fields="id,name,modifiedTime,parents")
                    .execute()
                )
                return [file_meta]
            except Exception:
                return []
        if file_name:
            query = f"name='{file_name}' and mimeType!='application/vnd.google-apps.folder'"
            return self._paginate(
                lambda pageToken=None: self.service.files().list(
                    q=query,
                    fields="nextPageToken,files(id,name,modifiedTime,parents)",
                    orderBy="modifiedTime desc",
                    pageSize=100,
                    pageToken=pageToken,
                )
            )
        return []

    def _find_folder(self, folder_name: str) -> List[dict]:
        """
        Private: find folder metadata by name.

        Args:
            folder_name (str): Name of the folder to find.

        Returns:
            List[dict]: List of folder metadata dicts (may be empty).
        """
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        return self._paginate(
            lambda pageToken=None: self.service.files().list(
                q=query,
                fields="nextPageToken,files(id,name,modifiedTime)",
                orderBy="modifiedTime desc",
                pageSize=100,
                pageToken=pageToken,
            )
        )

    def _paginate(self, request: Callable[..., Any]) -> List[dict]:
        """
        Private: handle paginated list responses from Google Drive API.

        Args:
            request (Callable[..., Any]): Function that takes pageToken & returns a list.

        Returns:
            List[dict]: Aggregated list of files across all pages.
        """
        items: List[dict] = []
        page_token: Optional[str] = None
        while True:
            response = request(pageToken=page_token).execute()
            items.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return items
