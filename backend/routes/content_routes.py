# backend/routes/content_routes.py
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import content_bp
from services.content_service import ContentService
from services.auth_service import AuthService
from models import db, ExtractionRule


@content_bp.route('/snippets', methods=['GET'])
@jwt_required()
def get_snippets():
    """Get snippets with filtering"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        # Get query parameters
        project_id = request.args.get('project_id', type=int)
        page_id = request.args.get('page_id', type=int)
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search')
        
        result = ContentService.get_snippets(
            project_id=project_id,
            page_id=page_id,
            status=status,
            user_id=user_id,
            user_role=user.role,
            page=page,
            per_page=min(per_page, 100),
            search=search
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        current_app.logger.error(f"Get snippets error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve snippets'
        }), 500


@content_bp.route('/snippets/<int:snippet_id>/approve', methods=['PUT'])
@jwt_required()
def approve_snippet(snippet_id):
    """Approve or reject snippet"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        status = data.get('status', 'approved') if data else 'approved'
        review_notes = data.get('review_notes') if data else None
        
        if status not in ['approved', 'rejected']:
            return jsonify({
                'success': False,
                'message': 'Invalid status. Must be approved or rejected'
            }), 400
        
        result = ContentService.update_snippet_status(
            snippet_id=snippet_id,
            status=status,
            user_id=user_id,
            review_notes=review_notes
        )
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        current_app.logger.error(f"Approve snippet error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to update snippet status'
        }), 500


@content_bp.route('/extract', methods=['POST'])
@jwt_required()
def extract_content():
    """Extract content from page"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('page_id'):
            return jsonify({
                'success': False,
                'message': 'Page ID is required'
            }), 400
        
        result = ContentService.extract_content_from_page(
            page_id=data['page_id'],
            rule_id=data.get('rule_id'),
            user_id=user_id
        )
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        current_app.logger.error(f"Extract content error: {e}")
        return jsonify({
            'success': False,
            'message': 'Content extraction failed'
        }), 500


@content_bp.route('/rules', methods=['GET'])
@jwt_required()
def get_extraction_rules():
    """Get extraction rules"""
    try:
        project_id = request.args.get('project_id', type=int)
        
        query = ExtractionRule.query
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        rules = query.order_by(ExtractionRule.priority.desc()).all()
        
        return jsonify({
            'success': True,
            'rules': [rule.to_dict() for rule in rules]
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Get extraction rules error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve extraction rules'
        }), 500


@content_bp.route('/rules', methods=['POST'])
@jwt_required()
def create_extraction_rule():
    """Create extraction rule"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not all(data.get(field) for field in ['project_id', 'name', 'rule_type', 'selector']):
            return jsonify({
                'success': False,
                'message': 'Project ID, name, rule type, and selector are required'
            }), 400
        
        rule = ExtractionRule(
            project_id=data['project_id'],
            name=data['name'],
            description=data.get('description'),
            rule_type=data['rule_type'],
            selector=data['selector'],
            attribute=data.get('attribute', 'text'),
            transform=data.get('transform'),
            required=data.get('required', False),
            multiple=data.get('multiple', False),
            priority=data.get('priority', 100)
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Extraction rule created successfully',
            'rule': rule.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create extraction rule error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to create extraction rule'
        }), 500


@content_bp.route('/search', methods=['GET'])
@jwt_required()
def search_content():
    """Search content"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        query = request.args.get('q')
        if not query:
            return jsonify({
                'success': False,
                'message': 'Search query is required'
            }), 400
        
        project_id = request.args.get('project_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        result = ContentService.search_content(
            query=query,
            project_id=project_id,
            user_id=user_id,
            user_role=user.role,
            page=page,
            per_page=min(per_page, 50)
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        current_app.logger.error(f"Search content error: {e}")
        return jsonify({
            'success': False,
            'message': 'Search failed'
        }), 500


@content_bp.route('/suggest-rules', methods=['POST'])
@jwt_required()
def suggest_extraction_rules():
    """Get AI suggestions for extraction rules"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('page_id') or not data.get('sample_content'):
            return jsonify({
                'success': False,
                'message': 'Page ID and sample content are required'
            }), 400
        
        result = ContentService.suggest_extraction_rules(
            page_id=data['page_id'],
            sample_content=data['sample_content'],
            user_id=user_id
        )
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        current_app.logger.error(f"Suggest extraction rules error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to suggest extraction rules'
        }), 500


