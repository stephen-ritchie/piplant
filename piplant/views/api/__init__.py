import datetime
import logging
from urllib.parse import urlparse

from flask import Blueprint, request, make_response, jsonify, Response, current_app
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash

from . import schemas
from piplant.models import db, User, Device, TPLinkSmartPlug, Schedule, DataPoint
from piplant.models import User
import piplant.lib as lib
import piplant.messages as messages


__version__ = '1'
api = Blueprint('api', __name__)


@api.errorhandler(400)
def bad_request(message, errors=None):
    json = {'message': message}
    if current_app.config['ENV'] != "production" and errors is not None:
        json.update({'errors': str(errors)})
    return make_response(jsonify(json), 400)


@api.errorhandler(403)
def forbidden(message=None, error=None):
    return Response(status=403)


@api.route('/', methods=['GET'])
def info():
    return make_response(jsonify({"version": str(__version__)}), 200)


@api.route('/whoami', methods=['GET'])
@login_required
def who_am_i():
    return make_response(jsonify({"id": current_user.id, "name": current_user.name}), 200)


@api.route('/token', methods=['POST'])
def get_token():
    errors = schemas.GetToken().validate(request.form)
    if errors:
        return bad_request("Could not get token.", str(errors))

    email = request.form.get('email')
    password = request.form.get('password')

    try:
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            raise Exception("Invalid credentials")
        auth_token = user.encode_auth_token(user.id)
        if auth_token:
            response_object = {
                'status': 'success',
                'message': 'Successfully logged in.',
                'auth_token': auth_token.decode()
            }
            return make_response(jsonify(response_object), 200)
    except Exception as err:
        logging.error(str(err))
        response_object = {
            'status': 'fail',
            'message': str(err)
        }
        return make_response(jsonify(response_object), 401)


@api.route('/users', methods=['POST'])
@login_required
def create_user():
    # Only admins can create new users
    if not current_user.is_admin():
        return forbidden()

    errors = schemas.CreateUser().validate(request.form)
    if errors:
        return bad_request(str(errors))

    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')

    try:
        user = lib.create_user(name=name, email=email, phone=phone, password=password)
        uri = urlparse(request.base_url + "/{}".format(user.id))
        response = make_response(jsonify({"status": messages.SUCCESS, "uri": uri.geturl()}), 201)
        response.headers["Location"] = uri.geturl()
        return response
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not create user')


@api.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    # TODO: Allow admins to get all users.
    if current_user.id != user_id:
        return forbidden()

    try:
        user = lib.get_user(user_id)
        return make_response(jsonify(user.get_info()), 200)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not get user with id %s' % user_id)


@api.route('/users', methods=['GET'])
@login_required
def get_all_users():
    return 'GET ALL USERS'


@api.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    # TODO: Allow admins to update all users.
    if current_user.id != user_id:
        return forbidden()

    errors = schemas.UpdateUser().validate(request.form)
    if errors:
        return bad_request(str(errors))

    name = request.form.get('name') or None
    email = request.form.get('email') or None
    phone = request.form.get('phone') or None

    try:
        lib.update_user(user_id, name=name, email=email, phone=phone)
        return Response(status=204)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not update user with id %s' % user_id)


@api.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    # TODO: Allow admins to deleted any user.
    if current_user.id != user_id:
        return forbidden()

    # TODO: Validate no args are passed in.

    # TODO: Is this in line with REST specification?
    try:
        lib.delete_user(user_id)
        redirect_url = lib.get_url_root(request.base_url)
        return make_response(jsonify({"redirect": True, "redirect_url": redirect_url}), 200)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not delete user with id %s' % user_id)


@api.route('/devices', methods=['POST'])
@login_required
def create_device():
    errors = schemas.CreateDevice().validate(request.form)
    if errors:
        return bad_request(str(errors))

    name = request.form.get('name')
    device_type = request.form.get('type')
    user_id = current_user.id if request.form.get('user_id') is None else request.form.get('user_id')
    description = request.form.get('description')
    ip_address = request.form.get('ip_address') or None
    serial_number = request.form.get('serial_number') or None

    try:
        device = lib.create_device(name=name, type=device_type, user_id=user_id, description=description, ip_address=ip_address, serial_number=serial_number)
        return make_response(jsonify(device.get_info()), 201)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not create device')


@api.route('/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    try:
        device = lib.get_device(device_id)
        return make_response(jsonify(device.get_all_info()), 200)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not get device with id %s' % device_id)


@api.route('/devices', methods=['GET'])
def get_all_devices():
    try:
        devices = lib.get_devices(current_user.id)
        return make_response(jsonify([device.get_info() for device in devices]), 200)
    except Exception as err:
        logging.error(str(err))
        return bad_request("Could not get devices")


@api.route('/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    errors = schemas.UpdateDevice().validate(request.form)
    if errors:
        return bad_request(str(errors))

    name = request.form.get('name')
    type = request.form.get('type')
    description = request.form.get('description')

    try:
        lib.update_device(device_id, name=name, type=type, description=description)
        return Response(status=204)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not update device with id %s' % device_id)


@api.route('/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    try:
        lib.delete_device(device_id)
        redirect_url = lib.get_url_root(request.base_url)
        return make_response(jsonify({"redirect": True, "redirect_url": redirect_url}), 200)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not delete device with id %s' % device_id)


@api.route('/schedules', methods=['POST'])
def create_schedule():
    errors = schemas.CreateSchedule().validate(request.form)
    if errors:
        return bad_request(messages.SCHEMA_VALIDATION_FAILED, str(errors))

    device_id = int(request.form.get('device_id'))
    starts = datetime.datetime.strptime(request.form.get('starts'), "%H:%M")
    ends = datetime.datetime.strptime(request.form.get('ends'), "%H:%M")
    frequency = request.form.get('frequency')
    bitmask = int(request.form.get('bitmask'), 2)

    try:
        schedule = lib.create_schedule(device_id, starts, ends, frequency, bitmask)
        return make_response(jsonify(schedule.get_info()), 201)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not create schedule', str(err))

# TODO: Get schedule(s)

# TODO: Update schedule(s)


@api.route('/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    try:
        lib.delete_schedule(schedule_id)
        return make_response(jsonify({"redirect": False}), 200)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not delete schedule with id %s' % schedule_id)


# TODO: Create task? Is this a use case?


@api.route('/tasks/<int:user_id>', methods=['GET'])
def get_tasks(user_id):
    try:
        tasks = lib.get_tasks(user_id)
        return make_response(jsonify(tasks), 200)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not get tasks for user with id %s' % user_id, err)


@api.route('/datapoints', methods=['POST'])
def create_data_point():
    errors = schemas.DataPoint().validate(request.form)
    if errors:
        return bad_request(messages.SCHEMA_VALIDATION_FAILED, str(errors))

    device_id = request.form.get("device_id")
    key = request.form.get("key")
    value = request.form.get("value")
    timestamp = request.form.get("timestamp")
    try:
        datapoint = lib.create_data_point(device_id=device_id, key=key, value=value, timestamp=timestamp)
        return make_response(jsonify(datapoint.get_info()), 201)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not create data point.', err)


@api.route('/datapoints/<int:data_point_id>', methods=['GET'])
def get_data_point(data_point_id):
    try:
        data_point = lib.get_data_point(data_point_id)
        return make_response(jsonify(data_point.get_info()), 200)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not get data point with id %s' % data_point_id, err)


# TODO: Update datapoint


# TODO: Delete datapoint


@api.route('/charts/<int:device_id>', methods=['GET'])
@login_required
def get_charts(device_id):
    # Only allow a user to see their own devices
    # TODO: Should someone be able to phish out device IDs by looking for 403s?
    device = lib.get_device(device_id)
    if device is None or device.user_id != current_user.id:
        return forbidden()

    # Get the unique keys for the device
    distinct_keys = []
    for value in db.session.query(DataPoint.key).filter(DataPoint.device_id == device_id).distinct():
        distinct_keys.append(value)

    # Create a Chart.js chart for each key type
    charts = []
    for key in distinct_keys:
        chart = {'type': 'line'}
        chart.update({'options': {}})
        chart.update({'title': key[0]})
        dataset_label = key[0]

        labels = []
        data = []
        for record in db.session.query(DataPoint).filter(DataPoint.device_id == device_id).filter(DataPoint.key == key[0]):
            labels.append(record.timestamp)
            data.append(record.value)

        chart.update({'data': {
            'labels': labels,
            'datasets': [{
                'label': dataset_label,
                'backgroundColor': 'rgb(80, 89, 120)',
                'borderColor': 'rgb(80, 89, 120)',
                'data': data
            }]
        }})

        charts.append(chart)

    return make_response(jsonify(charts), 200)


@api.route('/requests', methods=['POST'])
def process_request():
    device_id = request.get_json()['device_id']
    for key, value in request.get_json()['payload'].items():
        lib.create_data_point(device_id, key, value, datetime.datetime.now().isoformat())

    return Response(status=200)
