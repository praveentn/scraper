# backend/services/content_service.py
import re
from datetime import datetime
from flask import current_app
from bs4 import BeautifulSoup
from lxml import html, etree
from models import db, Page, Snippet, ExtractionRule, Website, Project
from services.auth_service import AuthorizationService, AuditService
from services.azure_openai_service import get_azure_openai_service
from sqlalchemy import text, desc, func


class ContentService:
    """Content extraction and management service"""
    
    @staticmethod
    def extract_content_from_page(page_id, rule_id=None, user_id=None):
        """Extract content from page using extraction rules"""
        try:
            page = Page.query.get(page_id)
            if not page:
                return {
                    'success': False,
                    'message': 'Page not found',
                    'snippets': []
                }
            
            # Get extraction rules
            if rule_id:
                rules = [ExtractionRule.query.get(rule_id)]
                if not rules[0]:
                    return {
                        'success': False,
                        'message': 'Extraction rule not found',
                        'snippets': []
                    }
            else:
                rules = ExtractionRule.query.filter_by(
                    project_id=page.website.project_id,
                    is_active=True
                ).order_by(ExtractionRule.priority.desc()).all()
            
            if not rules:
                return {
                    'success': False,
                    'message': 'No active extraction rules found',
                    'snippets': []
                }
            
            extracted_snippets = []
            
            for rule in rules:
                snippets = ContentService._apply_extraction_rule(page, rule)
                extracted_snippets.extend(snippets)
            
            # Save snippets to database
            saved_snippets = []
            for snippet_data in extracted_snippets:
                snippet = Snippet(
                    page_id=page_id,
                    extraction_rule_id=snippet_data['rule_id'],
                    content=snippet_data['content'],
                    context=snippet_data['context'],
                    xpath=snippet_data['xpath'],
                    position=snippet_data['position'],
                    confidence_score=snippet_data['confidence_score'],
                    status='pending'
                )
                
                db.session.add(snippet)
                saved_snippets.append(snippet)
            
            db.session.commit()
            
            # Log audit event
            if user_id:
                AuditService.log_action(
                    user_id=user_id,
                    action='extract_content',
                    resource_type='page',
                    resource_id=page_id,
                    details={'snippets_extracted': len(saved_snippets)}
                )
            
            return {
                'success': True,
                'message': f'Extracted {len(saved_snippets)} snippets',
                'snippets': [s.to_dict() for s in saved_snippets]
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Content extraction error: {e}")
            return {
                'success': False,
                'message': 'Content extraction failed',
                'snippets': []
            }
    
    @staticmethod
    def _apply_extraction_rule(page, rule):
        """Apply single extraction rule to page"""
        snippets = []
        
        try:
            if not page.raw_html:
                return snippets
            
            if rule.rule_type == 'css':
                snippets = ContentService._extract_with_css(page, rule)
            elif rule.rule_type == 'xpath':
                snippets = ContentService._extract_with_xpath(page, rule)
            elif rule.rule_type == 'regex':
                snippets = ContentService._extract_with_regex(page, rule)
            
        except Exception as e:
            current_app.logger.error(f"Rule application error for rule {rule.id}: {e}")
        
        return snippets
    
    @staticmethod
    def _extract_with_css(page, rule):
        """Extract content using CSS selector"""
        snippets = []
        
        try:
            soup = BeautifulSoup(page.raw_html, 'html.parser')
            elements = soup.select(rule.selector)
            
            for idx, element in enumerate(elements):
                # Get content based on attribute
                if rule.attribute == 'text':
                    content = element.get_text(strip=True)
                elif rule.attribute == 'html':
                    content = str(element)
                else:
                    content = element.get(rule.attribute, '')
                
                if not content:
                    continue
                
                # Apply transformations
                content = ContentService._apply_transformations(content, rule.transform)
                
                # Get context (parent element)
                context = str(element.parent) if element.parent else str(element)
                if len(context) > 500:
                    context = context[:500] + "..."
                
                # Calculate confidence score
                confidence = ContentService._calculate_confidence_score(content, rule)
                
                snippet_data = {
                    'rule_id': rule.id,
                    'content': content,
                    'context': context,
                    'xpath': ContentService._get_element_xpath(element),
                    'position': idx,
                    'confidence_score': confidence
                }
                
                snippets.append(snippet_data)
                
                if not rule.multiple:
                    break
            
        except Exception as e:
            current_app.logger.error(f"CSS extraction error: {e}")
        
        return snippets
    
    @staticmethod
    def _extract_with_xpath(page, rule):
        """Extract content using XPath expression"""
        snippets = []
        
        try:
            tree = html.fromstring(page.raw_html)
            elements = tree.xpath(rule.selector)
            
            for idx, element in enumerate(elements):
                # Get content based on attribute
                if rule.attribute == 'text':
                    content = element.text_content().strip()
                elif rule.attribute == 'html':
                    content = etree.tostring(element, encoding='unicode')
                else:
                    content = element.get(rule.attribute, '')
                
                if not content:
                    continue
                
                # Apply transformations
                content = ContentService._apply_transformations(content, rule.transform)
                
                # Get context
                parent = element.getparent()
                context = etree.tostring(parent, encoding='unicode') if parent is not None else etree.tostring(element, encoding='unicode')
                if len(context) > 500:
                    context = context[:500] + "..."
                
                # Calculate confidence score
                confidence = ContentService._calculate_confidence_score(content, rule)
                
                snippet_data = {
                    'rule_id': rule.id,
                    'content': content,
                    'context': context,
                    'xpath': tree.getpath(element),
                    'position': idx,
                    'confidence_score': confidence
                }
                
                snippets.append(snippet_data)
                
                if not rule.multiple:
                    break
            
        except Exception as e:
            current_app.logger.error(f"XPath extraction error: {e}")
        
        return snippets
    
    @staticmethod
    def _extract_with_regex(page, rule):
        """Extract content using regular expression"""
        snippets = []
        
        try:
            content_source = page.extracted_text if rule.attribute == 'text' else page.raw_html
            
            if not content_source:
                return snippets
            
            pattern = re.compile(rule.selector, re.IGNORECASE | re.DOTALL)
            matches = pattern.finditer(content_source)
            
            for idx, match in enumerate(matches):
                content = match.group(0)
                
                if not content:
                    continue
                
                # Apply transformations
                content = ContentService._apply_transformations(content, rule.transform)
                
                # Get context around match
                start = max(0, match.start() - 100)
                end = min(len(content_source), match.end() + 100)
                context = content_source[start:end]
                
                # Calculate confidence score
                confidence = ContentService._calculate_confidence_score(content, rule)
                
                snippet_data = {
                    'rule_id': rule.id,
                    'content': content,
                    'context': context,
                    'xpath': f"regex_match_{idx}",
                    'position': idx,
                    'confidence_score': confidence
                }
                
                snippets.append(snippet_data)
                
                if not rule.multiple:
                    break
            
        except Exception as e:
            current_app.logger.error(f"Regex extraction error: {e}")
        
        return snippets
    
    @staticmethod
    def _apply_transformations(content, transform_type):
        """Apply content transformations"""
        if not transform_type or not content:
            return content
        
        try:
            if transform_type == 'clean':
                # Remove extra whitespace
                content = re.sub(r'\s+', ' ', content.strip())
            elif transform_type == 'lowercase':
                content = content.lower()
            elif transform_type == 'uppercase':
                content = content.upper()
            elif transform_type == 'strip':
                content = content.strip()
            elif transform_type == 'strip_html':
                soup = BeautifulSoup(content, 'html.parser')
                content = soup.get_text()
            
        except Exception as e:
            current_app.logger.debug(f"Transformation error: {e}")
        
        return content
    
    @staticmethod
    def _calculate_confidence_score(content, rule):
        """Calculate confidence score for extracted content"""
        score = 0.5  # Base score
        
        try:
            # Length-based scoring
            if 10 <= len(content) <= 500:
                score += 0.2
            elif len(content) > 500:
                score += 0.1
            
            # Rule requirement scoring
            if rule.required and content:
                score += 0.2
            
            # Content quality scoring
            if content and not content.isspace():
                score += 0.1
            
            # Specific content patterns
            if rule.rule_type == 'css' and rule.selector in ['h1', 'h2', 'h3', 'title']:
                score += 0.1
            
        except Exception:
            pass
        
        return round(min(1.0, score), 3)
    
    @staticmethod
    def _get_element_xpath(element):
        """Get XPath for BeautifulSoup element (simplified)"""
        try:
            path_parts = []
            current = element
            
            while current and current.name:
                siblings = current.parent.find_all(current.name) if current.parent else [current]
                index = siblings.index(current) + 1 if len(siblings) > 1 else 1
                path_parts.append(f"{current.name}[{index}]")
                current = current.parent
            
            return '/' + '/'.join(reversed(path_parts))
        except Exception:
            return 'unknown'
    
    @staticmethod
    def get_snippets(project_id=None, page_id=None, status=None, user_id=None, user_role='user', 
                     page=1, per_page=50, search=None):
        """Get snippets with filtering and pagination"""
        try:
            query = Snippet.query.join(Page).join(Website)
            
            # Apply filters
            if project_id:
                query = query.filter(Website.project_id == project_id)
            
            if page_id:
                query = query.filter(Snippet.page_id == page_id)
            
            if status:
                query = query.filter(Snippet.status == status)
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(Snippet.content.ilike(search_term))
            
            # Permission check for non-admin users
            if user_role != 'admin' and user_id:
                from models import User, Project
                query = query.join(Project).filter(
                    db.or_(
                        Project.owner_id == user_id,
                        Project.collaborators.any(User.id == user_id)
                    )
                )
            
            # Order by most recent first
            query = query.order_by(desc(Snippet.created_at))
            
            # Paginate
            pagination = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'success': True,
                'snippets': [snippet.to_dict() for snippet in pagination.items],
                'pagination': {
                    'page': pagination.page,
                    'pages': pagination.pages,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Get snippets error: {e}")
            return {
                'success': False,
                'message': 'Failed to retrieve snippets',
                'snippets': [],
                'pagination': None
            }
    
    @staticmethod
    def update_snippet_status(snippet_id, status, user_id, review_notes=None):
        """Update snippet review status"""
        try:
            snippet = Snippet.query.get(snippet_id)
            if not snippet:
                return {
                    'success': False,
                    'message': 'Snippet not found'
                }
            
            # Check permissions
            project = snippet.page.website.project
            from models import User
            user = User.query.get(user_id)
            if not user or not AuthorizationService.can_edit_project(user, project):
                return {
                    'success': False,
                    'message': 'Permission denied'
                }
            
            # Update snippet
            snippet.status = status
            snippet.reviewed_by = user_id
            snippet.reviewed_at = datetime.utcnow()
            snippet.review_notes = review_notes
            
            db.session.commit()
            
            # Log audit event
            AuditService.log_action(
                user_id=user_id,
                action='review_snippet',
                resource_type='snippet',
                resource_id=snippet_id,
                details={
                    'status': status,
                    'has_notes': bool(review_notes)
                }
            )
            
            return {
                'success': True,
                'message': 'Snippet status updated',
                'snippet': snippet.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Update snippet status error: {e}")
            return {
                'success': False,
                'message': 'Failed to update snippet status'
            }
    
    @staticmethod
    def search_content(query, project_id=None, user_id=None, user_role='user', page=1, per_page=20):
        """Full-text search across page content"""
        try:
            if not query or not query.strip():
                return {
                    'success': False,
                    'message': 'Search query is required',
                    'results': [],
                    'pagination': None
                }
            
            # Use SQLite FTS5 for full-text search
            search_query = query.strip()
            
            # Build FTS query
            fts_query = text("""
                SELECT page_id, title, content, url,
                       snippet(pages_fts, 2, '<mark>', '</mark>', '...', 32) as highlight
                FROM pages_fts 
                WHERE pages_fts MATCH :query
                ORDER BY rank
                LIMIT :limit OFFSET :offset
            """)
            
            offset = (page - 1) * per_page
            
            # Execute FTS search
            fts_results = db.session.execute(
                fts_query,
                {'query': search_query, 'limit': per_page, 'offset': offset}
            ).fetchall()
            
            if not fts_results:
                return {
                    'success': True,
                    'results': [],
                    'pagination': {
                        'page': page,
                        'pages': 0,
                        'per_page': per_page,
                        'total': 0,
                        'has_next': False,
                        'has_prev': False
                    }
                }
            
            # Get page details and apply permission filters
            page_ids = [row.page_id for row in fts_results]
            
            pages_query = Page.query.filter(Page.id.in_(page_ids)).join(Website)
            
            # Apply project filter
            if project_id:
                pages_query = pages_query.filter(Website.project_id == project_id)
            
            # Apply permission filter for non-admin users
            if user_role != 'admin' and user_id:
                from models import User, Project
                pages_query = pages_query.join(Project).filter(
                    db.or_(
                        Project.owner_id == user_id,
                        Project.collaborators.any(User.id == user_id)
                    )
                )
            
            pages = {page.id: page for page in pages_query.all()}
            
            # Build results
            results = []
            for row in fts_results:
                if row.page_id in pages:
                    page = pages[row.page_id]
                    results.append({
                        'page_id': page.id,
                        'url': page.url,
                        'title': page.title,
                        'highlight': row.highlight,
                        'website_name': page.website.name,
                        'project_name': page.website.project.name,
                        'created_at': page.created_at.isoformat()
                    })
            
            # Get total count for pagination
            count_query = text("SELECT COUNT(*) FROM pages_fts WHERE pages_fts MATCH :query")
            total = db.session.execute(count_query, {'query': search_query}).scalar()
            
            return {
                'success': True,
                'results': results,
                'pagination': {
                    'page': page,
                    'pages': (total + per_page - 1) // per_page,
                    'per_page': per_page,
                    'total': total,
                    'has_next': page * per_page < total,
                    'has_prev': page > 1
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Content search error: {e}")
            return {
                'success': False,
                'message': 'Search failed',
                'results': [],
                'pagination': None
            }
    
    @staticmethod
    def suggest_extraction_rules(page_id, sample_content, user_id):
        """Use AI to suggest extraction rules based on sample content"""
        try:
            page = Page.query.get(page_id)
            if not page:
                return {
                    'success': False,
                    'message': 'Page not found',
                    'suggestions': []
                }
            
            # Check if AI service is available
            ai_service = get_azure_openai_service()
            if not ai_service.is_available():
                return {
                    'success': False,
                    'message': 'AI service not available',
                    'suggestions': []
                }
            
            # Get AI suggestions
            result = ai_service.suggest_extraction_rules(page.raw_html, sample_content)
            
            if result['success']:
                # Log audit event
                AuditService.log_action(
                    user_id=user_id,
                    action='suggest_rules',
                    resource_type='page',
                    resource_id=page_id,
                    details={'rules_suggested': len(result['rules'])}
                )
                
                return {
                    'success': True,
                    'suggestions': result['rules'],
                    'usage': result.get('usage')
                }
            else:
                return {
                    'success': False,
                    'message': result['error'],
                    'suggestions': []
                }
            
        except Exception as e:
            current_app.logger.error(f"Rule suggestion error: {e}")
            return {
                'success': False,
                'message': 'Failed to generate rule suggestions',
                'suggestions': []
            }