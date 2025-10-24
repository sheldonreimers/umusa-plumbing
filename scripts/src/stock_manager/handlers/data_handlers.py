"""
This module contains the DataHandlers class.

It handles operations related to processing Stock Manager data including
fetching staff, form responses, and performing data transformations.
"""

import logging
from typing import List, Dict, Any

import pandas as pd

from ..config import Config
from ..handlers.api_handlers import APIHandlers


class DataHandlers:
    """Handles Stock Manager data operations."""

    def __init__(self, config: Config, api_handlers: APIHandlers):
        """Initialize the DataHandlers class with config and API handlers.

        Args:
            config (Config): Configuration object with date settings.
            api_handlers (APIHandlers): Interface to external APIs.
        """
        self.config = config
        self.api_handlers = api_handlers
        logging.info('DataHandlers initialized')

    def fetch_staff_data(self) -> pd.DataFrame:
        """
        Fetch all staff data from ServiceM8 and filter to active staff.

        Returns:
            DataFrame with active staff members including uuid, first, last, and full_name.
        """
        logging.info('Fetching staff data from ServiceM8')
        
        # Get all staff from ServiceM8
        staff_data = self.api_handlers.servicem8.get_all_staff()
        staff_df = pd.DataFrame(staff_data)
        
        # Filter to active staff with specific security role
        active_staff = staff_df[
            (staff_df[self.config.data_config.security_role_uuid_column] == self.config.servicem8_config.active_staff_security_role) &
            (staff_df[self.config.data_config.active_column] == self.config.data_config.active_status_value)
        ].reset_index(drop=True)[self.config.staff_columns]
        
        # Create full_name column
        active_staff[self.config.data_config.full_name_column] = (
            active_staff[self.config.data_config.first_name_column] + ' ' + 
            active_staff[self.config.data_config.last_name_column]
        )
        
        logging.info(f'Found {len(active_staff)} active staff members')
        return active_staff

    def fetch_form_responses(self, search_date: str) -> List[List[Dict]]:
        """
        Fetch form responses from ServiceM8 for a specific date.

        Args:
            search_date: The date to search for form responses (YYYY-MM-DD format).

        Returns:
            List of form response lists.
        """
        logging.info(f'Fetching form responses for date: {search_date}')
        
        form_responses = self.api_handlers.servicem8.get_form_responses_by_date(
            form_uuid=self.config.servicem8_config.form_uuid,
            response_date=search_date
        )
        
        logging.info(f'Retrieved {len(form_responses)} form responses')
        return form_responses

    def filter_form_answers(self, form_responses: List[List[Dict]]) -> List[Dict]:
        """
        Filter form responses to only include Number type fields.

        Args:
            form_responses: List of form response lists from ServiceM8.

        Returns:
            Flattened list of answers that are Number type fields.
        """
        logging.info('Filtering form answers to Number type fields')
        
        filtered_answers = []
        for response in form_responses:
            filtered_items = []
            for item in response:
                if item.get('FieldType') == self.config.data_config.field_type_filter:
                    filtered_items.append(item)
            filtered_answers.append(filtered_items)
        
        # Flatten the list
        flattened_answers = [item for sublist in filtered_answers for item in sublist]
        
        logging.info(f'Filtered to {len(flattened_answers)} number field answers')
        return flattened_answers

    def create_response_dataframe(self, filtered_answers: List[Dict]) -> pd.DataFrame:
        """
        Convert filtered answers to a DataFrame.

        Args:
            filtered_answers: List of filtered form answer dictionaries.

        Returns:
            DataFrame with form response data.
        """
        logging.info('Creating response DataFrame')
        response_df = pd.DataFrame(filtered_answers)
        return response_df

    def merge_staff_with_responses(
        self,
        response_df: pd.DataFrame,
        staff_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Merge response data with staff data and clean up columns.

        Args:
            response_df: DataFrame with form responses.
            staff_df: DataFrame with staff information.

        Returns:
            Merged DataFrame with staff and response data.
        """
        logging.info('Merging staff data with responses')
        
        merged_df = response_df.merge(
            staff_df,
            how='left',
            left_on=self.config.data_config.staff_uuid_column,
            right_on='uuid'
        ).drop(
            labels=self.config.data_config.merge_drop_columns,
            axis=1
        )
        
        return merged_df

    def clean_and_aggregate_responses(
        self,
        merged_df: pd.DataFrame,
        col_name: str
    ) -> pd.DataFrame:
        """
        Clean response data and aggregate by staff and question.

        Args:
            merged_df: Merged DataFrame with staff and response data.
            col_name: The column name for the aggregated response date.

        Returns:
            Aggregated DataFrame grouped by full_name and Question.
        """
        logging.info('Cleaning and aggregating response data')
        
        # Replace commas with periods (European decimal notation)
        merged_df[self.config.data_config.response_column] = merged_df[
            self.config.data_config.response_column
        ].str.replace(
            self.config.data_config.decimal_separator_from,
            self.config.data_config.decimal_separator_to
        )
        
        # Filter out empty responses and convert to float
        filtered_df = merged_df[
            merged_df[self.config.data_config.response_column] != self.config.data_config.empty_value
        ].astype({self.config.data_config.response_column: float})
        
        # Group by full_name and Question, summing the Response values
        summed_df = filtered_df.groupby(
            self.config.data_config.groupby_columns
        )[self.config.data_config.response_column].sum().reset_index().rename(
            columns=self.config.data_config.get_column_rename_map(col_name)
        ).sort_values(
            by=self.config.data_config.sort_columns,
            ascending=self.config.data_config.sort_ascending
        )
        
        logging.info(f'Aggregated data: {len(summed_df)} rows')
        return summed_df

    def fetch_current_sheet_data(
        self,
        sheet_id: str,
        tab_name: str,
        starting_cell: str
    ) -> pd.DataFrame:
        """
        Fetch current data from Google Sheet tab.

        Args:
            sheet_id: The Google Sheet ID.
            tab_name: The tab name to read from.
            starting_cell: The starting cell for reading.

        Returns:
            DataFrame with current sheet data, or empty DataFrame if tab doesn't exist.
        """
        logging.info(f'Fetching current sheet data from tab: {tab_name}')
        
        # Check if tab exists
        tab_exists = self.api_handlers.google_sheets.check_for_tab(sheet_id, tab_name)
        
        if not tab_exists:
            logging.info(f'Tab {tab_name} does not exist')
            return pd.DataFrame()
        
        # Get the last column
        ending_cell = self.api_handlers.google_sheets.get_last_column(
            sheet_id=sheet_id,
            tab_name=tab_name,
            starting_cell=starting_cell
        )
        
        # Fetch data from sheet
        current_data = self.api_handlers.google_sheets.sheet_to_df(
            sheet_id=sheet_id,
            tab_name=tab_name,
            starting_cell=starting_cell,
            ending_cell=ending_cell
        )
        
        logging.info(f'Fetched {len(current_data)} rows from sheet')
        return current_data

    def merge_with_existing_data(
        self,
        summed_df: pd.DataFrame,
        current_data: pd.DataFrame,
        col_name: str
    ) -> pd.DataFrame:
        """
        Merge new summed data with existing sheet data.

        Args:
            summed_df: New aggregated data.
            current_data: Existing data from the sheet.
            col_name: The column name for the new data.

        Returns:
            Final merged DataFrame.
        """
        logging.info('Merging new data with existing sheet data')
        
        # Create reference dataframe with all unique combinations
        ref_df = pd.concat(
            [
                summed_df[self.config.data_config.reference_columns],
                current_data[self.config.data_config.reference_columns]
            ],
            ignore_index=True
        ).drop_duplicates(ignore_index=True)
        
        # Merge with current data - only include col_name if it exists
        if col_name in current_data.columns:
            merge_columns = self.config.data_config.reference_columns + [col_name]
        else:
            merge_columns = self.config.data_config.reference_columns
            
        sum_merged = ref_df.merge(
            current_data[merge_columns],
            how='left',
            on=self.config.data_config.reference_columns
        ).merge(
            summed_df,
            how='left',
            on=self.config.data_config.reference_columns
        ).fillna(0)
        
        # Handle column merging - check if columns exist before type conversion
        if col_name + '_x' in sum_merged.columns and col_name + '_y' in sum_merged.columns:
            # Both columns exist - sum them
            sum_merged = sum_merged.astype({
                col_name + '_x': float,
                col_name + '_y': float
            })
            sum_merged[col_name] = sum_merged[col_name + '_x'] + sum_merged[col_name + '_y']
            sum_completed = sum_merged.drop(labels=[col_name + '_x', col_name + '_y'], axis=1)
        elif col_name + '_x' in sum_merged.columns:
            # Only current data has the column
            sum_merged = sum_merged.astype({col_name + '_x': float})
            sum_completed = sum_merged.rename(columns={col_name + '_x': col_name})
        elif col_name + '_y' in sum_merged.columns:
            # Only new data has the column
            sum_merged = sum_merged.astype({col_name + '_y': float})
            sum_completed = sum_merged.rename(columns={col_name + '_y': col_name})
        else:
            # Neither has the column (shouldn't happen, but handle gracefully)
            sum_completed = sum_merged
        
        # Merge back with all current data columns
        final_df = current_data.merge(
            sum_completed,
            how='left',
            on=self.config.data_config.reference_columns,
            suffixes=('_cur', '')
        )
        
        # Drop the old column version if it exists
        if col_name + '_cur' in final_df.columns:
            final_df = final_df.drop(labels=col_name + '_cur', axis=1)
        
        logging.info(f'Final merged data: {len(final_df)} rows')
        return final_df

    def __repr__(self) -> str:
        """Return string representation of DataHandlers."""
        return f"DataHandlers(config={self.config.name})"
