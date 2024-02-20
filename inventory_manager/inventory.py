# System Library Import & directories
import os, sys
home_dir = 'umusa-plumbing'

# Working Libraries
import jira,shlex,time,requests,subprocess,json,io,shutil,csv,requests,json,zipfile,datetime,pytz, atexit
import pandas as pd
import numpy as np

from datetime import timedelta
from datetime import time
from tqdm.notebook import tqdm, trange
from ast import literal_eval
from pretty_html_table import build_table
from datetime import datetime as dt
from pretty_html_table import build_table

# Google Libraries
from apiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account

sys.path.append(home_dir+'/config')
from lib import GoogleSheets
from lib import ServiceM8