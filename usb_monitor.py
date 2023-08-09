import os
import pickle
import queue
import threading
import time

import pyudev
import blkinfo

from models.usb_device import UsbDevice
from extends import lsblk_fields as lsblk
from extends import pyudev_value as pyudev_vals



class LinuxUsbMonitor(threading.Thread):
    __TARGET_SUBSYSTEM = pyudev_vals.Subsystem.BLOCK
    __TARGET_DEVICE_TYPE = pyudev_vals.DeviceType.PARTITION
    __TARGET_TAG = pyudev_vals.Tag.SYSTEMD
    __PARENT_SUBSYSTEM = pyudev_vals.Subsystem.USB
    __ADD_ACTION = pyudev_vals.Action.ADD
    __DISC_PREFIX = 'sd'
    __RESERVE_SPACE = 10*1024

    def __init__(self, usb_ready_queue: queue.SimpleQueue, verification_file, access_key):
        super().__init__(daemon=True)
        self.__usb_ready_queue = usb_ready_queue
        self.__verification_file = verification_file
        self.__access_key = access_key

    def __init_monitor(self):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem=self.__TARGET_SUBSYSTEM,
                          device_type=self.__TARGET_DEVICE_TYPE)
        monitor.filter_by_tag(self.__TARGET_TAG)
        return monitor

    @property
    def ls_block(self):
        return blkinfo.BlkDiskInfo()

    def __send_usb(self, usb_device: UsbDevice):
        self.__usb_ready_queue.put(pickle.dumps(usb_device))

    def __is_required_device(self, device: pyudev.Device):
        return device.find_parent(self.__PARENT_SUBSYSTEM) is not None

    def run(self):
        self.__find_work_usb()
        monitor = self.__init_monitor()
        for device in iter(monitor.poll, None):
            if (device.action == self.__ADD_ACTION
                    and (usb_device := self.__create_usb(device.device_path))):
                try:
                    self.__clear_usb(usb_device)
                    self.__send_usb(usb_device)
                except Exception as e:
                    print(f'Failed to process usb device "{usb_device}".\n\tReason: {e}')

    def __find_work_usb(self):
        block_devices = pyudev.Context().list_devices(subsystem=self.__TARGET_SUBSYSTEM,
                                                      DEVTYPE=self.__TARGET_DEVICE_TYPE,
                                                      tag=self.__TARGET_TAG)
        suitable_usbs = [
            usb
            for device in block_devices
            if self.__is_required_device(device) and (usb := self.__create_usb(device.device_path))
        ]
        if not suitable_usbs:
            return
        paramount_usbs = [usb for usb in suitable_usbs if not self.__clear_usb(usb)]
        for usb in paramount_usbs:
            self.__send_usb(usb)
        suitable_usbs = [usb for usb in suitable_usbs if usb not in paramount_usbs]
        for usb in suitable_usbs:
            self.__send_usb(usb)

    def __create_usb(self, device_path):
        dev_path = device_path
        usb_host_name = dev_path.split('/')[-2:][0]
        time.sleep(1)
        device_data = self.ls_block.get_disks({lsblk.name: usb_host_name})
        if not device_data:
            return None
        device_data = device_data[0]
        mounted_partition = device_data[lsblk.children][0]
        mount = mounted_partition[lsblk.mountpoint]
        usb_device = UsbDevice(dev_path, mount, self.__RESERVE_SPACE)
        return usb_device if self.__validate_usb(usb_device) else None

    def __validate_usb(self, usb_device: UsbDevice):
        verify_file = os.path.join(usb_device.mount_path, self.__verification_file)
        if usb_device.mount_exists and os.path.isfile(verify_file):
            with open(verify_file, 'r') as frs:
                line = frs.readline().strip()
            return line and line == self.__access_key
        return False

    def __clear_usb(self, usb_device: UsbDevice):
        verify_file = os.path.join(usb_device.mount_path, self.__verification_file)
        with open(verify_file, 'r') as frs:
            lines = frs.readlines()
        lines = [res for x in lines if (res := x.strip())]
        if len(lines) == 1:
            usb_device.clear(except_files=[self.__verification_file])
            return True
        return False






