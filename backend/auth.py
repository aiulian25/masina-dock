from flask import Blueprint, request, jsonify, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
from werkzeug.security import check_password_hash
import pyotp
import qrcode
import io
import base64
import re
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({'error': 'Unauthorized access'}), 401

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Valid"

def send_verification_email(user, token):
    if not current_app.config.get('ENABLE_EMAIL_VERIFICATION'):
        return
    
    if not current_app.config.get('MAIL_USERNAME'):
        return
    
    try:
        from flask_mail import Message, Mail
        mail = Mail(current_app)
        
        msg = Message(
            'Verify your email for Masina-Dock',
            recipients=[user.email]
        )
        msg.body = f'''Hello {user.username},

Please verify your email address by clicking the link below:

http://localhost:5000/verify-email?token={token}

If you did not create an account, please ignore this email.

Best regards,
Masina-Dock Team
'''
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        if current_app.config.get('DISABLE_SIGNUPS'):
            return jsonify({'error': 'Registrations are currently disabled'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        is_first_user = User.query.count() == 0
        
        user = User(
            username=data['username'],
            email=data['email'],
            is_admin=is_first_user,
            language='en',
            unit_system='metric',
            currency='USD',
            email_verified=not current_app.config.get('ENABLE_EMAIL_VERIFICATION', False)
        )
        user.set_password(data['password'])
        
        if current_app.config.get('ENABLE_EMAIL_VERIFICATION', False):
            token = user.generate_email_verification_token()
            send_verification_email(user, token)
        
        db.session.add(user)
        db.session.commit()
        
        message = 'User registered successfully'
        if current_app.config.get('ENABLE_EMAIL_VERIFICATION', False):
            message += '. Please check your email to verify your account.'
        
        return jsonify({'message': message}), 201
    
    except Exception as e:
        print(f"Registration error: {e}")
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'error': 'Verification token required'}), 400
    
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        return jsonify({'error': 'Invalid or expired verification token'}), 400
    
    if user.verify_email(token):
        db.session.commit()
        return jsonify({'message': 'Email verified successfully'}), 200
    
    return jsonify({'error': 'Verification failed'}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Missing username or password'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        if current_app.config.get('ENABLE_EMAIL_VERIFICATION', False) and not user.email_verified:
            return jsonify({'error': 'Please verify your email before logging in'}), 403
        
        if user.two_factor_enabled:
            return jsonify({
                'requires_2fa': True,
                'user_id': user.id
            }), 200
        
        login_user(user, remember=True)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'theme': user.theme,
                'first_login': user.first_login,
                'must_change_credentials': user.must_change_credentials,
                'language': user.language,
                'unit_system': user.unit_system,
                'currency': user.currency,
                'photo': user.photo
            }
        }), 200
    
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/verify-2fa', methods=['POST'])
def verify_2fa():
    data = request.get_json()
    user_id = data.get('user_id')
    code = data.get('code')
    
    if not user_id or not code:
        return jsonify({'error': 'Missing required fields'}), 400
    
    user = User.query.get(user_id)
    
    if not user or not user.two_factor_enabled:
        return jsonify({'error': 'Invalid request'}), 400
    
    totp = pyotp.TOTP(user.two_factor_secret)
    
    if totp.verify(code) or user.verify_backup_code(code):
        login_user(user, remember=True)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'theme': user.theme,
                'first_login': user.first_login,
                'must_change_credentials': user.must_change_credentials,
                'language': user.language,
                'unit_system': user.unit_system,
                'currency': user.currency,
                'photo': user.photo
            }
        }), 200
    
    return jsonify({'error': 'Invalid 2FA code'}), 401

@auth_bp.route('/setup-2fa', methods=['POST'])
@login_required
def setup_2fa():
    if current_user.two_factor_enabled:
        return jsonify({'error': '2FA is already enabled'}), 400
    
    secret = pyotp.random_base32()
    current_user.two_factor_secret = secret
    
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name='Masina-Dock'
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code = base64.b64encode(buffer.getvalue()).decode()
    
    backup_codes = current_user.generate_backup_codes()
    
    db.session.commit()
    
    return jsonify({
        'secret': secret,
        'qr_code': f'data:image/png;base64,{qr_code}',
        'backup_codes': backup_codes
    }), 200

@auth_bp.route('/enable-2fa', methods=['POST'])
@login_required
def enable_2fa():
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({'error': 'Verification code required'}), 400
    
    if not current_user.two_factor_secret:
        return jsonify({'error': 'Please setup 2FA first'}), 400
    
    totp = pyotp.TOTP(current_user.two_factor_secret)
    
    if totp.verify(code):
        current_user.two_factor_enabled = True
        db.session.commit()
        return jsonify({'message': '2FA enabled successfully'}), 200
    
    return jsonify({'error': 'Invalid verification code'}), 400

@auth_bp.route('/disable-2fa', methods=['POST'])
@login_required
def disable_2fa():
    data = request.get_json()
    password = data.get('password')
    
    if not password:
        return jsonify({'error': 'Password required'}), 400
    
    if not current_user.check_password(password):
        return jsonify({'error': 'Invalid password'}), 401
    
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    current_user.backup_codes = None
    db.session.commit()
    
    return jsonify({'message': '2FA disabled successfully'}), 200

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'theme': current_user.theme,
        'language': current_user.language,
        'unit_system': current_user.unit_system,
        'currency': current_user.currency,
        'photo': current_user.photo,
        'must_change_credentials': current_user.must_change_credentials,
        'email_verified': current_user.email_verified,
        'two_factor_enabled': current_user.two_factor_enabled
    }), 200

@auth_bp.route('/update-credentials', methods=['POST'])
@login_required
def update_credentials():
    data = request.get_json()
    
    new_username = data.get('username')
    new_email = data.get('email')
    new_password = data.get('password')
    
    if not new_username or not new_email or not new_password:
        return jsonify({'error': 'Missing required fields'}), 400
    
    if new_username != current_user.username:
        existing_user = User.query.filter_by(username=new_username).first()
        if existing_user:
            return jsonify({'error': 'Username already taken'}), 400
        current_user.username = new_username
    
    if new_email != current_user.email:
        if not validate_email(new_email):
            return jsonify({'error': 'Invalid email format'}), 400
        existing_email = User.query.filter_by(email=new_email).first()
        if existing_email:
            return jsonify({'error': 'Email already registered'}), 400
        current_user.email = new_email
        
        if current_app.config.get('ENABLE_EMAIL_VERIFICATION', False):
            current_user.email_verified = False
            token = current_user.generate_email_verification_token()
            send_verification_email(current_user, token)
    
    is_valid, message = validate_password(new_password)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    current_user.set_password(new_password)
    current_user.must_change_credentials = False
    current_user.first_login = False
    
    db.session.commit()
    
    return jsonify({'message': 'Credentials updated successfully'}), 200

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    
    if not current_user.check_password(data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    is_valid, message = validate_password(data['new_password'])
    if not is_valid:
        return jsonify({'error': message}), 400
    
    current_user.set_password(data['new_password'])
    current_user.first_login = False
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200
