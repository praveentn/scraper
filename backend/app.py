# backend/app.py
import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config, init_directories, validate_azure_openai_config
from models import init_db
from routes import register_blueprints
from services.azure_openai_service import get_azure_openai_service


def create_app(config_name=None):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize directories
    init_directories()
    
    # Initialize database
    db = init_db(app)
    
    # Initialize CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Initialize rate limiter
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[app.config['RATELIMIT_DEFAULT']],
        storage_uri=app.config['RATELIMIT_STORAGE_URL']
    )
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Token has expired'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'success': False,
            'message': 'Authorization token is required'
        }), 401
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Endpoint not found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'message': 'Method not allowed'
        }), 405
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            'success': False,
            'message': 'Rate limit exceeded',
            'retry_after': str(e.retry_after)
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        try:
            from sqlalchemy import text
            # Check database connection
            with app.app_context():
                db.session.execute(text('SELECT 1'))
            
            # Check Azure OpenAI service
            ai_service = get_azure_openai_service()
            ai_status = ai_service.get_service_status()
            
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'azure_openai': 'available' if ai_status['available'] else 'unavailable',
                'version': app.config.get('APP_VERSION', '1.0.0')
            }), 200
            
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 503
    
    # API info endpoint
    @app.route('/api/info')
    def api_info():
        return jsonify({
            'name': app.config.get('APP_NAME', 'Blitz'),
            'version': app.config.get('APP_VERSION', '1.0.0'),
            'environment': os.environ.get('FLASK_ENV', 'development'),
            'endpoints': {
                'auth': '/api/auth/*',
                'projects': '/api/projects/*',
                'websites': '/api/websites/*',
                'scraping': '/api/scraping/*',
                'content': '/api/content/*',
                'reports': '/api/reports/*',
                'admin': '/api/admin/*'
            }
        }), 200
    
    # Debug endpoint for email validation
    @app.route('/api/debug/validate-email', methods=['POST'])
    def debug_validate_email():
        if not app.config.get('DEBUG'):
            return jsonify({'error': 'Debug endpoint not available'}), 404
        
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'Email required'}), 400
        
        from utils.validators import validate_email
        email = data['email']
        is_valid = validate_email(email)
        
        return jsonify({
            'email': email,
            'valid': is_valid,
            'message': 'Valid email format' if is_valid else 'Invalid email format'
        }), 200
    
    # Register blueprints
    register_blueprints(app)
    
    # Log startup information
    with app.app_context():
        app.logger.info(f"🚀 {app.config.get('APP_NAME')} starting up...")
        app.logger.info(f"   Environment: {os.environ.get('FLASK_ENV', 'development')}")
        app.logger.info(f"   Debug mode: {app.config.get('DEBUG', False)}")
        app.logger.info(f"   Port: {app.config.get('FLASK_PORT', 5232)}")
        
        # Validate Azure OpenAI configuration
        validation = validate_azure_openai_config(app.config)
        if validation['valid']:
            app.logger.info("   ✅ Azure OpenAI: Configured")
        else:
            app.logger.warning(f"   ⚠️  Azure OpenAI: Missing fields {validation['missing_fields']}")
    
    return app


def run_app():
    """Run the Flask application"""
    app = create_app()
    
    host = app.config.get('FLASK_HOST', '0.0.0.0')
    port = app.config.get('FLASK_PORT', 5232)
    debug = app.config.get('DEBUG', False)
    
    print(f"\n🌟 Starting Blitz Web Scraping Platform...")
    print(f"   📍 Server: http://{host}:{port}")
    print(f"   🔧 Debug: {debug}")
    print(f"   📚 API Docs: http://{host}:{port}/api/info")
    print(f"   ❤️  Health: http://{host}:{port}/health")
    print(f"   🎯 Frontend: http://localhost:{app.config.get('REACT_PORT', 3232)}")
    print()
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == '__main__':
    run_app()