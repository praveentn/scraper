# backend/services/auth_service.py
from datetime import datetime, timedelta
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from models import db, User, AuditLog
import secrets
import string


class AuthService:
    """Authentication and authorization service"""
    
    @staticmethod
    def authenticate_user(email, password):
        """Authenticate user with email and password"""
        try:
            user = User.query.filter_by(email=email.lower().strip()).first()
            
            if not user:
                return {
                    'success': False,
                    'message': 'Invalid email or password',
                    'user': None,
                    'tokens': None
                }
            
            if not user.is_active:
                return {
                    'success': False,
                    'message': 'Account is deactivated',
                    'user': None,
                    'tokens': None
                }
            
            if not user.check_password(password):
                return {
                    'success': False,
                    'message': 'Invalid email or password',
                    'user': None,
                    'tokens': None
                }
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Generate tokens
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            
            return {
                'success': True,
                'message': 'Login successful',
                'user': user.to_dict(),
                'tokens': {
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Authentication error: {e}")
            return {
                'success': False,
                'message': 'Authentication failed',
                'user': None,
                'tokens': None
            }
    
    @staticmethod
    def register_user(email, password, first_name, last_name, role='user'):
        """Register a new user"""
        try:
            # Validate email uniqueness
            print(f"Validating email: {email}")
            existing_user = User.query.filter_by(email=email.lower().strip()).first()
            if existing_user:
                return {
                    'success': False,
                    'message': 'Email already registered',
                    'user': None
                }
            else:
                print(f"Registering new user: {email}")
            
            # Create user
            user = User(
                email=email.lower().strip(),
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                role=role,
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'User registered successfully',
                'user': user.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {e}")
            return {
                'success': False,
                'message': 'Registration failed',
                'user': None
            }
    
    @staticmethod
    def refresh_access_token(refresh_token):
        """Generate new access token from refresh token"""
        try:
            # Decode refresh token to get user ID
            token_data = decode_token(refresh_token)
            user_id = token_data['sub']
            
            # Verify user still exists and is active
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return {
                    'success': False,
                    'message': 'Invalid refresh token',
                    'token': None
                }
            
            # Generate new access token
            access_token = create_access_token(identity=user_id)
            
            return {
                'success': True,
                'message': 'Token refreshed successfully',
                'token': access_token
            }
            
        except Exception as e:
            current_app.logger.error(f"Token refresh error: {e}")
            return {
                'success': False,
                'message': 'Token refresh failed',
                'token': None
            }
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        try:
            user = User.query.get(user_id)
            if user and user.is_active:
                return user
            return None
        except Exception as e:
            current_app.logger.error(f"Get user error: {e}")
            return None
    
    @staticmethod
    def update_user_profile(user_id, **kwargs):
        """Update user profile"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            # Update allowed fields
            allowed_fields = ['first_name', 'last_name', 'email']
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    if field == 'email':
                        value = value.lower().strip()
                        # Check email uniqueness
                        existing = User.query.filter_by(email=value).filter(User.id != user_id).first()
                        if existing:
                            return {
                                'success': False,
                                'message': 'Email already in use'
                            }
                    setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Profile updated successfully',
                'user': user.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Update profile error: {e}")
            return {
                'success': False,
                'message': 'Profile update failed'
            }
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        """Change user password"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            # Verify current password
            if not user.check_password(current_password):
                return {
                    'success': False,
                    'message': 'Current password is incorrect'
                }
            
            # Update password
            user.set_password(new_password)
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Password changed successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Change password error: {e}")
            return {
                'success': False,
                'message': 'Password change failed'
            }
    
    @staticmethod
    def generate_password_reset_token(email):
        """Generate password reset token"""
        try:
            user = User.query.filter_by(email=email.lower().strip()).first()
            if not user:
                # Don't reveal if email exists for security
                return {
                    'success': True,
                    'message': 'If email exists, reset instructions were sent'
                }
            
            # Generate reset token (in real implementation, store this securely)
            reset_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
            
            # TODO: Store reset token in database with expiration
            # TODO: Send email with reset instructions
            
            return {
                'success': True,
                'message': 'Password reset instructions sent to email',
                'reset_token': reset_token  # Remove this in production
            }
            
        except Exception as e:
            current_app.logger.error(f"Password reset error: {e}")
            return {
                'success': False,
                'message': 'Password reset failed'
            }


class AuthorizationService:
    """Role-based authorization service"""
    
    @staticmethod
    def has_role(user, required_role):
        """Check if user has required role"""
        role_hierarchy = {
            'admin': 3,
            'user': 1
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    @staticmethod
    def can_access_project(user, project):
        """Check if user can access project"""
        if user.role == 'admin':
            return True
        
        if project.owner_id == user.id:
            return True
        
        # Check if user is a collaborator
        role = project.get_collaborator_role(user.id)
        return role is not None
    
    @staticmethod
    def can_edit_project(user, project):
        """Check if user can edit project"""
        if user.role == 'admin':
            return True
        
        if project.owner_id == user.id:
            return True
        
        # Check if user is a collaborator with edit permissions
        role = project.get_collaborator_role(user.id)
        return role in ['owner', 'collaborator']
    
    @staticmethod
    def can_delete_project(user, project):
        """Check if user can delete project"""
        if user.role == 'admin':
            return True
        
        return project.owner_id == user.id


class AuditService:
    """Audit logging service"""
    
    @staticmethod
    def log_action(user_id, action, resource_type=None, resource_id=None, 
                   details=None, ip_address=None, user_agent=None):
        """Log user action for audit purposes"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if details:
                audit_log.set_details(details)
            
            db.session.add(audit_log)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Audit logging error: {e}")
            # Don't fail the main operation if audit logging fails
            db.session.rollback()
    
    @staticmethod
    def get_audit_logs(user_id=None, action=None, resource_type=None, 
                       start_date=None, end_date=None, page=1, per_page=50):
        """Get audit logs with filtering"""
        try:
            query = AuditLog.query
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if action:
                query = query.filter(AuditLog.action == action)
            
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            
            # Order by most recent first
            query = query.order_by(AuditLog.created_at.desc())
            
            # Paginate
            pagination = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'success': True,
                'logs': [log.to_dict() for log in pagination.items],
                'pagination': {
                    'page': pagination.page,
                    'pages': pagination.pages,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Get audit logs error: {e}")
            return {
                'success': False,
                'message': 'Failed to retrieve audit logs',
                'logs': [],
                'pagination': None
            }