import datetime

import peewee
from playhouse.shortcuts import model_to_dict

import settings

DB = peewee.Proxy()
SRC_DB = peewee.SqliteDatabase(settings.SRC_DB_CONNECTION)
DST_DB = None

class BaseModel(peewee.Model):
    class Meta:
        database = DB


class Video(BaseModel):
    class Meta:
        db_table = 'Videos'

    render_name = peewee.CharField(max_length=150)
    render_fps = peewee.IntegerField()
    src_name = peewee.CharField(max_length=150)
    src_fps = peewee.IntegerField()
    captured_fps = peewee.IntegerField()
    record_time = peewee.DateTimeField(default=datetime.datetime.now)
    finish_record = peewee.DateTimeField(index=True, null=True)

    @property
    @staticmethod
    def plug():
        return model_to_dict(Video(
            render_name='plug', render_fps=0,
            src_name='plug', src_fps=0,
            captured_fps=0, record_time=datetime.datetime(year=1, month=1, day=1),
        ))

    @staticmethod
    def create_plugs(video_ids: list):
        exist_videos = Video.select(Video.id).where(Video.id << video_ids)
        plug = Video.plug
        if plugs := [
            {**{'id': video.id}, **plug}
            for video in exist_videos
            if video.id not in video_ids
        ]:
            Video.insert_many(plugs).execute()

    def update_all_data(self, video):
        (self.render_name, self.render_fps,
         self.src_name, self.src_fps,
         self.captured_fps, self.record_time,
         self.finish_record) = (video.render_name, video.render_fps,
                                video.src_name, video.src_fps,
                                video.captured_fps, video.record_time,
                                video.finish_record)
        self.save()



class BaseEventTelemetryNetwork(BaseModel):
    event = peewee.IntegerField()
    polygon_id = peewee.IntegerField()
    zone_id = peewee.IntegerField()
    record_dtime = peewee.DateTimeField(index=True)

    rendered_video_time = peewee.TimeField()
    source_video_time = peewee.TimeField()
    video = peewee.ForeignKeyField(Video)

    @staticmethod
    def fields():
        return ('event',
                'x_coord', 'y_coord', 'width', 'height',
                'rendered_video_time', 'source_video_time', 'video')


class PeopleForbiddenZone_EventTelemetryNetrwork_Model(BaseEventTelemetryNetwork):
    class Meta:
        db_table = 'Event_Telemetry_Network__People_forbidden_zone'


class FrontLoader_EventTelemetryNetrwork_Model(BaseEventTelemetryNetwork):
    class Meta:
        db_table = 'Event_Telemetry_Network__Front_loader'

    @staticmethod
    def tablename():
        return FrontLoader_EventTelemetryNetrwork_Model._meta.table._path[0]


def init_db(db):
    DB.initialize(db)


def create_tables(db):
    DB.create_tables([Video,
                      PeopleForbiddenZone_EventTelemetryNetrwork_Model, FrontLoader_EventTelemetryNetrwork_Model
                      ])


