# Committing Commands
'''
cd /Users/sheldon.reimers/Documents/jupyterlab/umusa-plumbing/inventory_manager
git add . 
git commit -m "Correcting tab_name to week start"
git push origin main
'''
## SYSTEMS IMPORTING & VARIABLE CREATION
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
# sys.path.append('/Users/sheldon.reimers/Documents/jupyterlab/umusa-plumbing/config')
from lib import GoogleSheets
from lib import ServiceM8

# Access the secrets from environment variables
umusa_secret = json.loads(os.environ.get('UMUSA_SECRET'))
servicem8_secret = os.environ.get('SERVICEM8_SECRET')

## Activating API Systems
gpy = GoogleSheets(umusa_secret)
sm8 = ServiceM8(servicem8_secret)

# Script Variables
sm8_role = '2605a914-054a-46cc-948e-f300e516fecb'
sm_stock_form = '317211c5-7ba8-4e87-ba03-ac6e73e3eda6'
sheet_id = '1_fuV4FDD8LrLgbWrgMaq_o3Cz_d7yisSYFLWust1nOw'

# Setting datestamps for script for filtering to previous week
sa_timezone = pytz.timezone('Africa/Johannesburg')
now_date = dt.now(sa_timezone)

## SETTING DATE VARIABLES AND SYSTEM CHECKS FOR TAB CREATION
if now_date.weekday() == 0:  # Monday
    tab_name_str = (now_date - timedelta(days=7)).strftime("%Y-%m-%d")  # Monday date for the previous week
elif now_date.weekday() == 1: # Tuesday
    tab_name_str = (now_date - timedelta(days=1)).strftime("%Y-%m-%d")
    start_of_week_df = pd.DataFrame(columns=['full_name', 'inventory'])
    gpy.create_tab( sheet_id = sheet_id
                   ,tab_name = tab_name_str
                  )
    gpy.df_to_sheet( df=start_of_week_df
                    ,sheet_id=sheet_id
                    ,tab_name=tab_name_str
                    ,starting_cell='A1'
                    ,is_append=False)
else:
    days_difference = now_date.weekday()
    week_date = now_date - timedelta(days=days_difference)
    tab_name_str = week_date.strftime("%Y-%m-%d")

previous_day_date = now_date - timedelta(days=1)
previous_day_str = previous_day_date.strftime("%Y-%m-%d")

## Retrieving staff data and filtering to active staff
staff_cols = [ 'uuid'
              ,'first'
              ,'last'
              ,'email'
              ,'mobile'
              ]

staff_data = pd.DataFrame(sm8.get_all_staff())

active_staff = staff_data[(staff_data['security_role_uuid'] == '2605a914-054a-46cc-948e-f300e516fecb')
                         &
                         (staff_data['active'] == 1)].reset_index(drop = True)[staff_cols]

active_staff['full_name'] = active_staff['first'] + ' '+active_staff['last']
active_staff.drop(labels = ['first','last'],axis = 1,inplace = True)

## Getting form responses & filtering for the date
all_form_responses = sm8._get_form_responses(form_uuid = '317211c5-7ba8-4e87-ba03-ac6e73e3eda6')

for d in all_form_responses:
    # Split the timestamp string at the space character and keep only the date part
    d['date_str'] = d['timestamp'].split()[0]

latest_responses = [d for d in all_form_responses if previous_day_str == d['date_str']]

gsheet_df = gpy.sheet_to_df( sheet_id = sheet_id
                            ,tab_name = tab_name_str
                            ,starting_cell = 'A1'
                            ,ending_cell=gpy.get_last_column(sheet_id = sheet_id
                                                             ,tab_name = tab_name_str
                                                             ,starting_cell='A1'
                                                            )
                           )

if len(latest_responses) == 0:
    gsheet_df[previous_day_str] = ''
    gpy.df_to_sheet( df = gsheet_df.fillna(0)
                    ,sheet_id = sheet_id
                    ,tab_name = tab_name_str
                    ,starting_cell = 'A1'
                    ,is_append = False
               )
else:
    updated_responses = []
    
    for x in range(len(latest_responses)):
        responded_at = latest_responses[x]['timestamp']
        staff_uuid = latest_responses[x]['form_by_staff_uuid']
        job_uuid = latest_responses[x]['regarding_object_uuid']
        form_responses = json.loads(latest_responses[x]['field_data'])
        updated_answers = []
        for i in range(len(form_responses)):
            answer = form_responses[i]
            if (answer['FieldType'] == 'Number') and (answer['Response'] != ''):
                answer['responded_at'] = responded_at
                answer['staff_uuid'] = staff_uuid
                answer['job_uuid'] = job_uuid
                response = answer['Response'].replace(',','.')
                answer['Response'] = response
                answer.pop('SortOrder')
                answer.pop('UUID')
                updated_answers.append(answer)
        updated_responses.extend(updated_answers)
        
    updated_respnses_df = pd.DataFrame(updated_responses)
    
    merged_df = updated_respnses_df.merge( active_staff
                                          ,how = 'inner'
                                          ,left_on = 'staff_uuid'
                                          ,right_on = 'uuid'
                                         ).drop(labels = [ 'staff_uuid'
                                                          ,'uuid'
                                                          ,'FieldType']
                                                ,axis = 1).astype({'Response':float})
    
    previous_day_agg_df = merged_df.groupby([ 'full_name'
                                             ,'Question']).sum('Response'
                                                              ).reset_index().rename(columns = {'Response':previous_day_str
                                                                                  ,'Question':'inventory'})
    try:
        gsheet_df = gpy.sheet_to_df( sheet_id = sheet_id
                                    ,tab_name = tab_name_str
                                    ,starting_cell = 'A1'
                                    ,ending_cell=gpy.get_last_column(sheet_id = sheet_id
                                                                     ,tab_name = tab_name_str
                                                                     ,starting_cell='A1'
                                                                    )
                                   )
    
        complete_ref = gsheet_df[[ 'full_name'
                                  ,'inventory']].append(previous_day_agg_df[[ 'full_name'
                                                                             ,'inventory']]
                                                       ).drop_duplicates(ignore_index = True)
    
    
        full_merge = complete_ref.merge( gsheet_df
                                        ,how = 'left'
                                        ,on = ['full_name','inventory']
                                       ).merge( previous_day_agg_df
                                               ,how = 'left'
                                               ,on = ['full_name','inventory']
                                              )
    
        gpy.df_to_sheet( full_merge.fillna(0)
                        ,sheet_id = sheet_id
                        ,tab_name = tab_name_str
                        ,starting_cell = 'A1'
                        ,is_append = False
                       )
    except Exception as e:
        if 'Unable to parse range' in str(e):
            gpy.df_to_sheet( previous_day_agg_df.fillna(0)
                            ,sheet_id = sheet_id
                            ,tab_name = tab_name_str
                            ,starting_cell = 'A1'
                            ,is_append = False
                           )
        else:
            print(str(e))