from marshmallow import Schema, fields, validate


class User(Schema):
    name = fields.Str()
    email = fields.Email()
    password = fields.Str()
    phone = fields.Str()


class CreateUser(User):
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True)


class UpdateUser(User):
    name = fields.Str(required=False)
    email = fields.Email(required=False)
    phone = fields.Str(required=False)


class GetToken(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

# =========================================

class Device(Schema):
    name = fields.Str(required=True)
    type = fields.Str(validate=validate.OneOf(["device", "tp_link_smart_plug", "ds18b20"]))
    description = fields.Str(required=False)


class CreateDevice(Device):

    type = fields.Str(required=True, validate=validate.OneOf(["device", "tp_link_smart_plug", "ds18b20"]))
    user_id = fields.Integer(required=False)
    description = fields.Str()
    ip_address = fields.Str()  # TODO: This should be required if type is tp link smart plug
    serial_number = fields.Str()  # TODO: Required only for temperature probe
    pin = fields.Integer()


class UpdateDevice(Schema):
    id = fields.Integer(required=False)
    name = fields.Str()
    type = fields.Str(validate=validate.OneOf(["device", "tp_link_smart_plug", "ds18b20"]))
    description = fields.Str()
    ip_address = fields.Str()  # TODO: This should be required if type is tp link smart plug
    serial_number = fields.Str()
    pin = fields.Integer()


class CreateSchedule(Schema):
    device_id = fields.Integer(required=True)
    starts = fields.Str(required=True)
    ends = fields.Str(required=True)
    frequency = fields.Str(required=True, validate=validate.OneOf(['weekly', 'monthly']))
    bitmask = fields.Integer(required=True)


class DataPoint(Schema):
    id = fields.Integer()
    device_id = fields.Integer()
    key = fields.Str()
    value = fields.Str()
    timestamp = fields.DateTime()
