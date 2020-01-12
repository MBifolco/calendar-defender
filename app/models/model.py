from peewee import *
import peewee_async
import os

mysql_db = peewee_async.MySQLDatabase(
    'calendar_defense', 
    user=os.environ.get('DB_USER'), 
    password=os.environ.get('DB_PASS'),
    host=os.environ.get('DB_HOST'), 
    port=int(os.environ.get('DB_PORT'))
)

class BaseModel(Model):
    class Meta:
        legacy_table_names=False
        database = mysql_db 

class User(BaseModel):
    id = AutoField()
    public_id = CharField()
    email = CharField()
    created = DateTimeField()
    auth_code = CharField()
    access_token = CharField()
    access_token_expiration = DateTimeField()
    refresh_token = CharField()

class WatchedCalendar(BaseModel):
    id = AutoField()
    public_id = CharField()
    calendar_id = CharField()
    user_id = ForeignKeyField(User)
    expiration = DateTimeField()
    channel_id = CharField()
    status = CharField()
    last_check = CharField()