import json
from urllib.parse import urlparse

import requests

import piplant.lib as lib


class Scheduler:
    def __init__(self, app):
        self.app = app
        self.api_version = "v1"  # TODO: Make this configurable.
        self.client_base_url = self.app.config['CLIENT_BASE_URL']

    def update(self):
        url = "{}/api/{}/requests".format(self.app.config['CLIENT_BASE_URL'], self.api_version)
        with self.app.app_context():
            for user in lib.get_users():
                tasks = lib.get_tasks(user.id)
                self.send_tasks_to_client(tasks, url)

    def send_tasks_to_client(self, tasks, url):
        url = urlparse(url).geturl()
        try:
            headers = {'content-type': 'application/json'}
            response = requests.post(url=url, data=json.dumps(tasks), headers=headers)
            response.raise_for_status()
            self.app.logger.debug("Sent %s task(s) to %s" % (len(tasks), url))
        except Exception as err:
            self.app.logger.error("Could not POST tasks to %s" % url)

