"""Module providing API handlers for various services.

This module initializes and configures API clients for ServiceTemplate for the {{ ModuleName }} module.
"""

import logging
import os
from typing import Any

from services import ServiceTemplate

class APIHandlers:
    """Handles initialization and configuration of API clients for {{ ModuleName }}."""

    def __init__(self):
        """Initialize API handlers.

        Determines the deployment environment.
        Selects appropriate
            - Secret names
            - Initialize the API clients.
        """
        logging.info('Initialising various API packages')
        # Determine the environment
        environment = os.getenv('DEPLOY_ENV', 'STAGING')

        # Use different secret names for staging and production
        template_secret_name = "TEMPLATE_SECRET" if environment == "STAGING" else "TEMPLATE_GITHUB_SECRET"

        deploy_type = 'prod' if environment == 'PRODUCTION' else 'stg'

        # Initialize APIs
        # ServiceTemplate is a module; instantiate the ServiceTemplate class defined inside it
        self.ServiceTemplate = ServiceTemplate.ServiceTemplate(template_secret_name, deploy_type=deploy_type)