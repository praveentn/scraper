# backend/routes/scraping_routes.py
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import scraping_bp
from services.auth_service import AuthService
from models import db, Website, Page, Project, ScheduledJob
from services.scraping_service import ScrapingService


@scraping_bp.route('/stop/<int:website_id>', methods=['POST'])
@jwt_required()
def stop_scraping(website_id):
    """Stop scraping for a website - MISSING ENDPOINT"""
    try:
        user_id = get_jwt_identity()
        
        # Find the website
        website = Website.query.get(website_id)
        if not website:
            return jsonify({
                'success': False,
                'message': 'Website not found'
            }), 404
        
        # Use scraping service to stop
        result = ScrapingService.stop_scraping(website_id)
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        current_app.logger.error(f"Stop scraping error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to stop scraping'
        }), 500


@scraping_bp.route('/run', methods=['POST'])
@jwt_required()
def run_scraping():
    """Run scraping for a website"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('website_id'):
            return jsonify({
                'success': False,
                'message': 'Website ID is required'
            }), 400
        
        scraping_service = ScrapingService()
        
        # Check if single page or full crawl
        if data.get('single_page'):
            url = data.get('url')
            if not url:
                return jsonify({
                    'success': False,
                    'message': 'URL is required for single page scraping'
                }), 400
            
            result = scraping_service.scrape_single_page(
                website_id=data['website_id'],
                url=url,
                use_selenium=data.get('use_selenium', False)
            )
        else:
            result = scraping_service.crawl_website(
                website_id=data['website_id'],
                user_id=user_id,
                max_pages=data.get('max_pages'),
                use_selenium=data.get('use_selenium', False)
            )
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        current_app.logger.error(f"Run scraping error: {e}")
        return jsonify({
            'success': False,
            'message': 'Scraping failed'
        }), 500


@scraping_bp.route('/status/<int:website_id>', methods=['GET'])
@jwt_required()
def get_scraping_status(website_id):
    """Get scraping status for website"""
    try:
        scraping_service = ScrapingService()
        result = scraping_service.get_crawl_status(website_id)
        
        return jsonify(result), 200
    
    except Exception as e:
        current_app.logger.error(f"Get scraping status error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get scraping status'
        }), 500


@scraping_bp.route('/schedule', methods=['POST'])
@jwt_required()
def schedule_scraping():
    """Schedule scraping job"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('website_id'):
            return jsonify({
                'success': False,
                'message': 'Website ID is required'
            }), 400
        
        scraping_service = ScrapingService()
        result = scraping_service.schedule_crawl(
            website_id=data['website_id'],
            user_id=user_id,
            schedule_type=data.get('schedule_type', 'once'),
            schedule_config=data.get('schedule_config')
        )
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        current_app.logger.error(f"Schedule scraping error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to schedule scraping'
        }), 500

@scraping_bp.route('/jobs', methods=['GET'])
@jwt_required()
def get_scraping_jobs():
    """Get all scraping jobs with status - FIXED VERSION"""
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        project_id = request.args.get('project_id', type=int)
        
        # For now, return basic website info with mock status
        # In a real implementation, you'd have a separate JobStatus model
        query = Website.query
        
        # Filter by project if specified
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        # Order by most recent first
        query = query.order_by(Website.updated_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=min(per_page, 100), error_out=False
        )
        
        # Format results with basic info
        jobs_data = []
        for website in pagination.items:
            project = Project.query.get(website.project_id)
            
            job_dict = {
                'id': website.id,
                'website_id': website.id,
                'website_name': website.name or 'Unnamed Website',
                'website_url': website.url,
                'project_name': project.name if project else 'Unknown',
                'status': website.status or 'inactive',
                'pages_scraped': len(website.pages),
                'total_pages_found': website.total_pages or 0,
                'started_at': website.last_crawled.isoformat() if website.last_crawled else None,
                'progress_percentage': 0.0  # Placeholder
            }
            jobs_data.append(job_dict)
        
        return jsonify({
            'success': True,
            'jobs': jobs_data,
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
        current_app.logger.error(f"Get scraping jobs error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve scraping jobs'
        }), 500


@scraping_bp.route('/status', methods=['GET'])
@jwt_required()  
def get_all_scraping_status():
    """Get scraping status for all active jobs - FIXED VERSION"""
    try:
        user_id = get_jwt_identity()
        
        # Get active websites (representing active scraping jobs)
        active_websites = Website.query.filter(
            Website.status.in_(['active'])
        ).order_by(Website.updated_at.desc()).limit(50).all()
        
        status_data = []
        for website in active_websites:
            project = Project.query.get(website.project_id)
            
            status_dict = {
                'job_id': website.id,
                'website_id': website.id,
                'website_name': website.name or 'Unnamed Website',
                'website_url': website.url,
                'project_name': project.name if project else 'Unknown',
                'status': website.status or 'inactive',
                'pages_scraped': len(website.pages),
                'total_pages': website.total_pages or 0,
                'started_at': website.last_crawled.isoformat() if website.last_crawled else None,
                'last_activity': website.updated_at.isoformat() if website.updated_at else None,
                'progress_percentage': 0.0  # Placeholder - calculate based on actual logic
            }
            status_data.append(status_dict)
        
        return jsonify({
            'success': True,
            'active_jobs': status_data,
            'total_active': len(status_data)
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Get all scraping status error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve scraping status'
        }), 500
