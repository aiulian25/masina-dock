from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_login import login_required, current_user
from models import db, Vehicle, ServiceRecord, FuelRecord, Reminder, Todo
from auth import auth_bp, login_manager
from config import Config
import os
from datetime import datetime
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend/templates')
app.config.from_object(Config)

CORS(app, supports_credentials=True)
db.init_app(app)
login_manager.init_app(app)
app.register_blueprint(auth_bp)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/api/vehicles', methods=['GET', 'POST'])
@login_required
def vehicles():
    if request.method == 'GET':
        vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
        return jsonify([{
            'id': v.id,
            'year': v.year,
            'make': v.make,
            'model': v.model,
            'vin': v.vin,
            'license_plate': v.license_plate,
            'odometer': v.odometer,
            'photo': v.photo,
            'status': v.status
        } for v in vehicles]), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        vehicle = Vehicle(
            user_id=current_user.id,
            year=data['year'],
            make=data['make'],
            model=data['model'],
            vin=data.get('vin'),
            license_plate=data.get('license_plate'),
            odometer=data.get('odometer', 0)
        )
        db.session.add(vehicle)
        db.session.commit()
        return jsonify({'id': vehicle.id, 'message': 'Vehicle added successfully'}), 201

@app.route('/api/vehicles/<int:vehicle_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def vehicle_detail(vehicle_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'GET':
        return jsonify({
            'id': vehicle.id,
            'year': vehicle.year,
            'make': vehicle.make,
            'model': vehicle.model,
            'vin': vehicle.vin,
            'license_plate': vehicle.license_plate,
            'odometer': vehicle.odometer,
            'photo': vehicle.photo,
            'status': vehicle.status
        }), 200
    
    elif request.method == 'PUT':
        data = request.get_json()
        vehicle.year = data.get('year', vehicle.year)
        vehicle.make = data.get('make', vehicle.make)
        vehicle.model = data.get('model', vehicle.model)
        vehicle.vin = data.get('vin', vehicle.vin)
        vehicle.license_plate = data.get('license_plate', vehicle.license_plate)
        vehicle.odometer = data.get('odometer', vehicle.odometer)
        vehicle.status = data.get('status', vehicle.status)
        db.session.commit()
        return jsonify({'message': 'Vehicle updated successfully'}), 200
    
    elif request.method == 'DELETE':
        db.session.delete(vehicle)
        db.session.commit()
        return jsonify({'message': 'Vehicle deleted successfully'}), 200

@app.route('/api/vehicles/<int:vehicle_id>/service-records', methods=['GET', 'POST'])
@login_required
def service_records(vehicle_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'GET':
        records = ServiceRecord.query.filter_by(vehicle_id=vehicle_id).order_by(ServiceRecord.date.desc()).all()
        return jsonify([{
            'id': r.id,
            'date': r.date.isoformat(),
            'odometer': r.odometer,
            'description': r.description,
            'cost': r.cost,
            'notes': r.notes,
            'category': r.category,
            'document_path': r.document_path
        } for r in records]), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        record = ServiceRecord(
            vehicle_id=vehicle_id,
            date=datetime.fromisoformat(data['date']),
            odometer=data['odometer'],
            description=data['description'],
            cost=data.get('cost', 0.0),
            notes=data.get('notes'),
            category=data.get('category')
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({'id': record.id, 'message': 'Service record added successfully'}), 201

@app.route('/api/vehicles/<int:vehicle_id>/fuel-records', methods=['GET', 'POST'])
@login_required
def fuel_records(vehicle_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'GET':
        records = FuelRecord.query.filter_by(vehicle_id=vehicle_id).order_by(FuelRecord.date.desc()).all()
        return jsonify([{
            'id': r.id,
            'date': r.date.isoformat(),
            'odometer': r.odometer,
            'fuel_amount': r.fuel_amount,
            'cost': r.cost,
            'unit_cost': r.unit_cost,
            'distance': r.distance,
            'fuel_economy': r.fuel_economy,
            'unit': r.unit,
            'notes': r.notes
        } for r in records]), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        
        last_record = FuelRecord.query.filter_by(vehicle_id=vehicle_id).order_by(FuelRecord.odometer.desc()).first()
        distance = data['odometer'] - last_record.odometer if last_record else 0
        
        fuel_economy = None
        if distance > 0 and data['fuel_amount'] > 0:
            if data.get('unit', 'MPG') == 'MPG':
                fuel_economy = distance / data['fuel_amount']
            elif data.get('unit') == 'L/100KM':
                fuel_economy = (data['fuel_amount'] / distance) * 100
            elif data.get('unit') == 'KM/L':
                fuel_economy = distance / data['fuel_amount']
        
        record = FuelRecord(
            vehicle_id=vehicle_id,
            date=datetime.fromisoformat(data['date']),
            odometer=data['odometer'],
            fuel_amount=data['fuel_amount'],
            cost=data.get('cost', 0.0),
            unit_cost=data.get('unit_cost'),
            distance=distance,
            fuel_economy=fuel_economy,
            unit=data.get('unit', 'MPG'),
            notes=data.get('notes')
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({'id': record.id, 'message': 'Fuel record added successfully', 'fuel_economy': fuel_economy}), 201

@app.route('/api/vehicles/<int:vehicle_id>/reminders', methods=['GET', 'POST'])
@login_required
def reminders(vehicle_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'GET':
        reminders = Reminder.query.filter_by(vehicle_id=vehicle_id, completed=False).all()
        return jsonify([{
            'id': r.id,
            'description': r.description,
            'urgency': r.urgency,
            'due_date': r.due_date.isoformat() if r.due_date else None,
            'due_odometer': r.due_odometer,
            'metric': r.metric,
            'recurring': r.recurring,
            'interval_type': r.interval_type,
            'interval_value': r.interval_value,
            'notes': r.notes
        } for r in reminders]), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        reminder = Reminder(
            vehicle_id=vehicle_id,
            description=data['description'],
            urgency=data.get('urgency', 'not_urgent'),
            due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
            due_odometer=data.get('due_odometer'),
            metric=data.get('metric'),
            recurring=data.get('recurring', False),
            interval_type=data.get('interval_type'),
            interval_value=data.get('interval_value'),
            notes=data.get('notes')
        )
        db.session.add(reminder)
        db.session.commit()
        return jsonify({'id': reminder.id, 'message': 'Reminder added successfully'}), 201

@app.route('/api/vehicles/<int:vehicle_id>/todos', methods=['GET', 'POST'])
@login_required
def todos(vehicle_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'GET':
        todos = Todo.query.filter_by(vehicle_id=vehicle_id).all()
        return jsonify([{
            'id': t.id,
            'description': t.description,
            'cost': t.cost,
            'priority': t.priority,
            'status': t.status,
            'type': t.type,
            'notes': t.notes
        } for t in todos]), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        todo = Todo(
            vehicle_id=vehicle_id,
            description=data['description'],
            cost=data.get('cost', 0.0),
            priority=data.get('priority', 'medium'),
            status=data.get('status', 'planned'),
            type=data.get('type'),
            notes=data.get('notes')
        )
        db.session.add(todo)
        db.session.commit()
        return jsonify({'id': todo.id, 'message': 'Todo added successfully'}), 201

@app.route('/api/export/<data_type>', methods=['GET'])
@login_required
def export_data(data_type):
    vehicle_id = request.args.get('vehicle_id')
    
    if data_type == 'service_records':
        records = ServiceRecord.query.filter_by(vehicle_id=vehicle_id).all()
        df = pd.DataFrame([{
            'Date': r.date,
            'Odometer': r.odometer,
            'Description': r.description,
            'Cost': r.cost,
            'Category': r.category,
            'Notes': r.notes
        } for r in records])
    elif data_type == 'fuel_records':
        records = FuelRecord.query.filter_by(vehicle_id=vehicle_id).all()
        df = pd.DataFrame([{
            'Date': r.date,
            'Odometer': r.odometer,
            'Fuel Amount': r.fuel_amount,
            'Cost': r.cost,
            'Fuel Economy': r.fuel_economy,
            'Unit': r.unit
        } for r in records])
    else:
        return jsonify({'error': 'Invalid data type'}), 400
    
    output_file = f'/tmp/{data_type}_{vehicle_id}.csv'
    df.to_csv(output_file, index=False)
    return send_from_directory('/tmp', f'{data_type}_{vehicle_id}.csv', as_attachment=True)

@app.route('/api/settings/theme', methods=['POST'])
@login_required
def update_theme():
    data = request.get_json()
    current_user.theme = data['theme']
    db.session.commit()
    return jsonify({'message': 'Theme updated successfully'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False)
