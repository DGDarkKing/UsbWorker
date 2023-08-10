import datetime


from copy_strategy import CopyStrategy
from extends.general import create_file, strings_to_dict, PrefixSpliter
from models.usb_device import UsbDevice


###     Abbreviation "dt" is mean "datetime"
class CopyToDeviceFacade:
    __DATETIME_FORMAT: str = '%m/%d/%Y %H:%M:%S'

    def __init__(
            self,
            usb_device: UsbDevice,
            report_file: str,
            copy_strategies: dict[str, CopyStrategy],
            copy_gap_time: datetime.timedelta
    ):
        self.__usb_device = usb_device
        self.__report_file = report_file
        self.__copy_gap_time = copy_gap_time
        self.__copy_strategies = copy_strategies
        self.__init_strategies()

        prefixes = list(self.__copy_strategies.keys())
        self.__last_dt_dict: dict[str, datetime] = self.__check_file(self.__report_file, prefixes)

    def __init_strategies(self):
        for strategy in self.__copy_strategies.values():
            strategy.usb_device = self.__usb_device
            strategy.set_last_dt_delegate = self.__set_dt
    def release(self):
        for strategy in self.__copy_strategies.values():
            if strategy.usb_device is not None and strategy.usb_device == self.__usb_device:
                strategy.usb_device = None
            if strategy.set_last_dt_delegate is not None and strategy.set_last_dt_delegate == self.__set_dt:
                strategy.set_last_dt_delegate = None

    def __set_dt(self, prefix: str, value: datetime.datetime):
        self.__last_dt_dict[prefix] = value
        self.__log(self.__report_file, self.__last_dt_dict)

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
        CopyToDeviceFacade.__check_file(report_file, prefixes)

    @staticmethod
    def __dict_to_dt(data, key):
        if key in data:
            return datetime.datetime.strptime(data[key], CopyToDeviceFacade.__DATETIME_FORMAT)
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
                if dt := CopyToDeviceFacade.__dict_to_dt(data, prefix):
                    last_dt_dict[prefix] = dt
                else:
                    not_enough_data = True

            if not_enough_data:
                CopyToDeviceFacade.__log(report_file, last_dt_dict)
        else:
            CopyToDeviceFacade.__log(report_file, last_dt_dict)
        return last_dt_dict

    @staticmethod
    def __log(report_file, last_dt_dict: dict[str, datetime]):
        with open(report_file, 'r+') as fws:
            log_text = '\n'.join(
                [f'{k} {v.strftime(CopyToDeviceFacade.__DATETIME_FORMAT)}'
                 for k, v in last_dt_dict.items()]
            )
            fws.write(log_text)
