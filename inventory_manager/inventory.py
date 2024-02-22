# System Library Import & directories
import os
import sys

# Working Libraries
import time,requests,json,pytz
import pandas as pd

from datetime import timedelta
from tqdm.notebook import tqdm, trange
from datetime import datetime as dt

# Add the directory containing your custom libraries to the path
sys.path.append('config')
from lib import GoogleSheets
from lib import ServiceM8

# Access the secrets from environment variables
umusa_secret = json.loads(os.environ.get('UMUSA_SECRET'))
servicem8_secret = os.environ.get('SERVICEM8_SECRET')

## Activating API Systems
gpy = GoogleSheets(umusa_secret)
sm8 = ServiceM8(servicem8_secret)

## Setting datestamps for script for filtering to previous week
sa_timezone = pytz.timezone('Africa/Johannesburg')
now_date = dt.now(sa_timezone)
days_difference = now_date.weekday() + 7  # 0 represents Monday
previous_monday_date = now_date - timedelta(days=days_difference)
previous_monday_str = previous_monday_date.strftime("%Y-%m-%d")
following_sunday_date = previous_monday_date + timedelta(days=6)
following_sunday_str = following_sunday_date.strftime("%Y-%m-%d")

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

all_form_responses = sm8.get_form_responses(form_uuid = '317211c5-7ba8-4e87-ba03-ac6e73e3eda6')

latest_responses = [d for d in all_form_responses if previous_monday_str <= d['timestamp'] <= following_sunday_str]

updated_responses = []

for x in tqdm(range(len(latest_responses)), desc='primary_factoring'):
    responded_at = latest_responses[x]['timestamp']
    staff_uuid = latest_responses[x]['form_by_staff_uuid']
    job_uuid = latest_responses[x]['regarding_object_uuid']
    form_responses = json.loads(latest_responses[x]['field_data'])
    time.sleep(0.1)
    updated_answers = []
    for i in tqdm(range(len(form_responses)), desc='answer_refactoring'):
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
            time.sleep(0.01)
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

agg_df = merged_df.groupby([ 'full_name'
                            ,'Question']).sum('Response'
                                             ).reset_index().rename(columns = {'Question':'inventory_name'})

if len(agg_df) > 0:
    gpy.create_tab( sheet_id = '1_fuV4FDD8LrLgbWrgMaq_o3Cz_d7yisSYFLWust1nOw'
                   ,tab_name = previous_monday_str
                  )
    gpy.df_to_sheet( df = agg_df
                    ,sheet_id = '1_fuV4FDD8LrLgbWrgMaq_o3Cz_d7yisSYFLWust1nOw'
                    ,tab_name = previous_monday_str
                    ,starting_cell = 'A1'
                    ,is_append = False
                    ,include_header=True
                   )