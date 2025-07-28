# backend/utils/decorators.py
from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from services.auth_service import AuthService, AuthorizationService
from models import Project


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = get_jwt_identity()
            current_app.logger.debug(f"Admin check - User ID from token: {user_id}")
            
            if not user_id:
                current_app.logger.warning("Admin check failed - No user ID in token")
                return jsonify({
                    'success': False,
                    'message': 'Authorization token required'
                }), 401
            
            user = AuthService.get_user_by_id(user_id)
            current_app.logger.debug(f"Admin check - User found: {user.email if user else 'None'}, Role: {user.role if user else 'None'}")
            
            if not user:
                current_app.logger.warning(f"Admin check failed - User not found for ID: {user_id}")
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            if not user.is_active:
                current_app.logger.warning(f"Admin check failed - User not active: {user.email}")
                return jsonify({
                    'success': False,
                    'message': 'Account is deactivated'
                }), 403
            
            if user.role != 'admin':
                current_app.logger.warning(f"Admin check failed - User {user.email} has role '{user.role}', expected 'admin'")
                return jsonify({
                    'success': False,
                    'message': 'Admin access required'
                }), 403
            
            current_app.logger.debug(f"Admin check passed for user: {user.email}")
            return f(*args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f"Admin check error: {e}")
            return jsonify({
                'success': False,
                'message': 'Authorization failed'
            }), 500
    
    return decorated_function


def project_access_required(f):
    """Decorator to check project access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = get_jwt_identity()
            user = AuthService.get_user_by_id(user_id)
            project_id = kwargs.get('project_id')
            
            if not user or not project_id:
                return jsonify({
                    'success': False,
                    'message': 'Invalid request'
                }), 400
            
            project = Project.query.get(project_id)
            if not project:
                return jsonify({
                    'success': False,
                    'message': 'Project not found'
                }), 404
            
            if not AuthorizationService.can_access_project(user, project):
                return jsonify({
                    'success': False,
                    'message': 'Access denied'
                }), 403
            
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Project access check error: {e}")
            return jsonify({
                'success': False,
                'message': 'Authorization failed'
            }), 500
    
    return decorated_function