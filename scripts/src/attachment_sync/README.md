# Attachment Sync Module

Automated sync of ServiceM8 attachments (photos, videos, PDFs) to OneDrive folder structure.

## Overview

The Attachment Sync module monitors ServiceM8 for new attachments and automatically uploads them to a structured OneDrive folder hierarchy. Each job gets its own folder with subfolders for different file types (PDFs, photos, videos).

## Features

- **Incremental Sync**: Only processes attachments created since the last run
- **Organized Structure**: Automatically creates folder hierarchy by job
- **File Type Sorting**: Separates PDFs, photos, and videos into dedicated folders
- **Smart Naming**: Sanitizes folder and file names for OneDrive compatibility
- **Error Handling**: Continues processing even if individual uploads fail
- **Timestamp Tracking**: Records last successful upload for incremental syncing

## Architecture

```
attachment_sync/
├── config.py              # Configuration management
├── main.py                # Entry point
├── handlers/
│   ├── api_handlers.py    # API client initialization
│   └── file_handlers.py   # File operations and uploads
└── processor/
    └── upload_processor.py # Workflow orchestration
```

## Configuration

### Environment Variables

- `DEPLOY_ENV`: Deployment environment (`STAGING` or `PRODUCTION`)
- Secrets are managed automatically via `SecretManager`

### Secrets Required

1. **UMUSA_GOOGLE**: Google Sheets API credentials (for potential future use)
2. **UMUSA_SERVICEM8**: ServiceM8 API credentials
   ```json
   {
     "authorization": "Basic <base64_encoded_credentials>",
     "app_id": "<app_id>",
     "app_secret": "<app_secret>"
   }
   ```
3. **UMUSA_AZURE**: Azure/OneDrive credentials
   ```json
   {
     "tenant_id": "<tenant_id>",
     "client_id": "<client_id>",
     "client_secret": "<client_secret>",
     "redirect_uri": "<redirect_uri>",
     "auth_code": "<auth_code>",
     "refresh_token": "<refresh_token>"
   }
   ```

### File Locations

- **Last Run Tracking**: `config/last_run.json` (stores timestamp of last successful run)

## OneDrive Folder Structure

```
ServiceM8 Attachments/
└── #<JOB_ID>; <CUSTOMER_NAME>/
    ├── pdfs/          # PDF attachments
    ├── photos/        # JPEG/PNG images
    └── videos/        # MP4 videos
```

## Workflow

1. **Load Last Run**: Read timestamp from `last_run.json`
2. **Fetch Attachments**: Get all ServiceM8 attachments created after last run
3. **Group by Job**: Organize attachments by related job UUID
4. **Process Each Job**:
   - Fetch job details from ServiceM8
   - Skip unsuccessful jobs or jobs without customers
   - Get customer details
   - Create/find OneDrive folder structure
   - Upload files to appropriate subfolders
5. **Update Timestamp**: Save the latest attachment edit date to `last_run.json`

## Job Filtering

Jobs are skipped if:
- Status is "Unsuccessful"
- Job ID ends with a letter (indicates subproject)
- No customer associated with the job

## File Type Handling

Supported file types:
- **PDFs**: `.pdf` → uploaded to `pdfs/` subfolder
- **Videos**: `.mp4` → uploaded to `videos/` subfolder
- **Photos**: `.jpg`, `.jpeg`, `.png` → uploaded to `photos/` subfolder

Files are renamed using the pattern: `<timestamp>.<extension>`
- Special characters are sanitized (spaces → underscores, colons → hyphens)

## Usage

### Run as Module
```bash
cd /path/to/scripts
PYTHONPATH=/path/to/scripts python -m attachment_sync.main
```

### Import in Python
```python
from attachment_sync import Config, main

# Run with default configuration
main()

# Or use custom configuration
config = Config(
    environment='PRODUCTION',
    last_run_path='/custom/path/last_run.json'
)
```

## Logging

The module uses Python's built-in logging with the following levels:
- **INFO**: Normal workflow progress
- **WARNING**: Skipped jobs, unknown file types
- **ERROR**: Upload failures, API errors

Log format: `LEVEL    MODULE      : filename:line message`

## Error Handling

The module is designed to be resilient:
- Failed job fetches are logged and skipped
- Failed customer lookups are logged and skipped
- Failed file uploads are logged but don't stop the workflow
- Missing folder structures are created automatically
- If no new attachments exist, timestamp is updated to current time

## Dependencies

- `pandas`: Data manipulation
- `pytz`: Timezone handling
- `requests`: HTTP operations (via OneDrive service)
- `retry`: Retry logic for folder creation
- **Services**: GoogleSheets, ServiceM8, OneDrive

## Testing

### Manual Testing
```bash
# Test with STAGING environment
cd /home/Umusa/scripts
PYTHONPATH=/home/Umusa/scripts DEPLOY_ENV=STAGING python -m attachment_sync.main
```

### Verify Results
1. Check logs for processing summary
2. Verify `config/last_run.json` updated
3. Check OneDrive folder structure created
4. Confirm files uploaded to correct subfolders

## Configuration Details

### FileTypeConfig
- `extensions`: Tuple of supported file extensions
- `pdf_folder_name`: Name for PDF subfolder (default: "pdfs")
- `photo_folder_name`: Name for photo subfolder (default: "photos")
- `video_folder_name`: Name for video subfolder (default: "videos")

### OneDriveConfig
- `servicem8_attachments_folder`: Root folder ID in OneDrive
  - Default: `'4B4564E48AE9C501!523357'`

### ServiceM8Config
- `skip_statuses`: List of job statuses to skip
  - Default: `['Unsuccessful']`

## Troubleshooting

### No attachments processed
- Check `last_run.json` timestamp - may be too recent
- Verify ServiceM8 API credentials
- Confirm attachments exist in ServiceM8 for the date range

### OneDrive upload failures
- Verify Azure credentials and refresh token
- Check OneDrive folder permissions
- Ensure folder ID is correct

### Missing customer data
- Verify job has associated customer in ServiceM8
- Check customer UUID is valid

## Future Enhancements

- [ ] Add retry logic for failed uploads
- [ ] Support additional file types
- [ ] Add duplicate file detection
- [ ] Implement file size limits
- [ ] Add email notifications for failures
- [ ] Support multiple root folders
- [ ] Add dry-run mode for testing

## License

Proprietary - Internal use only. See repository root LICENSE file.

## Support

For issues or questions, contact the development team or create an issue in the repository.
