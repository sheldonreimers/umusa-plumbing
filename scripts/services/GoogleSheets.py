"""Module containing logic to interact with Google Sheet."""

import re

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from retry import retry

from .SecretManager import SecretManager


class GoogleSheets:
    """
    A class to interact with Google Sheets API.

    It allows the user to perform operations such as reading from and
    writing to Google Sheets.
    """

    __all__ = [
        # Initialization and Configuration
        "GoogleSheets",
        # Tab Management
        "create_tab",
        "rename_tab",
        "duplicate_sheet",
        "sort_tabs",
        "get_all_tab_details",
        "get_tab_details",
        "check_for_tab",
        # Data Operations
        "sheet_to_df",
        "df_to_sheet",
        "df_to_sheet_full_chunked",
        "clear_range",
        "get_cell_value",
        "update_cell",
        "update_row",
        "update_range",
        # Data Inspection
        "get_last_row",
        "get_last_column",
        # Row Operations
        "delete_row",
    ]

    def __init__(self, secret_name="GOOGLE_SECRET", deploy_type="STAGING"):
        """
        Initialize the GoogleSheets class with credentials from a secret manager.

        Args:
            secret_name : str
                The name of the secret to retrieve Google Sheets API credentials.
            deploy_type : str
                The type of deployment.
        """
        secret = SecretManager(deploy_type=deploy_type).get_secret(secret_name)
        creds = service_account.Credentials.from_service_account_info(secret)
        self._service = build(
            "sheets", "v4", credentials=creds, cache_discovery=False
        ).spreadsheets()
        self._value_service = self._service.values()

    def _starting_col_index(self, col):
        """
        Convert a column name (e.g., 'A', 'B', 'AA') to a 1-based index.

        Args:
            col : str
                The column name to convert.

        Returns:
            int
                The 1-based index of the column.
        """
        num = 0
        for c in col:
            num = num * 26 + (ord(c.upper()) - ord("A")) + 1
        return num

    @retry(tries=2, delay=60)
    def _end_col(self, num):
        """
        Convert a 1-based index to a column name (e.g., 1 -> 'A', 27 -> 'AA').

        Args:
            num : int
                The 1-based index to convert.

        Returns:
            str
                The column name corresponding to the index.

        Raises:
            ValueError: If the input number is less than or equal to zero.
        """
        if num <= 0:
            raise ValueError("Number must be greater than zero")
        result = []
        while num > 0:
            num, remainder = divmod(num - 1, 26)  # Convert to 0-based index
            result.append(chr(65 + remainder))  # ASCII code for 'A' plus remainder
        return "".join(reversed(result))

    @retry(tries=2, delay=60)
    def sheet_to_df(
        self,
        sheet_id,
        tab_name,
        starting_cell,
        ending_cell=None,
        include_header=True,
        format_type="FORMATTED_VALUE",
        clean_headers=True,
    ):
        """
        Read data from a Google Sheets tab into a pandas DataFrame.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to read data from.
            starting_cell : str
                The starting cell reference (e.g., 'A1') for reading data.
            ending_cell : str, optional
                The ending cell for reading data. Defaults to starting_cell.
            include_header : bool, optional
                Whether to include the first row as headers. Defaults to True.
            format_type : str, optional
                The format type for the data.
                Options: 'FORMATTED_VALUE' (default), 'UNFORMATTED_VALUE', 'FORMULA'.
            clean_headers : bool, optional
                Whether to clean the headers. Defaults to True.

        Returns:
            pd.DataFrame
                The data read from the Google Sheets tab as a pandas DataFrame.
        """
        if ending_cell is None:
            ending_cell = re.sub(r"[^a-zA-Z]", "", starting_cell)

        ranges = f"{tab_name}!{starting_cell}:{ending_cell}"

        payload = self._value_service.batchGet(
            spreadsheetId=sheet_id,
            valueRenderOption=format_type,
            dateTimeRenderOption="FORMATTED_STRING",
            ranges=ranges,
        )
        response = payload.execute()

        try:
            sheet_values = response["valueRanges"][0]["values"]
            if include_header:
                df = pd.DataFrame(sheet_values)
                col_headers = df.iloc[0]
                df = df[1:]
                df.columns = col_headers
                if clean_headers:
                    # Process column headers
                    df.columns = (
                        df.columns.str.lower()
                        .str.replace(r"\s+|[^a-zA-Z0-9]", "_", regex=True)
                        .str.replace(r"_+", "_", regex=True)
                    )
            else:
                df_values = sheet_values[1:]
                df = pd.DataFrame(df_values)
        except Exception:
            return pd.DataFrame([])

        return df

    @retry(tries=2, delay=60)
    def df_to_sheet(self, df, sheet_id, tab_name, starting_cell, is_append, include_header=True):
        """
        Write a pandas DataFrame to a Google Sheets tab.

        Args:
            df : pd.DataFrame
                The DataFrame to write to the Google Sheets tab.
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to write data to.
            starting_cell : str
                The starting cell reference (e.g., 'A1') for writing data.
            is_append : bool
                Whether to append the data to the existing data in the tab.
            include_header : bool, optional
                Whether to include the DataFrame's header as the first row.
                Defaults to True.

        Returns:
            String if the _is_append value is not correct.
        """
        if not isinstance(is_append, bool):
            is_append = str(is_append).lower()
            if is_append == "true":
                is_append = True
            elif is_append == "false":
                is_append = False
            else:
                return "Invalid value given"
        if is_append:
            self.df_append_sheet(
                df=df, sheet_id=sheet_id, tab_name=tab_name, starting_cell=starting_cell
            )
        else:
            self.df_to_sheet_full(
                df=df,
                sheet_id=sheet_id,
                tab_name=tab_name,
                starting_cell=starting_cell,
                include_header=include_header,
            )

    @retry(tries=2, delay=60)
    def clear_range(self, sheet_id, tab_name, starting_cell, df, include_header=True):
        """
        Clear a specific range in the Google Sheets tab.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to clear data from.
            starting_cell : str
                The starting cell reference (e.g., 'A1') for clearing data.
            df : pd.DataFrame
                The DataFrame to determine the range to clear.
            include_header : bool, optional
                Whether the first row is considered a header row. Defaults to True.

        Returns:
            string representing the Exception in string format.
        """
        try:
            start_col = re.findall(r"[a-zA-Z]+", starting_cell)[0]
            start_col_index = self._starting_col_index(start_col)
            end_col_index = start_col_index + df.shape[1]
            end_col = self._end_col(end_col_index)
        except Exception as e:
            return str(e)
        if include_header:
            starting_num = int(re.findall(r"\d+", starting_cell)[0]) + 1
            starting_col = re.findall(r"[a-zA-Z]+", starting_cell)[0]
            starting_cell = str(starting_col) + str(starting_num)

        clear_range = f"'{tab_name}'!{starting_cell}:{end_col}"

        body = {"dataFilters": [{"a1Range": clear_range}]}

        payload = self._value_service.batchClearByDataFilter(spreadsheetId=sheet_id, body=body)
        payload.execute()

    @retry(tries=2, delay=60)
    def df_to_sheet_full(self, df, sheet_id, tab_name, starting_cell, include_header=True):
        """
        Write a full DataFrame to a Google Sheets tab, clearing the target range first.

        Args:
            df : pd.DataFrame
                The DataFrame to write to the Google Sheets tab.
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to write data to.
            starting_cell : str
                The starting cell reference (e.g., 'A1') for writing data.
            include_header : bool, optional
                Whether to include the DataFrame's header as the first row.
                Defaults to True.
        """
        df = df.fillna("").astype(str)
        self.clear_range(
            sheet_id=sheet_id,
            tab_name=tab_name,
            starting_cell=starting_cell,
            df=df,
            include_header=include_header,
        )
        if include_header:
            df_headers = df.columns.to_list()
            upload_list = df.values.tolist()
            upload_list.insert(0, df_headers)
        else:
            upload_list = df.values.tolist()

        start_col = re.findall(r"[a-zA-Z]+", starting_cell)[0]
        start_col_index = self._starting_col_index(start_col)
        end_col_index = start_col_index + df.shape[1]
        end_col = self._end_col(end_col_index)

        insert_body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "majorDimension": "Rows",
                    "range": f"'{tab_name}'!{starting_cell}:{end_col}",
                    "values": upload_list,
                }
            ],
            "includeValuesInResponse": False,
            "responseDateTimeRenderOption": "FORMATTED_STRING",
            "responseValueRenderOption": "FORMATTED_VALUE",
        }

        payload = self._value_service.batchUpdate(spreadsheetId=sheet_id, body=insert_body)
        payload.execute()

    @retry(tries=2, delay=60)
    def df_to_sheet_full_chunked(
        self, df, sheet_id, tab_name, starting_cell, include_header=True, chunk_size=500
    ):
        """
        Write a DataFrame to a Google Sheets tab in smaller chunks.

        This method first clears the target range, then splits the DataFrame into chunks,
        and writes each chunk as a separate batchUpdate call.

        Args:
            df : pd.DataFrame
                The DataFrame to write.
            sheet_id : str
                The target spreadsheet ID.
            tab_name : str
                The tab (sheet) name.
            starting_cell : str
                The top-left cell for inserting data (e.g., 'A1').
            include_header : bool, optional
                Whether to include the DataFrame's header.
            chunk_size : int, optional
                The number of rows to send in each chunk.
        """
        df = df.fillna("").astype(str)
        self.clear_range(
            sheet_id=sheet_id,
            tab_name=tab_name,
            starting_cell=starting_cell,
            df=df,
            include_header=include_header,
        )
        if include_header:
            data = [df.columns.to_list()] + df.values.tolist()
        else:
            data = df.values.tolist()
        start_col = re.findall(r"[A-Za-z]+", starting_cell)[0]
        start_row = int(re.findall(r"\d+", starting_cell)[0])
        start_col_index = self._starting_col_index(start_col)
        end_col_index = start_col_index + df.shape[1]
        end_col = self._end_col(end_col_index)

        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            current_start_row = start_row + i
            current_end_row = current_start_row + len(chunk) - 1
            target_range = (
                f"'{tab_name}'!" f"{start_col}{current_start_row}:{end_col}{current_end_row}"
            )
            payload = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                        "range": target_range,
                        "majorDimension": "ROWS",
                        "values": chunk,
                    }
                ],
                "includeValuesInResponse": False,
                "responseDateTimeRenderOption": "FORMATTED_STRING",
                "responseValueRenderOption": "FORMATTED_VALUE",
            }
            self._value_service.batchUpdate(spreadsheetId=sheet_id, body=payload).execute()

    @retry(tries=2, delay=60)
    def df_append_sheet(self, df, sheet_id, tab_name, starting_cell, insert_methods="INSERT_ROWS"):
        """
        Append a pandas DataFrame to a Google Sheets tab.

        Args:
            df : pd.DataFrame
                The DataFrame to append to the Google Sheets tab.
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to append data to.
            starting_cell : str
                The starting cell reference (e.g., 'A1') for appending data.
            insert_methods : str, optional
                The method for inserting rows: 'INSERT_ROWS' (default) or 'OVERWRITE'.
        """
        df_check = self.sheet_to_df(
            sheet_id=sheet_id, tab_name=tab_name, starting_cell=starting_cell
        )
        df = df.astype(str)
        if 1 in df_check.index:
            upload_list = df.values.tolist()
        else:
            df_headers = df.columns.to_list()
            upload_list = df.values.tolist()
            upload_list.insert(0, df_headers)

        body = {"values": upload_list}
        ranges = f"'{tab_name}'!{starting_cell}"
        payload = self._value_service.append(
            spreadsheetId=sheet_id,
            body=body,
            range=ranges,
            valueInputOption="USER_ENTERED",
            insertDataOption=insert_methods,
            responseDateTimeRenderOption="FORMATTED_STRING",
        )
        payload.execute()

    @retry(tries=2, delay=60)
    def get_cell_value(
        self,
        sheet_id: str,
        tab_name: str,
        cell: str,
        format_type: str = "FORMATTED_VALUE",
    ) -> str | None:
        """
        Retrieve the value of a single cell.

        Args:
            sheet_id:       The ID of the spreadsheet.
            tab_name:       The name of the sheet/tab.
            cell:           The A1‑style cell reference (e.g. 'B2').
            format_type:    One of 'FORMATTED_VALUE', 'UNFORMATTED_VALUE', or 'FORMULA'.

        Returns:
            The cell’s value as a string, or None if empty/not present.

        Raises:
            Exception: If the Google Sheets API call fails.
        """
        range_name = f"'{tab_name}'!{cell}"
        try:
            response = self._value_service.get(
                spreadsheetId=sheet_id,
                range=range_name,
                valueRenderOption=format_type,
                dateTimeRenderOption="FORMATTED_STRING",
            ).execute()
            values = response.get("values", [])
            if values and values[0]:
                return values[0][0]
            return None
        except HttpError as e:
            raise Exception(f"Error fetching cell {tab_name}!{cell}: {e}")

    @retry(tries=2, delay=60)
    def update_cell(self, sheet_id, tab_name, cell, value=None, formatted=True, is_hyperlink=False):
        """
        Update a specific cell in the Google Sheets tab.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to update.
            cell : str
                The cell reference (e.g., 'A1') to update.
            value : str, optional
                The value to set in the cell. Defaults to None.
            formatted : bool, optional
                Whether to apply user-entered formatting. Defaults to True.
            is_hyperlink : bool, optional
                Whether the value is a hyperlink. Defaults to False.
        """
        update_range = f"'{tab_name}'!{cell}"
        # Detect hyperlink if not explicitly specified
        if is_hyperlink and isinstance(value, str):
            cell_value = f'=HYPERLINK("{value}", "Link")'
        else:
            cell_value = "" if value is None else value

        input_option = "USER_ENTERED" if formatted else "RAW"

        body = {"majorDimension": "ROWS", "values": [[cell_value]]}

        payload = self._value_service.update(
            spreadsheetId=sheet_id,
            range=update_range,
            body=body,
            valueInputOption=input_option,
            includeValuesInResponse=False,
            responseDateTimeRenderOption="FORMATTED_STRING",
            responseValueRenderOption="FORMATTED_VALUE",
        )

        payload.execute()

    @retry(tries=2, delay=60)
    def update_row(self, sheet_id, tab_name, cell, update_lst, formatted=True):
        """
        Update a specific row in the Google Sheets tab.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to update.
            cell : str
                The starting cell reference (e.g., 'A1') for the row to update.
            update_lst : list
                The list of values to update the row with.
            formatted : bool, optional
                Whether to apply user-entered formatting. Defaults to True.
        """
        update_range = f"'{tab_name}'!{cell}"

        formatted_state = "USER_ENTERED" if formatted else "RAW"

        body = {"majorDimension": "ROWS", "values": update_lst}

        payload = self._value_service.update(
            spreadsheetId=sheet_id,
            range=update_range,
            body=body,
            valueInputOption=formatted_state,
            includeValuesInResponse=False,
            responseDateTimeRenderOption="FORMATTED_STRING",
            responseValueRenderOption="FORMATTED_VALUE",
        )

        payload.execute()

    @retry(tries=2, delay=60)
    def update_range(self, sheet_id, tab_name, starting_cell, values, is_append, formatted=True):
        """
        Update a range in the Google Sheets tab.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to update.
            starting_cell : str
                The starting cell reference (e.g., 'A1') for updating data.
            values : list
                The list of values to update in the range.
            is_append : bool
                Whether to append the data to the existing data in the tab.
            formatted : bool, optional
                Whether to apply user-entered formatting. Defaults to True.
        """
        if is_append:
            current_values = self.get_last_row(sheet_id, tab_name, starting_cell)
            column = re.sub(r"\d", "", starting_cell)
            next_row = current_values + 1
            update_range = f"'{tab_name}'!{column}{next_row}"
        else:
            update_range = f"'{tab_name}'!{starting_cell}"

        formatted_state = "USER_ENTERED" if formatted else "RAW"

        body = {"majorDimension": "ROWS", "values": [values]}

        payload = self._value_service.update(
            spreadsheetId=sheet_id,
            range=update_range,
            body=body,
            valueInputOption=formatted_state,
            includeValuesInResponse=False,
            responseDateTimeRenderOption="FORMATTED_STRING",
            responseValueRenderOption="FORMATTED_VALUE",
        )

        payload.execute()

    @retry(tries=2, delay=60)
    def get_last_row(self, sheet_id, tab_name, starting_cell):
        """
        Get the last row with data in a specific column.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to check.
            starting_cell : str
                The starting cell reference (e.g., 'A1') in the column to check.

        Returns:
            int
                The index of the last row with data.
        """
        pattern = r"[A-Za-z]+"
        column_ref = re.search(pattern, starting_cell).group()
        range_name = f"'{tab_name}'!{column_ref}:{column_ref}"
        result = self._value_service.get(spreadsheetId=sheet_id, range=range_name).execute()

        values = result.get("values", [])
        return len(values)

    @retry(tries=2, delay=60)
    def get_last_column(self, sheet_id, tab_name, starting_cell):
        """
        Get the last column with data in a specific row.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to check.
            starting_cell : str
                The starting cell reference (e.g., 'A1') in the row to check.

        Returns:
            str
                The name of the last column with data.
        """
        starting_col = re.findall("[A-Za-z]+", starting_cell)
        result = 0
        for i, letter in enumerate(reversed(starting_col)):
            # Subtract 64 to convert ASCII to 1-based index
            result += (ord(letter) - 64) * (26**i)
        data = self._value_service.get(
            spreadsheetId=sheet_id, range=tab_name, majorDimension="COLUMNS"
        ).execute()
        try:
            sheet_results = data["values"][result:]
            for index, sublist in enumerate(sheet_results, start=result):
                if not sublist:  # Check if the sublist is empty
                    break
                result += 1
            n, remainder = divmod(result - 1, 26)
            column = chr(65 + remainder)
            return column
        except Exception:
            pattern = r"[A-Za-z]+"
            column_ref = re.search(pattern, starting_cell).group()
            return column_ref

    @retry(tries=2, delay=60)
    def delete_row(self, sheet_id, tab_name, row_number):
        """
        Delete a specific row in the Google Sheets tab.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to delete the row from.
            row_number : int
                The index of the row to delete.

        Returns:
            response object of the request.
        """
        sheet_details = self._service.get(spreadsheetId=sheet_id).execute()
        for sheet in sheet_details["sheets"]:
            if sheet["properties"]["title"] == tab_name:
                tab_id = sheet["properties"]["sheetId"]

        request = self._service.batchUpdate(
            spreadsheetId=sheet_id,
            body={
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": tab_id,
                                "dimension": "ROWS",
                                "startIndex": int(row_number) - 1,
                                "endIndex": int(row_number),
                            }
                        }
                    }
                ]
            },
        )
        response = request.execute()
        return response

    @retry(tries=2, delay=60)
    def create_tab(self, sheet_id, tab_name):
        """
        Create a new tab in the Google Sheets spreadsheet.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to create.

        Returns:
            string representing the Exception message.
        """
        body = {"requests": [{"addSheet": {"properties": {"title": tab_name}}}]}
        try:
            self._service.batchUpdate(spreadsheetId=sheet_id, body=body).execute()
        except Exception as e:
            return str(e)

    @retry(tries=2, delay=60)
    def get_all_tab_details(self, sheet_id):
        """
        Retrieve details of all tabs in the Google Sheets spreadsheet.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.

        Returns:
            list
                A list of dictionaries containing details of all tabs in the spreadsheet.
        """
        sheet_info = self._service.get(spreadsheetId=sheet_id).execute()["sheets"]
        return sheet_info

    @retry(tries=2, delay=60)
    def get_tab_details(self, sheet_id, tab_name):
        """
        Retrieve details of a specific tab in the Google Sheets spreadsheet.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to retrieve details for.

        Returns:
            dict
                A dictionary containing details of the specified tab.
        """
        all_tabs = self.get_all_tab_details(sheet_id)
        for x in all_tabs:
            sheet_properties = x.get("properties")
            if sheet_properties.get("title") == tab_name:
                return x

    def check_for_tab(self, sheet_id, tab_name):
        """
        Check if a specific tab exists in the Google Sheets spreadsheet.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the tab to check.

        Returns:
            bool
                True if the tab exists, False otherwise.
        """
        all_tabs = self.get_all_tab_details(sheet_id)
        for x in all_tabs:
            sheet_properties = x.get("properties")
            if sheet_properties.get("title") == tab_name:
                return True

    @retry(tries=2, delay=60)
    def duplicate_sheet(self, sheet_id, tab_name, new_sheet_name):
        """
        Duplicate a specific sheet in the Google Sheets spreadsheet.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            tab_name : str
                The name of the sheet to duplicate.
            new_sheet_name : str
                The name of the new duplicated sheet.

        Returns:
            dict
                The response from the Google Sheets API after duplicating the sheet.

        Raises:
            Exception: if the request fails.
        """
        source_sheet_id = self.get_tab_details(sheet_id, tab_name)["properties"]["sheetId"]
        source_sheet_index = self.get_tab_details(sheet_id, tab_name)["properties"]["index"] + 1
        requests = [
            {
                "duplicateSheet": {
                    "sourceSheetId": source_sheet_id,
                    "newSheetName": new_sheet_name,
                    "insertSheetIndex": source_sheet_index,
                }
            }
        ]

        body = {"requests": requests}

        try:
            response = self._service.batchUpdate(spreadsheetId=sheet_id, body=body).execute()
            return response
        except HttpError as error:
            raise Exception(f"An error occurred: {error}")

    @retry(tries=2, delay=60)
    def rename_tab(self, sheet_id, old_name, new_name):
        """
        Rename a specific tab in the Google Sheets spreadsheet.

        Args:
            sheet_id : str
                The ID of the Google Sheets spreadsheet.
            old_name : str
                The current name of the tab.
            new_name : str
                The new name for the tab.

        Raises:
            Exception: if the request fails.
        """
        source_sheet_id = self.get_tab_details(sheet_id, old_name)["properties"]["sheetId"]
        requests = [
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": source_sheet_id, "title": new_name},
                    "fields": "title",
                }
            }
        ]

        body = {"requests": requests}

        try:
            self._service.batchUpdate(spreadsheetId=sheet_id, body=body).execute()
        except HttpError as error:
            raise Exception(f"An error occurred: {error}")

    def sort_tabs(self, sheet_id, tab_id, new_index):
        """Sort the tabs of a given tab.

        Args:
            sheet_id: str of the sheet to update.
            tab_id: str of the tab name to update.
            new_index: New index to be applied.

        Returns:
            response object of the request.

        Raises:
            Exception: when the sorting failed.
        """
        requests = [
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": tab_id, "index": new_index},
                    "fields": "index",
                }
            }
        ]

        body = {"requests": requests}
        try:
            response = self._service.batchUpdate(spreadsheetId=sheet_id, body=body).execute()
            return response
        except HttpError as error:
            raise Exception(f"An error occurred: {error}")
