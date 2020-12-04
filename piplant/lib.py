import calendar
from datetime import datetime
from typing import List
from urllib.parse import urlparse

from werkzeug.security import generate_password_hash

from .models import db, User, Device, TPLinkSmartPlug, Schedule, DataPoint


def get_url_root(url):
    url = urlparse(url)
    root_url = urlparse("%s://%s" % (url.scheme, url.netloc))
    return root_url.geturl()


def create_user(name, email, password, phone):
    user = User.query.filter_by(email=email).first()
    if user:
        raise Exception("A user with email [%s] already exists." % email)

    if not email:
        raise Exception("Email address cannot be empty.")
    if not password:
        raise Exception("Password cannot be empty")

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
    if email is not None and User.query.filter_by(email=email).first() and email != user.email:
        raise Exception('Email address is already in use.')

    db.session.commit()

    return user


def delete_user(user_id):
    for device in get_devices(user_id):
        delete_device(device.id)

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
    for schedule in db.session.query(Schedule).filter(Schedule.device_id == device_id).all():
        delete_schedule(schedule.id)

    for data_point in get_all_data_points_by_device_id(device_id):
        delete_data_point(data_point.id)

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
        if device.type == "tp_link_smart_plug":
            tasks.append({"actions": list(["status"]), "info": device.get_info()})

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


def create_data_point(device_id: int, key: str, value: str, timestamp: str) -> DataPoint:
    datapoint = DataPoint(device_id=device_id, key=key, value=value, timestamp=timestamp)
    db.session.add(datapoint)
    db.session.commit()
    return datapoint


def get_data_point(data_point_id: int) -> DataPoint:
    return DataPoint.query.filter_by(id=data_point_id).first()


def get_all_data_points_by_device_id(device_id: int) -> List[DataPoint]:
    return [data_point for data_point in db.session.query(DataPoint).filter(DataPoint.device_id == device_id).all()]


# TODO: Should a data point be allowed to be updated?


def delete_data_point(data_point_id: int) -> None:
    data_point = get_data_point(data_point_id)
    db.session.delete(data_point)
    db.session.commit()
