#!flask/bin/python
from flask import Flask
from flask_restful import Api

from conf.config import HTTP_HOST, HTTP_PORT
from service.chat import CreateChat
from service.healthz import Healthz

app = Flask(__name__)
api = Api(app)

api.add_resource(Healthz, '/healthz')
api.add_resource(CreateChat, '/chat')

if __name__ == '__main__':
    app.run(host=HTTP_HOST, port=HTTP_PORT)
