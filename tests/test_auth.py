import pytest

from flask import session
from flask_login import current_user

from piplant import messages
from piplant.db import get_db


def test_register(client, app):
    # test that viewing the page renders without template errors
    assert client.get("/register").status_code == 200

    # test that successful registration redirects to the login page
    response = client.post("/register", data={"name": "User 1", "email": "user1@test.com", "password": "xxx"})
    assert "http://localhost/login" == response.headers["Location"]

    # test that the user was inserted into the database
    with app.app_context():
        assert (
            get_db().execute("select * from user where email = 'user1@test.com'").fetchone()
            is not None
        )


@pytest.mark.parametrize(
    ("name", "email", "password", "message"),
    (
        ("test", "test", "test", b"An account already exists with that email address."),
        ("test", "", "test", b"Could not create user."),
        ("test", "User1", "", b"Could not create user."),
    ),
)
def test_register_validate_input(client, name, email, password, message):
    response = client.post(
        "/register", data={"name": name, "email": email, "password": password},
        follow_redirects=True
    )
    assert message in response.data


def test_login(client, auth):
    # test that viewing the page renders without template errors
    assert client.get("/login").status_code == 200

    # test that successful login redirects to the index page
    response = auth.login()
    assert response.headers["Location"] == "http://localhost/"

    # login request set the user_id in the session
    # check that the user is loaded from the session
    with client:
        client.get("/")
        assert session["_user_id"] == '1'
        assert current_user.email == "test"


# TODO: def test_login_validate_input()


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert "user_id" not in session
