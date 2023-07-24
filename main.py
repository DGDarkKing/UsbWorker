import os.path
import pickle
import queue

import peewee

import settings
from copier import Copier
from models.usb_device import UsbDevice
from usb_monitor import LinuxUsbMonitor
import models.db_models as db


def main():
    db.init_db(db.SRC_DB)

    usb_ready_queue = queue.SimpleQueue()
    usb_monitor = LinuxUsbMonitor(usb_ready_queue, settings.VERIFICATION_FILE)
    usb_monitor.start()

    while True:
        usb_device: UsbDevice = pickle.loads(usb_ready_queue.get())

        if db.DST_DB is not None:
            db.DST_DB.close()
        if not usb_device.mount_exists:
            continue

        db.DST_DB = peewee.SqliteDatabase(os.path.join(usb_device.mount_path, settings.DST_DB_NAME))
        db.init_db(db.DST_DB)
        db.create_tables(db.DST_DB)

        copier = Copier(usb_device, settings.REPORT_FILE)
        copier.start_copy()




if __name__ == '__main__':
    main()