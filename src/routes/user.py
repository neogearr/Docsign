from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime
from src.models.user import User, Client
from src.models.tenant import Tenant
from src.extensions import db
from src.utils.auth import token_required, role_required, get_current_user, tenant_required, log_audit_action

user_bp = Blueprint('user', __name__)

@user_bp.route('/auth/register', methods=['POST'])
@tenant_required
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'User already exists'}), 409
        
        # Create new user
        user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data.get('role', 'viewer'),
            tenant_id=request.tenant.id
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Log audit action
        log_audit_action('CREATE', 'USER', user.id, {'email': user.email})
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@user_bp.route('/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'message': 'Account is inactive'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        # Log audit action
        log_audit_action('LOGIN', 'USER', user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

@user_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    new_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': new_token}), 200

@user_bp.route('/users/profile', methods=['GET'])
@token_required
def get_profile():
    """Get current user profile"""
    user = get_current_user()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200

@user_bp.route('/users/profile', methods=['PUT'])
@token_required
def update_profile():
    """Update current user profile"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            # Check if email is already taken
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'message': 'Email already taken'}), 409
            user.email = data['email']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log audit action
        log_audit_action('UPDATE', 'USER', user.id, data)
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Update failed', 'error': str(e)}), 500

@user_bp.route('/users', methods=['GET'])
@token_required
@role_required(['admin'])
def list_users():
    """List all users (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        users = User.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch users', 'error': str(e)}), 500

@user_bp.route('/clients', methods=['POST'])
@token_required
@role_required(['admin', 'editor', 'sender'])
def create_client():
    """Create a new client"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        # Validate required fields
        required_fields = ['email', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        # Create new client
        client = Client(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone'),
            company=data.get('company'),
            created_by=user.id
        )
        
        db.session.add(client)
        db.session.commit()
        
        # Log audit action
        log_audit_action('CREATE', 'CLIENT', client.id, {'email': client.email})
        
        return jsonify({
            'message': 'Client created successfully',
            'client': client.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Client creation failed', 'error': str(e)}), 500

@user_bp.route('/clients', methods=['GET'])
@token_required
def list_clients():
    """List clients created by current user"""
    try:
        user = get_current_user()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        clients = Client.query.filter_by(created_by=user.id).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'clients': [client.to_dict() for client in clients.items],
            'total': clients.total,
            'pages': clients.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch clients', 'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
