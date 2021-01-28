import os
from dotenv import load_dotenv
load_dotenv()
import django_heroku

try:
    IS_PRODUCTION = int(os.environ.get('IS_PRODUCTION'))
except:
    IS_PRODUCTION = 1

if IS_PRODUCTION==1:
    from .conf.production.settings import *
else:
    from .conf.development.settings import *

django_heroku.settings(locals())
