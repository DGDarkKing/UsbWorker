import os
import pickle
import queue
import threading
import time

import pyudev
import blkinfo

import settings
from models.usb_device import UsbDevice


# TODO: РЕФАКТОРИНГ

class LinuxUsbMonitor(threading.Thread):
    __ADD_ACTION = 'add'
    __REMOVE_ACTION = 'remove'

    def __init__(self, usb_ready_queue: queue.SimpleQueue, verification_file):
        super().__init__(daemon=True)
        self.__usb_ready_queue = usb_ready_queue
        self.__verification_file = verification_file
        self.__access_key = settings.KEY

        context = pyudev.Context()
        self.__monitor = self.__init_monitor(context)
        self.__lsblk_command = blkinfo.BlkDiskInfo()

    def __init_monitor(self, context):
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='usb')
        monitor.filter_by(subsystem='block', device_type='partition')
        monitor.filter_by_tag('systemd')
        return monitor

    def __validate_usb(self, usb_device):
        verify_file = os.path.join(usb_device.mount_path, self.__verification_file)
        if usb_device.mount_exists and os.path.isfile(verify_file):
            with open(verify_file, 'r') as frs:
                lines = frs.readlines()
            return lines and lines[0] == self.__access_key
        return False

    def __clear_usb(self, usb_device):
        verify_file = os.path.join(usb_device.mount_path, self.__verification_file)
        if usb_device.mount_exists and os.path.isfile(verify_file):
            lines = []
            with open(verify_file, 'r') as frs:
                lines = frs.readlines()
            if len(lines) == 1:
                usb_device.clear(except_files=[self.__verification_file])
                return True
            return False
        return None

    def __find_mount(self, disk):
        if disk['mountpoint']:
            # TODO: replace 'plug_path'
            usb_device = UsbDevice('plug_path', disk['mountpoint'])
            if self.__validate_usb(usb_device):
                return usb_device
        if disk['children']:
            for subdisk in disk['children']:
                if usb_device:= self.__find_mount(subdisk):
                    return usb_device
        return None

    def __find_work_usb(self):
        # TODO: НУЖНО сделать сканирование через pyudev, чтобы использовать готовую функцию __create_usb
        work_usbs = []
        for disk in [x for x in self.__lsblk_command.get_disks() if x['name'][:2] == 'sd']:
            if usb:= self.__find_mount(disk):
                work_usbs.append(usb)

        work_usb = None
        delete_usbs = []
        for usb in work_usbs:
            cleared = self.__clear_usb(usb)
            if not cleared:
                delete_usbs.append(usb)
                if not work_usb and cleared is not None:
                    work_usb = usb

        work_usbs = [usb for usb in work_usbs if usb not in delete_usbs]
        self.__usb_ready_queue.put(pickle.dumps(work_usb))
        for usb in work_usbs:
            self.__usb_ready_queue.put(pickle.dumps(usb))


    def run(self):
        self.__find_work_usb()

        for device in iter(self.__monitor.poll, None):
            if device.action == self.__ADD_ACTION:
                if usb_device := self.__create_usb(device.device_path):
                    try:
                        self.__clear_usb(usb_device)
                        self.__usb_ready_queue.put(pickle.dumps(usb_device))
                    except Exception as e:
                        # TODO: Logging
                        print(f'Failed to process usb device "{usb_device}".\n\tReason: {e}')



    def __create_usb(self, device_path):
        dev_path = device_path
        fullname = dev_path.split('/')[-2:]
        if 'sd' != fullname[0][:2]:
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
            usb_device = UsbDevice(dev_path, mount)
            if self.__validate_usb(usb_device):
                return usb_device
        return None







