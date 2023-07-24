import datetime
import os
import time
from itertools import groupby

from playhouse.shortcuts import model_to_dict

import settings
from extends import create_file, strings_to_dict, PrefixSpliter
from models.usb_device import UsbDevice
import models.db_models as db


###     Abbreviation "dt" is mean "datetime"

class Copier:
    __TELEMETRY_REPORT_PREFIX = 'telemetry'
    __VIDEO_REPORT_PREFIX = 'video'
    __DATETIME_FORMAT: str = '%m/%d/%Y %H:%M:%S'

    def __init__(self, usb_device: UsbDevice, report_file):
        self.__usb_device = usb_device
        self.__report_file = report_file
        create_file(self.__report_file)
        now = datetime.datetime.now()
        self.__last_telemetry_dt = now
        self.__last_video_dt = now
        self.__text_spliter = PrefixSpliter([self.__TELEMETRY_REPORT_PREFIX, self.__VIDEO_REPORT_PREFIX])
        self.__check_file()


    def __dict_to_dt(self, data, key):
        if key in data:
            return datetime.datetime.strptime(data[key], self.__DATETIME_FORMAT)
        return None


    def __check_file(self):
        with open(self.__report_file, 'r') as frs:
            file_data = frs.read().strip()
        not_enough_data = False
        if file_data:
            data: dict = strings_to_dict(file_data.splitlines(), self.__text_spliter)
            dt = self.__dict_to_dt(data, self.__TELEMETRY_REPORT_PREFIX)
            if dt:
                self.__last_telemetry_dt = dt
            else:
                not_enough_data = True

            dt = self.__dict_to_dt(data, self.__VIDEO_REPORT_PREFIX)
            if dt:
                self.__last_video_dt = dt
            else:
                not_enough_data = True

            if not_enough_data:
                self.__log()
        else:
            self.__log()

    def __log(self):
        with open(self.__report_file, 'r+') as fws:
            fws.write(f'{self.__TELEMETRY_REPORT_PREFIX} {self.__last_telemetry_dt.strftime(self.__DATETIME_FORMAT)}\n'
                      f'{self.__VIDEO_REPORT_PREFIX} {self.__last_video_dt.strftime(self.__DATETIME_FORMAT)}')

    def start_copy(self):
        if not self.__usb_device.mount_exists:
            return
        start_time = datetime.datetime.now()
        while os.path.exists(self.__usb_device.mount_path):
            time.sleep(settings.SLEEP_TIME.total_seconds())
            if not self.__usb_device.mount_exists:
                return
            elapsed_time = datetime.datetime.now() - start_time
            if elapsed_time < settings.COPY_TIME:
                continue
            if not self.copy_data(start_time, start_time + settings.COPY_TIME):
                return
            start_time = start_time + settings.COPY_TIME

    def copy_data(self, dt_from: datetime.datetime, dt_to: datetime.datetime):
        time.sleep(1)
        return self.copy_telemetry(dt_from, dt_to) and self.copy_videos(dt_from, dt_to)


    def copy_telemetry(self, dt_from: datetime.datetime, dt_to: datetime.datetime):
        front_loader_data = list(
            db.FrontLoader_EventTelemetryNetrwork_Model.using(db.SRC_DB).select().where(
                (dt_from <= db.FrontLoader_EventTelemetryNetrwork_Model.record_dtime)
                & (db.FrontLoader_EventTelemetryNetrwork_Model.record_dtime < dt_to)
            ).order_by(db.FrontLoader_EventTelemetryNetrwork_Model.video)
        )

        grouped_telemetry = dict(groupby(front_loader_data, key=lambda x: x.video_id))
        if not self.__usb_device.mount_exists:
            return False
        db.Video.using(db.DST_DB).create_plugs(list(grouped_telemetry.keys()))
        exist_data = [data.id
                      for data in db.FrontLoader_EventTelemetryNetrwork_Model.select(
                db.FrontLoader_EventTelemetryNetrwork_Model.id).where(
                db.FrontLoader_EventTelemetryNetrwork_Model.id << [data.id for data in front_loader_data]
            )
                      ]
        if inserted_data := [data for data in front_loader_data if data.id not in exist_data]:
            db.FrontLoader_EventTelemetryNetrwork_Model.insert_many(map(db.BaseEventTelemetryNetwork.map_to_dict,
                                                                        inserted_data)
                                                                    ).execute()
        self.__last_telemetry_dt = dt_to
        self.__log()
        return True

    def copy_videos(self, dt_from: datetime.datetime, dt_to: datetime.datetime):
        ready_videos = list(db.Video.using(db.SRC_DB).select().where(
            (dt_from <= db.Video.finish_record)
            & (db.Video.finish_record < dt_to)
        ).order_by(db.Video.finish_record))

        if not self.__usb_device.mount_exists:
            return False
        plug = db.Video.plug()
        plug.pop('id', None)
        videos = db.Video.using(db.DST_DB).select().where(
            db.Video.id << [video.id for video in ready_videos]
        )

        found_video_ids = [video.id for video in videos]
        for video in ready_videos:
            if not self.__usb_device.mount_exists:
                return False
            self.__usb_device.copy(os.path.join(settings.SRC_VIDEO_PATH, video.render_name))
            if not self.__usb_device.mount_exists:
                return False
            if video.id in found_video_ids:
                dst_record = next((x for x in videos if x.id == video.id), None)
                if dst_record != video:
                    dst_record.update_all_data(video)
            else:
                db.FrontLoader_EventTelemetryNetrwork_Model(model_to_dict(video)).save()

            self.__last_video_dt = video.finish_record
            self.__log()

        return True
















