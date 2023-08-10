import datetime

from copy_strategy import CopyToBackendStrategy
from extends import create_file, strings_to_dict, PrefixSpliter

from backend_reporter import BackendReporter


###     Abbreviation "dt" is mean "datetime"
class HttpCopyFacade:
    __DATETIME_FORMAT: str = '%m/%d/%Y %H:%M:%S'

    def __init__(
            self,
            http_client: BackendReporter,
            report_file: str,
            copy_strategies: dict[str, CopyToBackendStrategy],
            copy_gap_time: datetime.timedelta
    ):
        self.__http_client = http_client
        self.__report_file = report_file
        self.__copy_gap_time = copy_gap_time
        self.__copy_strategies = copy_strategies
        self.__events = self.__http_client.get_events()
        self.__init_strategies()

        prefixes = list(self.__copy_strategies.keys())
        self.__last_dt_dict: dict[str, datetime] = self.__check_file(self.__report_file, prefixes)

    def __init_strategies(self):
        for strategy in self.__copy_strategies.values():
            strategy.http_client = self.__http_client
            strategy.set_last_dt_delegate = self.__set_dt
            strategy.get_event_id_delegate = self.get_event_id

    def release(self):
        for strategy in self.__copy_strategies.values():
            if strategy.http_client is not None and strategy.http_client == self.__http_client:
                strategy.http_client = None
            if strategy.set_last_dt_delegate is not None and strategy.set_last_dt_delegate == self.__set_dt:
                strategy.set_last_dt_delegate = None
            if strategy.get_event_id_delegate is not None and strategy.get_event_id_delegate == self.get_event_id:
                strategy.get_event_id_delegate = None

    def __set_dt(self, prefix: str, value: datetime.datetime):
        self.__last_dt_dict[prefix] = value
        self.__log(self.__report_file, self.__last_dt_dict)

    def get_event_id(self, event_name):
        return next((event_data['id']
                     for event_data in self.__events
                     if event_data['label'] == event_name),
                    None)

    def copy(self):
        now = datetime.datetime.now()
        for prefix, strategy in self.__copy_strategies.items():
            last_strategy_dt = self.__last_dt_dict[prefix]
            strategy_delta_time = now - last_strategy_dt
            while strategy_delta_time > self.__copy_gap_time:
                if not strategy.copy(last_strategy_dt, last_strategy_dt + self.__copy_gap_time):
                    return False
                now = datetime.datetime.now()
                last_strategy_dt = self.__last_dt_dict[prefix]
                strategy_delta_time = now - last_strategy_dt
        return True

    @staticmethod
    def create_report_file(report_file: str, prefixes: list[str]):
        create_file(report_file)
        HttpCopyFacade.__check_file(report_file, prefixes)

    @staticmethod
    def __dict_to_dt(data, key):
        if key in data:
            return datetime.datetime.strptime(data[key], HttpCopyFacade.__DATETIME_FORMAT)
        return None

    @staticmethod
    def __check_file(report_file, prefixes):
        text_spliter = PrefixSpliter(prefixes)
        now = datetime.datetime.now()
        last_dt_dict: dict[str, datetime] = {prefix: now for prefix in prefixes}

        with open(report_file, 'r') as frs:
            file_data = frs.read().strip()
        if file_data:
            not_enough_data = False
            data: dict = strings_to_dict(file_data.splitlines(), text_spliter)
            for prefix in prefixes:
                if dt := HttpCopyFacade.__dict_to_dt(data, prefix):
                    last_dt_dict[prefix] = dt
                else:
                    not_enough_data = True

            if not_enough_data:
                HttpCopyFacade.__log(report_file, last_dt_dict)
        else:
            HttpCopyFacade.__log(report_file, last_dt_dict)
        return last_dt_dict

    @staticmethod
    def __log(report_file, last_dt_dict: dict[str, datetime]):
        with open(report_file, 'r+') as fws:
            log_text = '\n'.join(
                [f'{k} {v.strftime(HttpCopyFacade.__DATETIME_FORMAT)}'
                 for k, v in last_dt_dict.items()]
            )
            fws.write(log_text)
