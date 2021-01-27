import os
from dotenv import load_dotenv
load_dotenv()

MASTER_API = os.environ.get('MASTER_API')
MASTER_SECRET = os.environ.get('MASTER_SECRET')

SLAVE_API = os.environ.get('SLAVE_API')
SLAVE_SECRET = os.environ.get('SLAVE_SECRET')

LEVERAGE = os.environ.get('LEVERAGE')
