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
    distance = db.Column(db.Float)  # Changed from Integer to Float
    status = db.Column(db.String(50))
    datetime = db.Column(db.DateTime(timezone=True), server_default=func.now())
    duration = db.Column(db.Integer)
    fuel_consumed = db.Column(db.Float)
    percentage = db.Column(db.Integer)  # Kept as Integer
    liters = db.Column(db.Float)  # Changed from Integer to Float
    remainingFuel = db.Column(db.Float)  # Changed from Integer to Float


