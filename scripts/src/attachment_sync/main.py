"""Main entry point for attachment_sync module.""".

import logging
import os
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from attachment_sync.config import Config  # noqa: E402
from attachment_sync.handlers.api_handlers import APIHandlers  # noqa: E402
from attachment_sync.handlers.file_handlers import FileHandlers  # noqa: E402
from attachment_sync.processor.upload_processor import (  # noqa: E402
    UploadProcessor,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)-12s: %(filename)s:%(lineno)d %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def main():
    """Main execution function.""".
    try:
        logger.info("Starting attachment_sync module")

        # Initialize configuration
        config = Config()

        # Initialize API handlers
        api_handlers = APIHandlers(environment=config.environment)

        # Initialize file handlers
        file_handlers = FileHandlers(config, api_handlers)

        # Initialize processor
        processor = UploadProcessor(config, api_handlers, file_handlers)

        # Log processing summary
        summary = processor.get_processing_summary()
        logger.info("Processing configuration:")
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")

        # Run the process
        result = processor.process()

        if result:
            logger.info("Attachment sync module completed successfully")
            return 0
        else:
            logger.error("Attachment sync module completed with errors")
            return 1

    except Exception as e:
        logger.error(f"Fatal error in attachment_sync: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
