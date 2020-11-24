#!/usr/bin/env python3

import argparse
import logging
import os
import sys
from urllib.parse import urlparse

import pyHS100
import requests
from flask import Flask, request, make_response, jsonify, render_template


__version__ = "0.1.0"
app = Flask(__name__)


class Client:
    def __init__(self, app, server, token, api_version="v1"):
        self.app = app
        self.server = server
        self.token = token
        self.api_version = api_version

    def run(self, host, port, debug):
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])
        self.app.add_url_rule('/debug', 'debug', self.debug, methods=['GET'])
        self.app.add_url_rule('/api/{}/info'.format(self.api_version), 'client_info', self._client_info, methods=['GET'])
        self.app.add_url_rule('/api/{}/requests'.format(self.api_version), 'process_request', self.process_request, methods=['POST'])
        self.app.run(host=host, port=port, debug=debug)

    def process_request(self):
        # TODO: schema validation of incoming request
        status_code = 200
        payload = []

        for item in request.get_json():
            for action in item['actions']:
                if action == "status" and item['info']['type'] == 'tp_link_smart_plug':
                    plug = pyHS100.SmartPlug(item['info']['ip_address'])
                    payload.append({"device": item['info']['id'], "payload": plug.get_sysinfo()})

        return make_response(jsonify({"received": len(request.get_json()), "response": payload}), status_code)

    @staticmethod
    def _client_info():
        return make_response(jsonify({"version": __version__}), 200)

    def index(self):
        return render_template('index.html', version=__version__, server=self.server, token=self.token, routes=self.app.url_map)

    def debug(self):
        tp_link_devices = pyHS100.Discover.discover().values()
        return render_template('debug.html', tp_link_devices=tp_link_devices)

    @staticmethod
    def get_token(url, email, password):
        url = urlparse(url).geturl()
        response = requests.post(url=url, data={"email": email, "password": password})
        response.raise_for_status()
        return response.json()['auth_token']


# @app.route("/api/%s/tasks" % API_VERSION, methods=['POST'])
# def process_tasks():
#     tasks_received = len(request.get_json())
#     tasks_processed = 0
#     tasks_completed = 0
#
#     for task in request.get_json():
#         device_type = task['info']['type']
#         for action in task['actions']:
#             if device_type == "tp_link_smart_plug":
#                 ip_address = task['info']['ip_address']
#                 print(ip_address)
#                 plug = pyHS100.SmartPlug(ip_address)
#                 if action == "on":
#                     plug.turn_on()
#                 elif action == "off":
#                     plug.turn_off()
#
#     return 'RECEIVED %s TASKS' % tasks_received

def send_data(url, data):
    response = requests.post(url=url, data=data)
    response.raise_for_status()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PiPlant Client")
    parser.add_argument("server", help="PiPlant server hostname")
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-host", default="0.0.0.0", help="client hostname (default: %(default)s)")
    parser.add_argument("-port", default=5001, help="client port (default: %(default)s)")
    args = parser.parse_args()

    if os.getenv('FLASK_ENV') is None:
        logging.error("Environment variable FLASK_ENV is not set. Please set it to either 'production' or 'development'.")
        sys.exit(-1)

    try:
        auth_token = Client.get_token(url=urlparse("{}/api/v1/token".format(args.server)).geturl(), email=args.username, password=args.password)
        client = Client(app=app, server=args.server, token=auth_token)
        client.run(host="0.0.0.0", port=5001, debug=args.debug)
    except Exception as err:
        sys.exit(str(err))
