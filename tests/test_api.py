import pytest

from piplant.db import get_db


# name
# type
# user_id
# description
# ip_address
# serial_number
# pin

@pytest.fixture
def devices(client, auth):
    mock_data = [
        {"name": "Device 1", "type": "device", "description": "description"}
    ]

    # Create devices
    auth.login()
    _devices = []
    for device in mock_data:
        response = client.post("/api/v1/devices", data={"name": device["name"], "type": device["type"], "description": device["description"]})
        assert response.status_code == 201, response.get_json()
        _devices.append(response.get_json())

    yield _devices

    # Delete devices
    for device in _devices:
        response = client.delete("/api/v1/devices/%s" % device["id"])
        assert response.status_code == 200, response.get_json()


class TestAPIUtils:
    def test_whom_am_i(self, client, auth, api_url):
        response = client.get("{}/whoami".format(api_url))
        assert response.status_code == 302, response.get_json()

        auth.login()

        response = client.get("/api/v1/whoami")
        assert response.status_code == 200, response.get_json()
        assert response.get_json() == {"id": 1, "name": "test"}

    def test_get_info(self, client, api_url):
        response = client.get(api_url + "/")
        assert response.status_code == 200
        # TODO: Assert the JSON


class TestDeviceAPI:
    def test_create_device_no_auth(self, client):
        response = client.post("/api/v1/devices", data={"name": "Device 1", "type": "device", "user_id": "1"})
        assert response.status_code == 302, response.get_json()

    @pytest.mark.parametrize(
        ("name", "device_type", "user_id", "description"),
        (
            ("Device 1", "device", "1", "this is a description"),
            ("Device 2", "device", "1", "")

        ),
    )
    def test_create_generic_device(self, client, app, auth, api_url, name, device_type, user_id, description):
        auth.login()

        response = client.post("%s/devices" % api_url, data={"name": name, "type": device_type, "user_id": user_id, "description": description})
        assert response.status_code == 201, response.get_json()

        with app.app_context():
            assert (
                get_db().execute("select * from device where name = '{}' and type = '{}'".format(name, device_type)).fetchone()
                is not None
            )

    @pytest.mark.parametrize(
        ("name", "device_type", "user_id", "description"),
        (
            ("Device 1", "device", "", "this is a description"),
        ),
    )
    def test_create_generic_device_validate_input(self, client, auth, api_url, name, device_type, user_id, description):
        auth.login()

        response = client.post("%s/devices" % api_url, data={"name": name, "type": device_type, "user_id": user_id, "description": description})
        assert response.status_code == 400, response.get_json()

        # test with an added unexpected param
        response = client.post("%s/devices" % api_url, data={"name": name, "type": device_type, "user_id": user_id, "description": description, "invalid_param": "invalid_param"})
        assert response.status_code == 400, response.get_json()

    def test_get_device(self, client, auth, api_url, devices):
        auth.login()

        for device in devices:
            response = client.get("%s/devices/%s" % (api_url, device["id"]))
            assert response.status_code == 200, response.get_json()
            # TODO: Assert body

# TODO: GET /devices

# TODO: PUT /devices/<device_id>

# TODO: DELETE /devices/<device_id>
