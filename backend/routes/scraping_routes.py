# backend/routes/scraping_routes.py
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import scraping_bp
from services.scraping_service import ScrapingService
from services.auth_service import AuthService


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


@scraping_bp.route('/stop/<int:website_id>', methods=['POST'])
@jwt_required()
def stop_scraping(website_id):
    """Stop scraping for website"""
    try:
        user_id = get_jwt_identity()
        
        scraping_service = ScrapingService()
        result = scraping_service.stop_crawl(website_id, user_id)
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        current_app.logger.error(f"Stop scraping error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to stop scraping'
        }), 500


