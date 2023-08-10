import abc
import datetime
from abc import ABC
from typing import Callable

from backend_reporter import BackendReporter



class CopyToBackendStrategy(ABC):
    def __init__(
            self,
            http_client: BackendReporter | None,
            set_last_dt_delegate: Callable | None,
            get_event_id_delegate: Callable | None,
            prefix: str,
            target_event_name: str
    ):
        self.set_last_dt_delegate = set_last_dt_delegate
        self.get_event_id_delegate = get_event_id_delegate
        self.http_client = http_client
        self.__prefix = prefix
        self.__target_event_name = target_event_name

    def __del__(self):
        if self.set_last_dt_delegate is not None:
            self.set_last_dt_delegate = None

    @property
    def prefix(self):
        return self.__prefix

    @abc.abstractmethod
    def copy(self, dt_from: datetime.datetime, dt_to: datetime.datetime):
        pass
