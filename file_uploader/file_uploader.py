# Committing Commands
'''
cd /Users/sheldon.reimers/Documents/jupyterlab/umusa-plumbing/file_uploader
git add . 
git commit -m "Updating to fix Folder Naming"
git push origin main
'''
# System Library Import & directories
import os
import sys

# Working Libraries
import time,requests,json,pytz
import pandas as pd

from datetime import timedelta
# from tqdm.notebook import tqdm, trange
from datetime import datetime as dt

# Add the directory containing your custom libraries to the path
sys.path.append('config')
from lib import GoogleSheets
from lib import ServiceM8
from lib import OneDrive

# Access the secrets from environment variables
umusa_secret = json.loads(os.environ.get('UMUSA_SECRET'))
servicem8_secret = os.environ.get('SERVICEM8_SECRET')
umusa_azure = json.loads(os.environ.get('UMUSA_AZURE'))

## Activating API Systems
gpy = GoogleSheets(umusa_secret)
sm8 = ServiceM8(servicem8_secret)
od = OneDrive(umusa_azure)

# Script Variables
servicem8_attachments_folder = '4B4564E48AE9C501!523357'
sa_timezone = pytz.timezone('Africa/Johannesburg')
now_date = dt.now(sa_timezone)
lrj_path = 'config/last_run.json'
# Loaded with github pull
with open(lrj_path, 'r') as json_file:
    search_date = json.load(json_file)['last_upload']
      
# Retrieving all creeated folders
folder_data = od.get_items_by_folder_id(servicem8_attachments_folder)

dated_attachments = sm8.get_attachments_gt_datetime(search_date)

if len(dated_attachments) == 0:
    last_upload = {'last_upload':now_date.strftime("%Y-%m-%d %T")}
    with open(lrj_path, 'w') as json_file:
            json.dump(last_upload, json_file)
    # raise Exception('No new attachments')
else:
    
    sorted_attachments = sorted(dated_attachments, key=lambda x: x.get('edit_date', ''))
    
    unique_values = {item['related_object_uuid'] for item in sorted_attachments}
    for x in unique_values:
        job_data = sm8.get_job_by_uuid(x)
        company_uuid = job_data['company_uuid']
        generated_job_id = job_data['generated_job_id']
        if generated_job_id[-2].isalpha():
            continue
        customer_name = sm8.get_customer_details(company_uuid)['name']
        folder_name = ('#'+generated_job_id+'; '+customer_name.replace(',',';')).replace('/','-')
        if any(folder_name == item.get('name') for item in folder_data):
            for item in folder_data:
                if item.get('name') == folder_name:
                    folder_id = item['id']
            existing_files = od.get_items_by_folder_id(folder_id)
            if len(existing_files) > 0:
                existing_file_no = max([int(files['name'].split('_')[-1].split('.')[0]) for files in existing_files if files['name'].split('_')[-1].split('.')[0].isdigit()])
                file_name_no = existing_file_no+1
            else:
                file_name_no = 1
        else:
            created_folder = od.create_folder( parent_folder_id = servicem8_attachments_folder
                                              ,folder_name = folder_name
                                             )
            folder_id = created_folder[1]
            file_name_no = 1
        attachment_data = []
        for attachment in sorted_attachments:
            if attachment.get('related_object_uuid') == x:
                attachment_data.append(attachment)
        for y in attachment_data:
            attachment_uuid = y['uuid']
            file_type = y['attachment_source']
            file_ext = y['file_type']
            filename = y['attachment_name']
            if filename.endswith(file_ext):
                filename = y['attachment_name'].replace(file_ext,'')
            file_name = filename+'_'+str(file_name_no)+file_ext
            if file_ext == '.pdf':
                form_data = sm8.get_image( asset_uuid = attachment_uuid
                                           ,file_type = 'pdf'
                                           ,return_type = 'content'
                                          )
                file_name = y['attachment_name'].split(' by ')[0]+'_'+str(file_name_no)+file_ext
                od.upload_file( parent_id = folder_id
                               ,file_name = file_name
                               ,file_content = form_data
                              )
            elif file_ext == '.mp4':
                video_data = sm8.get_image( asset_uuid = attachment_uuid
                                           ,file_type = 'video'
                                           ,return_type = 'content'
                                          )
                od.upload_file( parent_id = folder_id
                               ,file_name = file_name
                               ,file_content = video_data
                              )
            else:
                photo_data = sm8.get_image( asset_uuid = attachment_uuid
                                           ,file_type = 'image'
                                           ,return_type = 'content'
                                          )
                od.upload_file( parent_id = folder_id
                               ,file_name = file_name
                               ,file_content = photo_data
                              )
            file_name_no += 1
            last_upload = {'last_upload':y['edit_date']}
    
    with open(lrj_path, 'w') as json_file:
        json.dump(last_upload, json_file)