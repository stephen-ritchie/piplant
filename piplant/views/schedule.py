import datetime
import logging

from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_required

import piplant.lib as lib
from piplant.models import Schedule

schedule = Blueprint('schedule', __name__)


@schedule.route('/', methods=['GET', 'POST'])
@login_required
def add():
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    time_intervals = []
    for i in range(1, 24):
        time_intervals.append(datetime.time(i, 0, 0).strftime("%H:%M:%S"))
        time_intervals.append(datetime.time(i, 30, 0).strftime("%H:%M:%S"))

    if request.method == 'POST':
        frequency = request.form.get("frequency")
        start_time = datetime.datetime.strptime(request.form.get("startTime"), "%H:%M:%S")
        end_time = datetime.datetime.strptime(request.form.get("endTime"), "%H:%M:%S")
        device_id = request.args.get("device_id")

        bitmask = []
        for index, day in enumerate(days):
            bitmask.append(str(request.form.get(day, 0)))
        bitmask = int("".join(bitmask), 2)

        try:
            lib.create_schedule(device_id, start_time, end_time, frequency, bitmask)
            return redirect(url_for('device.info', device_id=device_id))
        except Exception as err:
            logging.error(str(err))
            flash(str(err))

    return render_template('schedule/add.html', days=days, time_intervals=time_intervals)
