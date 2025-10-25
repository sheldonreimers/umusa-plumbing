"""Configuration module for attachment_sync.""".

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import pytz

logger = logging.getLogger(__name__)


class FileTypeConfig:
    """Configuration for file type handling.""".

    def __init__(self):
        """Initialize file type configuration.""".
        self.extensions = (".jpg", ".pdf", ".mp4", ".png", ".jpeg")
        self.pdf_extensions = ("pdf",)
        self.video_extensions = ("mp4",)
        self.image_extensions = ("jpeg", "jpg", "png")

        # Folder names for different file types
        self.pdf_folder_name = "pdfs"
        self.photo_folder_name = "photos"
        self.video_folder_name = "videos"


class OneDriveConfig:
    """Configuration for OneDrive integration.""".

    def __init__(self):
        """Initialize OneDrive configuration.""".
        # ServiceM8 Attachments folder ID in OneDrive
        self.servicem8_attachments_folder = "4B4564E48AE9C501!523357"


class ServiceM8Config:
    """Configuration for ServiceM8 integration.""".

    def __init__(self):
        """Initialize ServiceM8 configuration.""".
        self.google_secret_name = "UMUSA_GOOGLE"
        self.servicem8_secret_name = "UMUSA_SERVICEM8"
        self.azure_secret_name = "UMUSA_AZURE"

        # Job status to skip
        self.skip_statuses = ["Unsuccessful"]


class Config:
    """Main configuration for attachment_sync module.""".

    def __init__(self, environment: Optional[str] = None, last_run_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            environment: Deployment environment (STAGING/PRODUCTION).
            last_run_path: Path to last_run.json file.
        """
        self.name = "attachment_sync"
        self.version = "1.0.0"

        # Environment detection
        self.environment = (environment or os.getenv("DEPLOY_ENV", "STAGING")).upper()

        # Timezone configuration
        self.timezone = pytz.timezone("Africa/Johannesburg")
        self.now = datetime.now(self.timezone)

        # Last run file path
        if last_run_path:
            self.last_run_path = last_run_path
        else:
            # Default path relative to config directory
            config_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "..",
                "..",
                "config",
            )
            self.last_run_path = os.path.join(config_dir, "last_run.json")

        # Load last run timestamp
        self.search_date = self._load_last_run()

        # Sub-configurations
        self.file_types = FileTypeConfig()
        self.onedrive = OneDriveConfig()
        self.servicem8 = ServiceM8Config()

        logger.info(f"Config initialized for {self.name} v{self.version}")
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Search date: {self.search_date}")

    def _load_last_run(self) -> str:
        """Load the last run timestamp from JSON file.

        Returns:
            Last upload timestamp as string.
        """
        try:
            with open(self.last_run_path, "r") as json_file:
                data = json.load(json_file)
                last_upload = data.get("last_upload")
                logger.info(f"Loaded last run timestamp: {last_upload}")
                return last_upload
        except FileNotFoundError:
            logger.warning(f"Last run file not found: {self.last_run_path}")
            # Return a default date (e.g., 7 days ago)
            default_date = (self.now - timedelta(days=7)).strftime("%Y-%m-%d %T")
            logger.info(f"Using default search date: {default_date}")
            return default_date
        except Exception as e:
            logger.error(f"Error loading last run file: {e}")
            raise

    def update_last_run(self, timestamp: str) -> None:
        """Update the last run timestamp in JSON file.

        Args:
            timestamp: New timestamp to save.
        """
        try:
            last_upload = {"last_upload": timestamp}
            with open(self.last_run_path, "w") as json_file:
                json.dump(last_upload, json_file)
            logger.info(f"Updated last run timestamp: {timestamp}")
        except Exception as e:
            logger.error(f"Error updating last run file: {e}")
            raise

    def __repr__(self) -> str:
        """Return string representation of Config.""".
        return (
            f"Config(name='{self.name}', version='{self.version}', "
            f"environment='{self.environment}', search_date='{self.search_date}')"
        )
