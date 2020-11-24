import os
import tempfile

import pytest

from piplant.app import create_app
from piplant.models import db


@pytest.fixture
def app():
    # create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"TESTING": True, "DATABASE": db_path})

    # create the database and load test data
    with app.app_context():
        db.init_db()

    yield app

    # close and remove the temporary database
    os.close(db_fd)
    # os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()



