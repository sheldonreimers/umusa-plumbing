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
umusa_secret = os.environ.get('UMUSA_SECRET')
servicem8_secret = os.environ.get('SERVICEM8_SECRET')

# Print the secrets to verify
print("UMUSA_SECRET:", umusa_secret)
print("SERVICEM8_SECRET:", servicem8_secret)
