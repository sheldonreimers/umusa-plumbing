"""Module providing API handlers for Stock Manager services.

This module initializes and configures API clients for Google Sheets and
ServiceM8 for the Stock Manager module.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add scripts directory to Python path to enable services imports
scripts_path = Path(__file__).parent.parent.parent.parent
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))

from services.GoogleSheets import GoogleSheets
from services.ServiceM8 import ServiceM8


class APIHandlers:
    """Handles initialization and configuration of API clients for Stock Manager."""

    def __init__(self):
        """Initialize API handlers.

        Determines the deployment environment and selects appropriate
        secret names for Google Sheets and ServiceM8 API initialization.
        """
        logging.info('Initializing API packages for Stock Manager')
        
        # Determine the environment
        self.environment = os.getenv('DEPLOY_ENV', 'STAGING')
        
        # Use different secret names for staging and production
        if self.environment == 'PRODUCTION':
            google_secret_name = "GOOGLE_GITHUB_SECRET"
            servicem8_secret_name = "SERVICEM8_GITHUB_SECRET"
            deploy_type = 'PRODUCTION'
        else:
            google_secret_name = "UMUSA_GOOGLE"
            servicem8_secret_name = "UMUSA_SERVICEM8"
            deploy_type = 'STAGING'
        
        logging.info('API handlers initialized')
        
        # Initialize Google Sheets API
        try:
            self.google_sheets = GoogleSheets(
                secret_name=google_secret_name,
                deploy_type=deploy_type
            )
            logging.info('Google Sheets API initialized successfully')
        except Exception as e:
            logging.error(f'Failed to initialize Google Sheets API: {e}')
            raise
        
        # Initialize ServiceM8 API
        try:
            self.servicem8 = ServiceM8(
                secret_name=servicem8_secret_name,
                deploy_type=deploy_type
            )
            logging.info('ServiceM8 API initialized successfully')
        except Exception as e:
            logging.error(f'Failed to initialize ServiceM8 API: {e}')
            raise

    def __repr__(self) -> str:
        """Return string representation of APIHandlers."""
        return f"APIHandlers(environment='{self.environment}')"
