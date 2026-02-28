# backend/app/auth/rbac.py
from functools import wraps
from flask import request, jsonify, session, g
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import jwt
import os

db = SQLAlchemy()
bcrypt = Bcrypt()

# User roles
class Role:
    ADMIN = 'admin'
    OPERATOR = 'operator'
    FIELD_RESPONDER = 'field_responder'
    VIEWER = 'viewer'
    PUBLIC = 'public'

# Role permissions matrix
PERMISSIONS = {
    Role.ADMIN: {
        'manage_users': True,
        'manage_resources': True,
        'view_all_incidents': True,
        'dispatch_resources': True,
        'view_analytics': True,
        'configure_system': True
    },
    Role.OPERATOR: {
        'manage_users': False,
        'manage_resources': True,
        'view_all_incidents': True,
        'dispatch_resources': True,
        'view_analytics': True,
        'configure_system': False
    },
    Role.FIELD_RESPONDER: {
        'manage_users': False,
        'manage_resources': False,
        'view_all_incidents': False,
        'view_assigned_incidents': True,
        'update_incident_status': True,
        'view_analytics': False
    },
    Role.VIEWER: {
        'manage_users': False,
        'manage_resources': False,
        'view_all_incidents': True,
        'dispatch_resources': False,
        'view_analytics': True,
        'configure_system': False
    },
    Role.PUBLIC: {
        'manage_users': False,
        'manage_resources': False,
        'view_all_incidents': False,
        'report_incident': True,
        'view_public_alerts': True,
        'view_analytics': False
    }
}

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(50), default=Role.PUBLIC)
    department = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # For field responders - location tracking
    current_lat = db.Column(db.Float)
    current_lng = db.Column(db.Float)
    last_location_update = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        if self.role in PERMISSIONS:
            return PERMISSIONS[self.role].get(permission, False)
        return False
    
    def generate_token(self, expires_in=3600):
        """Generate JWT token"""
        payload = {
            'user_id': self.id,
            'username': self.username,
            'role': self.role,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in)
        }
        return jwt.encode(payload, os.getenv('SECRET_KEY', 'dev-secret'), algorithm='HS256')
    
    @staticmethod
    def verify_token(token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token, 
                os.getenv('SECRET_KEY', 'dev-secret'), 
                algorithms=['HS256']
            )
            return User.query.get(payload['user_id'])
        except:
            return None

# Decorators for role-based access control
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = User.verify_token(token)
        if not user or not user.is_active:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated

def require_role(*roles):
    """Require specific role(s) to access endpoint"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            if g.current_user.role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def require_permission(permission):
    """Require specific permission to access endpoint"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            if not g.current_user.has_permission(permission):
                return jsonify({'error': 'Permission denied'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# Flask routes for authentication
def init_auth_routes(app):
    from flask import Blueprint, request
    
    auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
    
    @auth_bp.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            role=data.get('role', Role.PUBLIC),
            department=data.get('department'),
            phone=data.get('phone')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }), 201
    
    @auth_bp.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 403
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        token = user.generate_token()
        
        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'permissions': PERMISSIONS.get(user.role, {})
            }
        })
    
    @auth_bp.route('/profile', methods=['GET'])
    @require_auth
    def profile():
        return jsonify({
            'id': g.current_user.id,
            'username': g.current_user.username,
            'email': g.current_user.email,
            'role': g.current_user.role,
            'department': g.current_user.department,
            'phone': g.current_user.phone,
            'permissions': PERMISSIONS.get(g.current_user.role, {})
        })
    
    @auth_bp.route('/logout', methods=['POST'])
    def logout():
        # Client-side token invalidation
        return jsonify({'message': 'Logged out successfully'})
    
    app.register_blueprint(auth_bp)
    
    return app