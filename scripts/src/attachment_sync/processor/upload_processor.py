"""Upload Processor - Main workflow orchestration for attachment sync.""".

import logging
from typing import Any, Dict, List

from ..config import Config

logger = logging.getLogger(__name__)


class UploadProcessor:
    """Orchestrates the file upload workflow.""".

    def __init__(self, config: Config, api_handlers, file_handlers):
        """Initialize Upload Processor.

        Args:
            config: Configuration object.
            api_handlers: APIHandlers instance.
            file_handlers: FileHandlers instance.
        """
        self.config = config
        self.api_handlers = api_handlers
        self.file_handlers = file_handlers
        logger.info("UploadProcessor initialized")

    def should_skip_job(self, job_data: Dict[str, Any]) -> tuple:
        """Check if a job should be skipped based on various criteria.

        Args:
            job_data: Job data dictionary from ServiceM8.

        Returns:
            Tuple of (should_skip: bool, reason: str).
        """
        job_id = job_data.get("generated_job_id", "Unknown")
        job_status = job_data.get("status")
        company_uuid = job_data.get("company_uuid", "")

        # Check job status
        if job_status in self.config.servicem8.skip_statuses:
            return True, f"Job {job_id} has status: {job_status}"

        # Check if job ID ends with a letter (indicates subproject or similar)
        if job_id and len(job_id) >= 2 and job_id[-2].isalpha():
            return True, f"Job {job_id} appears to be a subproject (ends with letter)"

        # Check if customer exists
        if len(company_uuid) == 0:
            return True, f"Job {job_id} has no customer"

        return False, ""

    def process_job_attachments(
        self,
        uuid: str,
        sorted_attachments: List[Dict[str, Any]],
        folder_data: List[Dict[str, Any]],
    ) -> tuple:
        """Process all attachments for a single job.

        Args:
            uuid: Job UUID.
            sorted_attachments: Sorted list of all attachments.
            folder_data: List of all existing folders in root.

        Returns:
            Tuple of (success: bool, last_edit_date: str or None).
        """# Fetch job data
        try:
            job_data = self.api_handlers.servicem8.get_job_by_uuid(uuid)
        except Exception as e:
            logger.error(f"Job fetch failed for UUID {uuid}: {e}")
            return False, None

        # Check if job should be skipped
        should_skip, reason = self.should_skip_job(job_data)
        if should_skip:
            logger.info(f"Skipping job: {reason}")
            return False, None

        # Extract job details
        job_id = job_data.get("generated_job_id")
        company_uuid = job_data.get("company_uuid")

        # Get customer details
        try:
            customer_details = self.api_handlers.servicem8.get_customer_details(company_uuid)
            customer_name = customer_details["name"]
        except Exception as e:
            logger.error(f"Failed to fetch customer details for job {job_id}: {e}")
            return False, None

        # Create folder name
        folder_name = self.file_handlers.sanitize_folder_name(job_id, customer_name)

        # Setup folder structure
        try:
            folder_id, pdf_folder, photo_folder, video_folder = self.file_handlers.setup_job_folder(
                folder_data, folder_name
            )
        except Exception as e:
            logger.error(f"Failed to setup folder structure for job {job_id}: {e}")
            return False, None

        # Filter attachments for this job
        job_attachments = [
            attachment
            for attachment in sorted_attachments
            if attachment["related_object_uuid"] == uuid
        ]

        logger.info(f"Processing {len(job_attachments)} attachments for job {job_id}")

        # Upload each attachment
        last_edit_date = None
        upload_count = 0
        for attachment in job_attachments:
            # Check if file has valid extension
            attachment_file_type = attachment.get("file_type", "")

            if attachment_file_type.endswith(self.config.file_types.extensions):
                success = self.file_handlers.upload_attachment(
                    attachment, pdf_folder, photo_folder, video_folder
                )

                if success:
                    upload_count += 1
                    # Track the last edit date
                    last_edit_date = attachment.get("edit_date")

        logger.info(f"Uploaded {upload_count}/{len(job_attachments)} files for job {job_id}")
        return True, last_edit_date

    def process(self) -> bool:
        """Main processing workflow.

        Returns:
            True if processing completed successfully, False otherwise.
        """
        try:
            logger.info("=" * 60)
            logger.info("Starting attachment sync workflow")
            logger.info(f"Search date: {self.config.search_date}")
            logger.info("=" * 60)

            # Step 1: Get folder data from OneDrive
            logger.info("Step 1: Fetching OneDrive folder structure")
            folder_data = self.api_handlers.onedrive.get_items_by_folder_id(
                self.config.onedrive.servicem8_attachments_folder
            )
            logger.info(f"Found {len(folder_data)} items in root folder")

            # Step 2: Get attachments from ServiceM8
            logger.info(f"Step 2: Fetching attachments since {self.config.search_date}")
            dated_attachments = self.api_handlers.servicem8.get_attachments_gt_datetime(
                self.config.search_date
            )

            if len(dated_attachments) == 0:
                logger.info("No new attachments found")
                # Update last run timestamp to now
                self.config.update_last_run(self.config.now.strftime("%Y-%m-%d %T"))
                return True

            logger.info(f"Found {len(dated_attachments)} new attachments")

            # Step 3: Sort attachments by edit date
            sorted_attachments = sorted(dated_attachments, key=lambda x: x.get("edit_date", ""))

            # Step 4: Get unique job UUIDs
            unique_uuids = {item["related_object_uuid"] for item in sorted_attachments}
            logger.info(f"Step 3: Processing {len(unique_uuids)} unique jobs")

            # Step 5: Process each job
            last_upload_time = None
            processed_jobs = 0
            for uuid in unique_uuids:
                success, last_edit = self.process_job_attachments(
                    uuid, sorted_attachments, folder_data
                )

                if success:
                    processed_jobs += 1
                    if last_edit:
                        last_upload_time = last_edit

            logger.info(f"Successfully processed {processed_jobs}/{len(unique_uuids)} jobs")

            # Step 6: Update last run timestamp
            if last_upload_time:
                self.config.update_last_run(last_upload_time)
                logger.info(f"Updated last run timestamp to: {last_upload_time}")

            logger.info("=" * 60)
            logger.info("Attachment sync workflow completed successfully")
            logger.info("=" * 60)
            return True

        except Exception as e:
            logger.error(f"Error during attachment sync processing: {e}", exc_info=True)
            return False

    def get_processing_summary(self) -> Dict[str, Any]:
        """Get a summary of processing configuration.

        Returns:
            Dictionary with processing summary.
        """
        return {
            "module": self.config.name,
            "version": self.config.version,
            "environment": self.config.environment,
            "search_date": self.config.search_date,
            "onedrive_root_folder": self.config.onedrive.servicem8_attachments_folder,
        }

    def __repr__(self) -> str:
        """Return string representation of UploadProcessor.""".
        return f"UploadProcessor(config={self.config.name})"
