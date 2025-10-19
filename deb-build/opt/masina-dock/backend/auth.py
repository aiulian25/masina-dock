from flask import Blueprint, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
from functools import wraps

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        is_admin=User.query.count() == 0
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully', 'user_id': user.id}), 201

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']):
        login_user(user, remember=True)
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'theme': user.theme,
                'first_login': user.first_login
            }
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/api/auth/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    
    if not current_user.check_password(data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    current_user.set_password(data['new_password'])
    current_user.first_login = False
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200

@auth_bp.route('/api/auth/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'is_admin': u.is_admin,
        'created_at': u.created_at.isoformat()
    } for u in users]), 200

@auth_bp.route('/api/auth/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200
