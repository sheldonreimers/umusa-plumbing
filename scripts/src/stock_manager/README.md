# 🚀 Stock Manager - Automated Inventory Tracking from ServiceM8 to Google Sheets

The Stock Manager module automates the daily collection and aggregation of inventory data from ServiceM8 field service forms, processing staff submissions, and maintaining historical records in Google Sheets. This system eliminates manual data entry, ensures accurate inventory tracking, and provides weekly consolidated views of stock levels across the organization.

---

## 📁 Directory Structure

```
stock_manager/
├── __init__.py                 # Module initialization
├── config.py                   # Configuration management (dates, sheet IDs, settings)
├── main.py                     # Entry point for script execution
├── handlers/
│   ├── __init__.py            # Handlers package initialization
│   ├── api_handlers.py        # API client initialization (GoogleSheets, ServiceM8)
│   └── data_handlers.py       # Data fetching and transformation logic
├── processor/
│   ├── __init__.py            # Processor package initialization
│   └── inventory_processor.py # Business logic orchestration
└── tests/
    ├── __init__.py            # Tests package initialization
    └── test_stock_manager.py  # Pytest suite with real reads + mocked writes
```

---

## 🛠️ Module Overview

### Purpose
The Stock Manager automates daily inventory tracking by:
1. Fetching form responses from ServiceM8 where field staff record inventory usage
2. Aggregating inventory counts by staff member and item type
3. Merging daily data with existing weekly records in Google Sheets
4. Creating new weekly tabs or updating existing ones based on date logic

This replaces manual spreadsheet updates and ensures all inventory movements are tracked accurately with minimal human intervention.

### Key Components
| Component | Purpose | Dependencies |
|-----------|---------|--------------|
| `config.py` | Manages all configuration including date calculations, sheet IDs, and processing rules | pytz, datetime |
| `api_handlers.py` | Initializes Google Sheets and ServiceM8 API clients with environment-aware secrets | services.GoogleSheets, services.ServiceM8 |
| `data_handlers.py` | Fetches, filters, merges, and aggregates inventory data | pandas, logging |
| `inventory_processor.py` | Orchestrates the complete workflow from data fetch to sheet write | All handlers |
| `main.py` | Entry point with logging, error handling, and execution flow | All modules |
| `test_stock_manager.py` | Comprehensive test suite with real API calls and mocked writes | pytest, unittest.mock |

### Integration Points
- **Input Sources**: 
  - ServiceM8 API (form responses, staff data)
  - Google Sheets (existing weekly data for merging)
- **Output Destinations**: 
  - Google Sheets (weekly inventory tabs)
- **External APIs**: 
  - ServiceM8 field service management platform
  - Google Sheets API
- **Secret Management**: 
  - GitHub Secrets (via SecretManager for API credentials)

---

## 🧑‍💻 Setup & Installation

### Prerequisites
```bash
# Python 3.8+ required
python --version

# Install required packages
pip install pandas pytz google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests retry pillow pymupdf pytest
```

### Environment Configuration
```bash
# Set deployment environment (affects which secrets are used)
export DEPLOY_ENV=STAGING  # or PRODUCTION

# Optional: Enable debug mode
export DEBUG=True
```

### Required Secrets/Variables
| Variable | Purpose | Example | Storage Location |
|----------|---------|---------|------------------|
| `GOOGLE_SECRET` | Google Sheets API credentials (staging) | `{"type": "service_account", ...}` | GitHub Secrets |
| `GOOGLE_GITHUB_SECRET` | Google Sheets API credentials (production) | `{"type": "service_account", ...}` | GitHub Secrets |
| `SERVICEM8_SECRET` | ServiceM8 API key (staging) | `Basic abc123...` | GitHub Secrets |
| `SERVICEM8_GITHUB_SECRET` | ServiceM8 API key (production) | `Basic xyz789...` | GitHub Secrets |
| `DEPLOY_ENV` | Environment selector | `STAGING` or `PRODUCTION` | Environment Variable |

### File Path Configuration
The module uses these configurable settings in `config.py`:

**ServiceM8 Settings:**
- Form UUID: `317211c5-7ba8-4e87-ba03-ac6e73e3eda6` (inventory form)
- Active Staff Security Role: `2605a914-054a-46cc-948e-f300e516fecb`

**Google Sheets Settings:**
- Production Sheet: `1_fuV4FDD8LrLgbWrgMaq_o3Cz_d7yisSYFLWust1nOw`
- Test Sheet: `1qiNp37402dQ6eO6dczUYby19WpWv-r0lzalU1fr2DgA`
- Auto-selected based on `DEPLOY_ENV`

---

## ⚡ Usage

### Running the Module

**From command line:**
```bash
# Navigate to the stock_manager directory
cd /home/Umusa/scripts/src/stock_manager

# Run the module
python -m stock_manager.main

# Or run main.py directly
python main.py
```

**With environment variables:**
```bash
# Run in production mode
DEPLOY_ENV=PRODUCTION python -m stock_manager.main

# Run with debug logging
DEBUG=True python -m stock_manager.main
```

**In a GitHub Actions workflow:**
```yaml
- name: Run Stock Manager
  env:
    DEPLOY_ENV: PRODUCTION
    GOOGLE_GITHUB_SECRET: ${{ secrets.GOOGLE_GITHUB_SECRET }}
    SERVICEM8_GITHUB_SECRET: ${{ secrets.SERVICEM8_GITHUB_SECRET }}
  run: |
    cd scripts/src/stock_manager
    python main.py
```

### Configuration Options

**Date Logic (automatic):**
- **Monday before 6 AM**: Searches previous day, uses week starting 7 days ago
- **Monday after 6 AM**: Searches today, uses week starting 7 days ago
- **Other days before 6 AM**: Searches previous day, uses current week start
- **Other days after 6 AM**: Searches today, uses current week start

**Timezone:**
- All date calculations use `Africa/Johannesburg` timezone
- Configured in `config.py` via `pytz.timezone()`

**Data Processing:**
- Form responses filtered to `Number` type fields only
- Decimal separator conversion: `,` → `.` (European format support)
- Empty responses filtered out before aggregation
- Data grouped by: `full_name` + `inventory item`

### Expected Outputs

**Successful Execution:**
```
2025-10-24 14:30:00 - INFO - ================================================================================
2025-10-24 14:30:00 - INFO - STOCK MANAGER - Starting execution
2025-10-24 14:30:00 - INFO - ================================================================================
...
2025-10-24 14:30:45 - INFO - Successfully wrote 150 rows x 8 columns to sheet "2025-10-21"
2025-10-24 14:30:45 - INFO - ================================================================================
2025-10-24 14:30:45 - INFO - STOCK MANAGER - Completed successfully in 45.32 seconds
2025-10-24 14:30:45 - INFO - ================================================================================
```

**Google Sheets Output:**
- New tab created with name format: `YYYY-MM-DD` (week start date)
- Columns: `full_name`, `inventory`, `[daily date columns]`
- Daily data accumulated throughout the week
- Existing data preserved and merged with new submissions

---

## 🔧 Testing

### Running Tests

**All tests (requires API credentials):**
```bash
# From repository root with proper PYTHONPATH
cd /home/Umusa/scripts
PYTHONPATH=/home/Umusa/scripts pytest src/stock_manager/tests/

# Or from scripts directory
cd scripts
PYTHONPATH=$(pwd) pytest src/stock_manager/tests/
```

**Configuration tests only (no credentials needed):**
```bash
cd /home/Umusa/scripts
PYTHONPATH=/home/Umusa/scripts pytest src/stock_manager/tests/test_stock_manager.py::TestConfig -v
```

**Verbose output with logging:**
```bash
cd /home/Umusa/scripts
PYTHONPATH=/home/Umusa/scripts pytest -v -s src/stock_manager/tests/
```

**Specific test classes:**
```bash
# Configuration tests only
PYTHONPATH=/home/Umusa/scripts pytest src/stock_manager/tests/test_stock_manager.py::TestConfig

# Integration smoke test (requires credentials)
PYTHONPATH=/home/Umusa/scripts pytest src/stock_manager/tests/test_stock_manager.py::TestIntegrationSmoke

# Data handlers with real API calls (requires credentials)
PYTHONPATH=/home/Umusa/scripts pytest src/stock_manager/tests/test_stock_manager.py::TestDataHandlers
```

**Important:** Tests that interact with APIs require proper credentials configured. See [Required Secrets/Variables](#required-secretsvariables) section.

### Test Coverage

**What is Tested:**
- ✅ Configuration initialization and date calculations
- ✅ API handler initialization (real clients)
- ✅ **Real ServiceM8 API calls** (staff data, form responses)
- ✅ **Real Google Sheets API calls** (reading existing data)
- ✅ Data filtering, merging, and aggregation logic
- ✅ Complete workflow orchestration

**What is Mocked:**
- 🔇 Google Sheets write operations (`df_to_sheet`, `create_tab`)
- 🔇 No actual data modification during tests

**Test Strategy:**
The test suite uses **real production API calls** for data fetching to ensure accuracy, but **mocks all write operations** to prevent accidental data modification. This approach validates the complete workflow with real-world data while maintaining safety.

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'services'` | Python path not including parent directory | Run from `scripts/src/stock_manager/` or add parent to `PYTHONPATH` |
| `KeyError: 'GOOGLE_SECRET'` | Secret not found in environment | Verify secret exists in GitHub Secrets and environment variable is set |
| `401 Unauthorized` from ServiceM8 | Invalid or expired API key | Check `SERVICEM8_SECRET` is correct and base64 encoded |
| `Empty DataFrame returned` | No form responses for search date | Check date logic - may be searching wrong date due to timezone |
| `Tab already exists` error | Attempting to create duplicate tab | Normal - code should handle this, check logs for actual error |
| Import error for `services.GoogleSheets` | Services directory not in path | Ensure running from correct directory or adjust imports |

### Debugging

**Enable verbose logging:**
```python
# In main.py or any module
logging.basicConfig(level=logging.DEBUG)
```

**Check configuration values:**
```python
from stock_manager.config import Config
config = Config()
print(config)
print(f"Search Date: {config.search_date_str}")
print(f"Tab Name: {config.tab_name}")
print(f"Active Sheet: {config.sheets_config.active_sheet_id}")
```

**Verify API connectivity:**
```python
from stock_manager.handlers.api_handlers import APIHandlers
api = APIHandlers()
staff = api.servicem8.get_all_staff()
print(f"Retrieved {len(staff)} staff members")
```

**Log Locations:**
- Console output (stdout/stderr)
- GitHub Actions workflow logs (if running in CI/CD)

### Performance Monitoring

**Expected Execution Times:**
- Staff data fetch: 2-5 seconds
- Form responses fetch: 3-10 seconds (depends on volume)
- Data processing: 1-2 seconds
- Sheet write: 2-5 seconds
- **Total**: 30-60 seconds typical

**Performance Issues:**
- If > 2 minutes: Check network connectivity to APIs
- If repeated failures: Check API rate limits
- If memory errors: Check DataFrame sizes (large date ranges)

---

## 📋 Maintenance & Handover

### Regular Maintenance Tasks
- **Weekly**: Review logs for successful execution
- **Monthly**: Verify sheet data accuracy vs ServiceM8 source
- **Quarterly**: Review and update test data if ServiceM8 form changes
- **As needed**: Update sheet IDs if new tracking sheets are created

### Code Architecture Notes

**Separation of Concerns:**
1. **Config** - All configurable values (no code changes for settings)
2. **API Handlers** - Pure API client initialization
3. **Data Handlers** - Stateless data transformation functions
4. **Processor** - Workflow orchestration (uses handlers)
5. **Main** - Entry point and error handling

**Key Design Decisions:**
- **Configuration-driven**: All hard-coded values moved to `config.py` to allow updates without code changes
- **Environment-aware**: Automatic secret selection based on `DEPLOY_ENV`
- **Timezone-aware**: South Africa timezone for date calculations
- **Idempotent**: Running multiple times same day won't duplicate data (merge logic)
- **Fail-safe**: Errors logged but don't corrupt existing data

**Date Calculation Logic:**
The module uses complex date logic to determine:
- `search_date_str`: Which date's form responses to fetch
- `tab_name`: Which weekly tab to write to
- `col_name`: Which column to update with today's data

This ensures data is organized by week starting Monday, with proper handling of early morning runs (before 6 AM).

### Business Impact

**If this module fails:**
- ❌ Daily inventory tracking is not updated
- ❌ Staff cannot see current stock levels
- ❌ Weekly reports will be incomplete
- ❌ Manual data entry required (time-consuming, error-prone)

**Critical Success Factors:**
- ✅ Runs daily (automated via GitHub Actions or cron)
- ✅ ServiceM8 form responses submitted by staff
- ✅ API credentials remain valid
- ✅ Google Sheet permissions maintained

**Recovery Time Objective (RTO):**
- Module can be re-run for missed days
- Historical data preserved in ServiceM8
- Maximum 24 hours acceptable gap

### Escalation Path

**Issue Type: Configuration/Settings**
- Update `config.py` values
- No deployment needed for sheet IDs or UUIDs

**Issue Type: API Credentials**
- Contact: Platform administrator
- Update GitHub Secrets
- Re-run workflow

**Issue Type: Data Accuracy**
- Verify ServiceM8 source data first
- Check data processing logic in `data_handlers.py`
- Review merge logic in `merge_with_existing_data()`

**Issue Type: Code Bugs**
- Check GitHub Issues for known problems
- Review logs for stack traces
- Run tests: `pytest -v scripts/src/stock_manager/tests/`
- Create detailed bug report with logs

**Emergency Contact:**
- Primary: Development team lead
- Secondary: Operations team
- Escalation: Platform owner

---

## 📊 Dependencies & Integration

### External Dependencies

**ServiceM8 API:**
- Purpose: Field service management platform
- Used for: Form responses, staff data
- Authentication: Basic auth with API key
- Documentation: https://developer.servicem8.com/
- Rate Limits: Check with ServiceM8 documentation

**Google Sheets API:**
- Purpose: Spreadsheet storage and reporting
- Used for: Reading existing data, writing aggregated results
- Authentication: Service account OAuth2
- Documentation: https://developers.google.com/sheets/api
- Rate Limits: 100 requests per 100 seconds per user

**Python Packages:**
- `pandas`: Data manipulation and aggregation
- `pytz`: Timezone handling (Africa/Johannesburg)
- `google-api-python-client`: Google Sheets API client
- `requests`: HTTP client for ServiceM8
- `retry`: Automatic retry logic for API calls
- `pytest`: Testing framework

### Internal Dependencies

**Services Module:**
- `services.GoogleSheets`: Google Sheets service wrapper
- `services.ServiceM8`: ServiceM8 API wrapper
- `services.SecretManager`: GitHub secrets retrieval

**Configuration Files:**
- None - all configuration in `config.py` code

**Shared Resources:**
- Google Sheets: `1_fuV4FDD8LrLgbWrgMaq_o3Cz_d7yisSYFLWust1nOw` (production)
- ServiceM8 form: `317211c5-7ba8-4e87-ba03-ac6e73e3eda6`

### Downstream Impact

**Systems Depending on This Module:**
- Weekly inventory reports (read from generated sheets)
- Stock level dashboards (visualization of historical data)
- Procurement planning (uses aggregated trends)

**Data Consumers:**
- Management reporting
- Operations team for stock reordering
- Field staff for inventory visibility

**Integration Pattern:**
- **Push model**: This module writes to Google Sheets
- **Pull model**: Downstream systems read from sheets
- **Frequency**: Daily updates, weekly aggregation

---

## 🎯 Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] GitHub Secrets configured (GOOGLE_SECRET, SERVICEM8_SECRET)
- [ ] DEPLOY_ENV set appropriately
- [ ] Test run successful: `pytest scripts/src/stock_manager/tests/`
- [ ] Manual run successful: `python main.py`
- [ ] Verify output in Google Sheets
- [ ] Schedule in GitHub Actions workflow
- [ ] Monitor first week of automated runs
- [ ] Document any environment-specific settings

---

## 📝 Version History

**v1.0.0** (2025-10-24)
- Initial modular architecture migration
- Migrated from monolithic `inventory_v2.py`
- Added comprehensive test suite
- Configuration-driven design
- Environment-aware secret management
- GitHub Actions ready

---

## 🔗 Related Documentation

- [Script Template README](../script_template/README.md) - Template structure this follows
- [Services Documentation](../../services/README.md) - Shared API services
- ServiceM8 API Documentation
- Google Sheets API Documentation

---

**Maintained by**: Development Team  
**Last Updated**: October 24, 2025  
**Module Version**: 1.0.0
