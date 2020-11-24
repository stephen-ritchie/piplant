import os
import tempfile

import pytest

from piplant.app import create_app
from piplant.models import db


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
        print("************* Created a database ************")
        db.create_all()

    yield _app

    # close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()



