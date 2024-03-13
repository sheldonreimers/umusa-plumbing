# Committing Commands
'''
cd /Users/sheldon.reimers/Documents/jupyterlab/umusa-plumbing/file_uploader
git add . 
git commit -m "Updating secret"
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

# Retrieves all jobs done that day
all_jobs = sm8.all_jobs_date( search_date = '2024-03-12'
                             ,search_operator = 'eq'
                            )

for x in tqdm(all_jobs):
    job_uuid = x['uuid']
    company_uuid = x['company_uuid']
    generated_job_id = x['generated_job_id']
    customer_name = sm8.get_customer_details(company_uuid)['name']
    folder_name = '#'+generated_job_id+'; '+customer_name.replace(',',';')
    created_folder = od.create_folder( parent_folder_id = servicem8_attachments_folder
                                      ,folder_name = folder_name
                                     )
    new_folder_id = created_folder[1]
    attachment_data = sm8.get_attachments_by_job(job_uuid)
    file_name_no = 1
    for y in tqdm(attachment_data):
        attachment_uuid = y['uuid']
        file_type = y['attachment_source']
        file_ext = y['file_type']
        file_name = y['attachment_name']+'_'+str(file_name_no)+file_ext
        if file_type.lower() == 'photo':
            photo_data = sm8.get_image( asset_uuid = attachment_uuid
                                       ,file_type = 'image'
                                       ,return_type = 'content'
                                      )
            od.upload_file( parent_id = new_folder_id
                           ,file_name = file_name
                           ,file_content = photo_data
                          )
        elif file_type.lower() == 'video':
            video_data = sm8.get_image( asset_uuid = attachment_uuid
                                       ,file_type = 'video'
                                       ,return_type = 'content'
                                      )
            od.upload_file( parent_id = new_folder_id
                           ,file_name = file_name
                           ,file_content = video_data
                          )
        elif file_type.lower() == 'form':
            form_data = sm8.get_image( asset_uuid = attachment_uuid
                                       ,file_type = 'pdf'
                                       ,return_type = 'content'
                                      )
            file_name = y['attachment_name'].split(' by ')[0]+'_'+str(file_name_no)+file_ext
            od.upload_file( parent_id = new_folder_id
                           ,file_name = file_name
                           ,file_content = form_data
                          )
        file_name_no += 1