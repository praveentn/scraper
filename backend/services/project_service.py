# backend/services/project_service.py
from datetime import datetime
from flask import current_app
from sqlalchemy import desc, func
from models import db, Project, Website, User, project_collaborators
from services.auth_service import AuthorizationService, AuditService


class ProjectService:
    """Project management service"""
    
    @staticmethod
    def create_project(user_id, name, description=None, tags=None, industry=None, priority='medium'):
        """Create a new project"""
        try:
            # Validate input
            if not name or not name.strip():
                return {
                    'success': False,
                    'message': 'Project name is required',
                    'project': None
                }
            
            # Create project
            project = Project(
                name=name.strip(),
                description=description.strip() if description else None,
                industry=industry.strip() if industry else None,
                priority=priority,
                status='active',
                owner_id=user_id
            )
            
            # Set tags if provided
            if tags:
                if isinstance(tags, list):
                    project.set_tags(tags)
                elif isinstance(tags, str):
                    # Split comma-separated tags
                    tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                    project.set_tags(tag_list)
            
            db.session.add(project)
            db.session.commit()
            
            # Log audit event
            AuditService.log_action(
                user_id=user_id,
                action='create_project',
                resource_type='project',
                resource_id=project.id,
                details={'project_name': project.name}
            )
            
            return {
                'success': True,
                'message': 'Project created successfully',
                'project': project.to_dict(include_stats=True)
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Create project error: {e}")
            return {
                'success': False,
                'message': 'Failed to create project',
                'project': None
            }
    
    @staticmethod
    def get_projects(user_id, user_role='user', page=1, per_page=20, search=None, status=None, industry=None):
        """Get projects with filtering and pagination"""
        try:
            query = Project.query
            
            # Filter by access permissions
            if user_role != 'admin':
                # User can see owned projects and projects they collaborate on
                query = query.filter(
                    db.or_(
                        Project.owner_id == user_id,
                        Project.collaborators.any(User.id == user_id)
                    )
                )
            
            # Apply filters
            if search:
                search_term = f"%{search.strip()}%"
                query = query.filter(
                    db.or_(
                        Project.name.ilike(search_term),
                        Project.description.ilike(search_term),
                        Project.tags.ilike(search_term)
                    )
                )
            
            if status:
                query = query.filter(Project.status == status)
            
            if industry:
                query = query.filter(Project.industry == industry)
            
            # Order by most recent first
            query = query.order_by(desc(Project.updated_at))
            
            # Paginate
            pagination = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            # Get projects with stats
            projects = []
            for project in pagination.items:
                projects.append(project.to_dict(include_stats=True))
            
            return {
                'success': True,
                'projects': projects,
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
            current_app.logger.error(f"Get projects error: {e}")
            return {
                'success': False,
                'message': 'Failed to retrieve projects',
                'projects': [],
                'pagination': None
            }
    
    @staticmethod
    def get_project_by_id(project_id, user_id, user_role='user'):
        """Get project by ID with permission check"""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {
                    'success': False,
                    'message': 'Project not found',
                    'project': None
                }
            
            # Check permissions
            user = User.query.get(user_id)
            if not user or not AuthorizationService.can_access_project(user, project):
                return {
                    'success': False,
                    'message': 'Access denied',
                    'project': None
                }
            
            return {
                'success': True,
                'project': project.to_dict(include_stats=True)
            }
            
        except Exception as e:
            current_app.logger.error(f"Get project error: {e}")
            return {
                'success': False,
                'message': 'Failed to retrieve project',
                'project': None
            }
    
    @staticmethod
    def update_project(project_id, user_id, user_role='user', **kwargs):
        """Update project with permission check"""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {
                    'success': False,
                    'message': 'Project not found'
                }
            
            # Check permissions
            user = User.query.get(user_id)
            if not user or not AuthorizationService.can_edit_project(user, project):
                return {
                    'success': False,
                    'message': 'Permission denied'
                }
            
            # Update allowed fields
            allowed_fields = ['name', 'description', 'industry', 'priority', 'status']
            updated_fields = {}
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    if field in ['name', 'description', 'industry'] and value:
                        value = value.strip()
                    
                    if field == 'name' and not value:
                        return {
                            'success': False,
                            'message': 'Project name cannot be empty'
                        }
                    
                    setattr(project, field, value)
                    updated_fields[field] = value
            
            # Handle tags separately
            if 'tags' in kwargs:
                tags = kwargs['tags']
                if isinstance(tags, list):
                    project.set_tags(tags)
                elif isinstance(tags, str):
                    tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                    project.set_tags(tag_list)
                updated_fields['tags'] = project.get_tags()
            
            project.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Log audit event
            AuditService.log_action(
                user_id=user_id,
                action='update_project',
                resource_type='project',
                resource_id=project.id,
                details={'updated_fields': updated_fields}
            )
            
            return {
                'success': True,
                'message': 'Project updated successfully',
                'project': project.to_dict(include_stats=True)
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Update project error: {e}")
            return {
                'success': False,
                'message': 'Failed to update project'
            }
    
    @staticmethod
    def delete_project(project_id, user_id, user_role='user'):
        """Delete project with permission check"""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {
                    'success': False,
                    'message': 'Project not found'
                }
            
            # Check permissions
            user = User.query.get(user_id)
            if not user or not AuthorizationService.can_delete_project(user, project):
                return {
                    'success': False,
                    'message': 'Permission denied'
                }
            
            project_name = project.name
            
            # Delete project (cascading deletes will handle related records)
            db.session.delete(project)
            db.session.commit()
            
            # Log audit event
            AuditService.log_action(
                user_id=user_id,
                action='delete_project',
                resource_type='project',
                resource_id=project_id,
                details={'project_name': project_name}
            )
            
            return {
                'success': True,
                'message': 'Project deleted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Delete project error: {e}")
            return {
                'success': False,
                'message': 'Failed to delete project'
            }
    
    @staticmethod
    def add_collaborator(project_id, user_id, collaborator_email, role='viewer', requester_role='user'):
        """Add collaborator to project"""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {
                    'success': False,
                    'message': 'Project not found'
                }
            
            # Check permissions
            user = User.query.get(user_id)
            if not user or not AuthorizationService.can_edit_project(user, project):
                return {
                    'success': False,
                    'message': 'Permission denied'
                }
            
            # Find collaborator user
            collaborator = User.query.filter_by(email=collaborator_email.lower().strip()).first()
            if not collaborator:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            # Check if already a collaborator
            if project.get_collaborator_role(collaborator.id):
                return {
                    'success': False,
                    'message': 'User is already a collaborator'
                }
            
            # Add collaborator
            from sqlalchemy import insert
            stmt = insert(project_collaborators).values(
                user_id=collaborator.id,
                project_id=project.id,
                role=role,
                created_at=datetime.utcnow()
            )
            db.session.execute(stmt)
            db.session.commit()
            
            # Log audit event
            AuditService.log_action(
                user_id=user_id,
                action='add_collaborator',
                resource_type='project',
                resource_id=project.id,
                details={
                    'collaborator_email': collaborator_email,
                    'role': role
                }
            )
            
            return {
                'success': True,
                'message': 'Collaborator added successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Add collaborator error: {e}")
            return {
                'success': False,
                'message': 'Failed to add collaborator'
            }
    
    @staticmethod
    def remove_collaborator(project_id, user_id, collaborator_id, requester_role='user'):
        """Remove collaborator from project"""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {
                    'success': False,
                    'message': 'Project not found'
                }
            
            # Check permissions
            user = User.query.get(user_id)
            if not user or not AuthorizationService.can_edit_project(user, project):
                return {
                    'success': False,
                    'message': 'Permission denied'
                }
            
            # Remove collaborator
            from sqlalchemy import delete
            stmt = delete(project_collaborators).where(
                project_collaborators.c.user_id == collaborator_id,
                project_collaborators.c.project_id == project_id
            )
            result = db.session.execute(stmt)
            
            if result.rowcount == 0:
                return {
                    'success': False,
                    'message': 'Collaborator not found'
                }
            
            db.session.commit()
            
            # Log audit event
            AuditService.log_action(
                user_id=user_id,
                action='remove_collaborator',
                resource_type='project',
                resource_id=project.id,
                details={'collaborator_id': collaborator_id}
            )
            
            return {
                'success': True,
                'message': 'Collaborator removed successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Remove collaborator error: {e}")
            return {
                'success': False,
                'message': 'Failed to remove collaborator'
            }
    
    @staticmethod
    def get_project_collaborators(project_id, user_id, user_role='user'):
        """Get project collaborators"""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {
                    'success': False,
                    'message': 'Project not found',
                    'collaborators': []
                }
            
            # Check permissions
            user = User.query.get(user_id)
            if not user or not AuthorizationService.can_access_project(user, project):
                return {
                    'success': False,
                    'message': 'Access denied',
                    'collaborators': []
                }
            
            # Get collaborators with roles
            collaborators = []
            
            # Add owner
            if project.owner:
                collaborators.append({
                    'user': project.owner.to_dict(),
                    'role': 'owner',
                    'added_at': project.created_at.isoformat()
                })
            
            # Add other collaborators
            query = db.session.query(User, project_collaborators.c.role, project_collaborators.c.created_at).join(
                project_collaborators, User.id == project_collaborators.c.user_id
            ).filter(project_collaborators.c.project_id == project_id)
            
            for user_obj, role, added_at in query.all():
                collaborators.append({
                    'user': user_obj.to_dict(),
                    'role': role,
                    'added_at': added_at.isoformat()
                })
            
            return {
                'success': True,
                'collaborators': collaborators
            }
            
        except Exception as e:
            current_app.logger.error(f"Get collaborators error: {e}")
            return {
                'success': False,
                'message': 'Failed to retrieve collaborators',
                'collaborators': []
            }
    
    @staticmethod
    def get_project_statistics(project_id, user_id, user_role='user'):
        """Get detailed project statistics"""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {
                    'success': False,
                    'message': 'Project not found',
                    'statistics': None
                }
            
            # Check permissions
            user = User.query.get(user_id)
            if not user or not AuthorizationService.can_access_project(user, project):
                return {
                    'success': False,
                    'message': 'Access denied',
                    'statistics': None
                }
            
            # Calculate statistics
            from sqlalchemy import func
            
            stats = {}
            
            # Website statistics
            website_stats = db.session.query(
                func.count(Website.id).label('total_websites'),
                func.count(func.nullif(Website.status, 'active')).label('inactive_websites')
            ).filter(Website.project_id == project_id).first()
            
            stats['websites'] = {
                'total': website_stats.total_websites or 0,
                'active': (website_stats.total_websites or 0) - (website_stats.inactive_websites or 0),
                'inactive': website_stats.inactive_websites or 0
            }
            
            # Page statistics
            from models import Page
            page_stats = db.session.query(
                func.count(Page.id).label('total_pages'),
                func.avg(Page.load_time).label('avg_load_time')
            ).join(Website).filter(Website.project_id == project_id).first()
            
            stats['pages'] = {
                'total': page_stats.total_pages or 0,
                'avg_load_time': round(page_stats.avg_load_time, 3) if page_stats.avg_load_time else 0.0
            }
            
            # Snippet statistics
            from models import Snippet
            snippet_stats = db.session.query(
                func.count(Snippet.id).label('total_snippets'),
                func.count(func.nullif(Snippet.status, 'pending')).label('reviewed_snippets'),
                func.count(func.nullif(Snippet.status, 'approved')).label('approved_snippets')
            ).join(Page).join(Website).filter(Website.project_id == project_id).first()
            
            stats['snippets'] = {
                'total': snippet_stats.total_snippets or 0,
                'pending': (snippet_stats.total_snippets or 0) - (snippet_stats.reviewed_snippets or 0),
                'approved': snippet_stats.approved_snippets or 0,
                'rejected': (snippet_stats.reviewed_snippets or 0) - (snippet_stats.approved_snippets or 0)
            }
            
            # Recent activity
            recent_pages = db.session.query(Page).join(Website).filter(
                Website.project_id == project_id
            ).order_by(desc(Page.created_at)).limit(5).all()
            
            stats['recent_activity'] = [
                {
                    'type': 'page_scraped',
                    'url': page.url,
                    'title': page.title,
                    'timestamp': page.created_at.isoformat()
                }
                for page in recent_pages
            ]
            
            return {
                'success': True,
                'statistics': stats
            }
            
        except Exception as e:
            current_app.logger.error(f"Get project statistics error: {e}")
            return {
                'success': False,
                'message': 'Failed to retrieve project statistics',
                'statistics': None
            }