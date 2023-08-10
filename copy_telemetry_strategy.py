import datetime
from itertools import groupby

from copy_strategy import CopyStrategy
import models.db_models as db



class CopyTelemetryStrategy(CopyStrategy):
    def __select_source_data(self, dt_from, dt_to):
        return list(
            db.FrontLoader_EventTelemetryNetrwork_Model.using(db.SRC_DB).select().where(
                (db.FrontLoader_EventTelemetryNetrwork_Model.event == 1)
                & (dt_from <= db.FrontLoader_EventTelemetryNetrwork_Model.record_dtime)
                & (db.FrontLoader_EventTelemetryNetrwork_Model.record_dtime < dt_to)
            ).order_by(db.FrontLoader_EventTelemetryNetrwork_Model.video)
        )

    def __select_exist_data(self, front_loader_data):
        return [data.id
                      for data in db.FrontLoader_EventTelemetryNetrwork_Model.select(
                db.FrontLoader_EventTelemetryNetrwork_Model.id).where(
                db.FrontLoader_EventTelemetryNetrwork_Model.id << [data.id for data in front_loader_data]
            )
                ]

    def copy(self, dt_from: datetime.datetime, dt_to: datetime.datetime):
        front_loader_data = self.__select_source_data(dt_from, dt_to)
        if not front_loader_data:
            self.set_last_dt_delegate(self.prefix, dt_to)
            return True

        grouped_telemetry = dict(groupby(front_loader_data, key=lambda x: x.video_id))
        if not self.usb_device.mount_exists:
            return False
        db.Video.using(db.DST_DB).create_plugs(list(grouped_telemetry.keys()))

        exist_data = self.__select_exist_data(front_loader_data)
        if inserted_data := [data for data in front_loader_data if data.id not in exist_data]:
            db.FrontLoader_EventTelemetryNetrwork_Model.insert_many(map(db.BaseEventTelemetryNetwork.map_to_dict,
                                                                        inserted_data)
                                                                    ).execute()

        self.set_last_dt_delegate(self.prefix, dt_to)
        return True
