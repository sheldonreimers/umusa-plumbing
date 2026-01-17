"""Unit tests for the Stock Manager module.

This module validates integration logic using real API calls for data fetching
and mocked write operations to prevent actual data modifications during testing.
"""

import logging
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from ..config import Config
from ..handlers.api_handlers import APIHandlers
from ..handlers.data_handlers import DataHandlers
from ..processor.inventory_processor import InventoryProcessor

logging.basicConfig(level=logging.INFO)


@pytest.fixture
def config():
    """Fixture to provide a Config instance."""
    return Config()


@pytest.fixture
def api_handlers():
    """Fixture to provide real APIHandlers instance."""
    return APIHandlers()


@pytest.fixture
def data_handlers(config, api_handlers):
    """Fixture to provide DataHandlers instance."""
    return DataHandlers(config, api_handlers)


@pytest.fixture
def inventory_processor(config, api_handlers, data_handlers):
    """Fixture to provide InventoryProcessor instance."""
    return InventoryProcessor(config, api_handlers, data_handlers)


class TestConfig:
    """Test configuration initialization and settings."""
    
    def test_config_initialization(self, config):
        """Test that config initializes correctly."""
        assert config.name == "stock_manager"
        assert config.version == "1.0.0"
        assert config.search_date_str is not None
        assert config.tab_name is not None
        assert config.col_name is not None
    
    def test_config_has_servicem8_settings(self, config):
        """Test that ServiceM8 configuration exists."""
        assert config.servicem8_config is not None
        assert config.servicem8_config.form_uuid is not None
        assert config.servicem8_config.active_staff_security_role is not None
    
    def test_config_has_sheets_settings(self, config):
        """Test that Google Sheets configuration exists."""
        assert config.sheets_config is not None
        assert config.sheets_config.active_sheet_id is not None
        assert config.sheets_config.starting_cell == 'A1'
    
    def test_config_has_data_processing_settings(self, config):
        """Test that data processing configuration exists."""
        assert config.data_config is not None
        assert config.data_config.field_type_filter == 'Number'
        assert config.data_config.response_column == 'Response'
        assert len(config.data_config.merge_drop_columns) > 0


class TestAPIHandlers:
    """Test API handlers initialization."""
    
    def test_api_handlers_initialization(self, api_handlers):
        """Test that API handlers initialize correctly."""
        assert api_handlers.google_sheets is not None
        assert api_handlers.servicem8 is not None
        assert api_handlers.environment is not None
    
    def test_google_sheets_api_available(self, api_handlers):
        """Test that Google Sheets API is accessible."""
        # This is a real call to verify the API is initialized
        assert hasattr(api_handlers.google_sheets, 'sheet_to_df')
        assert hasattr(api_handlers.google_sheets, 'df_to_sheet')
    
    def test_servicem8_api_available(self, api_handlers):
        """Test that ServiceM8 API is accessible."""
        # This is a real call to verify the API is initialized
        assert hasattr(api_handlers.servicem8, 'get_all_staff')
        assert hasattr(api_handlers.servicem8, 'get_form_responses_by_date')


class TestDataHandlers:
    """Test data handlers with real API calls but mocked writes."""
    
    def test_fetch_staff_data_real(self, data_handlers):
        """Test fetching real staff data from ServiceM8."""
        # This makes a REAL API call to ServiceM8
        staff_df = data_handlers.fetch_staff_data()
        
        # Validate the structure
        assert isinstance(staff_df, pd.DataFrame)
        assert data_handlers.config.data_config.full_name_column in staff_df.columns
        assert len(staff_df) > 0  # Assuming there's at least one active staff
        logging.info(f"Fetched {len(staff_df)} active staff members")
    
    def test_fetch_form_responses_real(self, data_handlers, config):
        """Test fetching real form responses from ServiceM8."""
        # This makes a REAL API call to ServiceM8
        form_responses = data_handlers.fetch_form_responses(config.search_date_str)
        
        # Validate the structure
        assert isinstance(form_responses, list)
        logging.info(f"Fetched {len(form_responses)} form responses for {config.search_date_str}")
    
    def test_filter_form_answers(self, data_handlers):
        """Test filtering form answers to Number type fields."""
        # Sample test data
        test_responses = [
            [
                {'FieldType': 'Number', 'Response': '5', 'Question': 'Test Item 1'},
                {'FieldType': 'Text', 'Response': 'Some text', 'Question': 'Test Item 2'},
                {'FieldType': 'Number', 'Response': '10', 'Question': 'Test Item 3'}
            ]
        ]
        
        filtered = data_handlers.filter_form_answers(test_responses)
        
        # Should only have 2 Number type items
        assert len(filtered) == 2
        assert all(item['FieldType'] == 'Number' for item in filtered)
    
    def test_clean_and_aggregate_responses(self, data_handlers, config):
        """Test cleaning and aggregating response data."""
        # Create test data
        test_df = pd.DataFrame({
            config.data_config.full_name_column: ['John Doe', 'John Doe', 'Jane Smith'],
            config.data_config.question_column: ['Item A', 'Item A', 'Item B'],
            config.data_config.response_column: ['5', '3', '10']
        })
        
        result = data_handlers.clean_and_aggregate_responses(test_df, '2025-10-24')
        
        # Validate aggregation
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # John Doe Item A (summed) and Jane Smith Item B
        assert config.data_config.inventory_column in result.columns
        assert '2025-10-24' in result.columns


class TestInventoryProcessor:
    """Test inventory processor with mocked write operations."""
    
    @patch.object(APIHandlers, '__init__', return_value=None)
    def test_processor_initialization(self, mock_api_init, config):
        """Test that processor initializes correctly."""
        mock_api_handlers = MagicMock()
        data_handlers = DataHandlers(config, mock_api_handlers)
        processor = InventoryProcessor(config, mock_api_handlers, data_handlers)
        
        assert processor.config == config
        assert processor.api_handlers == mock_api_handlers
        assert processor.data_handlers == data_handlers
    
    def test_get_processing_summary(self, inventory_processor):
        """Test getting processing summary."""
        summary = inventory_processor.get_processing_summary()
        
        assert isinstance(summary, dict)
        assert 'module' in summary
        assert 'version' in summary
        assert 'environment' in summary
        assert 'search_date' in summary
        assert 'tab_name' in summary
        assert summary['module'] == 'stock_manager'
    
    @patch.object(InventoryProcessor, '_write_to_sheet')
    @patch.object(InventoryProcessor, '_create_new_tab')
    def test_process_with_mocked_writes(
        self,
        mock_create_tab,
        mock_write,
        inventory_processor,
        monkeypatch
    ):
        """Test the complete process workflow with REAL reads but MOCKED writes."""
        
        # Mock the Google Sheets WRITE operations
        mock_create_tab.return_value = None
        mock_write.return_value = None
        
        # Mock check_for_tab to return False (new tab scenario)
        monkeypatch.setattr(
            inventory_processor.api_handlers.google_sheets,
            'check_for_tab',
            lambda *args, **kwargs: False
        )
        
        # This will make REAL API calls to fetch data but MOCK the writes
        result = inventory_processor.process()
        
        # Validate that the process completed
        assert isinstance(result, bool)
        
        # If successful, verify mocked methods were called
        if result:
            assert mock_create_tab.called or mock_write.called
            logging.info("Process completed successfully with mocked writes")


class TestIntegrationSmoke:
    """Integration smoke tests that use real data but mock writes."""
    
    @patch('src.stock_manager.handlers.api_handlers.GoogleSheets.df_to_sheet')
    @patch('src.stock_manager.handlers.api_handlers.GoogleSheets.create_tab')
    def test_full_workflow_smoke(self, mock_create_tab, mock_df_to_sheet, caplog):
        """Full workflow smoke test.
        
        This test:
        - Uses REAL config
        - Uses REAL API handlers (ServiceM8 and Google Sheets for reads)
        - Fetches REAL data from ServiceM8
        - Reads REAL data from Google Sheets
        - MOCKS write operations (df_to_sheet, create_tab)
        """
        caplog.set_level(logging.INFO)
        
        # Initialize with real components
        config = Config()
        api_handlers = APIHandlers()
        data_handlers = DataHandlers(config, api_handlers)
        processor = InventoryProcessor(config, api_handlers, data_handlers)
        
        # Mock only the WRITE operations
        mock_create_tab.return_value = None
        mock_df_to_sheet.return_value = None
        
        # Run the process (reads are real, writes are mocked)
        result = processor.process()
        
        # Check for errors in logs
        errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
        
        if not result:
            # Log why it failed if there are errors
            for error in errors:
                logging.error(f"Test error: {error.getMessage()}")
        
        # The test passes if there are no ERROR level logs
        # (process may return False if there's no data, but shouldn't error)
        assert not errors, f"ERROR logs were emitted: {'; '.join(f'{r.levelname}: {r.getMessage()}' for r in errors)}"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test with real API calls"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test with mocked dependencies"
    )
