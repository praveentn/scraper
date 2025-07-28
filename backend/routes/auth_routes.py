# backend/routes/auth_routes.py
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from . import auth_bp
from services.auth_service import AuthService, AuditService
from utils.validators import validate_email, validate_password


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        email = data['email'].strip()
        password = data['password']
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400
        
        # Authenticate user
        result = AuthService.authenticate_user(email, password)
        
        if result['success']:
            # Log successful login
            AuditService.log_action(
                user_id=result['user']['id'],
                action='login',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify(result), 200
        else:
            # Log failed login attempt
            AuditService.log_action(
                user_id=None,
                action='login_failed',
                details={'email': email},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify(result), 401
    
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'message': 'Login failed'
        }), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['email', 'password', 'first_name', 'last_name']
        if not data or not all(data.get(field) for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            }), 400
        
        email = data['email'].strip()
        password = data['password']
        first_name = data['first_name'].strip()
        last_name = data['last_name'].strip()
        
        # Validate email format
        print(f"Validating email: {email}")
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400
        
        # Validate password strength
        if not validate_password(password):
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters long'
            }), 400
        
        # Register user
        result = AuthService.register_user(email, password, first_name, last_name)
        
        if result['success']:
            # Log registration
            AuditService.log_action(
                user_id=result['user']['id'],
                action='register',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        current_app.logger.error(f"Registration error: {e}")
        return jsonify({
            'success': False,
            'message': 'Registration failed'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        refresh_token = get_jwt()
        result = AuthService.refresh_access_token(refresh_token)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {e}")
        return jsonify({
            'success': False,
            'message': 'Token refresh failed'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint"""
    try:
        user_id = get_jwt_identity()
        
        # Log logout
        AuditService.log_action(
            user_id=user_id,
            action='logout',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # TODO: Add token to blacklist
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Logout error: {e}")
        return jsonify({
            'success': False,
            'message': 'Logout failed'
        }), 500


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        if user:
            return jsonify({
                'success': True,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
    
    except Exception as e:
        current_app.logger.error(f"Get profile error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get profile'
        }), 500


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Validate email if provided
        if 'email' in data and not validate_email(data['email']):
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400
        
        result = AuthService.update_user_profile(user_id, **data)
        
        if result['success']:
            # Log profile update
            AuditService.log_action(
                user_id=user_id,
                action='update_profile',
                details={'updated_fields': list(data.keys())}
            )
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        current_app.logger.error(f"Update profile error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to update profile'
        }), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'message': 'Current and new passwords are required'
            }), 400
        
        # Validate new password
        if not validate_password(data['new_password']):
            return jsonify({
                'success': False,
                'message': 'New password must be at least 8 characters long'
            }), 400
        
        result = AuthService.change_password(
            user_id, 
            data['current_password'], 
            data['new_password']
        )
        
        if result['success']:
            # Log password change
            AuditService.log_action(
                user_id=user_id,
                action='change_password'
            )
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        current_app.logger.error(f"Change password error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to change password'
        }), 500


