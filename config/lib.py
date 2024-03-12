'''
cd /Users/sheldon.reimers/Documents/jupyterlab/umusa-plumbing/config
git add . 
git commit -m "Adding in OneDrive library"
git push origin main
'''

# General Libraries
import csv, io, os, sys, re
import requests
import json
import pandas as pd
import datetime as dt
from datetime import datetime, timezone, timedelta
from retry import retry
import numpy as np
from requests.auth import HTTPBasicAuth

# Google Libraries
from apiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account

class ServiceM8():

    def __init__(self,key):
        self.base_url = 'https://api.servicem8.com/api_1.0'
        self.headers = headers = { 'accept': 'application/json'
                                  ,'authorization': f'Basic {key}'
          }

    def all_jobs_date(self,search_date, search_operator):
        '''Usable operators: 
                {eq : Equal
                ,ne : Not Equal
                ,gt : Greater Than
                ,lt : Less Than}'''
        if isinstance(search_date,str):
            pass
        else:
            try:
                search_date.astype(str)
            except:
                print('unable to convert to string')
        endpoint = f"/job.json?%24filter=date%20{search_operator}%20'{search_date}'"
        response = requests.get(url = self.base_url + endpoint, headers = self.headers)
        return response.json()

    def get_job_activity(self,job_uuid):
        endpoint = f'/jobactivity.json?%24filter=job_uuid%20eq%20{job_uuid}'
        response = requests.get(url = self.base_url + endpoint, headers = self.headers)
        return response.json()

    def job_activity_dated(self,search_date, search_operator):
        '''Usable operators: 
                {eq : Equal
                ,ne : Not Equal
                ,gt : Greater Than
                ,lt : Less Than}'''
        all_jobs = self.all_jobs_date(search_date = search_date, search_operator = search_operator)
        job_activity_list = []
        for job in all_jobs:
            job_uuid = job['uuid']
            job_activity = self.get_job_activity(job_uuid = job_uuid)
            job_activity_list.extend(job_activity)
        return job_activity_list

    def all_job_materials_date(self,search_date, search_operator):
        if isinstance(search_date,str):
            pass
        else:
            try:
                search_date.astype(str)
            except:
                print('unable to convert to string')
        endpoint = f"/jobmaterial.json?%24filter=edit_date%20{search_operator}%20'{search_date}'"
        response = requests.get(url = self.base_url + endpoint, headers = self.headers)
        try:
            return response.json()
        except: 
            return 'No materials used'

    def active_materials(self):
        endpoint = '/material.json'
        response = requests.get(url = self.base_url + endpoint, headers = self.headers)
        response_json = response.json()
        active_materials = [item for item in response_json if item.get('active') == 1]
        return active_materials

    def get_job_by_uuid(self,job_uuid):
        endpoint = f'/job/{job_uuid}.json'
        response = requests.get(url = self.base_url + endpoint, headers = self.headers).json()
        return response

    def get_all_staff(self):
        endpoint = '/staff.json'
        response = requests.get(url = self.base_url + endpoint, headers = self.headers)
        try:
            response_json = response.json()
            return response_json
        except Exception as e:
            return str(e)

    def get_staff_by_uuid(self,staff_uuid):
        endpoint = f'/staff/{staff_uuid}.json'
        response = requests.get(url = self.base_url + endpoint, headers = self.headers)
        return response
    
    def get_form_responses(self, form_uuid):
        endpoint = f"/formresponse.json?%24filter=form_uuid%20eq%20'{form_uuid}'"
        response = requests.get(url = self.base_url + endpoint, headers = self.headers)
        try:
            return response.json()
        except Exception as e:
            return str(e)
        

class GoogleSheets():
    def __init__(self,service_secret):
        creds = service_account.Credentials.from_service_account_info(service_secret)
        self.service = build('sheets', 'v4', credentials=creds).spreadsheets()
        
        self.value_service = self.service.values()
        
    def _end_col(self,num):
        if num <= 0:
            raise ValueError("Number must be greater than zero")

        result = []
        while num > 0:
            num, remainder = divmod(num - 1, 26)  # Convert to 0-based index
            result.append(chr(65 + remainder))    # ASCII code for 'A' plus remainder

        return ''.join(reversed(result))
        
    def sheet_to_df(self,sheet_id, tab_name, starting_cell, ending_cell = None, include_header = True):
        if ending_cell == None:
            ending_cell = self._get_last_column(sheet_id = sheet_id, tab_name = tab_name)
        else:
            pass
            
        ranges = tab_name+'!'+starting_cell+':'+ending_cell
            
        payload = self.value_service.batchGet(spreadsheetId=sheet_id
                                             ,dateTimeRenderOption = 'FORMATTED_STRING'
                                             ,ranges = ranges
                                            )
        response = payload.execute()
        
        try:
            sheet_values = response['valueRanges'][0]['values']
            if include_header == True:
                df = pd.DataFrame(sheet_values)
                col_headers = df.iloc[0]
                df = df[1:]
                df.columns = col_headers
            else:
                df_values = sheet_values[1:]
                df = pd.DataFrame(df_values)
        except Exception as e:
            return pd.DataFrame([])

        return df
    
    def df_to_sheet(self,df,  sheet_id, tab_name, starting_cell,is_append, include_header = True):
        if type(is_append) != bool:
            is_append = str(is_append).lower()
            if is_append == 'true':
                is_append = True
            elif is_append == 'false':
                is_append = False
            else:
                return 'Invalid value given'
        if is_append == True:
            try:
                self.df_append_sheet( df = df
                                      ,sheet_id = sheet_id
                                      ,tab_name = tab_name
                                      ,starting_cell = starting_cell
                                     )
            except Exception as e:
                if 'Invalid dataFilter[0]' in str(e):
                    self.create_tab( sheet_id = sheet_id
                                    ,tab_name = tab_name
                                   )
                    self.df_append_sheet( df = df
                                         ,sheet_id = sheet_id
                                         ,tab_name = tab_name
                                         ,starting_cell = starting_cell
                                        )
                else:
                    return e
        elif is_append == False:
            try:
                self.df_to_sheet_full(df = df
                                       ,sheet_id = sheet_id
                                       ,tab_name = tab_name
                                       ,starting_cell = starting_cell
                                       ,include_header = include_header)
            except Exception as e:
                if 'Invalid dataFilter[0]' in str(e):
                    self.create_tab( sheet_id = sheet_id
                                    ,tab_name = tab_name
                                   )
                    self.df_to_sheet_full( df = df
                                          ,sheet_id = sheet_id
                                          ,tab_name = tab_name
                                          ,starting_cell = starting_cell
                                          ,include_header = include_header)
                else:
                    return e
        else:
            return 'Append Value is a requirements'
    
    def clear_range(self,sheet_id, tab_name, starting_cell, df, include_header = True):
        try:
            end_col = self._end_col(df.shape[1])
        except Exception as e:
            return str(e)
        if include_header == True:
            starting_num = int(re.findall(r'\d+',starting_cell)[0]) + 1
            starting_col = re.findall(r'[a-zA-Z]+',starting_cell)[0]
            starting_cell = str(starting_col) + str(starting_num)

        
        clear_range = f"'{tab_name}'!{starting_cell}:{end_col}"
        
        body = {"dataFilters": 
                [
                    {
                        "a1Range": clear_range
                    }
                ]
               }
        
        payload = self.value_service.batchClearByDataFilter( spreadsheetId = sheet_id
                                                            ,body = body
                                                           )
        response = payload.execute()

    @retry(tries=2,delay = 5)
    def df_to_sheet_full(self,df,  sheet_id, tab_name, starting_cell, include_header = True):
        df = df.fillna('').astype(str)
        self.clear_range( sheet_id = sheet_id
                         ,tab_name = tab_name
                         ,starting_cell = starting_cell
                         ,df = df
                         ,include_header = include_header
                        )
        if include_header == True:
            df_headers = df.columns.to_list()
            upload_list = df.values.tolist()
            upload_list.insert(0,df_headers)
        else:
            upload_list = df.values.tolist()
        end_col = self._end_col(df.shape[1])
        insert_body = {"valueInputOption": "USER_ENTERED",
                       "data": [
                           {
                               "majorDimension": "Rows",
                               "range": f"'{tab_name}'!{starting_cell}:{end_col}",
                               "values": upload_list
                           }
                       ],
                       "includeValuesInResponse": False,
                       "responseDateTimeRenderOption": "FORMATTED_STRING",
                       "responseValueRenderOption": "FORMATTED_VALUE"
                      }
        
        payload = self.value_service.batchUpdate(spreadsheetId = sheet_id,body = insert_body)
        response = payload.execute()

    @retry(tries=2,delay = 5)
    def df_append_sheet(self,df, sheet_id, tab_name, starting_cell, insert_methods = 'INSERT_ROWS'):
        """ insert_methods: 'INSERT_ROWS' or 'OVERWRITE'"""
        df_check = self.sheet_to_df( sheet_id = sheet_id
                                    ,tab_name = tab_name
                                    ,starting_cell = starting_cell
                                   )
        df = df.astype(str)
        if 1 in df_check.index:
            upload_list = df.values.tolist()
        else:
            df_headers = df.columns.to_list()
            upload_list = df.values.tolist()
            upload_list.insert(0,df_headers)

        body = {"values": upload_list}
        ranges = f"'{tab_name}'!{starting_cell}"
        payload = self.value_service.append( spreadsheetId = sheet_id
                                            ,body = body
                                            ,range = ranges
                                            ,valueInputOption = 'USER_ENTERED'
                                            ,insertDataOption = insert_methods
                                            ,responseDateTimeRenderOption = 'FORMATTED_STRING'
                                           )
        response = payload.execute()

    @retry(tries=2,delay = 5)
    def update_cell(self, sheet_id, tab_name, cell, value = None,formatted = True):
        update_range = f"'{tab_name}'!{cell}"
        if value == None:
            cell_value = ''
        else:
            cell_value = value
        if formatted == True:
            formatted_state = 'USER_ENTERED'
        else:
            formatted_state = 'RAW'
        
        body = {"majorDimension": "ROWS",
                "values": [[cell_value]]
               }
        
        payload = self.value_service.update( spreadsheetId = sheet_id
                                            ,range = update_range
                                            ,body = body
                                            ,valueInputOption = formatted_state
                                            ,includeValuesInResponse = False
                                            ,responseDateTimeRenderOption = 'FORMATTED_STRING'
                                            ,responseValueRenderOption = 'FORMATTED_VALUE'
                                           )
        
        response = payload.execute()

    @retry(tries=2,delay = 5)
    def update_row(self, sheet_id, tab_name, cell, update_lst,formatted = True):
        update_range = f"'{tab_name}'!{cell}"
        
        if formatted == True:
            formatted_state = 'USER_ENTERED'
        else:
            formatted_state = 'RAW'
        
        body = {"majorDimension": "ROWS",
                "values": update_lst
               }
        
        payload = self.value_service.update( spreadsheetId = sheet_id
                                            ,range = update_range
                                            ,body = body
                                            ,valueInputOption = formatted_state
                                            ,includeValuesInResponse = False
                                            ,responseDateTimeRenderOption = 'FORMATTED_STRING'
                                            ,responseValueRenderOption = 'FORMATTED_VALUE'
                                           )
        
        response = payload.execute()

    @retry(tries=2,delay = 5)
    def update_range(self, sheet_id, tab_name, starting_cell, values, is_append, formatted=True,):
        if is_append == True:
            current_values = self.get_last_row(sheet_id, tab_name,starting_cell)
            column = re.sub(r'\d', '', starting_cell)
            next_row = current_values + 1
            update_range = f"'{tab_name}'!{column}{next_row}"
        else:
            update_range = f"'{tab_name}'!{starting_cell}"

        if formatted:
            formatted_state = 'USER_ENTERED'
        else:
            formatted_state = 'RAW'

        body = {
            "majorDimension": "ROWS",
            "values": [values]
        }

        payload = self.value_service.update(
            spreadsheetId=sheet_id,
            range=update_range,
            body=body,
            valueInputOption=formatted_state,
            includeValuesInResponse=False,
            responseDateTimeRenderOption='FORMATTED_STRING',
            responseValueRenderOption='FORMATTED_VALUE'
        )

        response = payload.execute()
        
    def get_last_row(self, sheet_id, tab_name,starting_cell):
        pattern = r'[A-Za-z]+'
        column_ref = re.search(pattern, starting_cell).group()
        range_name = f"'{tab_name}'!{column_ref}:{column_ref}"
        result = (
            self.value_service.get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
        )
        values = result.get('values', [])
        return len(values)
    
    def _get_last_column(self,sheet_id, tab_name):
        result = self.value_service.get( spreadsheetId=sheet_id
                                        ,range=tab_name
                                        ,majorDimension = 'COLUMNS'
                                       ).execute()['values']
        last_col = self._end_col(len(result))
        return last_col
    
    def delete_row(self
                   ,sheet_id
                   ,tab_name
                   ,row_number):
        sheet_details = self.service.get(spreadsheetId=sheet_id).execute()
        for sheet in sheet_details['sheets']:
            if sheet['properties']['title'] == tab_name:
                tab_id = sheet['properties']['sheetId']

        request = self.service.batchUpdate(
            spreadsheetId=sheet_id,
            body={
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": tab_id
                                ,"dimension": "ROWS"
                                ,"startIndex":int(row_number)  - 1
                                ,"endIndex": int(row_number)
                            }
                        }
                    }
                ]
            }
        )
        response = request.execute()
        return response

    def create_tab( self
                   ,sheet_id
                   ,tab_name
                  ):
        body = {'requests' : 
                [
                    {'addSheet' : 
                     {'properties' : 
                      {'title' : tab_name
                      }
                     }
                    }
                ]
               }
        try:
            self.service.batchUpdate( spreadsheetId = sheet_id
                                     ,body = body
                                    ).execute()
        except Exception as e:
            return str(e)

class OneDrive():
    
    def __init__(self,secret_dict):
        # init Variables
        scope = 'https://graph.microsoft.com/.default'
        token_endpoint = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
        tenant_id = secret_dict['tenant_id']
        client_id = secret_dict['client_id']
        client_secret = secret_dict['client_secret']
        redirect_uri = secret_dict['redirect_uri']
        auth_code = secret_dict['auth_code']
        refresh_token = secret_dict['refresh_token']
        
        # Dict Creations
        token_data = { 'client_id': client_id
                           ,'client_secret': client_secret
                           ,'refresh_token': refresh_token
                           ,'grant_type': 'refresh_token'
                          }
        
        # POST for Access Tokens
        response = requests.post(token_endpoint, data=token_data)
        self.refresh_token = response.json()['refresh_token']
        self.access_token = response.json()['access_token']
        
        #System Variables
        self.headers = {'Authorization': f'Bearer {self.access_token}'
                        ,'Content-Type': 'application/json'
                       }
        self.base_url = 'https://graph.microsoft.com/v1.0/me/drive'
        # print(self.access_token)
        
    def get_folders(self):
        endpoint = '/root/children'
        response = requests.get(self.base_url+endpoint, headers=self.headers)
        return response
    
    def get_items_by_folder_id(self,folder_id):
        endpoint = f'/items/{folder_id}/children'
        response = requests.get(self.base_url+endpoint, headers=self.headers)
        return response
    
    def create_folder(self,parent_folder_id, folder_name):
        endpoint = f'/items/{parent_folder_id}/children'
        payload = { 'name': folder_name
                   ,'folder': {}
                   ,'@microsoft.graph.conflictBehavior': 'rename'
                  }
        response = requests.post( self.base_url+endpoint
                                ,headers=self.headers
                                ,json = payload
                                )
        if response.status_code == 201:
            response_json = response.json()
            return response_json['name'],response_json['id']
        else:
            return response
        
    def delete_folder(self,folder_id):
        endpoint = f'/items/{folder_id}'
        response = requests.delete( self.base_url+endpoint
                                ,headers=self.headers)
        if response.status_code == 204:
            
            return 'file deleted'
        else:
            return response
        
    def upload_file(self,parent_id,file_name,file_path=None,file_content=None):
        self.headers['Content-Type'] = 'application/octet-stream'
        if file_path != None and file_content == None:
            endpoint = f'/items/{parent_id}:/{file_path.split("/")[-1]}:/content'
            with open(file_path, 'rb') as file:
                file_content = file.read()
            response = requests.put( self.base_url+endpoint
                                    ,headers = self.headers
                                    ,data = file_content
                                   )
            return response
        elif file_path == None and file_content != None:
            endpoint = f'/items/{parent_id}:/{file_name}:/content'
            response = requests.put( self.base_url+endpoint
                                    ,headers = self.headers
                                    ,data = file_content
                                   )
            return response