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
    """Execute raw SQL query"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('sql'):
            return jsonify({
                'success': False,
                'message': 'SQL query is required'
            }), 400
        
        sql_query = data['sql'].strip()
        page = data.get('page', 1)
        per_page = min(data.get('per_page', 100), 1000)  # Max 1000 rows per page
        
        # Basic SQL injection protection
        dangerous_keywords = ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update']
        sql_lower = sql_query.lower()
        
        # Allow only SELECT statements and basic commands for safety
        if not sql_lower.startswith('select') and not sql_lower.startswith('with'):
            # Check if it's a potentially dangerous operation
            if any(keyword in sql_lower for keyword in dangerous_keywords):
                # Allow if explicitly confirmed
                if not data.get('confirm_dangerous', False):
                    return jsonify({
                        'success': False,
                        'message': 'This appears to be a potentially dangerous operation. Set confirm_dangerous=true if you want to proceed.',
                        'requires_confirmation': True
                    }), 400
        
        try:
            # For SELECT queries, add pagination
            if sql_lower.startswith('select'):
                # Count total rows first
                count_query = f"SELECT COUNT(*) as total FROM ({sql_query}) as subquery"
                count_result = db.session.execute(text(count_query))
                total_rows = count_result.scalar()
                
                # Add pagination to original query
                offset = (page - 1) * per_page
                paginated_query = f"{sql_query} LIMIT {per_page} OFFSET {offset}"
                
                result = db.session.execute(text(paginated_query))
                rows = result.fetchall()
                
                # Get column names
                columns = list(result.keys()) if hasattr(result, 'keys') else []
                
                # Convert rows to dictionaries
                data_rows = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i] if i < len(row) else None
                    data_rows.append(row_dict)
                
                response_data = {
                    'success': True,
                    'columns': columns,
                    'rows': data_rows,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total_rows,
                        'pages': (total_rows + per_page - 1) // per_page if total_rows > 0 else 0,
                        'has_next': page * per_page < total_rows,
                        'has_prev': page > 1
                    }
                }
            else:
                # For non-SELECT queries
                result = db.session.execute(text(sql_query))
                db.session.commit()
                
                # Get affected rows count if available
                rowcount = getattr(result, 'rowcount', 0)
                
                response_data = {
                    'success': True,
                    'message': f'Query executed successfully. {rowcount} rows affected.',
                    'rowcount': rowcount
                }
            
            # Log the SQL execution
            AuditService.log_action(
                user_id=user_id,
                action='execute_sql',
                details={
                    'query_type': 'SELECT' if sql_lower.startswith('select') else 'MODIFY',
                    'query_length': len(sql_query)
                }
            )
            
            return jsonify(response_data), 200
            
        except Exception as sql_error:
            db.session.rollback()
            current_app.logger.error(f"SQL execution error: {sql_error}")
            
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