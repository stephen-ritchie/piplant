import logging
import json
from urllib.parse import urlparse

import requests
from flask import jsonify

import piplant.lib as lib


class Scheduler:
    def __init__(self, app):
        self.app = app

    def update(self):
        with self.app.app_context():
            for user in lib.get_users():
                tasks = lib.get_tasks(user.id)
                url = "http://0.0.0.0:5001/api/v1/tasks"
                self.send_tasks_to_client(tasks, url)

    def send_tasks_to_client(self, tasks, url):
        print("Sending {} tasks to {}".format(len(tasks), url))
        print(tasks)
        url = urlparse(url).geturl()
        try:
            headers = {'content-type': 'application/json'}
            response = requests.post(url=url, data=json.dumps(tasks), headers=headers)
            response.raise_for_status()
        except Exception as err:
            logging.error(str(err))

