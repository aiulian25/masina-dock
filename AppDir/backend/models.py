from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    theme = db.Column(db.String(20), default='dark')
    first_login = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    make = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    vin = db.Column(db.String(17))
    license_plate = db.Column(db.String(20))
    odometer = db.Column(db.Integer, default=0)
    photo = db.Column(db.String(255))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    service_records = db.relationship('ServiceRecord', backref='vehicle', lazy=True, cascade='all, delete-orphan')
    fuel_records = db.relationship('FuelRecord', backref='vehicle', lazy=True, cascade='all, delete-orphan')
    reminders = db.relationship('Reminder', backref='vehicle', lazy=True, cascade='all, delete-orphan')
    todos = db.relationship('Todo', backref='vehicle', lazy=True, cascade='all, delete-orphan')

class ServiceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    odometer = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    category = db.Column(db.String(50))
    document_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FuelRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    odometer = db.Column(db.Integer, nullable=False)
    fuel_amount = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, default=0.0)
    unit_cost = db.Column(db.Float)
    distance = db.Column(db.Integer)
    fuel_economy = db.Column(db.Float)
    unit = db.Column(db.String(20), default='MPG')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    urgency = db.Column(db.String(20), default='not_urgent')
    due_date = db.Column(db.DateTime)
    due_odometer = db.Column(db.Integer)
    metric = db.Column(db.Integer)
    recurring = db.Column(db.Boolean, default=False)
    interval_type = db.Column(db.String(20))
    interval_value = db.Column(db.Integer)
    notes = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    cost = db.Column(db.Float, default=0.0)
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='planned')
    type = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
