import pickle
import queue
import threading
import time

import pyudev
import blkinfo

from models.usb_device import UsbDevice


class LinuxUsbMonitor(threading.Thread):
    __ADD_ACTION = 'add'
    __REMOVE_ACTION = 'remove'

    def __init__(self, usb_ready_queue: queue.SimpleQueue):
        super().__init__(daemon=True)
        self.__usb_ready_queue = usb_ready_queue

        context = pyudev.Context()
        self.__monitor = self.__init_monitor(context)
        self.__lsblk_command = blkinfo.BlkDiskInfo()

    def __init_monitor(self, context):
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='usb')
        monitor.filter_by(subsystem='block', device_type='partition')
        monitor.filter_by_tag('systemd')
        return monitor

    def run(self):
        # actions_reaction = [self.__ADD_ACTION, self.__REMOVE_ACTION]
        for device in iter(self.__monitor.poll, None):
            if device.action == self.__ADD_ACTION:
                usb_device = self.__create_usb(device.device_path)
                if usb_device:
                    try:
                        usb_device.clear()
                        self.__usb_ready_queue.put(pickle.dumps(usb_device))
                    except Exception as e:
                        # TODO: Logging
                        print(f'Failed to process usb device "{usb_device}".\n\tReason: {e}')

    def __create_usb(self, device_path):
        dev_path = device_path
        fullname = dev_path.split('/')[-2:]
        if 'sd' not in fullname[0]:
            del fullname[0]
        time.sleep(1)
        device_additional_data = self.__lsblk_command.get_disks({'name': fullname[0]})
        if device_additional_data:
            if len(fullname) == 2:
                mount = list(filter(lambda x: x['name'] == fullname[1],
                                    device_additional_data[0]['children']))[0]['mountpoint']
            else:
                mount = device_additional_data[0]['mountpoint']
            print(f'MOUNTPOINT: {mount}')
            return UsbDevice(dev_path, mount)
        return None



