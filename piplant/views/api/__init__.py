import datetime
import logging
from urllib.parse import urlparse

from flask import Blueprint, request, make_response, jsonify, Response, current_app
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash

from . import schemas
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
    return make_response(jsonify({"version": __version__}), 200)


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
def create_user():
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
    if current_user.id != user_id:
        return forbidden()

    try:
        user = lib.get_user(user_id)
        return make_response(jsonify(user.get_info()), 200)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not get user with id %s' % user_id)


@api.route('/users', methods=['GET'])
def get_all_users():
    return 'GET ALL USERS'


@api.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    if current_user.id != user_id:
        return forbidden()

    errors = schemas.UpdateUser().validate(request.form)
    if errors:
        return bad_request(str(errors))

    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')

    try:
        lib.update_user(user_id, name=name, email=email, phone=phone)
        return Response(status=204)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not update user with id %s' % user_id)


@api.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
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
def create_device():
    errors = schemas.CreateDevice().validate(request.form)
    if errors:
        return bad_request(str(errors))

    name = request.form.get('name')
    device_type = request.form.get('type')
    user_id = current_user.id if request.form.get('user_id') is None else request.form.get('user_id')
    description = request.form.get('description')

    try:
        device = lib.create_device(name=name, type=device_type, user_id=user_id, description=description)
        return make_response(jsonify(device.get_info()), 201)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not create device')


@api.route('/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    try:
        device = lib.get_device(device_id)
        return make_response(jsonify(device.get_info()), 200)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not get device with id %s' % device_id)


@api.route('/devices', methods=['GET'])
def get_all_devices():
    return 'GET ALL DEVICES'


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


@api.route('/tasks', methods=['GET'])
def get_tasks():
    user_id = request.form.get("user_id")
    try:
        tasks = lib.get_tasks(user_id)
        return make_response(jsonify(tasks), 200)
    except Exception as err:
        logging.error(str(err))
        return bad_request('Could not get tasks for user with id %s' % user_id, err)
