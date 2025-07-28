# backend/routes/admin_routes.py
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from . import admin_bp
from services.auth_service import AuthService, AuditService
from models import db, User
from utils.decorators import admin_required


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    """Get all users"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search')
        
        query = User.query
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )
        
        pagination = query.paginate(
            page=page, per_page=min(per_page, 100), error_out=False
        )
        
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in pagination.items],
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Get users error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve users'
        }), 500


@admin_bp.route('/sql/execute', methods=['POST'])
@jwt_required()
@admin_required
def execute_sql():
    """Execute raw SQL query - FIXED VERSION"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('sql'):
            return jsonify({
                'success': False,
                'message': 'SQL query is required'
            }), 400
        
        sql_query = data['sql'].strip()
        
        if not sql_query:
            return jsonify({
                'success': False,
                'message': 'SQL query cannot be empty'
            }), 400
        
        # Basic validation - reject dangerous operations in certain contexts
        dangerous_patterns = ['drop database', 'format c:', 'rm -rf', 'del /']
        sql_lower = sql_query.lower()
        
        for pattern in dangerous_patterns:
            if pattern in sql_lower:
                return jsonify({
                    'success': False,
                    'message': 'Query contains potentially dangerous operations'
                }), 400
        
        try:
            # **FIX: Wrap SQL in text() for SQLAlchemy 2.0+ compatibility**
            result = db.session.execute(text(sql_query))
            
            # Handle different types of queries
            if sql_lower.startswith(('select', 'show', 'describe', 'explain')):
                # For SELECT queries, fetch results
                rows = result.fetchall()
                
                # Convert rows to dictionaries if they have column names
                if rows and hasattr(result, 'keys'):
                    columns = list(result.keys())
                    data_rows = [dict(zip(columns, row)) for row in rows]
                else:
                    data_rows = [list(row) for row in rows] if rows else []
                    columns = [f"column_{i}" for i in range(len(data_rows[0]))] if data_rows else []
                
                response_data = {
                    'success': True,
                    'query_type': 'SELECT',
                    'columns': columns,
                    'data': data_rows,
                    'row_count': len(data_rows),
                    'message': f'Query executed successfully. {len(data_rows)} rows returned.'
                }
            else:
                # For INSERT, UPDATE, DELETE, CREATE, etc.
                db.session.commit()
                rowcount = result.rowcount if hasattr(result, 'rowcount') else 0
                
                response_data = {
                    'success': True,
                    'query_type': 'MODIFY',
                    'message': f'Query executed successfully. {rowcount} rows affected.',
                    'rowcount': rowcount
                }
            
            # Log the SQL execution
            AuditService.log_action(
                user_id=user_id,
                action='execute_sql',
                details={
                    'query_type': 'SELECT' if sql_lower.startswith('select') else 'MODIFY',
                    'query_length': len(sql_query),
                    'success': True
                }
            )
            
            return jsonify(response_data), 200
            
        except Exception as sql_error:
            db.session.rollback()
            current_app.logger.error(f"SQL execution error: {sql_error}")
            
            # Log the failed execution
            AuditService.log_action(
                user_id=user_id,
                action='execute_sql',
                details={
                    'query_length': len(sql_query),
                    'success': False,
                    'error': str(sql_error)
                }
            )
            
            return jsonify({
                'success': False,
                'message': f'SQL execution failed: {str(sql_error)}',
                'error_type': type(sql_error).__name__
            }), 400
    
    except Exception as e:
        current_app.logger.error(f"Execute SQL error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to execute SQL query'
        }), 500


@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
@admin_required
def get_audit_logs():
    """Get audit logs"""
    try:
        user_id = request.args.get('user_id', type=int)
        action = request.args.get('action')
        resource_type = request.args.get('resource_type')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        result = AuditService.get_audit_logs(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            page=page,
            per_page=min(per_page, 200)
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        current_app.logger.error(f"Get audit logs error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve audit logs'
        }), 500


@admin_bp.route('/settings', methods=['GET'])
@jwt_required()
@admin_required
def get_settings():
    """Get system settings"""
    try:
        # Get Azure OpenAI service status
        from services.azure_openai_service import get_azure_openai_service
        ai_service = get_azure_openai_service()
        
        settings = {
            'azure_openai': ai_service.get_service_status(),
            'database': {
                'uri': current_app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('///', '').split('/')[-1],
                'echo': current_app.config.get('SQLALCHEMY_ECHO', False)
            },
            'app': {
                'name': current_app.config.get('APP_NAME'),
                'version': current_app.config.get('APP_VERSION'),
                'debug': current_app.config.get('DEBUG'),
                'flask_port': current_app.config.get('FLASK_PORT'),
                'react_port': current_app.config.get('REACT_PORT')
            }
        }
        
        return jsonify({
            'success': True,
            'settings': settings
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Get settings error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve settings'
        }), 500


@admin_bp.route('/system/status', methods=['GET'])
@jwt_required()
@admin_required
def get_system_status():
    """Get system status"""
    try:
        # Get database statistics
        stats_query = text("""
            SELECT 
                'users' as table_name, COUNT(*) as count FROM users
            UNION ALL
            SELECT 'projects', COUNT(*) FROM projects
            UNION ALL
            SELECT 'websites', COUNT(*) FROM websites
            UNION ALL
            SELECT 'pages', COUNT(*) FROM pages
            UNION ALL
            SELECT 'snippets', COUNT(*) FROM snippets
        """)
        
        stats_result = db.session.execute(stats_query).fetchall()
        table_stats = {row[0]: row[1] for row in stats_result}
        
        # Check recent activity
        recent_activity_query = text("""
            SELECT action, COUNT(*) as count 
            FROM audit_logs 
            WHERE created_at >= datetime('now', '-24 hours')
            GROUP BY action
            ORDER BY count DESC
            LIMIT 10
        """)
        
        activity_result = db.session.execute(recent_activity_query).fetchall()
        recent_activity = [{'action': row[0], 'count': row[1]} for row in activity_result]
        
        status = {
            'table_statistics': table_stats,
            'recent_activity_24h': recent_activity,
            'system_info': {
                'uptime': 'Not implemented',  # Would need process tracking
                'memory_usage': 'Not implemented',  # Would need psutil
                'cpu_usage': 'Not implemented'  # Would need psutil
            }
        }
        
        return jsonify({
            'success': True,
            'status': status
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Get system status error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve system status'
        }), 500