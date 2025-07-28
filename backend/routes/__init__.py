# backend/routes/__init__.py
from flask import Blueprint

# Create blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')
websites_bp = Blueprint('websites', __name__, url_prefix='/api/websites')
scraping_bp = Blueprint('scraping', __name__, url_prefix='/api/scraping')
content_bp = Blueprint('content', __name__, url_prefix='/api/content')
reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Import route handlers
from . import auth_routes, project_routes, website_routes, scraping_routes, content_routes, report_routes, admin_routes

def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(websites_bp)
    app.register_blueprint(scraping_bp)
    app.register_blueprint(content_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)


