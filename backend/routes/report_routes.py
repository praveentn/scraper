# backend/routes/report_routes.py
from flask import request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import reports_bp
from services.export_service import ExportService
from services.auth_service import AuthService


@reports_bp.route('/export', methods=['POST'])
@jwt_required()
def create_export():
    """Create export job"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('export_type'):
            return jsonify({
                'success': False,
                'message': 'Export type is required'
            }), 400
        
        if data['export_type'] not in ['csv', 'excel', 'pdf', 'json']:
            return jsonify({
                'success': False,
                'message': 'Invalid export type'
            }), 400
        
        result = ExportService.create_export(
            user_id=user_id,
            export_type=data['export_type'],
            filters=data.get('filters'),
            filename=data.get('filename')
        )
        
        return jsonify(result), 201 if result['success'] else 400
    
    except Exception as e:
        current_app.logger.error(f"Create export error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to create export'
        }), 500


@reports_bp.route('/exports', methods=['GET'])
@jwt_required()
def get_exports():
    """Get user's exports"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        result = ExportService.get_user_exports(
            user_id=user_id,
            user_role=user.role,
            page=page,
            per_page=min(per_page, 100)
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        current_app.logger.error(f"Get exports error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve exports'
        }), 500


@reports_bp.route('/exports/<int:export_id>', methods=['GET'])
@jwt_required()
def get_export_status(export_id):
    """Get export status"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        result = ExportService.get_export_status(
            export_id=export_id,
            user_id=user_id,
            user_role=user.role
        )
        
        return jsonify(result), 200 if result['success'] else 404
    
    except Exception as e:
        current_app.logger.error(f"Get export status error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get export status'
        }), 500


@reports_bp.route('/downloads/<int:export_id>', methods=['GET'])
@jwt_required()
def download_export(export_id):
    """Download export file"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        result = ExportService.download_export(
            export_id=export_id,
            user_id=user_id,
            user_role=user.role
        )
        
        if result['success']:
            return send_file(
                result['file_path'],
                as_attachment=True,
                download_name=result['filename']
            )
        else:
            return jsonify(result), 400
    
    except Exception as e:
        current_app.logger.error(f"Download export error: {e}")
        return jsonify({
            'success': False,
            'message': 'Download failed'
        }), 500


