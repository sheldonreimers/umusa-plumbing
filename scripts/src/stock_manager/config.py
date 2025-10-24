"""Config for Stock Manager script.

This module contains configuration settings for the stock/inventory management
system including date calculations, sheet IDs, form IDs, and staff filtering.
"""

import os
import pytz
from datetime import datetime, timedelta
from typing import Optional, Dict


class Config:
    """Holds configuration for Stock Manager script."""

    def __init__(self):
        """Initialize configuration with date calculations and settings."""
        # Basic metadata
        self.name = "stock_manager"
        self.version = "1.0.0"
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'

        # Determine environment
        self.environment = os.getenv('DEPLOY_ENV', 'STAGING')
        
        # Timezone configuration
        self.timezone = pytz.timezone('Africa/Johannesburg')
        self.now_date = datetime.now(self.timezone)
        
        # Date calculations
        self._calculate_dates()
        
        # ServiceM8 configuration
        self.servicem8_config = ServiceM8Config(
            form_uuid='317211c5-7ba8-4e87-ba03-ac6e73e3eda6',
            active_staff_security_role='2605a914-054a-46cc-948e-f300e516fecb'
        )
        
        # Google Sheets configuration
        self.sheets_config = SheetsConfig(
            # Primary production sheet ID
            primary_sheet_id='1_fuV4FDD8LrLgbWrgMaq_o3Cz_d7yisSYFLWust1nOw',
            # Test sheet ID for staging/development
            test_sheet_id='1_fuV4FDD8LrLgbWrgMaq_o3Cz_d7yisSYFLWust1nOw',#'1qiNp37402dQ6eO6dczUYby19WpWv-r0lzalU1fr2DgA',
            environment=self.environment
        )
        
        # Staff data columns to retrieve
        self.staff_columns = ['uuid', 'first', 'last']
        
        # Data processing configuration
        self.data_config = DataProcessingConfig()

    def _calculate_dates(self) -> None:
        """
        Calculate search_date, week_date, and tab_name based on current date/time.
        
        Logic:
        - If Monday (weekday=0): week_date is 7 days ago
        - Otherwise: week_date is start of current week (Monday)
        - If before 6 AM: search yesterday's data
        - Otherwise: search today's data
        - tab_name is week_date in YYYY-MM-DD format
        """
        if self.now_date.weekday() == 0:  # Monday
            self.week_date = self.now_date - timedelta(days=7)
            if self.now_date.hour <= 6:
                search_date = self.now_date - timedelta(days=1)
                self.search_date_str = search_date.strftime("%Y-%m-%d")
            else:
                self.search_date_str = self.now_date.strftime("%Y-%m-%d")
        else:
            days_difference = self.now_date.weekday()
            self.week_date = self.now_date - timedelta(days=days_difference)
            if self.now_date.hour <= 6:
                search_date = self.now_date - timedelta(days=1)
                self.search_date_str = search_date.strftime("%Y-%m-%d")
            else:
                self.search_date_str = self.now_date.strftime("%Y-%m-%d")
        
        # Tab name is the week start date
        self.tab_name = self.week_date.strftime("%Y-%m-%d")
        
        # Column name for the current data (yesterday's date)
        self.col_name = (self.now_date - timedelta(days=1)).strftime("%Y-%m-%d")

    def __repr__(self) -> str:
        """Return string representation of Config."""
        return (
            f"Config("
            f"name='{self.name}', "
            f"version='{self.version}', "
            f"environment='{self.environment}', "
            f"search_date='{self.search_date_str}', "
            f"tab_name='{self.tab_name}', "
            f"col_name='{self.col_name}'"
            f")"
        )


class ServiceM8Config:
    """Configuration for ServiceM8 API integration."""

    def __init__(
        self,
        form_uuid: str,
        active_staff_security_role: str
    ):
        """
        Initialize ServiceM8 configuration.
        
        Args:
            form_uuid: The UUID of the inventory form in ServiceM8.
            active_staff_security_role: The security role UUID for active staff members.
        """
        self.form_uuid = form_uuid
        self.active_staff_security_role = active_staff_security_role

    def __repr__(self) -> str:
        """Return string representation of ServiceM8Config."""
        return (
            f"ServiceM8Config("
            f"form_uuid='{self.form_uuid}', "
            f"active_staff_security_role='{self.active_staff_security_role}'"
            f")"
        )


class SheetsConfig:
    """Configuration for Google Sheets integration."""

    def __init__(
        self,
        primary_sheet_id: str,
        test_sheet_id: str,
        environment: str = 'STAGING'
    ):
        """
        Initialize Google Sheets configuration.
        
        Args:
            primary_sheet_id: The production Google Sheet ID.
            test_sheet_id: The test/staging Google Sheet ID.
            environment: The deployment environment (STAGING or PRODUCTION).
        """
        self.primary_sheet_id = primary_sheet_id
        self.test_sheet_id = test_sheet_id
        self.environment = environment
        
        # Select sheet ID based on environment
        if environment == 'PRODUCTION':
            self.active_sheet_id = primary_sheet_id
        else:
            self.active_sheet_id = test_sheet_id
        
        # Default cell configurations
        self.starting_cell = 'A1'

    def __repr__(self) -> str:
        """Return string representation of SheetsConfig."""
        return (
            f"SheetsConfig("
            f"environment='{self.environment}', "
            f"active_sheet_id='{self.active_sheet_id}'"
            f")"
        )


class DataProcessingConfig:
    """Configuration for data processing operations."""

    def __init__(self):
        """Initialize data processing configuration."""
        # Form response filtering
        self.field_type_filter = 'Number'  # Filter form responses to this field type
        
        # Staff filtering
        self.active_status_value = 1  # Value indicating active staff status
        
        # Column names used in processing
        self.response_column = 'Response'
        self.question_column = 'Question'
        self.inventory_column = 'inventory'
        self.full_name_column = 'full_name'
        self.staff_uuid_column = 'staff_uuid'
        self.uuid_column = 'uuid'
        self.security_role_uuid_column = 'security_role_uuid'
        self.active_column = 'active'
        self.first_name_column = 'first'
        self.last_name_column = 'last'
        
        # Columns to drop after merging staff with responses
        self.merge_drop_columns = [
            'staff_uuid',
            'uuid',
            'first',
            'last',
            'SortOrder'
        ]
        
        # Empty value identifier
        self.empty_value = ''
        
        # Grouping columns for aggregation
        self.groupby_columns = ['full_name', 'Question']
        
        # Sorting configuration
        self.sort_columns = ['inventory', 'full_name']
        self.sort_ascending = [True, True]
        
        # Reference columns for merging
        self.reference_columns = ['full_name', 'inventory']
        
        # Decimal separator replacement (European format)
        self.decimal_separator_from = ','
        self.decimal_separator_to = '.'

    def get_column_rename_map(self, col_name: str) -> Dict[str, str]:
        """
        Get the column rename mapping for aggregation.
        
        Args:
            col_name: The target column name for the date.
            
        Returns:
            Dictionary mapping old column names to new ones.
        """
        return {
            self.response_column: col_name,
            self.question_column: self.inventory_column
        }

    def __repr__(self) -> str:
        """Return string representation of DataProcessingConfig."""
        return (
            f"DataProcessingConfig("
            f"field_type_filter='{self.field_type_filter}', "
            f"response_column='{self.response_column}'"
            f")"
        )


# Default instance for tests and quick runs
DEFAULT_CONFIG = Config()
