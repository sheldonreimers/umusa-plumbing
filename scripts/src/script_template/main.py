"""
Entry point for running a {{ ModuleName }} script service.

Initializes configuration, handlers, and runs the main process for the
{{ ModuleName }} module.
"""

import logging

# Project-specific imports
from .config import Config
from .handlers.api_handlers import APIHandlers
from .handlers.data_handlers import DataHandlers
from .processor.processorTemplate import ProcessorTemplate

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)


def main():
    """Run the {{ ModuleName }} module's main process."""
    try:
        # Initialize configuration.
        config = Config()

        # Initialize API handlers
        api_handlers = APIHandlers()

        # Initialize data handlers
        data_handlers = DataHandlers(config, api_handlers)

        # Initialize ProcessorTemplate processor
        template_processor = ProcessorTemplate(config, api_handlers, data_handlers)

        # Run the session creation process
        template_processor.process(items=[])

        logging.info("Session creation process completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred during the session creation process: {e}")


if __name__ == "__main__":
    main()
