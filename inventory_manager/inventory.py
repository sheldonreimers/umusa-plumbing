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

staff_data = sm8.get_all_staff()

print(staff_data)