import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from piplant.views.api import schemas
import piplant.lib as lib

device = Blueprint('device', __name__)


@device.route('/devices/<int:device_id>', methods=['GET'])
@login_required
def info(device_id):
    schedules = lib.get_schedules_by_device(device_id)
    return render_template('device/about.html', device=lib.get_device(device_id), schedules=schedules)


@device.route('/devices/<int:device_id>', methods=['POST'])
def update(device_id):
    errors = schemas.UpdateDevice().validate(request.form)
    if errors:
        logging.error(str(errors))
        flash(str(errors))
        return redirect(url_for('device.info', device_id=device_id))

    name = request.form.get('name')
    device_type = request.form.get('type')
    description = request.form.get('description')
    ip_address = request.form.get('ip_address', None)
    serial_number = request.form.get('serial_number', None)

    try:
        lib.update_device(device_id=device_id, name=name, type=device_type, description=description, ip_address=ip_address, serial_number=serial_number)
    except Exception as err:
        logging.error(str(err))
        flash(str(err))

    return redirect(url_for('device.info', device_id=device_id))


@device.route('/devices', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        errors = schemas.CreateDevice().validate(request.form)
        if errors:
            logging.error(str(errors))
            flash(str(errors))
            return redirect(url_for('device.add'))

        name = request.form.get('name')
        device_type = request.form.get('type')
        description = request.form.get('description')
        ip_address = request.form.get('ip_address', None)
        serial_number = request.form.get('serial_number', None)

        try:
            lib.create_device(name=name, type=device_type, user_id=current_user.id, description=description, ip_address=ip_address, serial_number=serial_number)
            return redirect(url_for("home.landing"))
        except Exception as err:
            logging.error(str(err))
            flash(str(err))
            return redirect(url_for('device.add'))

    return render_template('device/add.html')
