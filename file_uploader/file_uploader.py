# Committing Commands
'''
cd /home/sheldonreimers/umusa-plumbing/file_uploader
git add file_uploader.py
git commit -m "Adding system variables"
git push origin main
'''
# System Library Import & directories
import os
import sys

# Working Libraries
import time,requests,json,pytz
import pandas as pd

from datetime import timedelta
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

# Used for Github running
lrj_path = 'config/last_run.json'

# Loaded with github pull
with open(lrj_path, 'r') as json_file:
    search_date = json.load(json_file)['last_upload']

def uploadFiles():
    ## Activating API Systems
    gpy = GoogleSheets(umusa_secret)
    sm8 = ServiceM8(servicem8_secret)
    od = OneDrive(umusa_azure)

    # Script Variables
    servicem8_attachments_folder = '4B4564E48AE9C501!523357'
    sa_timezone = pytz.timezone('Africa/Johannesburg')
    now_date = dt.now(sa_timezone)
    file_extensions = ('.jpg', '.pdf', '.mp4', '.png','.jpeg')
        
    def is_file(item):
        return 'file' in item  # This assumes that items will have a 'file' key if they are files
    
    def extract_file_number(filename):
        parts = filename.split('_')[-1].split('.')
        return int(parts[0]) if parts[0].isdigit() else None
          
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
    
    for uuid in unique_values:
        try:
            job_data = sm8.get_job_by_uuid(uuid)
        except Exception as e:
            print('Job Fetch Failed: ',uuid)
            continue
        job_status = job_data.get('status')
        job_id = job_data.get('generated_job_id')
        job_po = job_data.get('purchase_order_number')
        company_uuid = job_data.get('company_uuid')
        try:
            job_badge_lst = json.loads(job_data['badges'])
        except:
            job_badge_lst = []
        if job_status == 'Unsuccessful':
            print('Job Unsuccessful :',job_id)
            continue
        if job_id[-2].isalpha():
            continue
        if len(company_uuid) == 0:
            print('Empty Customer: ',job_id)
            continue
        customer_details = sm8.get_customer_details(company_uuid)
        customer_name = customer_details['name']
        customer_uuid = customer_details['uuid']
        customer_address = customer_details['address']
        folder_name = ('#'+job_id+'; '+customer_name.replace(',',';')).replace('/','-')
        folder_exists = next((item for item in folder_data if item.get('name') == folder_name), None)
        if folder_exists:
            folder_id = folder_exists['id']
            existing_files = od.get_items_by_folder_id(folder_id)
    
            pdf_folder = next((files.get('id') for files in existing_files if files.get('name') == 'pdfs'), None)
            if not pdf_folder:
                created_pdf_folder = od.create_folder(parent_folder_id=folder_id, folder_name='pdfs')
                pdf_folder = created_pdf_folder[1]
    
            photo_folder = next((files.get('id') for files in existing_files if files.get('name') == 'photos'), None)
            if not photo_folder:
                created_photo_folder = od.create_folder(parent_folder_id=folder_id, folder_name='photos')
                photo_folder = created_photo_folder[1]
    
            video_folder = next((files.get('id') for files in existing_files if files.get('name') == 'videos'), None)
            if not video_folder:
                created_video_folder = od.create_folder(parent_folder_id=folder_id, folder_name='videos')
                video_folder = created_video_folder[1]
    
        else:
            created_folder = od.create_folder(parent_folder_id=servicem8_attachments_folder, folder_name=folder_name)
            folder_id = created_folder[1]
            
            created_pdf_folder = od.create_folder(parent_folder_id=folder_id, folder_name='pdfs')
            pdf_folder = created_pdf_folder[1]
    
            created_photo_folder = od.create_folder(parent_folder_id=folder_id, folder_name='photos')
            photo_folder = created_photo_folder[1]
    
            created_video_folder = od.create_folder(parent_folder_id=folder_id, folder_name='videos')
            video_folder = created_video_folder[1]
    
        job_attachments = [attachment for attachment in sorted_attachments if attachment['related_object_uuid'] == uuid]
        for image in job_attachments:
            attachment_uuid = image.get('uuid')
            attachment_name = image.get('attachment_name')
            if attachment_name.endswith(file_extensions):
                attachment_name = attachment_name[: -len([ext for ext in file_extensions if attachment_name.endswith(ext)][0])]
            attachment_file_type = image.get('file_type')
            attachment_attachment_source = image.get('attachment_source')
            attachment_timestamp = image.get('timestamp')
            attachment_edited_at = image.get('edit_date')
            if attachment_file_type.endswith('pdf'):
                form_data = sm8.get_image( asset_uuid = attachment_uuid
                                          ,file_type = 'pdf'
                                          ,return_type = 'content'
                                         )
                od.upload_file( parent_id = pdf_folder
                               ,file_name = (attachment_timestamp+attachment_file_type).replace(" ", "_").replace(":", "-")
                               ,file_content = form_data
                              )
            if attachment_file_type.endswith('mp4'):
                video_data = sm8.get_image( asset_uuid = attachment_uuid
                                           ,file_type = 'video'
                                           ,return_type = 'content'
                                          )
                od.upload_file( parent_id = video_folder
                               ,file_name = (attachment_timestamp+attachment_file_type).replace(" ", "_").replace(":", "-")
                               ,file_content = video_data
                              )
            if attachment_file_type.endswith(('jpeg','jpg')):
                photo_data = sm8.get_image( asset_uuid = attachment_uuid
                                           ,file_type = 'image'
                                           ,return_type = 'content'
                                          )
                od.upload_file( parent_id = photo_folder
                               ,file_name = (attachment_timestamp+attachment_file_type).replace(" ", "_").replace(":", "-")
                               ,file_content = photo_data
                              )
            last_upload = {'last_upload':attachment_edited_at}

    with open(lrj_path, 'w') as json_file:
            json.dump(last_upload, json_file)

if __name__ == '__main__':
    uploadFiles()