# backend/routes/project_routes.py
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import projects_bp
from services.project_service import ProjectService
from services.auth_service import AuthService
from utils.decorators import admin_required, project_access_required


@projects_bp.route('', methods=['GET'])
@jwt_required()
def get_projects():
    """Get projects with filtering and pagination"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search')
        status = request.args.get('status')
        industry = request.args.get('industry')
        
        # Limit per_page to prevent abuse
        per_page = min(per_page, 100)
        
        result = ProjectService.get_projects(
            user_id=user_id,
            user_role=user.role,
            page=page,
            per_page=per_page,
            search=search,
            status=status,
            industry=industry
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        current_app.logger.error(f"Get projects error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve projects'
        }), 500


@projects_bp.route('', methods=['POST'])
@jwt_required()
def create_project():
    """Create a new project"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Project name is required'
            }), 400
        
        result = ProjectService.create_project(
            user_id=user_id,
            name=data['name'],
            description=data.get('description'),
            tags=data.get('tags'),
            industry=data.get('industry'),
            priority=data.get('priority', 'medium')
        )
        
        return jsonify(result), 201 if result['success'] else 400
    
    except Exception as e:
        current_app.logger.error(f"Create project error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to create project'
        }), 500


@projects_bp.route('/<int:project_id>', methods=['GET'])
@jwt_required()
@project_access_required
def get_project(project_id):
    """Get project by ID"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        result = ProjectService.get_project_by_id(
            project_id=project_id,
            user_id=user_id,
            user_role=user.role
        )
        
        return jsonify(result), 200 if result['success'] else 404
    
    except Exception as e:
        current_app.logger.error(f"Get project error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve project'
        }), 500


@projects_bp.route('/<int:project_id>', methods=['PUT'])
@jwt_required()
@project_access_required
def update_project(project_id):
    """Update project"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        result = ProjectService.update_project(
            project_id=project_id,
            user_id=user_id,
            user_role=user.role,
            **data
        )
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        current_app.logger.error(f"Update project error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to update project'
        }), 500


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
@project_access_required
def delete_project(project_id):
    """Delete project"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        result = ProjectService.delete_project(
            project_id=project_id,
            user_id=user_id,
            user_role=user.role
        )
        
        return jsonify(result), 200 if result['success'] else 403
    
    except Exception as e:
        current_app.logger.error(f"Delete project error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to delete project'
        }), 500


@projects_bp.route('/<int:project_id>/collaborators', methods=['GET'])
@jwt_required()
@project_access_required
def get_project_collaborators(project_id):
    """Get project collaborators"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        result = ProjectService.get_project_collaborators(
            project_id=project_id,
            user_id=user_id,
            user_role=user.role
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        current_app.logger.error(f"Get collaborators error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve collaborators'
        }), 500


@projects_bp.route('/<int:project_id>/collaborators', methods=['POST'])
@jwt_required()
@project_access_required
def add_collaborator(project_id):
    """Add collaborator to project"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        data = request.get_json()
        
        if not data or not data.get('email'):
            return jsonify({
                'success': False,
                'message': 'Collaborator email is required'
            }), 400
        
        result = ProjectService.add_collaborator(
            project_id=project_id,
            user_id=user_id,
            collaborator_email=data['email'],
            role=data.get('role', 'viewer'),
            requester_role=user.role
        )
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        current_app.logger.error(f"Add collaborator error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to add collaborator'
        }), 500


@projects_bp.route('/<int:project_id>/statistics', methods=['GET'])
@jwt_required()
@project_access_required
def get_project_statistics(project_id):
    """Get project statistics"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        result = ProjectService.get_project_statistics(
            project_id=project_id,
            user_id=user_id,
            user_role=user.role
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        current_app.logger.error(f"Get project statistics error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve project statistics'
        }), 500


