import json

import requests

from models.backend_models import TelemetryButch, Video


class BackendReporter:
    __AVAILABLE_PROTOCOLS = ['http', 'https']
    __MAX_PORT = 65536

    def __init__(
            self,
            type_http: str = 'http',
            host: str = 'localhost',
            port: int = 80
    ):
        self.__protocol = None
        self.__host = None
        self.__port = None
        self.__url = None

        self.protocol = type_http
        self.host = host
        self.port = port
        self.__set_url()

    @property
    def url(self):
        return self.__url

    def __set_url(self):
        self.__url = f'{self.protocol}://{self.host}:{self.port}/'

    @property
    def protocol(self):
        return self.__protocol

    @protocol.setter
    def protocol(self, value:str):
        value = value.lower()
        if value not in self.__AVAILABLE_PROTOCOLS:
            raise Exception(f'Protocol must be "http" or "https"\n'
                            f'\tYour protocol: {value}')
        self.__protocol = value
        self.__set_url()

    @property
    def host(self):
        return self.__host

    @host.setter
    def host(self, value):
        self.__host = value
        self.__set_url()

    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, value: int):
        if not (0 <= value <= self.__MAX_PORT):
            raise Exception(f'Port must be between [0; {self.__MAX_PORT}\n'
                            f'\tYour port: {value}')
        self.__port = value
        self.__set_url()


    def post_telemtry(self, telemtry: TelemetryButch):
        requests.post(f'{self.__url}network/telemetry/', json=telemtry.to_json())

    def post_video(self, video: Video):
        requests.post(f'{self.__url}network/video/', json=video.to_json())


    def get_events(self):
        return requests.get(f'{self.__url}events/').json()