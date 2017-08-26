import json
import uuid

from cassandra.cqlengine import connection
from flask import make_response
from flask_restful import Resource, request

from conf.config import CASSANDRA_HOSTS, MESSAGE_KEYSPACE, CHAT_CREATED_TOPIC

from google.cloud import pubsub

from model.chat import ChatByChatId, ChatByUserId


class CreateChat(Resource):
    def post(self):

        data = request.get_json(silent=True)

        user_ids = data.get('user_ids')

        if not user_ids or len(user_ids) == 0:
            return make_response("You must send the user ids", 500)

        chat_id = str(abs(hash(''.join(list(set(user_ids))))))

        connection.setup(hosts=CASSANDRA_HOSTS, default_keyspace=MESSAGE_KEYSPACE)

        for user_id in user_ids:
            ChatByChatId.create(
                chat_id=chat_id,
                user_id=user_id
            )
            ChatByUserId.create(
                chat_id=chat_id,
                user_id=user_id
            )
            chat_object = {
                "chat_id": chat_id,
                "user_id": user_id
            }
            self._chat_created(chat_object)

        return {
            "success": True,
            "chat_id": chat_id
        }

    @staticmethod
    def _chat_created(chat_object):
        client = pubsub.Client()
        topic = client.topic(CHAT_CREATED_TOPIC)
        message_grammar = {
            "verb": "chat-created",
            "subject": "chat",
            "directObject": chat_object
        }
        topic.publish(json.dumps(message_grammar))
        return True
