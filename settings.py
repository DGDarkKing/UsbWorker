import datetime
import os

COPY_TIME = datetime.timedelta(hours=0, minutes=2, seconds=0)

SRC_DB_CONNECTION = os.environ['SRC_DB_CONNECTION']

AREA_ID = int(os.environ['AREA_ID'])

PROTOCOL = os.environ['BACKEND_PROTOCOL']
HOST = os.environ['BACKEND_HOST']
PORT = int(os.environ['BACKEND_PORT'])
REPORT_FILE = 'report.txt'


