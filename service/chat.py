import json

import time
from cassandra.cqlengine import connection
from cassandra.util import uuid_from_time
from flask import make_response
from flask_restful import Resource, request

from conf.config import CASSANDRA_HOSTS, CHAT_KEYSPACE, CHAT_CREATED_TOPIC

from google.cloud import pubsub

from model.chat import ChatByChatId, ChatByUserId, ChatMessageByChatId
from service.common import get_user_id_from_jwt


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
            #self._chat_created(chat_id, user_id)

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
    def get(self):
        user_id = get_user_id_from_jwt()
        connection.setup(hosts=CASSANDRA_HOSTS, default_keyspace=CHAT_KEYSPACE)
        chat_rows = ChatByUserId.filter(user_id=user_id)

        chat_list = []
        for chat in chat_rows:
            chat_list.append(chat.to_object())

        return {
            "results": len(chat_list),
            "chats": chat_list
        }


class GetChatMessages(Resource):
    def get(self, chat_id):
        connection.setup(hosts=CASSANDRA_HOSTS, default_keyspace=CHAT_KEYSPACE)

        message_rows = ChatMessageByChatId.filter(chat_id=str(chat_id))

        message_list = []
        for message in message_rows:
            message_object = message.to_object()
            message_object['meta_data'] = json.loads(message_object['meta_data'])
            message_list.append(message_object)

        return {
            "results": len(message_list),
            "messages": message_list
        }


class WriteMessage(Resource):
    def post(self):
        author_id = get_user_id_from_jwt()

        data = request.get_json(silent=True)

        type = data.get('type', 'text')
        chat_id = data.get('chat_id')
        message_id = str(uuid_from_time(time.time()))
        text = data.get('text', '')
        asset_name = data.get('asset_name', '')
        meta_data = data.get('meta_data', {})
        connection.setup(hosts=CASSANDRA_HOSTS, default_keyspace=CHAT_KEYSPACE)

        if type not in ChatMessageByChatId.allowed_type:
            return make_response("Type not allowed. Only allowed type: " + ChatMessageByChatId.allowed_type, 403)

        if type == 'glimpse':
            seconds_allowed = meta_data.get('seconds_allowed', 10)
            effect = meta_data.get('effect')
            meta_data = {
                'seconds_allowed': seconds_allowed,
                'effect': effect
            }

        elif type == 'glimpse_narrative':
            path_id = meta_data.get('path_id')
            meta_data = {
                'path_id': path_id,
            }

        meta_data = json.dumps(meta_data)

        ChatMessageByChatId.create(
            chat_id=chat_id,
            message_id=message_id,
            author_id=author_id,
            type=type,
            text=text,
            asset_name=asset_name,
            meta_data=meta_data,
        )

        #self._message_sent(chat_id, author_id, text, asset_name)

        return {
            "success": True
        }

    @staticmethod
    def _message_sent(chat_id, author_id, text, asset_name):
        chat_object = {
            "chat_id": chat_id,
            "author_id": author_id,
            "text": text,
            "asset_name": asset_name,
        }
