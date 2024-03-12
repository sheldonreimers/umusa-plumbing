# Committing Commands
'''
cd /Users/sheldon.reimers/Documents/jupyterlab/umusa-plumbing/file_uploader
git add . 
git commit -m "Adding in OneDrive library"
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
umusa_secret = json.loads(os.environ.get('UMUSA_AZURE'))

## Activating API Systems
gpy = GoogleSheets(umusa_secret)
sm8 = ServiceM8(servicem8_secret)
od = OneDrive(umusa_secret)