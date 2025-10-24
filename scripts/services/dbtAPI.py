"""Module containing DBT API logic."""

# General Libraries
import atexit

import requests
from requests.exceptions import HTTPError

from .SecretManager import SecretManager


class dbtAPI:
    """
    A class to interact with the DBT API.

    Allows for the retreival of DBT run data.
    """

    __all__ = ["get_runs", "get_run_details", "get_run_artifact"]

    def __init__(self, secret_name, deploy_type="stg"):
        """
        Initialize the dbtAPI class with authentication and session settings.

        Args:
            secret_name (str): The name of the secret containing authentication details.
            deploy_type (str, optional): The deployment type (default is 'stg').
        """
        secret = SecretManager(deploy_type=deploy_type).get_secret(secret_name)
        self._baseURL = secret["baseURL"]
        self._accountID = secret["accountID"]
        self._urlPrefix = secret["urlPrefix"]
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f'Bearer {secret["token"]}',
            }
        )
        atexit.register(self._close_session)

    def _close_session(self):
        """Close the session when the object is deleted or script exits."""
        self.session.close()

    def _handle_response(self, response):
        """
        Handle the HTTP response, raising an error if the status code indicates a failure.

        Args:
            response (requests.Response): The response object returned by the API request.

        Raises:
            RuntimeError: If the response status code indicates an error.
        """
        try:
            response.raise_for_status()
        except HTTPError as e:
            try:
                error_message = response.json()
            except ValueError:
                error_message = response.text
            raise RuntimeError(f"HTTP error occurred: {e}, Response: {error_message}") from e

    def get_runs(self, **kwargs) -> dict:
        """
        Retrieve a list of dbt Cloud runs, with optional filtering, sorting and exclusion.

        Args:
            **kwargs: Optional parameters include:
                - job_name (str, required): The name of the job.
                - job_status (str, optional): Filter jobs by status.
                - job_order_by (str, optional): Field to order jobs by.
                - job_is_ascending (bool, optional): Ascending job sort order.
                - run_status (list, optional): Statuses to include.
                - exclude_statuses (list, optional): Statuses to exclude.
                - run_order_by (str, optional): Field to order runs by.
                - run_is_ascending (bool, optional): Ascending run sort order.

        Returns:
            dict: A dictionary containing run details.

        Raises:
            ValueError: If `job_name` is missing or no matching job is found.
        """
        job_name = kwargs.get("job_name")
        if not job_name:
            raise ValueError("job_name is required to fetch run details.")
        job_status = kwargs.get("job_status", None)
        job_order_by = kwargs.get("job_order_by", None)
        job_is_ascending = kwargs.get("job_is_ascending", True)
        job_details = self.get_job(
            job_name=job_name,
            job_status=job_status,
            order_by=job_order_by,
            is_ascending=job_is_ascending,
        )
        if not job_details:
            raise ValueError(f"No job found matching name: {job_name}")
        job_id = job_details.get("id")
        run_status = kwargs.get("run_status", [])
        exclude_statuses = kwargs.get("exclude_statuses", [])
        run_order_by = kwargs.get("run_order_by", None)
        run_is_ascending = kwargs.get("run_is_ascending", True)
        status_mapping = {
            "Queued": 1,
            "Starting": 2,
            "Running": 3,
            "Success": 10,
            "Error": 20,
            "Cancelled": 30,
        }
        status_codes = {status_mapping[status] for status in run_status if status in status_mapping}
        exclude_codes = {
            status_mapping[status] for status in exclude_statuses if status in status_mapping
        }
        payload = {
            "order_by": (
                f'{"" if run_is_ascending else "-"}{run_order_by}' if run_order_by else None
            ),
            "job_definition_id": job_id,
        }
        if status_codes:
            payload["status"] = list(status_codes)
        payload = {k: v for k, v in payload.items() if v is not None}

        endpoint = f"/accounts/{self._accountID}/runs"
        response = self.session.get(url=f"{self._baseURL}{endpoint}", params=payload)
        self._handle_response(response)
        runs = response.json().get("data", [])
        runs = [run for run in runs if run.get("status") not in exclude_codes]
        _response_total = response.json()["extra"]["pagination"]["count"]
        _response_offset = response.json()["extra"]["filters"]["offset"]

        while _response_total == 100:
            _response_offset += _response_total
            payload["offset"] = _response_offset
            next_page = self.session.get(url=f"{self._baseURL}{endpoint}", params=payload)
            self._handle_response(next_page)
            _response_total = next_page.json()["extra"]["pagination"]["count"]
            next_runs = next_page.json().get("data", [])
            next_runs = [run for run in next_runs if run.get("status") not in exclude_codes]
            runs.extend(next_runs)
        return runs

    def get_run_details(self, run_id) -> dict:
        """
        Retrieve detailed information for a specific dbt Cloud run.

        Args:
            run_id (int): The ID of the run to retrieve details for.

        Returns:
            dict: A dictionary containing details of the specified run.
        """
        endpoint = f"/accounts/{self._accountID}/runs/{run_id}"
        response = self.session.get(url=f"{self._baseURL}{endpoint}")
        self._handle_response(response)
        return response.json()["data"]

    def get_run_artifact(self, **kwargs):
        """
        Retrieve a specific artifact for a given dbt Cloud run.

        Args:
            **kwargs: Optional parameters include:
                - run_id (int): ID of the run.
                - artifact (str): Name of the artifact (e.g. 'manifest', 'run_results').
                - step_function (str, optional): Function fetch specific step index.
                - include_items (str or list, optional): Items to include in the response.

        Returns:
            dict: The requested artifact data.

        Raises:
            ValueError: If required parameters are missing or data cannot be retrieved.
        """
        run_id = kwargs.get("run_id", None)
        artifact = kwargs.get("artifact", None)
        step_function = kwargs.get("step_function", None)
        include_items = kwargs.get("include_items", "run_steps" if step_function else None)
        if not run_id or not artifact:
            raise ValueError("Both 'run_id' and 'artifact' parameters are required.")

        job_steps = self._get_run_steps(run_id=run_id, include_items=include_items)

        if not job_steps or include_items not in job_steps:
            raise ValueError(f"Unable to retrieve job steps for run_id: {run_id}.")

        step_index = None
        for data in job_steps[include_items]:
            step_name = data.get("name", None)
            if step_function and step_function in step_name:
                step_index = data.get("index", None)
                break

        params = {"step": step_index} if step_index is not None else {}
        endpoint = f"/accounts/{self._accountID}/runs/{run_id}/artifacts/{artifact}.json"
        response = self.session.get(url=f"{self._baseURL}{endpoint}", params=params)
        self._handle_response(response)
        return response.json()

    def _list_jobs(self, job_status=None, order_by=None, is_ascending=True) -> dict:
        """
        Retrieve a list of jobs from the account, filtering by status and sorting order.

        Args:
            job_status (str, optional): The status of jobs to filter by.
                Supported values include 'Active' and 'Deleted'. Defaults to all jobs.
            order_by (str, optional): The field by which to sort the job list.
            is_ascending (bool, optional): Whether to sort the jobs in ascending order.
                Set to False for descending order. Defaults to True.

        Returns:
            dict: A dictionary containing job data retrieved from the API.
        """
        endpoint = f"/accounts/{self._accountID}/jobs/"
        status_mapping = {"Active": 1, "Deleted": 2}
        status_code = status_mapping.get(job_status, None) if job_status else "all"
        params = {"state": status_code}
        if order_by is not None:
            params["order_by"] = f'{"" if is_ascending else "-"}{order_by}'
        response = self.session.get(url=f"{self._baseURL}{endpoint}", params=params)
        self._handle_response(response)
        return response.json()["data"]

    def get_job(self, job_name, **kwargs) -> dict:
        """
        Retrieve a specific job by name, with optional filtering and sorting.

        Args:
            job_name (str): The name or partial name of the job to retrieve.
            **kwargs: Additional filtering and sorting arguments passed to `_list_jobs`.
                Supported arguments include:
                - job_status (str): Filter jobs by status
                    - Active
                    - Deleted
                    - None for all.
                - order_by (str): Sort jobs by a specific field.
                - is_ascending (bool): Sort order.

        Returns:
            dict: A dictionary containing job details if found, otherwise None.
        """
        job_list = self._list_jobs(**kwargs)
        for job in job_list:
            if job_name in job.get("name"):
                break

        return job

    def _get_run_steps(self, **kwargs):
        run_id = kwargs.get("run_id", None)
        if not run_id:
            raise ValueError("Parameter 'run_id' is required.")
        endpoint = f"/accounts/{self._accountID}/runs/{run_id}"
        params = {}

        include_items = kwargs.get("include_items", None)

        # Ensure include_items is a list for multiple parameters
        if include_items:
            if isinstance(include_items, str):  # Convert single string to list
                include_items = [include_items]
            params["include_related"] = ",".join(include_items)

        response = self.session.get(url=f"{self._baseURL}{endpoint}", params=params)
        self._handle_response(response)

        response_data = response.json().get("data", {})

        # Extract specified include items
        if include_items:
            return {item: response_data[item] for item in include_items if item in response_data}

        return response_data  # Return full data if no include_items specified
