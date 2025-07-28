# backend/routes/website_routes.py
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import websites_bp
from services.auth_service import AuthService
from models import db, Website, Project
from utils.decorators import project_access_required
from utils.validators import validate_url


@websites_bp.route('', methods=['POST'])
@jwt_required()
def create_website():
    """Create a new website"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('project_id') or not data.get('url'):
            return jsonify({
                'success': False,
                'message': 'Project ID and URL are required'
            }), 400
        
        # Validate URL
        if not validate_url(data['url']):
            return jsonify({
                'success': False,
                'message': 'Invalid URL format'
            }), 400
        
        # Check project access
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({
                'success': False,
                'message': 'Project not found'
            }), 404
        
        # Create website
        website = Website(
            project_id=data['project_id'],
            url=data['url'].strip(),
            name=data.get('name', '').strip(),
            description=data.get('description', '').strip(),
            crawl_depth=data.get('crawl_depth', 1),
            follow_external_links=data.get('follow_external_links', False),
            respect_robots_txt=data.get('respect_robots_txt', True),
            rate_limit_delay=float(data.get('rate_limit_delay', 1.0)),
            auth_type=data.get('auth_type', 'none')
        )
        
        # Set auth config if provided
        if data.get('auth_config'):
            website.set_auth_config(data['auth_config'])
        
        db.session.add(website)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Website created successfully',
            'website': website.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create website error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to create website'
        }), 500


@websites_bp.route('/<int:website_id>', methods=['GET'])
@jwt_required()
def get_website(website_id):
    """Get website by ID"""
    try:
        website = Website.query.get(website_id)
        if not website:
            return jsonify({
                'success': False,
                'message': 'Website not found'
            }), 404
        
        return jsonify({
            'success': True,
            'website': website.to_dict(include_stats=True)
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Get website error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve website'
        }), 500


@websites_bp.route('/<int:website_id>', methods=['PUT'])
@jwt_required()
def update_website(website_id):
    """Update website"""
    try:
        website = Website.query.get(website_id)
        if not website:
            return jsonify({
                'success': False,
                'message': 'Website not found'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Update allowed fields
        allowed_fields = ['name', 'description', 'crawl_depth', 'follow_external_links', 
                         'respect_robots_txt', 'rate_limit_delay', 'auth_type', 'status']
        
        for field in allowed_fields:
            if field in data:
                if field == 'rate_limit_delay':
                    setattr(website, field, float(data[field]))
                else:
                    setattr(website, field, data[field])
        
        # Update auth config if provided
        if 'auth_config' in data:
            website.set_auth_config(data['auth_config'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Website updated successfully',
            'website': website.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update website error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to update website'
        }), 500


@websites_bp.route('/<int:website_id>', methods=['DELETE'])
@jwt_required()
def delete_website(website_id):
    """Delete website"""
    try:
        website = Website.query.get(website_id)
        if not website:
            return jsonify({
                'success': False,
                'message': 'Website not found'
            }), 404
        
        db.session.delete(website)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Website deleted successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete website error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to delete website'
        }), 500


