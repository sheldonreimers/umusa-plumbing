# Committing Commands
'''
cd /Users/sheldon.reimers/Documents/jupyterlab/umusa-plumbing/inventory_manager
git add . 
git commit -m "Fixing First Line"
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

# Access the secrets from environment variables
umusa_secret = json.loads(os.environ.get('UMUSA_SECRET'))
servicem8_secret = os.environ.get('SERVICEM8_SECRET')

## Activating API Systems
gpy = GoogleSheets(umusa_secret)
sm8 = ServiceM8(servicem8_secret)

# Setting datestamps for script for filtering to previous day
sa_timezone = pytz.timezone('Africa/Johannesburg')
now_date = dt.now(sa_timezone)

# Setting of search parameters & tab_name configuration
if now_date.weekday() == 0:
    week_date = now_date - timedelta(days=7)
    tab_name = week_date.strftime("%Y-%m-%d")
    if now_date.hour <= 6:
        search_date = now_date - timedelta(days=1)
        search_date_str = search_date.strftime("%Y-%m-%d")
    else:
        search_date_str = now_date.strftime("%Y-%m-%d")
else:
    days_difference = now_date.weekday()
    week_date = now_date - timedelta(days=days_difference)
    tab_name = week_date.strftime("%Y-%m-%d")
    if now_date.hour <= 6:
        search_date = now_date - timedelta(days=1)
        search_date_str = search_date.strftime("%Y-%m-%d")
    else:
        search_date_str = now_date.strftime("%Y-%m-%d")
        
## Retrieving staff data and filtering to active staff
staff_cols = [ 'uuid'
              ,'first'
              ,'last'
              ]

col_name = (now_date - timedelta(days=1)).strftime("%Y-%m-%d")

# Primary Sheet ID
# primary_sheet_id = '1_fuV4FDD8LrLgbWrgMaq_o3Cz_d7yisSYFLWust1nOw'
# Primary Sheet ID - Test Sheets
primary_sheet_id = '1qiNp37402dQ6eO6dczUYby19WpWv-r0lzalU1fr2DgA'

dated_responses = sm8.get_form_responses_by_date( '317211c5-7ba8-4e87-ba03-ac6e73e3eda6'
                                                 ,search_date_str
                                                )

filtered_answers = []
for x in dated_responses:
    filtered_items = []
    for i in x:
        if i['FieldType'] == 'Number':
            filtered_items.append(i)
    filtered_answers.append(filtered_items)
    
response_df = pd.DataFrame([item for sublist in filtered_answers for item in sublist])

staff_data = pd.DataFrame(sm8.get_all_staff())

active_staff = staff_data[(staff_data['security_role_uuid'] == '2605a914-054a-46cc-948e-f300e516fecb')
                         &
                         (staff_data['active'] == 1)].reset_index(drop = True)[staff_cols]

active_staff['full_name'] = active_staff['first'] +' '+active_staff['last']

merged_df = response_df.merge( active_staff
                              ,how = 'left'
                              ,left_on = 'staff_uuid'
                              ,right_on = 'uuid'
                             ).drop(labels = [ 'staff_uuid'
                                              ,'uuid'
                                              ,'first'
                                              ,'last'
                                              ,'SortOrder'
                                             ]
                                    ,axis = 1
                                   )

merged_df['Response'] = merged_df['Response'].str.replace(',', '.')

filtered_df = merged_df[merged_df['Response'] != ''].astype({'Response':float})

summed_df = filtered_df.groupby(['full_name'
                                 ,'Question']).sum('Response'
                                                  ).reset_index().rename(columns = {'Response':col_name
                                                                                    ,'Question':'inventory'}).sort_values(by = ['inventory'
                                                                                                                                ,'full_name'],ascending=[True,True])

tab_lookup = gpy.lookup_tab( primary_sheet_id
                            ,tab_name
                           )

if tab_lookup:
    current_data = gpy.sheet_to_df( sheet_id = primary_sheet_id
                                   ,tab_name = tab_name
                                   ,starting_cell = 'A1'
                                   ,ending_cell = gpy.get_last_column(sheet_id = primary_sheet_id
                                                                      ,tab_name = tab_name
                                                                      ,starting_cell = 'A1'
                                                                     )
                                  )
    ref_df = summed_df[[ 'full_name'
                        ,'inventory']].append(current_data[[ 'full_name'
                                                            ,'inventory']]).drop_duplicates(ignore_index = True)
    sum_merged = ref_df.merge( current_data[['full_name','inventory',col_name]]
                              ,how = 'left'
                              ,on = ['full_name','inventory']
                             ).merge( summed_df
                                     ,how = 'left'
                                     ,on = ['full_name','inventory']
                                     ).fillna(0).astype({ col_name+'_x':float
                                                         ,col_name+'_x':float})
    sum_merged[col_name] = sum_merged[col_name+'_x'] + sum_merged[col_name+'_y']
    sum_completed = sum_merged.drop(labels = [col_name+'_x',col_name+'_y'], axis =1)
    final_df = current_data.merge( sum_completed
                                  ,how = 'left'
                                  ,on = ['full_name','inventory']
                                  ,suffixes=('_cur','')
                                 ).drop(labels = col_name+'_cur'
                                        ,axis = 1
                                       )
else:
    gpy.create_tab( sheet_id = primary_sheet_id
                   ,tab_name = tab_name
                  )
    gpy.df_to_sheet( df = summed_df
                    ,sheet_id = primary_sheet_id
                    ,tab_name = tab_name
                    ,starting_cell = 'A1'
                    ,is_append = False
                   )