from enum import Enum


class Subsystem:
    BLOCK = 'block'
    USB = 'usb'


class DeviceType:
    USB_DEVICE = 'usb_device'
    USB_INTERFACE = 'usb_interface'
    DISK = 'disk'
    PARTITION = 'partition'


class Tag:
    SYSTEMD = 'systemd'


class Action:
    ADD = 'add'
    REMOVE = 'remove'
