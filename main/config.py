import os
from dotenv import load_dotenv
load_dotenv()

MASTER_API = os.environ.get('MASTER_API')
MASTER_SECRET = os.environ.get('MASTER_SECRET')

try:
    NUM_SLAVES = int(os.environ.get('NUM_SLAVES'))
except:
    NUM_SLAVES = 1

if NUM_SLAVES < 1:
    NUM_SLAVES = 1

SLAVE_APIS = []
SLAVE_SECRETS = []
SLAVE_NAMES = []
for i in range(NUM_SLAVES):
    SLAVE_APIS.append(os.environ.get(f'SLAVE_API{i+1}'))
    SLAVE_SECRETS.append(os.environ.get(f'SLAVE_SECRET{i+1}'))
    SLAVE_NAMES.append(os.environ.get(f'SLAVE_SUBACC_NAME{i+1}'))

MASTER_LEVERAGE = int(os.environ.get("MASTER_LEVERAGE"))
SLAVE_LEVERAGE = int(os.environ.get("SLAVE_LEVERAGE"))