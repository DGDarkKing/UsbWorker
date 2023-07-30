import datetime
import os
import time
from itertools import groupby

from playhouse.shortcuts import model_to_dict

import settings
from backend_reporter import BackendReporter
from extends import create_file, strings_to_dict, PrefixSpliter
import models.db_models as db
from models.backend_models import Video, Telemetry, TelemetryButch


###     Abbreviation "dt" is mean "datetime"

class Copier:
    __VIDEO_REPORT_PREFIX = 'video'
    __DATETIME_FORMAT: str = '%m/%d/%Y %H:%M:%S'

    def __init__(self, http_client: BackendReporter, report_file, stop_event):
        self.__http_client = http_client
        self.__report_file = report_file
        create_file(self.__report_file)
        now = datetime.datetime.now()
        self.__last_telemetry_dt = now
        self.__last_video_dt = now
        self.__text_spliter = PrefixSpliter([self.__VIDEO_REPORT_PREFIX])
        self.__stop_event = stop_event
        self.__event_id = next([event_data['id']
                                for event_data in self.__http_client.get_events()
                                if event_data['label'] == 'Подача'],
                               None)
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
            if dt := self.__dict_to_dt(data, self.__VIDEO_REPORT_PREFIX):
                self.__last_video_dt = dt
            else:
                not_enough_data = True

            if not_enough_data:
                self.__log()
        else:
            self.__log()

    def __log(self):
        with open(self.__report_file, 'r+') as fws:
            fws.write(f'{self.__VIDEO_REPORT_PREFIX} {self.__last_video_dt.strftime(self.__DATETIME_FORMAT)}')

    def start_copy(self):
        start_time = datetime.datetime.now()
        while not self.__stop_event():
            time.sleep(settings.SLEEP_TIME.total_seconds())
            elapsed_time = datetime.datetime.now() - start_time
            if elapsed_time < settings.COPY_TIME:
                continue
            if not self.copy_data(start_time, start_time + settings.COPY_TIME):
                return
            start_time = start_time + settings.COPY_TIME

    def copy_data(self, dt_from: datetime.datetime, dt_to: datetime.datetime):
        time.sleep(1)
        ready_videos = list(db.Video.select(db.Video.id, db.Video.render_name,
                                            db.Video.finish_record).where(
            (dt_from <= db.Video.finish_record)
            & (db.Video.finish_record < dt_to)
        ).order_by(db.Video.finish_record))

        ready_videos = [Video(id=video.id, name=video.render_name, finish_record=video.finish_record)
                        for video in ready_videos]
        for video_record in ready_videos:
            telemetry_of_video = list(
                db.FrontLoader_EventTelemetryNetrwork_Model.select(
                    db.FrontLoader_EventTelemetryNetrwork_Model.id,
                    db.FrontLoader_EventTelemetryNetrwork_Model.zone_id,
                    db.FrontLoader_EventTelemetryNetrwork_Model.polygon_id,
                    db.FrontLoader_EventTelemetryNetrwork_Model.record_dtime,
                    db.FrontLoader_EventTelemetryNetrwork_Model.rendered_video_time
                ).where(
                    (dt_from <= db.FrontLoader_EventTelemetryNetrwork_Model.record_dtime)
                    & (db.FrontLoader_EventTelemetryNetrwork_Model.record_dtime < dt_to)
                ).order_by(db.FrontLoader_EventTelemetryNetrwork_Model.video)
            )

            if telemetry_of_video:
                telemetry_of_video = [
                    Telemetry(id=telemetry.id,
                              zone=telemetry.zone_id, polygon=telemetry.polygon_id,
                              time=telemetry.record_dtime, video_time=telemetry.rendered_video_time)
                    for telemetry in telemetry_of_video
                ]

                butch = TelemetryButch(event_id=self.__event_id,
                                       video_data=video_record,
                                       events_data=telemetry_of_video)

                self.__http_client.post_telemtry(butch)
            else:
                self.__http_client.post_video(video_record)
