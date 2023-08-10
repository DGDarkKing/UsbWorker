import time

import models.db_models as db
from models.backend_models import Video, Telemetry, TelemetryButch

from copy_strategy import CopyToBackendStrategy


class CopyByVideoStrategy(CopyToBackendStrategy):

    @staticmethod
    def select_videos(dt_from, dt_to):
        ready_videos = list(db.Video.select(db.Video.id,
                                            db.Video.render_name,
                                            db.Video.finish_record)
                            .where((dt_from <= db.Video.finish_record)
                                   & (db.Video.finish_record < dt_to)
                                   )
                            .order_by(db.Video.finish_record)
                            )

        return [Video(id=video.id, name=video.render_name, finish_record=video.finish_record)
                for video in ready_videos]

    @staticmethod
    def select_telemetry(video_record):
        return list(
            db.FrontLoader_EventTelemetryNetrwork_Model.select(
                db.FrontLoader_EventTelemetryNetrwork_Model.id,
                db.FrontLoader_EventTelemetryNetrwork_Model.zone_id,
                db.FrontLoader_EventTelemetryNetrwork_Model.polygon_id,
                db.FrontLoader_EventTelemetryNetrwork_Model.record_dtime,
                db.FrontLoader_EventTelemetryNetrwork_Model.rendered_video_time
            ).where(
                (db.FrontLoader_EventTelemetryNetrwork_Model.video_id == video_record.id)
                & (db.FrontLoader_EventTelemetryNetrwork_Model.event == 1)
            ).order_by(db.FrontLoader_EventTelemetryNetrwork_Model.video)
        )

    def __map_to_butch(self, telemetry_of_video, video_record):
        telemetry_of_video = [Telemetry(id=telemetry.id,
                                        zone=telemetry.zone_id, polygon=telemetry.polygon_id,
                                        time=telemetry.record_dtime, video_time=telemetry.rendered_video_time)
                              for telemetry in telemetry_of_video
                              ]

        return TelemetryButch(event_id=self.get_event_id_delegate(self.__target_event_name),
                              video_data=video_record,
                              events_data=telemetry_of_video)

    def copy(self, dt_from, dt_to):
        time.sleep(1)
        ready_videos = self.select_videos(dt_from, dt_to)

        for video_record in ready_videos:
            if telemetry_of_video := self.select_telemetry(video_record):
                butch = self.__map_to_butch(telemetry_of_video, video_record)
                self.http_client.post_telemtry(butch)
            else:
                self.http_client.post_video(video_record)
            self.set_last_dt_delegate(self.prefix, video_record.finish_record)
