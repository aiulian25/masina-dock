from flask import Flask, jsonify, request, send_from_directory, send_file, session, redirect
from flask_cors import CORS
from flask_login import login_required, current_user
from flask_mail import Mail
from models import db, Vehicle, ServiceRecord, FuelRecord, Reminder, Todo, User, RecurringExpense
from auth import auth_bp, login_manager
from config import Config
import os
from datetime import datetime, timedelta
import pandas as pd
from werkzeug.utils import secure_filename
import io
import shutil
import zipfile
import tempfile
import secrets
import re

app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend/templates')
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})
db.init_app(app)
login_manager.init_app(app)
mail = Mail(app)

app.register_blueprint(auth_bp)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_ATTACHMENT_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'odt', 'ods'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_attachment(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_ATTACHMENT_EXTENSIONS

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@app.before_request
def check_session():
    session.permanent = True
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)

@app.route('/')
def index():
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/login')
def login_page():
    return send_from_directory(app.template_folder, 'login.html')

@app.route('/register')
def register_page():
    return send_from_directory(app.template_folder, 'register.html')

@app.route('/first-login')
@login_required
def first_login_page():
    if not current_user.must_change_credentials:
        return redirect('/dashboard')
    return send_from_directory(app.template_folder, 'first_login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return send_from_directory(app.template_folder, 'dashboard.html')

@app.route('/settings')
@login_required
def settings_page():
    return send_from_directory(app.template_folder, 'settings.html')

@app.route('/vehicles')
@login_required
def vehicles_page():
    return send_from_directory(app.template_folder, 'vehicles.html')

@app.route('/vehicle-detail')
@login_required
def vehicle_detail_page():
    return send_from_directory(app.template_folder, 'vehicle_detail.html')

@app.route('/service-records')
@login_required
def service_records_page():
    return send_from_directory(app.template_folder, 'service_records.html')

@app.route('/repairs')
@login_required
def repairs_page():
    return send_from_directory(app.template_folder, 'repairs.html')

@app.route('/fuel')
@login_required
def fuel_page():
    return send_from_directory(app.template_folder, 'fuel.html')

@app.route('/taxes')
@login_required
def taxes_page():
    return send_from_directory(app.template_folder, 'taxes.html')

@app.route('/notes')
@login_required
def notes_page():
    return send_from_directory(app.template_folder, 'notes.html')

@app.route('/reminders')
@login_required
def reminders_page():
    return send_from_directory(app.template_folder, 'reminders.html')

@app.route('/planner')
@login_required
def planner_page():
    return send_from_directory(app.template_folder, 'planner.html')

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory('/app/uploads', filename)

@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'language': current_user.language,
        'unit_system': current_user.unit_system,
        'currency': current_user.currency,
        'theme': current_user.theme,
        'photo': current_user.photo
    }), 200

@app.route('/api/settings/language', methods=['POST'])
@login_required
def update_language():
    data = request.get_json()
    current_user.language = data.get('language', 'en')
    db.session.commit()
    return jsonify({'message': 'Language updated successfully'}), 200

@app.route('/api/settings/units', methods=['POST'])
@login_required
def update_units():
    data = request.get_json()
    current_user.unit_system = data.get('unit_system', 'metric')
    current_user.currency = data.get('currency', 'USD')
    db.session.commit()
    return jsonify({'message': 'Units and currency updated successfully'}), 200

@app.route('/api/settings/theme', methods=['POST'])
@login_required
def update_theme():
    data = request.get_json()
    current_user.theme = data['theme']
    db.session.commit()
    return jsonify({'message': 'Theme updated successfully'}), 200

@app.route('/api/user/update-profile', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json()
    
    if 'username' in data and data['username'] != current_user.username:
        existing = User.query.filter_by(username=data['username']).first()
        if existing:
            return jsonify({'error': 'Username already taken'}), 400
        current_user.username = data['username']
    
    if 'email' in data and data['email'] != current_user.email:
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        existing = User.query.filter_by(email=data['email']).first()
        if existing:
            return jsonify({'error': 'Email already registered'}), 400
        current_user.email = data['email']
    
    if 'photo' in data:
        current_user.photo = data['photo']
    
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200

@app.route('/api/backup/create', methods=['GET'])
@login_required
def create_backup():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'masina_dock_backup_{timestamp}.zip'
    
    temp_dir = tempfile.mkdtemp()
    backup_path = os.path.join(temp_dir, backup_filename)
    
    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            db_path = '/app/data/masina_dock.db'
            if os.path.exists(db_path):
                zipf.write(db_path, 'masina_dock.db')
            
            uploads_dir = '/app/uploads'
            if os.path.exists(uploads_dir):
                for root, dirs, files in os.walk(uploads_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, '/app')
                        zipf.write(file_path, arcname)
        
        return send_file(
            backup_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=backup_filename
        )
    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/restore', methods=['POST'])
@login_required
def restore_backup():
    if 'backup' not in request.files:
        return jsonify({'error': 'No backup file provided'}), 400
    
    file = request.files['backup']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.zip'):
        return jsonify({'error': 'Invalid file type. Please upload a .zip file.'}), 400
    
    temp_dir = tempfile.mkdtemp()
    backup_path = os.path.join(temp_dir, secure_filename(file.filename))
    
    try:
        file.save(backup_path)
        
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(temp_dir)
        
        extracted_db = os.path.join(temp_dir, 'masina_dock.db')
        if os.path.exists(extracted_db):
            target_db = '/app/data/masina_dock.db'
            backup_db = '/app/data/masina_dock.db.backup'
            
            if os.path.exists(target_db):
                shutil.copy2(target_db, backup_db)
                os.remove(target_db)
            
            shutil.copy2(extracted_db, target_db)
        else:
            raise Exception('Database file not found in backup')
        
        extracted_uploads = os.path.join(temp_dir, 'uploads')
        if os.path.exists(extracted_uploads):
            target_uploads = '/app/uploads'
            
            for item in os.listdir(target_uploads):
                item_path = os.path.join(target_uploads, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"Error removing {item_path}: {e}")
            
            for root, dirs, files in os.walk(extracted_uploads):
                rel_path = os.path.relpath(root, extracted_uploads)
                target_path = os.path.join(target_uploads, rel_path) if rel_path != '.' else target_uploads
                
                os.makedirs(target_path, exist_ok=True)
                
                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(target_path, file)
                    shutil.copy2(src_file, dst_file)
                    os.chmod(dst_file, 0o644)
        
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        return jsonify({'message': 'Backup restored successfully'}), 200
        
    except zipfile.BadZipFile:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return jsonify({'error': 'Invalid or corrupted backup file'}), 400
    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return jsonify({'error': f'Restore failed: {str(e)}'}), 500

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
            odometer=data.get('odometer', 0),
            photo=data.get('photo')
        )
        db.session.add(vehicle)
        db.session.commit()
        return jsonify({'id': vehicle.id, 'message': 'Vehicle added successfully'}), 201

@app.route('/api/upload/photo', methods=['POST'])
@login_required
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo provided'}), 400
    
    file = request.files['photo']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_image(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = secrets.token_hex(4)
        filename = f"{timestamp}_{random_suffix}_{filename}"
        
        uploads_dir = '/app/uploads'
        os.makedirs(uploads_dir, exist_ok=True)
        
        filepath = os.path.join(uploads_dir, filename)
        file.save(filepath)
        
        os.chmod(filepath, 0o644)
        
        return jsonify({'photo_url': f'/uploads/{filename}'}), 200
    
    return jsonify({'error': 'Invalid file type. Only images are allowed.'}), 400

@app.route('/api/upload/attachment', methods=['POST'])
@login_required
def upload_attachment():
    if 'attachment' not in request.files:
        return jsonify({'error': 'No attachment provided'}), 400
    
    file = request.files['attachment']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_attachment(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = secrets.token_hex(4)
        filename = f"{timestamp}_{random_suffix}_{filename}"
        
        attachments_dir = '/app/uploads/attachments'
        os.makedirs(attachments_dir, exist_ok=True)
        
        filepath = os.path.join(attachments_dir, filename)
        file.save(filepath)
        
        os.chmod(filepath, 0o644)
        
        relative_path = f'attachments/{filename}'
        return jsonify({'file_path': relative_path}), 200
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/attachments/download', methods=['GET'])
@login_required
def download_attachment():
    file_path = request.args.get('path')
    
    if not file_path:
        return jsonify({'error': 'No file path provided'}), 400
    
    full_path = os.path.join('/app/uploads', file_path)
    
    if not os.path.exists(full_path):
        return jsonify({'error': 'File not found'}), 404
    
    if not full_path.startswith('/app/uploads'):
        return jsonify({'error': 'Invalid file path'}), 403
    
    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)
    
    return send_from_directory(directory, filename, as_attachment=True)

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
        vehicle.photo = data.get('photo', vehicle.photo)
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
            category=data.get('category'),
            document_path=data.get('document_path')
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

@app.route('/api/vehicles/<int:vehicle_id>/recurring-expenses', methods=['GET', 'POST'])
@login_required
def recurring_expenses(vehicle_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'GET':
        expenses = RecurringExpense.query.filter_by(vehicle_id=vehicle_id, is_active=True).all()
        return jsonify([{
            'id': e.id,
            'expense_type': e.expense_type,
            'description': e.description,
            'amount': e.amount,
            'frequency': e.frequency,
            'start_date': e.start_date.isoformat(),
            'next_due_date': e.next_due_date.isoformat(),
            'is_active': e.is_active,
            'notes': e.notes
        } for e in expenses]), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        
        start_date = datetime.fromisoformat(data['start_date']).date()
        frequency = data['frequency']
        
        if frequency == 'monthly':
            next_due = start_date + timedelta(days=30)
        elif frequency == 'quarterly':
            next_due = start_date + timedelta(days=90)
        elif frequency == 'yearly':
            next_due = start_date + timedelta(days=365)
        else:
            next_due = start_date
        
        expense = RecurringExpense(
            vehicle_id=vehicle_id,
            expense_type=data['expense_type'],
            description=data['description'],
            amount=data['amount'],
            frequency=frequency,
            start_date=start_date,
            next_due_date=next_due,
            notes=data.get('notes')
        )
        
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({
            'id': expense.id,
            'message': 'Recurring expense added successfully',
            'next_due_date': next_due.isoformat()
        }), 201

@app.route('/api/vehicles/<int:vehicle_id>/recurring-expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def cancel_recurring_expense(vehicle_id, expense_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    expense = RecurringExpense.query.filter_by(id=expense_id, vehicle_id=vehicle_id).first_or_404()
    
    expense.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Recurring expense cancelled successfully'}), 200

@app.route('/api/vehicles/<int:vehicle_id>/export-all', methods=['GET'])
@login_required
def export_all_vehicle_data(vehicle_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    
    service_records = ServiceRecord.query.filter_by(vehicle_id=vehicle_id).order_by(ServiceRecord.date.desc()).all()
    fuel_records = FuelRecord.query.filter_by(vehicle_id=vehicle_id).order_by(FuelRecord.date.desc()).all()
    reminders = Reminder.query.filter_by(vehicle_id=vehicle_id).all()
    todos = Todo.query.filter_by(vehicle_id=vehicle_id).all()
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        vehicle_data = pd.DataFrame([{
            'Year': vehicle.year,
            'Make': vehicle.make,
            'Model': vehicle.model,
            'VIN': vehicle.vin or '',
            'License Plate': vehicle.license_plate or '',
            'Current Odometer': vehicle.odometer,
            'Status': vehicle.status,
            'Photo URL': vehicle.photo or ''
        }])
        vehicle_data.to_excel(writer, sheet_name='Vehicle Info', index=False)
        
        if service_records:
            service_df = pd.DataFrame([{
                'Date': r.date.strftime('%Y-%m-%d'),
                'Odometer': r.odometer,
                'Description': r.description,
                'Category': r.category or '',
                'Cost': r.cost,
                'Notes': r.notes or '',
                'Document': r.document_path or ''
            } for r in service_records])
            service_df.to_excel(writer, sheet_name='Service Records', index=False)
        
        if fuel_records:
            fuel_df = pd.DataFrame([{
                'Date': r.date.strftime('%Y-%m-%d'),
                'Odometer': r.odometer,
                'Fuel Amount': r.fuel_amount,
                'Unit': r.unit,
                'Cost': r.cost,
                'Unit Cost': r.unit_cost or 0,
                'Distance': r.distance or 0,
                'Fuel Economy': r.fuel_economy or 0,
                'Notes': r.notes or ''
            } for r in fuel_records])
            fuel_df.to_excel(writer, sheet_name='Fuel Records', index=False)
        
        if reminders:
            reminders_df = pd.DataFrame([{
                'Description': r.description,
                'Urgency': r.urgency,
                'Due Date': r.due_date.strftime('%Y-%m-%d') if r.due_date else '',
                'Due Odometer': r.due_odometer or '',
                'Recurring': r.recurring,
                'Interval Type': r.interval_type or '',
                'Interval Value': r.interval_value or '',
                'Notes': r.notes or '',
                'Completed': r.completed
            } for r in reminders])
            reminders_df.to_excel(writer, sheet_name='Reminders', index=False)
        
        if todos:
            todos_df = pd.DataFrame([{
                'Description': t.description,
                'Type': t.type or '',
                'Priority': t.priority,
                'Status': t.status,
                'Cost': t.cost,
                'Notes': t.notes or ''
            } for t in todos])
            todos_df.to_excel(writer, sheet_name='Todos', index=False)
    
    output.seek(0)
    
    filename = f"{vehicle.year}_{vehicle.make}_{vehicle.model}_Complete_Data_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False)

# Edit/Delete operations for Service Records
@app.route('/api/vehicles/<int:vehicle_id>/service-records/<int:record_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def service_record_operations(vehicle_id, record_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    record = ServiceRecord.query.filter_by(id=record_id, vehicle_id=vehicle_id).first_or_404()
    
    if request.method == 'GET':
        return jsonify({
            'id': record.id,
            'date': record.date.isoformat(),
            'odometer': record.odometer,
            'description': record.description,
            'category': record.category,
            'cost': record.cost,
            'notes': record.notes or '',
            'document_path': record.document_path or ''
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        record.date = datetime.fromisoformat(data['date']).date() if 'date' in data else record.date
        record.odometer = data.get('odometer', record.odometer)
        record.description = data.get('description', record.description)
        record.category = data.get('category', record.category)
        record.cost = data.get('cost', record.cost)
        record.notes = data.get('notes', record.notes)
        db.session.commit()
        return jsonify({'message': 'Service record updated successfully'})
    
    elif request.method == 'DELETE':
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Service record deleted successfully'})

# Edit/Delete operations for Fuel Records
@app.route('/api/vehicles/<int:vehicle_id>/fuel-records/<int:record_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def fuel_record_operations(vehicle_id, record_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    record = FuelRecord.query.filter_by(id=record_id, vehicle_id=vehicle_id).first_or_404()
    
    if request.method == 'GET':
        return jsonify({
            'id': record.id,
            'date': record.date.isoformat(),
            'odometer': record.odometer,
            'fuel_amount': record.fuel_amount,
            'cost': record.cost,
            'notes': record.notes or ''
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        record.date = datetime.fromisoformat(data['date']).date() if 'date' in data else record.date
        record.odometer = data.get('odometer', record.odometer)
        record.fuel_amount = data.get('fuel_amount', record.fuel_amount)
        record.cost = data.get('cost', record.cost)
        record.notes = data.get('notes', record.notes)
        db.session.commit()
        return jsonify({'message': 'Fuel record updated successfully'})
    
    elif request.method == 'DELETE':
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Fuel record deleted successfully'})

# Edit/Delete operations for Reminders
@app.route('/api/vehicles/<int:vehicle_id>/reminders/<int:reminder_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def reminder_operations(vehicle_id, reminder_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    reminder = Reminder.query.filter_by(id=reminder_id, vehicle_id=vehicle_id).first_or_404()
    
    if request.method == 'GET':
        return jsonify({
            'id': reminder.id,
            'description': reminder.description,
            'urgency': reminder.urgency,
            'due_date': reminder.due_date.isoformat() if reminder.due_date else None,
            'due_odometer': reminder.due_odometer,
            'notes': reminder.notes or ''
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        reminder.description = data.get('description', reminder.description)
        reminder.urgency = data.get('urgency', reminder.urgency)
        if 'due_date' in data and data['due_date']:
            reminder.due_date = datetime.fromisoformat(data['due_date']).date()
        reminder.due_odometer = data.get('due_odometer', reminder.due_odometer)
        reminder.notes = data.get('notes', reminder.notes)
        db.session.commit()
        return jsonify({'message': 'Reminder updated successfully'})
    
    elif request.method == 'DELETE':
        db.session.delete(reminder)
        db.session.commit()
        return jsonify({'message': 'Reminder deleted successfully'})
