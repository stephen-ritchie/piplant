import os
import tempfile

import pytest

from piplant.app import create_app
from piplant.models import db
from piplant.db import get_db


# read in SQL for populating test data
with open(os.path.join(os.path.dirname(__file__), "data.sql"), "rb") as f:
    _data_sql = f.read().decode("utf8")


@pytest.fixture
def app():
    # create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    _app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": 'sqlite:///' + os.path.join(db_path, db_path),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": 'dev',
        "DATABASE": db_path})

    # create the database and load test data
    with _app.app_context():
        db.create_all()
        get_db().executescript(_data_sql)

    yield _app

    # close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, email="test", password="test"):
        return self._client.post(
            "/login", data={"email": email, "password": password}
        )

    def logout(self):
        return self._client.get("/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)




