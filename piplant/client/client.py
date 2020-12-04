#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys
import time
from urllib.parse import urlparse

import pyHS100
import requests
from flask import Flask, request, make_response, jsonify, render_template, Response


__version__ = "0.1.0"
app = Flask(__name__)


class Client:
    def __init__(self, _app, server, token, api_version="v1"):
        self.app = _app
        self.server = server
        self.token = token
        self.api_version = api_version

    def run(self, host, port, debug):
        # Set the version as a jinja global so all templates can see it
        self.app.jinja_env.globals['BUILD_VERSION'] = __version__

        # Add endpoints to Flask app
        self.app.add_url_rule('/', 'index', self._index, methods=['GET'])
        self.app.add_url_rule('/debug', 'debug', self._debug, methods=['GET'])
        self.app.add_url_rule('/api/{}/info'.format(self.api_version), 'client_info', self._client_info, methods=['GET'])
        self.app.add_url_rule('/api/{}/requests'.format(self.api_version), 'process_request', self.process_request, methods=['POST'])

        self.app.run(host=host, port=port, debug=debug)

    def process_request(self):
        # TODO: schema validation of incoming request
        self.app.logger.info("Received %s new request(s) from %s" % (len(request.get_json()), request.remote_addr))
        for item in request.get_json():
            device_id = item['info']['id']
            for action in item['actions']:
                if item['info']['type'] == 'tp_link_smart_plug':
                    self._process_tp_link_smart_plug(device_id, item['info']['ip_address'], action)
                elif item['info']['type'] == 'ds18b20':
                    self._process_temperature_probe(device_id, item['info']['serial_number'], action)

        return Response(status=200)

    def _process_tp_link_smart_plug(self, device_id, ip_address, action):
        plug = pyHS100.SmartPlug(ip_address)
        if action == "on":
            plug.turn_on()
        elif action == "off":
            plug.turn_off()
        elif action == "status":
            sys_info = plug.get_sysinfo()
            payload = {}
            payload.update({"relay_state": sys_info['relay_state']})
            if plug.has_emeter:
                for key, value in plug.get_emeter_realtime().items():
                    payload.update({key: value})
            self._send_data(device_id, payload=payload)
        else:
            self.app.logger.error('Unknown action type for TP Link Smart Plug: %s' % action)

    def _process_temperature_probe(self, device_id, serial_number, action):
        temperature_probe = TemperatureProbe(serial_number)
        if action == "status":
            self._send_data(device_id, payload={"temperature": temperature_probe.current_temperature})
        else:
            self.app.logger.error('Unknown action for DS18B20: %s' % action)

    def _send_data(self, device_id, payload):
        url = urlparse(self.server + "/api/{}/requests".format(self.api_version)).geturl()
        headers = {"Authorization": "Bearer {}".format(self.token), "Content-Type": "application/json"}
        try:
            response = requests.post(url=url, headers=headers, data=json.dumps({"device_id": device_id, "payload": payload}))
            response.raise_for_status()
            self.app.logger.debug("Sent payload for device %s to %s" % (device_id, url))
        except Exception as err:
            self.app.logger.error(str(err))

    @staticmethod
    def _client_info():
        return make_response(jsonify({"version": __version__}), 200)

    def _index(self):
        return render_template('index.html', version=__version__, server=self.server, token=self.token, routes=self.app.url_map, api_version=self.api_version)

    @staticmethod
    def _debug():
        tp_link_devices = pyHS100.Discover.discover().values()
        return render_template('debug.html', tp_link_devices=tp_link_devices)

    @staticmethod
    def get_token(url, email, password):
        url = urlparse(url).geturl()
        response = requests.post(url=url, data={"email": email, "password": password})
        response.raise_for_status()
        return response.json()['auth_token']


class TemperatureProbe:
    def __init__(self, serial_number):
        self.serial_number = serial_number

    @property
    def current_temperature(self, units="F"):
        temp_c, temp_f = self._read_temp()
        return temp_f if units == "F" else temp_c

    def _read_temp(self):
        lines = self._read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self._read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            return temp_c, temp_f

    def _read_temp_raw(self):
        base_dir = '/sys/bus/w1/devices/'
        # device_folder = glob.glob(base_dir + '28*')[0]
        device_folder = os.path.join(base_dir, self.serial_number)
        device_file = device_folder + '/w1_slave'

        infile = open(device_file, 'r')
        lines = infile.readlines()
        infile.close()
        return lines


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PiPlant Client")
    parser.add_argument("server", help="PiPlant server hostname")
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-host", default="0.0.0.0", help="client hostname (default: %(default)s)")
    parser.add_argument("-port", default=5001, help="client port (default: %(default)s)")
    parser.add_argument("--api-version", default="v1", help="(default: %(default)s)")
    args = parser.parse_args()

    if os.getenv('FLASK_ENV') is None:
        app.logger.error("Environment variable FLASK_ENV is not set. Please set it to either 'production' or 'development'.")
        sys.exit(-1)

    # Configure the logger
    file_handler = logging.FileHandler("%s.log" % app.name)
    file_handler.setLevel(logging.DEBUG if args.debug else logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    app.logger.addHandler(file_handler)

    # Get token and start the client
    try:
        auth_url = urlparse("{}/api/{}/token".format(args.server, args.api_version)).geturl()
        auth_token = Client.get_token(url=auth_url, email=args.username, password=args.password)
        app.logger.debug("Auth token is %s" % auth_token)  # TODO: Should this be logged?

        client = Client(_app=app, server=args.server, token=auth_token, api_version=args.api_version)
        client.run(host=args.host, port=args.port, debug=args.debug)
    except requests.exceptions.InvalidSchema:
        app.logger.exception("Authentication url is invalid")
    except Exception as e:
        # TODO: Make exception catching less broad.
        app.logger.exception("Could not start client")
