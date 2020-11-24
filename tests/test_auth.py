import pytest

from piplant import messages


def test_register(client, app):
    # test that viewing the page renders without template errors
    assert client.get("/register").status_code == 200

    # TODO: test that successful registration redirects to the login page
    # response = client.post("/auth/register", data={"username": "a", "password": "a"})
    # assert "http://localhost/auth/login" == response.headers["Location"]

    # TODO: test that the user was inserted into the database


def test_register_via_api(client):
    data = {"name": "User 1", "email": "user1@test.com", "password": "xxx"}
    response = client.post("/api/v1/users", data=data)
    assert response.status_code == 201
    assert response.get_json()['status'] == messages.SUCCESS

    # test you cannot register again
    response = client.post("/api/v1/users", data=data)
    assert response.status_code == 400
