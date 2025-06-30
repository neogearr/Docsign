from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from src.models.user import User
from src.models.tenant import Tenant
from src.extensions import db

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated

def role_required(allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or not user.is_active:
                return jsonify({'message': 'User not found or inactive'}), 401
            
            if user.role not in allowed_roles:
                return jsonify({'message': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def get_current_user():
    """Get current user from JWT token"""
    try:
        current_user_id = get_jwt_identity()
        return User.query.get(current_user_id)
    except:
        return None

def get_tenant_from_subdomain(subdomain):
    """Get tenant information from subdomain"""
    return Tenant.query.filter_by(subdomain=subdomain).first()

def tenant_required(f):
    """Decorator to require valid tenant context"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Extract subdomain from request headers or URL
        subdomain = request.headers.get('X-Tenant-Subdomain')
        
        if not subdomain:
            # Try to extract from Host header
            host = request.headers.get('Host', '')
            if '.' in host:
                subdomain = host.split('.')[0]
        
        if not subdomain:
            return jsonify({'message': 'Tenant subdomain required'}), 400
        
        tenant = get_tenant_from_subdomain(subdomain)
        if not tenant or tenant.status != 'active':
            return jsonify({'message': 'Invalid or inactive tenant'}), 404
        
        # Add tenant to request context
        request.tenant = tenant
        
        return f(*args, **kwargs)
    return decorated

def log_audit_action(action, resource_type, resource_id=None, details=None):
    """Log audit action"""
    from src.models.signature import AuditLog
    
    user = get_current_user()
    user_id = user.id if user else None
    
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    db.session.add(audit_log)
    db.session.commit()

def check_tenant_limits(tenant, resource_type):
    """Check if tenant has reached resource limits"""
    from src.models.user import User, Client
    from src.models.document import Document
    from src.models.signature import Signature
    
    if resource_type == 'users':
        current_count = User.query.filter_by(tenant_id=tenant.id).count()
        return current_count < tenant.max_users
    
    elif resource_type == 'documents':
        current_count = Document.query.join(User).filter(User.tenant_id == tenant.id).count()
        return current_count < tenant.max_documents
    
    elif resource_type == 'signatures':
        current_count = Signature.query.join(Document).join(User).filter(User.tenant_id == tenant.id).count()
        return current_count < tenant.max_signatures
    
    return True

