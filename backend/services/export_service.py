# backend/services/export_service.py
import os
import csv
import json
from datetime import datetime, timedelta
from io import StringIO, BytesIO
from flask import current_app
from models import db, Export, Page, Snippet, Project, Website
from services.auth_service import AuthorizationService, AuditService
import pandas as pd


class ExportService:
    """Data export and reporting service"""
    
    @staticmethod
    def create_export(user_id, export_type, filters=None, filename=None):
        """Create a new export job"""
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"export_{export_type}_{timestamp}.{export_type}"
            
            # Create export record
            export = Export(
                user_id=user_id,
                project_id=filters.get('project_id') if filters else None,
                export_type=export_type,
                filename=filename,
                status='pending',
                progress=0
            )
            
            if filters:
                export.set_filters(filters)
            
            # Set expiration (7 days from now)
            export.expires_at = datetime.utcnow() + timedelta(days=7)
            
            db.session.add(export)
            db.session.commit()
            
            # Start export processing
            try:
                ExportService._process_export(export.id)
            except Exception as e:
                current_app.logger.error(f"Export processing failed: {e}")
                export.status = 'failed'
                export.error_message = str(e)
                db.session.commit()
            
            # Log audit event
            AuditService.log_action(
                user_id=user_id,
                action='create_export',
                resource_type='export',
                resource_id=export.id,
                details={
                    'export_type': export_type,
                    'filters': filters
                }
            )
            
            return {
                'success': True,
                'message': 'Export created successfully',
                'export': export.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Create export error: {e}")
            return {
                'success': False,
                'message': 'Failed to create export',
                'export': None
            }
    
    @staticmethod
    def _process_export(export_id):
        """Process export job"""
        export = Export.query.get(export_id)
        if not export:
            return
        
        try:
            export.status = 'processing'
            export.progress = 10
            db.session.commit()
            
            # Get data based on export type and filters
            if export.export_type in ['csv', 'excel']:
                data = ExportService._get_export_data(export)
                file_path = ExportService._create_data_export(export, data)
            elif export.export_type == 'pdf':
                file_path = ExportService._create_pdf_export(export)
            elif export.export_type == 'json':
                data = ExportService._get_export_data(export)
                file_path = ExportService._create_json_export(export, data)
            else:
                raise ValueError(f"Unsupported export type: {export.export_type}")
            
            # Update export record
            export.status = 'completed'
            export.progress = 100
            export.file_path = file_path
            export.completed_at = datetime.utcnow()
            
            # Get file size
            if os.path.exists(file_path):
                export.file_size = os.path.getsize(file_path)
            
            db.session.commit()
            
        except Exception as e:
            export.status = 'failed'
            export.error_message = str(e)
            db.session.commit()
            raise
    
    @staticmethod
    def _get_export_data(export):
        """Get data for export based on filters"""
        filters = export.get_filters()
        
        # Build base query
        if filters.get('data_type') == 'snippets':
            query = Snippet.query.join(Page).join(Website)
            data_type = 'snippets'
        else:
            query = Page.query.join(Website)
            data_type = 'pages'
        
        # Apply filters
        if export.project_id:
            query = query.filter(Website.project_id == export.project_id)
        
        if filters.get('status') and data_type == 'snippets':
            query = query.filter(Snippet.status == filters['status'])
        
        if filters.get('date_from'):
            date_from = datetime.fromisoformat(filters['date_from'])
            if data_type == 'snippets':
                query = query.filter(Snippet.created_at >= date_from)
            else:
                query = query.filter(Page.created_at >= date_from)
        
        if filters.get('date_to'):
            date_to = datetime.fromisoformat(filters['date_to'])
            if data_type == 'snippets':
                query = query.filter(Snippet.created_at <= date_to)
            else:
                query = query.filter(Page.created_at <= date_to)
        
        # Execute query
        results = query.all()
        
        # Convert to export format
        export_data = []
        for item in results:
            if data_type == 'snippets':
                export_data.append({
                    'snippet_id': item.id,
                    'content': item.content,
                    'status': item.status,
                    'confidence_score': item.confidence_score,
                    'page_url': item.page.url,
                    'page_title': item.page.title,
                    'website_name': item.page.website.name,
                    'project_name': item.page.website.project.name,
                    'created_at': item.created_at.isoformat(),
                    'reviewed_at': item.reviewed_at.isoformat() if item.reviewed_at else None
                })
            else:
                export_data.append({
                    'page_id': item.id,
                    'url': item.url,
                    'title': item.title,
                    'status_code': item.status_code,
                    'content_length': item.content_length,
                    'load_time': item.load_time,
                    'sentiment_score': item.sentiment_score,
                    'website_name': item.website.name,
                    'project_name': item.website.project.name,
                    'created_at': item.created_at.isoformat()
                })
        
        export.row_count = len(export_data)
        return export_data
    
    @staticmethod
    def _create_data_export(export, data):
        """Create CSV or Excel export"""
        export_dir = 'exports'
        os.makedirs(export_dir, exist_ok=True)
        
        file_path = os.path.join(export_dir, export.filename)
        
        if not data:
            # Create empty file
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['No data found'])
            return file_path
        
        if export.export_type == 'csv':
            # Create CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        
        elif export.export_type == 'excel':
            # Create Excel using pandas
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False, engine='openpyxl')
        
        return file_path
    
    @staticmethod
    def _create_json_export(export, data):
        """Create JSON export"""
        export_dir = 'exports'
        os.makedirs(export_dir, exist_ok=True)
        
        file_path = os.path.join(export_dir, export.filename)
        
        export_payload = {
            'export_info': {
                'created_at': export.created_at.isoformat(),
                'export_type': export.export_type,
                'filters': export.get_filters(),
                'row_count': len(data)
            },
            'data': data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_payload, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    @staticmethod
    def _create_pdf_export(export):
        """Create PDF export (simplified - would need proper PDF library)"""
        export_dir = 'exports'
        os.makedirs(export_dir, exist_ok=True)
        
        file_path = os.path.join(export_dir, export.filename)
        
        # Placeholder PDF creation - would use reportlab or similar
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("PDF export functionality requires additional PDF generation library\n")
            f.write(f"Export created: {export.created_at}\n")
            f.write(f"Filters: {export.get_filters()}\n")
        
        return file_path
    
    @staticmethod
    def get_export_status(export_id, user_id, user_role='user'):
        """Get export status"""
        try:
            export = Export.query.get(export_id)
            if not export:
                return {
                    'success': False,
                    'message': 'Export not found',
                    'export': None
                }
            
            # Check permissions
            if user_role != 'admin' and export.user_id != user_id:
                return {
                    'success': False,
                    'message': 'Access denied',
                    'export': None
                }
            
            return {
                'success': True,
                'export': export.to_dict()
            }
            
        except Exception as e:
            current_app.logger.error(f"Get export status error: {e}")
            return {
                'success': False,
                'message': 'Failed to get export status',
                'export': None
            }
    
    @staticmethod
    def download_export(export_id, user_id, user_role='user'):
        """Get export file for download"""
        try:
            export = Export.query.get(export_id)
            if not export:
                return {
                    'success': False,
                    'message': 'Export not found',
                    'file_path': None
                }
            
            # Check permissions
            if user_role != 'admin' and export.user_id != user_id:
                return {
                    'success': False,
                    'message': 'Access denied',
                    'file_path': None
                }
            
            # Check if export is completed
            if export.status != 'completed':
                return {
                    'success': False,
                    'message': f'Export is {export.status}',
                    'file_path': None
                }
            
            # Check if file exists
            if not export.file_path or not os.path.exists(export.file_path):
                return {
                    'success': False,
                    'message': 'Export file not found',
                    'file_path': None
                }
            
            # Check if expired
            if export.expires_at and export.expires_at < datetime.utcnow():
                return {
                    'success': False,
                    'message': 'Export has expired',
                    'file_path': None
                }
            
            # Log download
            AuditService.log_action(
                user_id=user_id,
                action='download_export',
                resource_type='export',
                resource_id=export_id
            )
            
            return {
                'success': True,
                'file_path': export.file_path,
                'filename': export.filename,
                'file_size': export.file_size
            }
            
        except Exception as e:
            current_app.logger.error(f"Download export error: {e}")
            return {
                'success': False,
                'message': 'Download failed',
                'file_path': None
            }
    
    @staticmethod
    def get_user_exports(user_id, user_role='user', page=1, per_page=20):
        """Get user's export history"""
        try:
            query = Export.query
            
            # Filter by user for non-admin users
            if user_role != 'admin':
                query = query.filter(Export.user_id == user_id)
            
            # Order by most recent first
            query = query.order_by(Export.created_at.desc())
            
            # Paginate
            pagination = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'success': True,
                'exports': [export.to_dict() for export in pagination.items],
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
            current_app.logger.error(f"Get user exports error: {e}")
            return {
                'success': False,
                'message': 'Failed to retrieve exports',
                'exports': [],
                'pagination': None
            }
    
    @staticmethod
    def cleanup_expired_exports():
        """Clean up expired export files"""
        try:
            expired_exports = Export.query.filter(
                Export.expires_at < datetime.utcnow(),
                Export.status == 'completed'
            ).all()
            
            cleaned_count = 0
            for export in expired_exports:
                if export.file_path and os.path.exists(export.file_path):
                    try:
                        os.remove(export.file_path)
                        cleaned_count += 1
                    except Exception as e:
                        current_app.logger.warning(f"Failed to delete export file {export.file_path}: {e}")
                
                # Update export status
                export.status = 'expired'
                export.file_path = None
            
            db.session.commit()
            
            current_app.logger.info(f"Cleaned up {cleaned_count} expired export files")
            return cleaned_count
            
        except Exception as e:
            current_app.logger.error(f"Export cleanup error: {e}")
            return 0