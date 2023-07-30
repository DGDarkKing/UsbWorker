import datetime

import peewee
from playhouse.shortcuts import model_to_dict

import settings

DB = peewee.Proxy()
SRC_DB = peewee.SqliteDatabase(settings.SRC_DB_CONNECTION)

class BaseModel(peewee.Model):
    class Meta:
        database = DB

    @classmethod
    def using(cls, db):
        cls._meta.database.initialize(db)
        return cls


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


class BaseEventTelemetryNetwork(BaseModel):
    event = peewee.IntegerField()
    polygon_id = peewee.IntegerField()
    zone_id = peewee.IntegerField()
    record_dtime = peewee.DateTimeField(index=True)

    rendered_video_time = peewee.TimeField()
    source_video_time = peewee.TimeField()
    video = peewee.ForeignKeyField(Video)

    @staticmethod
    def map_to_dict(record):
        result = model_to_dict(record)
        video_data = result.pop('video', None)
        result['video'] = video_data['id']
        return result

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
    db.create_tables([Video,
                      PeopleForbiddenZone_EventTelemetryNetrwork_Model, FrontLoader_EventTelemetryNetrwork_Model
                      ])


