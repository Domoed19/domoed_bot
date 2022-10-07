from marshmallow import Schema, fields


class MessageSchema(Schema):
    chat_id = fields.Int()
    message = fields.Str(required=True)