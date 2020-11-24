import calendar
from datetime import datetime
from urllib.parse import urlparse

from werkzeug.security import generate_password_hash

from .models import db, User, Device, TPLinkSmartPlug, Schedule


def get_url_root(url):
    url = urlparse(url)
    root_url = urlparse("%s://%s" % (url.scheme, url.netloc))
    return root_url.geturl()


def create_user(name, email, password, phone):
    user = User.query.filter_by(email=email).first()
    if user:
        raise Exception("A user with email [%s] already exists." % email)

    db.session.add(
        User(
            email=email,
            name=name,
            phone=phone,
            password=generate_password_hash(password, method='sha256')
        )
    )
    db.session.commit()

    return User.query.filter_by(email=email).first()


def get_user(user_id):
    return User.query.filter_by(id=user_id).first()


def get_users():
    # TODO: Restrict users that can be seen by role
    return [user for user in User.query.filter_by().all()]


def update_user(user_id, name=None, email=None, password=None, phone=None):
    user = get_user(user_id)
    user.name = user.name if name is None else name
    user.password = user.password if password is None else generate_password_hash(password, method='sha256')
    user.phone = user.phone if phone is None else phone

    # Make sure email address is not already in use
    # TODO: This logic doesn't work when passing in your own email address
    if email is not None and User.query.filter_by(email=email).first():
        raise Exception('Email address is already in use.')

    db.session.commit()

    return user


def delete_user(user_id):
    user = get_user(user_id)
    db.session.delete(user)
    db.session.commit()


def create_device(name, type, user_id, description, ip_address=None):
    if type == "tp_link_smart_plug":
        device = TPLinkSmartPlug(name=name, user_id=user_id, ip_address=ip_address, description=description)
    else:
        device = Device(name=name, type=type, user_id=user_id, description=description)

    db.session.add(device)
    db.session.commit()
    return device


def get_device(device_id):
    return Device.query.filter_by(id=device_id).first()


def get_devices(user_id):
    return [device for device in db.session.query(Device).filter(Device.user_id == user_id).all()]


def update_device(device_id, name=None, type=None, description=None, ip_address=None):
    device = get_device(device_id)
    device.name = device.name if name is None else name
    device.type = device.type if type is None else type
    device.description = device.description if description is None else description
    if device.is_tp_link_smart_plug:
        device.ip_address = device.ip_address if ip_address is None else ip_address

    db.session.commit()

    return device


def delete_device(device_id):
    device = get_device(device_id)
    db.session.delete(device)
    db.session.commit()


def create_schedule(device_id, starts, ends, frequency, bitmask):
    schedule = Schedule(device_id=device_id, starts=starts, ends=ends, frequency=frequency, bitmask=bitmask)
    db.session.add(schedule)
    db.session.commit()
    return schedule


def get_schedule(schedule_id):
    return Schedule.query.filter_by(id=schedule_id).first()


def get_schedules_by_device(device_id):
    return [schedule for schedule in db.session.query(Schedule).filter(Schedule.device_id == device_id).all()]


def get_schedules_by_user(user_id):
    return


def update_schedule(schedule_id):
    return


def delete_schedule(schedule_id):
    schedule = get_schedule(schedule_id)
    db.session.delete(schedule)
    db.session.commit()


def get_tasks(user_id):
    tasks = []
    for device in get_devices(user_id):
        actions = []
        for schedule in get_schedules_by_device(device.id):
            date_format = "%Y-%m-%d %H:%M:%S"
            starts = datetime.strptime(schedule.starts, date_format)
            ends = datetime.strptime(schedule.ends, date_format)
            now = datetime.now()

            if ends.time() > now.time() > starts.time() and calendar.day_name[now.weekday()] in Schedule.int_to_weekdays(schedule.bitmask):
                actions.append("on")
            else:
                actions.append("off")

            tasks.append({"actions": actions, "info": device.get_info()})

    return tasks
