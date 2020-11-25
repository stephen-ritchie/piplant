import datetime

import jwt
from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Text

from . import messages

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    email = Column(Text, unique=True)
    phone = Column(Text)
    password = Column(Text)

    def __init__(self, name, email, password, phone=None):
        self.name = name
        self.email = email
        self.password = password
        self.phone = phone

    @staticmethod
    def encode_auth_token(user_id):
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(
                payload,
                current_app.config.get('SECRET_KEY'),
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        try:
            payload = jwt.decode(auth_token, current_app.config.get('SECRET_KEY'), algorithms='HS256')
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return messages.JWT_SIGNATURE_EXPIRED
        except jwt.InvalidTokenError:
            return messages.JWT_INVALID_TOKEN

    def get_info(self):
        return {"id": self.id, "email": self.email, "name": self.name, "phone": self.phone}


class Device(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    type = Column(Text)
    user_id = Column(Integer)
    description = Column(Text)

    __mapper_args__ = {
        'polymorphic_identity': 'device',
        'polymorphic_on': type
    }

    def __init__(self, name, type, user_id, description):
        self.name = name
        self.type = type
        self.user_id = user_id
        self.description = description

    @property
    def is_tp_link_smart_plug(self):
        return self.type == "tp_link_smart_plug"

    def get_info(self):
        return {"id": self.id, "name": self.name, "type": self.type, "user_id": self.user_id, "description": self.description}


class TPLinkSmartPlug(Device):
    ip_address = Column(Text)

    __mapper_args__ = {
        'polymorphic_identity': 'tp_link_smart_plug',
    }

    def __init__(self, name, user_id, ip_address, description):
        super().__init__(name=name, type="tp_link_smart_plug", user_id=user_id, description=description)
        self.ip_address = ip_address

    def get_info(self):
        info = super().get_info()
        info['ip_address'] = self.ip_address
        return info


class DataPoint(db.Model):
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, nullable=False)
    key = Column(Text, nullable=False)
    value = Column(Text, nullable=False)

    def __init__(self, device_id, key, value):
        self.device_id = device_id
        self.key = key
        self.value = value

    def get_info(self):
        return {"id": self.id, "device_id": self.device_id, "key": self.key, "value": self.value}


class Schedule(db.Model):
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer)
    starts = Column(Text)
    ends = Column(Text)
    frequency = Column(Text)
    bitmask = Column(Integer)

    def __init__(self, device_id, starts, ends, frequency, bitmask):
        self.device_id = device_id
        self.starts = starts
        self.ends = ends
        self.frequency = frequency
        self.bitmask = bitmask

    def get_info(self):
        return {"id": self.id, "device_id": self.device_id, "starts": self.starts, "ends": self.ends, "frequency": self.frequency, "bitmask": self.bitmask}

    @staticmethod
    def datetime_to_time(datetime_str):
        return datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S").time()

    @staticmethod
    def int_to_weekdays(bitmask):
        number = int(bitmask)
        num_bits = 7
        bits = [(number >> bit) & 1 for bit in range(num_bits - 1, -1, -1)]

        days = []
        if bool(bits[0]):
            days.append("Sunday")
        if bool(bits[1]):
            days.append("Monday")
        if bool(bits[2]):
            days.append("Tuesday")
        if bool(bits[3]):
            days.append("Wednesday")
        if bool(bits[4]):
            days.append("Thursday")
        if bool(bits[5]):
            days.append("Friday")
        if bool(bits[6]):
            days.append("Saturday")

        # for position, bit in enumerate(bits):
        #     print('%d  %5r (%d)' % (position, bool(bit), bit))

        return days
