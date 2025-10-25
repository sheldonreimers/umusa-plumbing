"""API Handlers for attachment_sync - Initialize and manage API connections.""".

import logging
import os
import sys

# Add scripts directory to path for services imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from services import GoogleSheets, OneDrive, ServiceM8  # noqa: E402

logger = logging.getLogger(__name__)


class APIHandlers:
    """Handles initialization and management of all API clients.""".

    def __init__(self, environment: str = "STAGING"):
        """Initialize API handlers.

        Args:
            environment: Deployment environment (STAGING or PRODUCTION).
        """
        self.environment = environment.upper()
        logger.info("Initializing API packages for Attachment Sync")

        # Secret names
        google_secret_name = "UMUSA_GOOGLE"
        servicem8_secret_name = "UMUSA_SERVICEM8"
        azure_secret_name = "UMUSA_AZURE"

        # Determine deployment type for secret manager
        deploy_type = "PRODUCTION" if self.environment == "PRODUCTION" else "STAGING"

        # Initialize Google Sheets API
        try:
            self.google_sheets = GoogleSheets(
                secret_name=google_secret_name, deploy_type=deploy_type
            )
            logger.info("Google Sheets API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets API: {e}")
            raise

        # Initialize ServiceM8 API
        try:
            self.servicem8 = ServiceM8(secret_name=servicem8_secret_name, deploy_type=deploy_type)
            logger.info("ServiceM8 API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ServiceM8 API: {e}")
            raise

        # Initialize OneDrive API
        try:
            self.onedrive = OneDrive(secret_name=azure_secret_name, deploy_type=deploy_type)
            logger.info("OneDrive API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OneDrive API: {e}")
            raise

        logger.info("API handlers initialized")

    def __repr__(self) -> str:
        """Return string representation of APIHandlers.""".
        return f"APIHandlers(environment='{self.environment}')"
