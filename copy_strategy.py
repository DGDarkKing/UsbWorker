import abc
import datetime
from abc import ABC
from typing import Callable

from models.usb_device import UsbDevice



class CopyStrategy(ABC):
    def __init__(
            self,
            usb_device: UsbDevice,
            set_last_dt_delegate: Callable,
            prefix: str
    ):
        self.set_last_dt_delegate = set_last_dt_delegate
        self.usb_device = usb_device
        self.__prefix = prefix

    def __del__(self):
        if self.set_last_dt_delegate != None:
            self.set_last_dt_delegate = None

    @property
    def prefix(self):
        return self.__prefix

    @abc.abstractmethod
    def copy(self, dt_from: datetime.datetime, dt_to: datetime.datetime):
        pass
