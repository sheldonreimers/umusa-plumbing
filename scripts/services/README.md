# services Directory

This package contains shared configuration modules and API client wrappers used throughout the Data Analytics Automations project. Each module encapsulates logic for interacting with an external service or providing common utilities.

## Contents

| Module/File             | Description                                                                                       |
|------------------------- |--------------------------------------------------------------------------------------------------|
| `__init__.py`            | Marks this directory as a Python package.                                                         |
| `requirements.txt`       | Lists Python dependencies required by these modules.                                              |
| **API Clients & Utilities** |                                                                                                  |
| `SecretManager.py`       | Fetches secrets from Google Cloud Secret Manager or environment variables via `SecretManager`.    |
| `Logger.py`              | Provides a standardized logger via `get_logger(name: str)`.                                       |
| `GoogleDrive.py`         | Wrapper around Google Drive API: list, download, and upload file operations.                      |
| `GoogleSheets.py`        | Wrapper around Google Sheets API: read, write, and append sheet data.                             |
| `dbtAPI.py`              | Interfaces with DBT Cloud REST API: trigger jobs and fetch job statuses using `dbtAPI`.          |

## Installation

Install dependencies:

```bash
pip install -r services/requirements.txt
```

## Configuration & Usage

Before using any client, ensure credentials are available via environment variables or Google Secret Manager:

| Service      | Env Var / Secret Name             |
|------------- |-----------------------------------|
| Google APIs  | `GOOGLE_APPLICATION_CREDENTIALS`  |
| DBT Cloud    | `DBT_CLOUD_TOKEN`                 |

Clients fetch credentials via:

```python
from services.SecretManager import SecretManager
sm = SecretManager()
token = sm.get_secret("DBT_CLOUD_TOKEN")
```

Instantiate clients as needed:

```python
from services.GoogleSheets import GoogleSheets
sheets = GoogleSheets()
data = sheets.read_sheet(SPREADSHEET_ID, "Sheet1!A1:D10")
```

