"""
Entry point for running the Stock Manager script.

Initializes configuration, handlers, and runs the main process for the
Stock Manager module to track inventory from ServiceM8 forms and write
to Google Sheets.
"""

import logging
import sys
from datetime import datetime

# Project-specific imports
from .config import Config
from .handlers.api_handlers import APIHandlers
from .handlers.data_handlers import DataHandlers
from .processor.inventory_processor import InventoryProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def main():
    """Run the Stock Manager module's main process."""
    start_time = datetime.now()
    
    try:
        logging.info('=' * 80)
        logging.info('STOCK MANAGER - Starting execution')
        logging.info('=' * 80)
        
        # Initialize configuration
        logging.info('Initializing configuration...')
        config = Config()
        logging.info(f'Configuration: {config}')
        
        # Initialize API handlers
        logging.info('Initializing API handlers...')
        api_handlers = APIHandlers()
        logging.info(f'API Handlers: {api_handlers}')
        
        # Initialize data handlers
        logging.info('Initializing data handlers...')
        data_handlers = DataHandlers(config, api_handlers)
        logging.info(f'Data Handlers: {data_handlers}')
        
        # Initialize inventory processor
        logging.info('Initializing inventory processor...')
        inventory_processor = InventoryProcessor(config, api_handlers, data_handlers)
        logging.info(f'Inventory Processor: {inventory_processor}')
        
        # Display processing summary
        summary = inventory_processor.get_processing_summary()
        logging.info('Processing Summary:')
        for key, value in summary.items():
            logging.info(f'  {key}: {value}')
        
        # Run the inventory processing workflow
        logging.info('Starting inventory processing workflow...')
        success = inventory_processor.process()
        
        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        if success:
            logging.info('=' * 80)
            logging.info(f'STOCK MANAGER - Completed successfully in {execution_time:.2f} seconds')
            logging.info('=' * 80)
            sys.exit(0)
        else:
            logging.error('=' * 80)
            logging.error(f'STOCK MANAGER - Failed after {execution_time:.2f} seconds')
            logging.error('=' * 80)
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.warning('Process interrupted by user')
        sys.exit(130)
        
    except Exception as e:
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        logging.error('=' * 80)
        logging.error(f'STOCK MANAGER - Fatal error after {execution_time:.2f} seconds')
        logging.error(f'Error: {e}', exc_info=True)
        logging.error('=' * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
