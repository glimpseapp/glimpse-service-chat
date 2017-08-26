import json
import uuid

import time
from cassandra.cqlengine import connection
from cassandra.util import uuid_from_time
from flask import make_response
from flask_restful import Resource, request

from conf.config import CASSANDRA_HOSTS, CHAT_KEYSPACE, CHAT_CREATED_TOPIC

from google.cloud import pubsub

from model.chat import ChatByChatId, ChatByUserId, ChatMessageByChatId


class CreateChat(Resource):
    def post(self):

        data = request.get_json(silent=True)

        user_ids = data.get('user_ids')

        if not user_ids or len(user_ids) == 0:
            return make_response("You must send the user ids", 500)

        user_names = ', '.join(list(set(user_ids)))
        chat_name = (user_names[:30] + '...') if len(user_names) > 30 else user_names
        chat_id = str(abs(hash(''.join(list(set(user_ids))))))

        connection.setup(hosts=CASSANDRA_HOSTS, default_keyspace=CHAT_KEYSPACE)

        # todo: check if the chat_id for certain user already exists, if it does don't create it again

        for user_id in user_ids:
            ChatByChatId.create(
                chat_id=chat_id,
                user_id=user_id,
                chat_name=chat_name,
            )
            ChatByUserId.create(
                chat_id=chat_id,
                user_id=user_id,
                chat_name=chat_name,
            )
            self._chat_created(chat_id, user_id)

        return {
            "success": True,
            "chat_id": chat_id
        }

    @staticmethod
    def _chat_created(chat_id, user_id):
        chat_object = {
            "chat_id": chat_id,
            "user_id": user_id
        }
        client = pubsub.Client()
        topic = client.topic(CHAT_CREATED_TOPIC)
        message_grammar = {
            "verb": "chat-created",
            "subject": "chat",
            "directObject": chat_object
        }
        topic.publish(json.dumps(message_grammar))


class GetChatList(Resource):
    def get(self, user_id):
        connection.setup(hosts=CASSANDRA_HOSTS, default_keyspace=CHAT_KEYSPACE)

        chat_rows = ChatByUserId.filter(user_id=user_id)

        chat_list = []
        for chat in chat_rows:
            chat_list.append(chat.to_object())

        return {
            "tot": len(chat_list),
            "requests": chat_list
        }


class GetChatMessages(Resource):
    def get(self, chat_id):
        connection.setup(hosts=CASSANDRA_HOSTS, default_keyspace=CHAT_KEYSPACE)

        message_rows = ChatMessageByChatId.filter(chat_id=str(chat_id))

        message_list = []
        for message in message_rows:
            message_list.append(message.to_object())

        return {
            "tot": len(message_list),
            "messages": message_list
        }


class WriteMessage(Resource):
    def post(self):
        data = request.get_json(silent=True)

        author_id = data.get('author_id')
        chat_id = data.get('chat_id')
        message = data.get('message')
        message_id = str(uuid_from_time(time.time()))
        asset_name = data.get('asset_name')

        connection.setup(hosts=CASSANDRA_HOSTS, default_keyspace=CHAT_KEYSPACE)

        ChatMessageByChatId.create(
            chat_id=chat_id,
            message_id=message_id,
            author_id=author_id,
            message=message,
            asset_name=asset_name,
        )

        self._message_sent(chat_id, author_id, message, asset_name)

        return {
            "success": True
        }

    @staticmethod
    def _message_sent(chat_id, author_id, message, asset_name):
        chat_object = {
            "chat_id": chat_id,
            "author_id": author_id,
            "message": message,
            "asset_name": asset_name
        }
