from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    theme = db.Column(db.String(10), default='dark')
    first_login = db.Column(db.Boolean, default=True)
    must_change_credentials = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(5), default='en')
    unit_system = db.Column(db.String(20), default='imperial')
    currency = db.Column(db.String(10), default='GBP')
    photo = db.Column(db.String(255))
    
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100))
    email_verification_sent_at = db.Column(db.DateTime)
    
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))
    backup_codes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_email_verification_token(self):
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = datetime.utcnow()
        return self.email_verification_token
    
    def verify_email(self, token):
        if self.email_verification_token == token:
            self.email_verified = True
            self.email_verification_token = None
            return True
        return False
    
    def generate_backup_codes(self):
        codes = [secrets.token_hex(4).upper() for _ in range(10)]
        self.backup_codes = ','.join([generate_password_hash(code) for code in codes])
        return codes
    
    def verify_backup_code(self, code):
        if not self.backup_codes:
            return False
        
        codes = self.backup_codes.split(',')
        for i, hashed_code in enumerate(codes):
            if check_password_hash(hashed_code, code.upper()):
                codes.pop(i)
                self.backup_codes = ','.join(codes)
                return True
        return False

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
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
    recurring_expenses = db.relationship('RecurringExpense', backref='vehicle', lazy=True, cascade='all, delete-orphan')

class ServiceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    odometer = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    cost = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    category = db.Column(db.String(50))
    document_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FuelRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    odometer = db.Column(db.Integer, nullable=False)
    fuel_amount = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float)
    distance = db.Column(db.Integer)
    fuel_economy = db.Column(db.Float)
    unit = db.Column(db.String(20), default='MPG')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    urgency = db.Column(db.String(20), default='not_urgent')
    due_date = db.Column(db.Date)
    due_odometer = db.Column(db.Integer)
    metric = db.Column(db.String(50))
    recurring = db.Column(db.Boolean, default=False)
    interval_type = db.Column(db.String(20))
    interval_value = db.Column(db.Integer)
    completed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    cost = db.Column(db.Float, default=0.0)
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='planned')
    type = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RecurringExpense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    expense_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
