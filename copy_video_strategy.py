import os
from typing import Callable

from playhouse.shortcuts import model_to_dict

from copy_strategy import CopyStrategy
import models.db_models as db
from models.usb_device import UsbAvailableSizeException, UsbDevice


class CopyVideoStrategy(CopyStrategy):
    def __init__(
            self,
            usb_device: UsbDevice,
            set_last_dt_delegate: Callable,
            prefix: str,
            src_video_path: str
    ):
        super().__init__(usb_device, set_last_dt_delegate, prefix)
        self.__src_video_path = src_video_path

    def __select_data(self, dt_from, dt_to):
        return (db.Video.using(db.SRC_DB).select().where(
            (dt_from <= db.Video.finish_record)
            & (db.Video.finish_record < dt_to)
        ).order_by(db.Video.finish_record))

    @staticmethod
    def videos(ready_videos):
        return db.Video.using(db.DST_DB).select().\
            where(db.Video.id << [video.id for video in ready_videos])

    def __copy_video(self, video):
        if not self.usb_device.mount_exists:
            return False
        try:
            self.usb_device.copy(os.path.join(self.__src_video_path, video.render_name))
        except UsbAvailableSizeException:
            return False

    def copy(self, dt_from, dt_to):
        ready_videos = self.__select_data(dt_from, dt_to)
        if not self.usb_device.mount_exists:
            return False
        if not ready_videos:
            self.set_last_dt_delegate(self.prefix, dt_to)
            return True
        videos = self.videos(ready_videos)
        found_video_ids = [video.id for video in videos]
        for video in ready_videos:
            if not self.__copy_video(video):
                return False
            if video.id in found_video_ids:
                dst_record = next((x for x in videos if x.id == video.id), None)
                if dst_record != video:
                    dst_record.update_all_data(video)
            else:
                db.FrontLoader_EventTelemetryNetrwork_Model(model_to_dict(video)).save()
            self.set_last_dt_delegate(self.prefix, video.finish_record)

        self.set_last_dt_delegate(self.prefix, dt_to)
        return True


