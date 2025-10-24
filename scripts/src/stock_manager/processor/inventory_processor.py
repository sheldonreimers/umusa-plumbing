"""
This module defines the processor class for the Stock Manager module.

The InventoryProcessor orchestrates the complete workflow of fetching,
processing, and writing inventory data from ServiceM8 to Google Sheets.
"""

import logging
from typing import Optional

import pandas as pd

from ..config import Config
from ..handlers.api_handlers import APIHandlers
from ..handlers.data_handlers import DataHandlers


logging.basicConfig(level=logging.INFO)


class InventoryProcessor:
    """Coordinates inventory data processing and result logging via configured handlers."""

    def __init__(
        self,
        config: Config,
        api_handlers: APIHandlers,
        data_handlers: DataHandlers
    ):
        """
        Initialize InventoryProcessor with config, API, and data handlers.

        Args:
            config (Config): Configuration object containing sheet and date settings.
            api_handlers (APIHandlers): Handles external API interactions (Sheets, ServiceM8).
            data_handlers (DataHandlers): Executes queries and handles data operations.
        """
        self.config = config
        self.api_handlers = api_handlers
        self.data_handlers = data_handlers
        logging.info('InventoryProcessor initialized')

    def process(self) -> bool:
        """
        Execute the complete inventory processing workflow.
        
        This method:
        1. Fetches staff data
        2. Fetches form responses for the search date
        3. Filters and processes the responses
        4. Checks if the weekly tab exists
        5. Either creates new tab or merges with existing data
        6. Writes results to Google Sheets
        
        Returns:
            bool: True if processing completed successfully, False otherwise.
        """
        try:
            logging.info('=' * 60)
            logging.info('Starting inventory processing workflow')
            logging.info(f'Search Date: {self.config.search_date_str}')
            logging.info(f'Tab Name: {self.config.tab_name}')
            logging.info(f'Column Name: {self.config.col_name}')
            logging.info('=' * 60)

            # Step 1: Fetch staff data
            logging.info('Step 1: Fetching staff data')
            staff_df = self.data_handlers.fetch_staff_data()
            
            # Step 2: Fetch form responses for the search date
            logging.info(f'Step 2: Fetching form responses for {self.config.search_date_str}')
            form_responses = self.data_handlers.fetch_form_responses(
                self.config.search_date_str
            )
            
            # Step 3: Filter and process responses
            logging.info('Step 3: Filtering and processing form responses')
            filtered_answers = self.data_handlers.filter_form_answers(form_responses)
            
            # Create response dataframe
            response_df = self.data_handlers.create_response_dataframe(filtered_answers)
            
            # Merge staff with responses
            merged_df = self.data_handlers.merge_staff_with_responses(
                response_df,
                staff_df
            )
            
            # Clean and aggregate
            summed_df = self.data_handlers.clean_and_aggregate_responses(
                merged_df,
                self.config.col_name
            )
            
            logging.info(f'Processed {len(summed_df)} inventory records')
            
            # Step 4: Check if tab exists
            logging.info(f'Step 4: Checking if tab "{self.config.tab_name}" exists')
            current_data = self.data_handlers.fetch_current_sheet_data(
                sheet_id=self.config.sheets_config.active_sheet_id,
                tab_name=self.config.tab_name,
                starting_cell=self.config.sheets_config.starting_cell
            )
            
            # Step 5: Process based on tab existence
            if len(current_data) > 0:
                # Tab exists - merge with existing data
                logging.info('Step 5: Tab exists - merging with existing data')
                final_df = self.data_handlers.merge_with_existing_data(
                    summed_df=summed_df,
                    current_data=current_data,
                    col_name=self.config.col_name
                )
                
                # Step 6: Write merged data to existing tab
                logging.info('Step 6: Writing merged data to Google Sheets')
                self._write_to_sheet(
                    df=final_df,
                    is_new_tab=False
                )
                
            else:
                # Tab doesn't exist - create new tab
                logging.info('Step 5: Tab does not exist - creating new tab')
                self._create_new_tab()
                
                # Step 6: Write new data to new tab
                logging.info('Step 6: Writing new data to Google Sheets')
                self._write_to_sheet(
                    df=summed_df,
                    is_new_tab=True
                )
            
            logging.info('=' * 60)
            logging.info('Inventory processing completed successfully')
            logging.info('=' * 60)
            return True
            
        except Exception as e:
            logging.error(f'Error during inventory processing: {e}', exc_info=True)
            return False

    def _create_new_tab(self) -> None:
        """
        Create a new tab in the Google Sheet.
        
        Raises:
            Exception: If tab creation fails.
        """
        try:
            self.api_handlers.google_sheets.create_tab(
                sheet_id=self.config.sheets_config.active_sheet_id,
                tab_name=self.config.tab_name
            )
            logging.info(f'Successfully created tab: {self.config.tab_name}')
        except Exception as e:
            logging.error(f'Failed to create tab {self.config.tab_name}: {e}')
            raise

    def _write_to_sheet(
        self,
        df: pd.DataFrame,
        is_new_tab: bool
    ) -> None:
        """
        Write DataFrame to Google Sheets.
        
        Args:
            df: DataFrame to write.
            is_new_tab: Whether writing to a new tab (affects behavior).
            
        Raises:
            Exception: If write operation fails.
        """
        try:
            self.api_handlers.google_sheets.df_to_sheet(
                df=df,
                sheet_id=self.config.sheets_config.active_sheet_id,
                tab_name=self.config.tab_name,
                starting_cell=self.config.sheets_config.starting_cell,
                is_append=False
            )
            
            rows_written = len(df)
            cols_written = len(df.columns)
            logging.info(
                f'Successfully wrote {rows_written} rows x {cols_written} columns to '
                f'sheet "{self.config.tab_name}"'
            )
            
        except Exception as e:
            logging.error(f'Failed to write data to sheet: {e}')
            raise

    def get_processing_summary(self) -> dict:
        """
        Get a summary of the current processing configuration.
        
        Returns:
            dict: Summary of configuration and settings (excludes sensitive IDs).
        """
        return {
            'module': self.config.name,
            'version': self.config.version,
            'environment': self.config.environment,
            'search_date': self.config.search_date_str,
            'tab_name': self.config.tab_name,
            'column_name': self.config.col_name
        }

    def __repr__(self) -> str:
        """Return string representation of InventoryProcessor."""
        return (
            f"InventoryProcessor("
            f"config={self.config.name}, "
            f"environment={self.config.environment}"
            f")"
        )
