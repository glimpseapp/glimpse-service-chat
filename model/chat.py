import time
import uuid

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from cassandra.util import datetime_from_timestamp, uuid_from_time, datetime_from_uuid1


def date_now():
    return datetime_from_timestamp(time.time())


class ChatByChatId(Model):
    chat_id = columns.Text(primary_key=True)
    user_id = columns.Text()
    chat_name = columns.Text()
    time = columns.DateTime(default=date_now)  # rename to creation_date

    def to_object(self):
        return {
            'chat_id': self.chat_id,
            'user_id': self.user_id,
            'chat_name': self.chat_name,
            'time': self.time.isoformat()
        }


class ChatByUserId(Model):
    user_id = columns.Text(primary_key=True)
    chat_id = columns.Text()
    chat_name = columns.Text()
    time = columns.DateTime(default=date_now)  # rename to creation_date

    def to_object(self):
        return {
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'chat_name': self.chat_name,
            'time': self.time.isoformat()
        }


class ChatMessageByChatId(Model):
    chat_id = columns.Text(primary_key=True)
    message_id = columns.TimeUUID()
    author_id = columns.Text()
    message = columns.Text()
    asset_name = columns.Text()

    def to_object(self):
        return {
            'chat_id': self.chat_id,
            'message_id': str(self.message_id),
            'author_id': self.author_id,
            'message': self.message,
            'asset_name': self.asset_name,
            'time': datetime_from_uuid1(self.message_id).isoformat()
        }
