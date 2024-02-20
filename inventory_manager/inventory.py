# System Library Import & directories
import os, sys
home_dir = 'umusa-plumbing'

# Working Libraries
import time,requests,json,pytz
import pandas as pd

from datetime import timedelta
from tqdm.notebook import tqdm, trange
from datetime import datetime as dt

<<<<<<< HEAD
sys.path.append('config')
=======
sys.path.append('/config')
>>>>>>> f8db2bd (repo setup)
from lib import GoogleSheets
from lib import ServiceM8
