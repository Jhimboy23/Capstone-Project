from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))

class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    distance = db.Column(db.Integer)  # Storing distance as an integer
    status = db.Column(db.String(50))  # Storing sensor status as a string (e.g., 'low', 'medium', 'high')
    datetime = db.Column(db.DateTime(timezone=True), server_default=func.now())  # Storing timestamp
    duration = db.Column(db.Integer)  # Storing duration in seconds or any other appropriate unit
    fuel_consumed = db.Column(db.Float)  # Storing fuel consumed in liters or another appropriate unit
    percentage = db.Column(db.Integer)  # Storing fuel consumed in liters or another appropriate unit
    liters = db.Column(db.Integer)  # Storing fuel consumed in liters or another appropriate unit
    remainingFuel = db.Column(db.Integer)  # Storing fuel consumed in liters or another appropriate unit


