import os
from dotenv import load_dotenv
load_dotenv()
import django_heroku

IS_PRODUCTION = os.environ.get('IS_PRODUCTION')

if IS_PRODUCTION==1:
    from .conf.production.settings import *
else:
    from .conf.development.settings import *

django_heroku.settings(locals())
