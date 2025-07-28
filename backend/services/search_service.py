# backend/services/search_service.py
import sys
import os

# Add the search_engine module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from search_engine import WebSearchEngine
except ImportError:
    # Fallback if search_engine is not available
    WebSearchEngine = None

from flask import current_app
from models import db, Page, Website, Project
from services.auth_service import AuditService


class SearchService:
    """Advanced search service for content discovery"""
    
    def __init__(self):
        self.web_search_engine = None
        if WebSearchEngine:
            try:
                self.web_search_engine = WebSearchEngine()
            except Exception as e:
                current_app.logger.warning(f"Failed to initialize web search engine: {e}")
    
    def search_web(self, query, search_type="general", max_results=10, user_id=None):
        """Search the web using integrated search engine"""
        try:
            if not self.web_search_engine:
                return {
                    'success': False,
                    'message': 'Web search engine not available',
                    'results': []
                }
            
            # Perform comprehensive search
            results = self.web_search_engine.comprehensive_search(
                query=query,
                search_type=search_type,
                max_results=max_results
            )
            
            # Log audit event
            if user_id:
                AuditService.log_action(
                    user_id=user_id,
                    action='web_search',
                    details={
                        'query': query,
                        'search_type': search_type,
                        'results_count': len(results)
                    }
                )
            
            return {
                'success': True,
                'results': results,
                'query': query,
                'search_type': search_type
            }
            
        except Exception as e:
            current_app.logger.error(f"Web search error: {e}")
            return {
                'success': False,
                'message': 'Web search failed',
                'results': []
            }
    
    def search_internal_content(self, query, filters=None, user_id=None, user_role='user'):
        """Search internal scraped content"""
        try:
            from services.content_service import ContentService
            
            # Extract filters
            project_id = filters.get('project_id') if filters else None
            status = filters.get('status') if filters else None
            page = filters.get('page', 1) if filters else 1
            per_page = filters.get('per_page', 20) if filters else 20
            
            # Use content service for internal search
            result = ContentService.search_content(
                query=query,
                project_id=project_id,
                user_id=user_id,
                user_role=user_role,
                page=page,
                per_page=per_page
            )
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Internal search error: {e}")
            return {
                'success': False,
                'message': 'Internal search failed',
                'results': [],
                'pagination': None
            }
    
    def get_search_suggestions(self, partial_query, user_id=None):
        """Get search suggestions based on partial query"""
        try:
            # Simple implementation - can be enhanced with ML/AI
            suggestions = []
            
            if len(partial_query) >= 2:
                # Search in page titles
                pages = Page.query.filter(
                    Page.title.ilike(f"%{partial_query}%")
                ).limit(5).all()
                
                for page in pages:
                    suggestions.append({
                        'type': 'page_title',
                        'text': page.title,
                        'url': page.url,
                        'project': page.website.project.name
                    })
                
                # Search in project names
                projects = Project.query.filter(
                    Project.name.ilike(f"%{partial_query}%")
                ).limit(3).all()
                
                for project in projects:
                    suggestions.append({
                        'type': 'project',
                        'text': project.name,
                        'description': project.description
                    })
            
            return {
                'success': True,
                'suggestions': suggestions
            }
            
        except Exception as e:
            current_app.logger.error(f"Search suggestions error: {e}")
            return {
                'success': False,
                'suggestions': []
            }
    
    def close(self):
        """Clean up search engine resources"""
        if self.web_search_engine:
            try:
                self.web_search_engine.close()
            except Exception as e:
                current_app.logger.debug(f"Error closing search engine: {e}")


