import datetime
import os.path
import pickle
import queue
import time
from collections import OrderedDict

import peewee

import settings
from copy_telemetry_strategy import CopyTelemetryStrategy
from copy_to_device_facade import CopyToDeviceFacade
from copy_video_strategy import CopyVideoStrategy
from models.usb_device import UsbDevice
from usb_monitor import LinuxUsbMonitor
import models.db_models as db



def can_get_started(usb_device: UsbDevice):
    return usb_device.mount_exists


def initialize_database(database_context: peewee.Database):
    if db.DST_DB is not None:
        db.DST_DB.close()
    db.DST_DB = database_context
    db.init_db(db.DST_DB)
    db.create_tables(db.DST_DB)


def initilize_usb(usb_device: UsbDevice):
    with open(usb_device.get_file(settings.VERIFICATION_FILE), 'r') as frs:
        lines = frs.readlines()
        lines = [res for x in lines if (res := x.strip())]
        has_file_init = len(lines) != 1
    if not has_file_init:
        with open(usb_device.get_file(settings.VERIFICATION_FILE), 'a') as fws:
            fws.write(str(settings.AREA_ID))


prefixes = ['telemetry', 'video']
target_strategies = {prefixes[0]: CopyTelemetryStrategy(None, None, prefixes[0]),
                     prefixes[1]: CopyVideoStrategy(None, None, prefixes[1], settings.SRC_VIDEO_PATH)}

def start_copy(usb_device: UsbDevice):
    copier = None
    try:
        # TODO LOGIC
        copier = CopyToDeviceFacade(usb_device, settings.REPORT_FILE, target_strategies, settings.COPY_TIME)
        while not usb_device.mount_exists and not copier.copy():
            time.sleep(settings.COPY_TIME.total_seconds())
        copier.release()
    except KeyboardInterrupt:
        print('exit')
        raise
    except Exception as e:
        print(e)  # TODO: Log
    if copier is not None:
        copier.release()


def main():
    db.init_db(db.SRC_DB)
    usb_ready_queue = queue.SimpleQueue()
    usb_monitor = LinuxUsbMonitor(usb_ready_queue,
                                  settings.VERIFICATION_FILE, settings.KEY)
    usb_monitor.start()
    CopyToDeviceFacade.create_report_file(settings.REPORT_FILE)

    while True:
        usb_device: UsbDevice = pickle.loads(usb_ready_queue.get())

        if not can_get_started(usb_device):
            continue
        db_context = peewee.SqliteDatabase(os.path.join(usb_device.mount_path, settings.DST_DB_NAME))
        try:
            initialize_database(db_context)
        except Exception as e:
            print(e) # TODO: Log
            db_context.close()
            continue

        initilize_usb(usb_device)
        start_copy(usb_device)




if __name__ == '__main__':
    main()