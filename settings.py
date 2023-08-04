import datetime
import os

COPY_TIME = datetime.timedelta(hours=0, minutes=30, seconds=0)
SLEEP_TIME = datetime.timedelta(hours=0, minutes=5, seconds=0)


VERIFICATION_FILE = 'usb_worker.verify'
KEY = '55269ac1-cc82-4a97-9a91-48f8d7ccbf9f'

AREA_ID = int(os.environ['AREA_ID'])

SRC_DB_CONNECTION = os.environ['SRC_DB_CONNECTION']
SRC_VIDEO_PATH = os.environ['SRC_VIDEO_PATH']

DST_DB_NAME = 'Telemetry.db'
REPORT_FILE = 'report.txt'

