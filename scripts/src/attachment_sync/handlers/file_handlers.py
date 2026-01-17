"""File Handlers for attachment_sync - Manage file operations and uploads.""".

import logging
from typing import Any, Dict, List

from ..config import Config

logger = logging.getLogger(__name__)


class FileHandlers:
    """Handles file processing and upload operations.""".

    def __init__(self, config: Config, api_handlers):
        """Initialize File Handlers.

        Args:
            config: Configuration object.
            api_handlers: APIHandlers instance with initialized API clients.
        """
        self.config = config
        self.api_handlers = api_handlers
        logger.info("FileHandlers initialized")

    def sanitize_filename(self, timestamp: str, file_type: str) -> str:
        """Sanitize filename by replacing special characters.

        Args:
            timestamp: Original timestamp string.
            file_type: File extension/type.

        Returns:
            Sanitized filename.
        """
        return (timestamp + file_type).replace(" ", "_").replace(":", "-")

    def sanitize_folder_name(self, job_id: str, customer_name: str) -> str:
        """Create sanitized folder name from job ID and customer name.

        Args:
            job_id: Job ID string.
            customer_name: Customer name string.

        Returns:
            Sanitized folder name.
        """# Replace commas with semicolons and forward slashes with hyphens
        sanitized = customer_name.replace(",", ";").replace("/", "-")
        return f"#{job_id}; {sanitized}"

    def ensure_subfolder_exists(
        self,
        existing_files: List[Dict[str, Any]],
        parent_folder_id: str,
        subfolder_name: str,
    ) -> str:
        """Ensure a subfolder exists, create if it doesn't.

        Args:
            existing_files: List of existing files/folders in parent.
            parent_folder_id: Parent folder ID.
            subfolder_name: Name of subfolder to check/create.

        Returns:
            Subfolder ID.
        """# Check if subfolder already exists
        subfolder = next(
            (files.get("id") for files in existing_files if files.get("name") == subfolder_name),
            None,
        )

        if not subfolder:
            # Create the subfolder
            created_folder = self.api_handlers.onedrive.create_folder(
                parent_folder_id=parent_folder_id, folder_name=subfolder_name
            )
            subfolder = created_folder[1]
            logger.info(f"Created subfolder: {subfolder_name}")

        return subfolder

    def setup_job_folder(self, folder_data: List[Dict[str, Any]], folder_name: str) -> tuple:
        """Setup job folder structure with subfolders for pdfs, photos, videos.

        Args:
            folder_data: List of all existing folders in root.
            folder_name: Name of the job folder.

        Returns:
            Tuple of (folder_id, pdf_folder_id, photo_folder_id, video_folder_id).
        """# Check if folder already exists
        folder_exists = next(
            (item for item in folder_data if item.get("name") == folder_name), None
        )

        if folder_exists:
            folder_id = folder_exists["id"]
            existing_files = self.api_handlers.onedrive.get_items_by_folder_id(folder_id)

            # Ensure all subfolders exist
            pdf_folder = self.ensure_subfolder_exists(
                existing_files, folder_id, self.config.file_types.pdf_folder_name
            )
            photo_folder = self.ensure_subfolder_exists(
                existing_files, folder_id, self.config.file_types.photo_folder_name
            )
            video_folder = self.ensure_subfolder_exists(
                existing_files, folder_id, self.config.file_types.video_folder_name
            )
        else:
            # Create main folder
            created_folder = self.api_handlers.onedrive.create_folder(
                parent_folder_id=self.config.onedrive.servicem8_attachments_folder,
                folder_name=folder_name,
            )
            folder_id = created_folder[1]
            logger.info(f"Created job folder: {folder_name}")

            # Create all subfolders
            created_pdf_folder = self.api_handlers.onedrive.create_folder(
                parent_folder_id=folder_id,
                folder_name=self.config.file_types.pdf_folder_name,
            )
            pdf_folder = created_pdf_folder[1]

            created_photo_folder = self.api_handlers.onedrive.create_folder(
                parent_folder_id=folder_id,
                folder_name=self.config.file_types.photo_folder_name,
            )
            photo_folder = created_photo_folder[1]

            created_video_folder = self.api_handlers.onedrive.create_folder(
                parent_folder_id=folder_id,
                folder_name=self.config.file_types.video_folder_name,
            )
            video_folder = created_video_folder[1]

        return folder_id, pdf_folder, photo_folder, video_folder

    def upload_attachment(
        self,
        attachment: Dict[str, Any],
        pdf_folder: str,
        photo_folder: str,
        video_folder: str,
    ) -> bool:
        """Upload a single attachment to the appropriate folder.

        Args:
            attachment: Attachment metadata dictionary.
            pdf_folder: PDF folder ID.
            photo_folder: Photo folder ID.
            video_folder: Video folder ID.

        Returns:
            True if uploaded successfully, False otherwise.
        """
        attachment_uuid = attachment.get("uuid")
        attachment_timestamp = attachment.get("timestamp")
        attachment_file_type = attachment.get("file_type")

        try:
            if attachment_file_type.endswith("pdf"):
                # Fetch PDF content
                form_data = self.api_handlers.servicem8.get_image(
                    asset_uuid=attachment_uuid, file_type="pdf", return_type="content"
                )

                # Upload to PDF folder
                self.api_handlers.onedrive.upload_file(
                    parent_id=pdf_folder,
                    file_name=self.sanitize_filename(attachment_timestamp, attachment_file_type),
                    file_content=form_data,
                )
                logger.info(f"Uploaded PDF: {attachment_uuid}")
                return True

            elif attachment_file_type.endswith("mp4"):
                # Fetch video content
                video_data = self.api_handlers.servicem8.get_image(
                    asset_uuid=attachment_uuid, file_type="video", return_type="content"
                )

                # Upload to video folder
                self.api_handlers.onedrive.upload_file(
                    parent_id=video_folder,
                    file_name=self.sanitize_filename(attachment_timestamp, attachment_file_type),
                    file_content=video_data,
                )
                logger.info(f"Uploaded video: {attachment_uuid}")
                return True

            elif attachment_file_type.endswith(self.config.file_types.image_extensions):
                # Fetch photo content
                photo_data = self.api_handlers.servicem8.get_image(
                    asset_uuid=attachment_uuid, file_type="image", return_type="content"
                )

                # Upload to photo folder
                self.api_handlers.onedrive.upload_file(
                    parent_id=photo_folder,
                    file_name=self.sanitize_filename(attachment_timestamp, attachment_file_type),
                    file_content=photo_data,
                )
                logger.info(f"Uploaded photo: {attachment_uuid}")
                return True

            else:
                logger.warning(f"Unknown file type: {attachment_file_type}")
                return False

        except Exception as e:
            logger.error(f"Failed to upload attachment {attachment_uuid}: {e}")
            return False

    def __repr__(self) -> str:
        """Return string representation of FileHandlers.""".
        return f"FileHandlers(config={self.config.name})"
