import logging
from urllib.parse import urlparse

from flask import Flask, request, make_response, jsonify, current_app
import pyHS100
import requests

__version = "0.1.0"
app = Flask(__name__)
API_VERSION = "v1"
SERVER_URL = urlparse("http://0.0.0.0:5000/api/{}/request".format(API_VERSION)).geturl()


@app.errorhandler(400)
def bad_request(message, errors=None):
    json = {'message': message}
    if current_app.config['ENV'] != "production" and errors is not None:
        json.update({'errors': str(errors)})
    return make_response(jsonify(json), 400)


@app.route("/")
def index():
    return "PiPlant Client"


@app.route("/api/%s/request" % API_VERSION, methods=["POST"])
def process_request():
    device_info = request.get_json()['device_info']
    action = request.get_json()['action']
    device_type = device_info['type']

    if action == "status":
        data = None
        if device_type == "tp_link_smart_plug":
            data = pyHS100.SmartPlug(device_info['ip_address']).get_sysinfo()

        try:
            send_data(SERVER_URL, data)
        except Exception as err:
            logging.error(str(err))
            return bad_request("Could not process request.", err)

    return make_response(jsonify({"message": "Request has been processed."}), 200)


def send_data(url, data):
    response = requests.post(url=url, data=data)
    response.raise_for_status()



if __name__ == "__main__":
    app.run(port=6000, debug=True)

