"""Module containing logic to interact with ServiceM8 API.

This module provides a comprehensive interface to interact with the ServiceM8
field service management platform, including jobs, materials, staff, forms,
and attachments.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image as PILImage
from io import BytesIO
import fitz  # PyMuPDF
from retry import retry

from .SecretManager import SecretManager


class ServiceM8:
    """
    A class to interact with ServiceM8 API.

    It allows the user to perform operations such as retrieving jobs, staff,
    form responses, materials, and attachments from the ServiceM8 platform.
    """

    __all__ = [
        # Initialization
        "ServiceM8",
        # Job Operations
        "all_jobs_date",
        "get_job_by_uuid",
        "get_job_activity",
        "job_activity_dated",
        # Material Operations
        "all_job_materials_date",
        "active_materials",
        # Staff Operations
        "get_all_staff",
        "get_staff_by_uuid",
        # Form Operations
        "get_form_responses",
        "get_form_responses_by_date",
        "get_form_responses_gt_datetime",
        # Attachment Operations
        "get_attachments_by_job",
        "get_attachments_by_date",
        "get_attachments_gt_datetime",
        "get_image",
        # Customer Operations
        "get_customer_details",
    ]

    def __init__(self, secret_name: str = "SERVICEM8_SECRET", deploy_type: str = "STAGING"):
        """
        Initialize ServiceM8 API client.

        Args:
            secret_name (str): The name of the secret containing the ServiceM8 API key.
            deploy_type (str): Deployment type - 'STAGING' or 'PRODUCTION'.
        """
        logging.info("Initializing ServiceM8 API client")
        
        # Retrieve API key from SecretManager
        secret_manager = SecretManager()
        api_key = secret_manager.get_secret(secret_name, deploy_type)
        
        self._base_url = 'https://api.servicem8.com/api_1.0'
        self._headers = {
            'accept': 'application/json',
            'authorization': f'Basic {api_key}'
        }

    def _handle_response(self, response: requests.Response) -> None:
        """
        Handle HTTP response and raise exceptions for errors.

        Args:
            response: The HTTP response object.

        Raises:
            HTTPError: If the response status indicates an error.
        """
        try:
            response.raise_for_status()
        except Exception as e:
            logging.error(f"ServiceM8 API error: {e}")
            raise e

    def all_jobs_date(self, search_date: Union[str, Any], search_operator: str) -> List[Dict]:
        """
        Retrieve all jobs for a specific date.

        Args:
            search_date: The date to search for (string format 'YYYY-MM-DD' or date object).
            search_operator: The comparison operator to use.
                Available operators:
                    - 'eq': Equal
                    - 'ne': Not Equal
                    - 'gt': Greater Than
                    - 'lt': Less Than

        Returns:
            List of job dictionaries.
        """
        if not isinstance(search_date, str):
            try:
                search_date = str(search_date)
            except Exception as e:
                logging.error(f"Unable to convert search_date to string: {e}")
                raise
        
        endpoint = f"/job.json?%24filter=date%20{search_operator}%20'{search_date}'"
        response = requests.get(url=self._base_url + endpoint, headers=self._headers)
        self._handle_response(response)
        return response.json()

    def get_job_activity(self, job_uuid: str) -> List[Dict]:
        """
        Retrieve job activity for a specific job.

        Args:
            job_uuid: The UUID of the job.

        Returns:
            List of job activity dictionaries.
        """
        endpoint = f'/jobactivity.json?%24filter=job_uuid%20eq%20{job_uuid}'
        response = requests.get(url=self._base_url + endpoint, headers=self._headers)
        self._handle_response(response)
        return response.json()

    def job_activity_dated(self, search_date: Union[str, Any], search_operator: str) -> List[Dict]:
        """
        Retrieve all job activities for jobs on a specific date.

        Args:
            search_date: The date to search for.
            search_operator: The comparison operator to use.

        Returns:
            List of job activity dictionaries.
        """
        all_jobs = self.all_jobs_date(search_date=search_date, search_operator=search_operator)
        job_activity_list = []
        for job in all_jobs:
            job_uuid = job['uuid']
            job_activity = self.get_job_activity(job_uuid=job_uuid)
            job_activity_list.extend(job_activity)
        return job_activity_list

    def all_job_materials_date(self, search_date: Union[str, Any], search_operator: str) -> Union[List[Dict], str]:
        """
        Retrieve all job materials edited on or after a specific date.

        Args:
            search_date: The date to search for.
            search_operator: The comparison operator to use.

        Returns:
            List of job material dictionaries or error message.
        """
        if not isinstance(search_date, str):
            try:
                search_date = str(search_date)
            except Exception as e:
                logging.error(f"Unable to convert search_date to string: {e}")
                return 'No materials used'
        
        endpoint = f"/jobmaterial.json?%24filter=edit_date%20{search_operator}%20'{search_date}'"
        response = requests.get(url=self._base_url + endpoint, headers=self._headers)
        try:
            self._handle_response(response)
            return response.json()
        except Exception:
            return 'No materials used'

    def active_materials(self) -> List[Dict]:
        """
        Retrieve all active materials.

        Returns:
            List of active material dictionaries.
        """
        endpoint = '/material.json'
        response = requests.get(url=self._base_url + endpoint, headers=self._headers)
        self._handle_response(response)
        response_json = response.json()
        active_materials = [item for item in response_json if item.get('active') == 1]
        return active_materials

    def get_job_by_uuid(self, job_uuid: str) -> Dict:
        """
        Retrieve a specific job by UUID.

        Args:
            job_uuid: The UUID of the job.

        Returns:
            Job dictionary.
        """
        endpoint = f'/job/{job_uuid}.json'
        response = requests.get(url=self._base_url + endpoint, headers=self._headers)
        self._handle_response(response)
        return response.json()

    def get_attachments_by_job(self, job_uuid: str) -> List[Dict]:
        """
        Retrieve all attachments for a specific job.

        Args:
            job_uuid: The UUID of the job.

        Returns:
            List of attachment dictionaries.
        """
        endpoint = f'/attachment.json?%24filter=related_object_uuid%20eq%20{job_uuid}'
        response = requests.get(url=self._base_url + endpoint, headers=self._headers)
        self._handle_response(response)
        return response.json()

    def get_attachments_by_date(self, search_date: str, related_object: str = 'job') -> List[Dict]:
        """
        Retrieve all attachments edited on a specific date.

        Args:
            search_date: The date to search for (format 'YYYY-MM-DD').
            related_object: The type of related object (default: 'job').

        Returns:
            List of attachment dictionaries for the specified date.
        """
        endpoint = f"/attachment.json?%24filter=edit_date%20gt%20'{search_date}'"
        response = requests.get(url=self._base_url + endpoint, headers=self._headers)
        self._handle_response(response)
        response_json = response.json()
        
        search_date_dt = datetime.strptime(search_date, "%Y-%m-%d")
        filtered_json = []
        for item in response_json:
            edit_date = datetime.fromisoformat(item['edit_date'])
            if edit_date.date() == search_date_dt.date() and item.get('related_object') == related_object:
                filtered_json.append(item)
        return filtered_json

    def get_attachments_gt_datetime(self, search_datetime: str, related_object: str = 'job') -> List[Dict]:
        """
        Retrieve all attachments edited after a specific datetime.

        Args:
            search_datetime: The datetime to search for (format 'YYYY-MM-DD HH:MM:SS').
            related_object: The type of related object (default: 'job').

        Returns:
            List of attachment dictionaries after the specified datetime.
        """
        endpoint = f"/attachment.json?%24filter=edit_date%20gt%20'{search_datetime}'"
        response = requests.get(url=self._base_url + endpoint, headers=self._headers)
        self._handle_response(response)
        response_json = response.json()
        
        search_datetime_dt = datetime.strptime(search_datetime, "%Y-%m-%d %H:%M:%S")
        filtered_json = []
        for item in response_json:
            edit_datetime = datetime.fromisoformat(item['edit_date'])
            if edit_datetime > search_datetime_dt and item.get('related_object') == related_object:
                filtered_json.append(item)
        return filtered_json

    def get_image(
        self,
        asset_uuid: str,
        file_type: str,
        file_path: Optional[str] = None,
        return_type: Optional[str] = None
    ) -> Optional[Union[PILImage.Image, bytes, Exception]]:
        """
        Download and retrieve images, PDFs, or videos from ServiceM8.

        Args:
            asset_uuid: The UUID of the asset/attachment.
            file_type: Type of file - 'image', 'pdf', or 'video'.
            file_path: Optional path to save the file.
            return_type: Optional return type - 'image' or 'content'.

        Returns:
            Image object, file content bytes, or None if saved to file.
        """
        endpoint = f'/attachment/{asset_uuid}.file'
        response = requests.get(url=self._base_url + endpoint, headers=self._headers)
        
        try:
            response_url = response.url
            image_response = requests.get(response_url).content
            
            if file_type == 'image':
                if file_path is not None:
                    with open(file_path, 'wb') as f:
                        f.write(image_response)
                elif file_path is None:
                    if return_type == 'image':
                        return PILImage.open(BytesIO(image_response))
                    elif return_type == 'content':
                        return image_response
                else:
                    logging.error('Not all variables supplied')
                    
            elif file_type == 'pdf':
                fitz_response = fitz.open(stream=image_response, filetype="pdf")
                if file_path is not None:
                    output_pdf = fitz.open()
                    for page_number in range(len(fitz_response)):
                        page = fitz_response.load_page(page_number)
                        pix = page.get_pixmap()
                        output_pdf.insert_page(page_number, width=pix.width, height=pix.height)
                        output_pdf[page_number].insert_image((0, 0, pix.width, pix.height), pixmap=pix)
                    output_pdf.save(file_path)
                elif file_path is None and return_type == 'content':
                    return image_response
                    
            elif file_type == 'video':
                if file_path is not None:
                    with open(file_path, 'wb') as f:
                        f.write(image_response)
                elif return_type == 'content':
                    return image_response
                else:
                    logging.error('Missing fields')
                    
        except Exception as e:
            logging.error(f"Error retrieving image/file: {e}")
            return e

    def get_customer_details(self, customer_uuid: str) -> Dict:
        """
        Retrieve customer/company details by UUID.

        Args:
            customer_uuid: The UUID of the customer/company.

        Returns:
            Customer dictionary.
        """
        endpoint = f'/company/{customer_uuid}.json'
        response = requests.get(url=self._base_url + endpoint, headers=self._headers)
        self._handle_response(response)
        return response.json()

    def get_all_staff(self) -> Union[List[Dict], str]:
        """
        Retrieve all staff members.

        Returns:
            List of staff dictionaries or error message.
        """
        endpoint = '/staff.json'
        response = requests.get(url=self._base_url + endpoint, headers=self._headers)
        try:
            self._handle_response(response)
            return response.json()
        except Exception as e:
            logging.error(f"Error retrieving staff: {e}")
            return str(e)

    def get_staff_by_uuid(self, staff_uuid: str) -> requests.Response:
        """
        Retrieve a specific staff member by UUID.

        Args:
            staff_uuid: The UUID of the staff member.

        Returns:
            HTTP response object.
        """
        endpoint = f'/staff/{staff_uuid}.json'
        response = requests.get(url=self._base_url + endpoint, headers=self._headers)
        return response

    def _get_form_responses(self, form_uuid: str) -> Union[List[Dict], str]:
        """
        Internal method to retrieve all form responses for a specific form.

        Args:
            form_uuid: The UUID of the form.

        Returns:
            List of form response dictionaries or error message.
        """
        endpoint = f"/formresponse.json?%24filter=form_uuid%20eq%20'{form_uuid}'"
        response = requests.get(url=self._base_url + endpoint, headers=self._headers)
        try:
            self._handle_response(response)
            return response.json()
        except Exception as e:
            logging.error(f"Error retrieving form responses: {e}")
            return str(e)

    def get_form_responses(self, form_uuid: str) -> List[List[Dict]]:
        """
        Retrieve and restructure all form responses for a specific form.

        Args:
            form_uuid: The UUID of the form.

        Returns:
            List of restructured form response lists.
        """
        responses = self._get_form_responses(form_uuid)
        restructured_form = []
        
        for item in responses:
            edit_date = item['edit_date']
            related_object = item['regarding_object']
            related_object_uuid = item['regarding_object_uuid']
            staff_uuid = item['form_by_staff_uuid']
            answers = json.loads(item['field_data'])
            answers_edited = []
            
            for x in answers:
                x['edit_date'] = edit_date
                x['related_object'] = related_object
                x['related_object_uuid'] = related_object_uuid
                x['staff_uuid'] = staff_uuid
                answers_edited.append(x)
            
            restructured_form.append(answers_edited)
        
        return restructured_form

    def get_form_responses_by_date(
        self,
        form_uuid: str,
        response_date: Union[str, Any]
    ) -> List[List[Dict]]:
        """
        Retrieve form responses for a specific date.

        Args:
            form_uuid: The UUID of the form.
            response_date: The date to filter by (string 'YYYY-MM-DD' or date object).

        Returns:
            List of restructured form response lists for the specified date.
        """
        responses = self._get_form_responses(form_uuid)
        restructured_form = []
        
        if isinstance(response_date, str):
            ref_date = datetime.strptime(response_date, "%Y-%m-%d").date()
        else:
            ref_date = response_date.date()
        
        for item in responses:
            edit_date = datetime.fromisoformat(item['edit_date'])
            if edit_date.date() == ref_date:
                edit_date_str = item['edit_date']
                related_object = item['regarding_object']
                related_object_uuid = item['regarding_object_uuid']
                staff_uuid = item['form_by_staff_uuid']
                answers = json.loads(item['field_data'])
                answers_edited = []
                
                for x in answers:
                    x['edit_date'] = edit_date_str
                    x['related_object'] = related_object
                    x['related_object_uuid'] = related_object_uuid
                    x['staff_uuid'] = staff_uuid
                    answers_edited.append(x)
                
                restructured_form.append(answers_edited)
        
        return restructured_form

    def get_form_responses_gt_datetime(
        self,
        form_uuid: str,
        response_datetime: Union[str, datetime]
    ) -> List[List[Dict]]:
        """
        Retrieve form responses after a specific datetime.

        Args:
            form_uuid: The UUID of the form.
            response_datetime: The datetime to filter by (string 'YYYY-MM-DD HH:MM:SS' or datetime object).

        Returns:
            List of restructured form response lists after the specified datetime.
        """
        responses = self._get_form_responses(form_uuid)
        restructured_form = []
        
        if isinstance(response_datetime, str):
            ref_datetime = datetime.strptime(response_datetime, "%Y-%m-%d %H:%M:%S")
        else:
            ref_datetime = response_datetime
        
        for item in responses:
            edit_datetime = datetime.fromisoformat(item['edit_date'])
            if edit_datetime > ref_datetime:
                edit_date = item['edit_date']
                related_object = item['regarding_object']
                related_object_uuid = item['regarding_object_uuid']
                staff_uuid = item['form_by_staff_uuid']
                answers = json.loads(item['field_data'])
                answers_edited = []
                
                for x in answers:
                    x['edit_date'] = edit_date
                    x['related_object'] = related_object
                    x['related_object_uuid'] = related_object_uuid
                    x['staff_uuid'] = staff_uuid
                    answers_edited.append(x)
                
                restructured_form.append(answers_edited)
        
        return restructured_form
