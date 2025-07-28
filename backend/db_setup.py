# backend/db_setup.py
import os
import sys
from datetime import datetime
from flask import Flask
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config, init_directories
from models import db, User, Project, Website, Page, ExtractionRule, Snippet, ScheduledJob, Export, AuditLog


def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    config = get_config()()
    app.config.from_object(config)
    
    # Initialize directories
    init_directories()
    
    # Initialize database
    db.init_app(app)
    
    return app


def create_tables(app):
    """Create all database tables"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            
            # Create FTS5 virtual table for full-text search
            db.session.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
                    page_id,
                    title,
                    content,
                    url
                );
            """))
            
            # Create FTS5 triggers for automatic indexing
            db.session.execute(text("""
                CREATE TRIGGER IF NOT EXISTS pages_fts_insert AFTER INSERT ON pages BEGIN
                    INSERT INTO pages_fts(page_id, title, content, url) 
                    VALUES (new.id, new.title, new.extracted_text, new.url);
                END;
            """))
            
            db.session.execute(text("""
                CREATE TRIGGER IF NOT EXISTS pages_fts_delete AFTER DELETE ON pages BEGIN
                    DELETE FROM pages_fts WHERE page_id = old.id;
                END;
            """))
            
            db.session.execute(text("""
                CREATE TRIGGER IF NOT EXISTS pages_fts_update AFTER UPDATE ON pages BEGIN
                    DELETE FROM pages_fts WHERE page_id = old.id;
                    INSERT INTO pages_fts(page_id, title, content, url) 
                    VALUES (new.id, new.title, new.extracted_text, new.url);
                END;
            """))
            
            # Create indexes for better performance
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id);"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_websites_project ON websites(project_id);"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_pages_website ON pages(website_id);"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_pages_url ON pages(url);"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_snippets_page ON snippets(page_id);"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_snippets_status ON snippets(status);"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);"))
            
            db.session.commit()
            print("✅ Database tables created successfully")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating tables: {e}")
            raise


def create_admin_user(app, email="admin@example.com", password="admin123", first_name="Admin", last_name="User"):
    """Create default admin user"""
    with app.app_context():
        try:
            # Check if admin already exists
            existing_admin = User.query.filter_by(email=email).first()
            if existing_admin:
                print(f"ℹ️  Admin user already exists: {email}")
                return existing_admin
            
            # Create admin user
            admin = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='admin',
                is_active=True
            )
            admin.set_password(password)
            
            db.session.add(admin)
            db.session.commit()
            
            print(f"✅ Admin user created: {email} / {password}")
            return admin
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin user: {e}")
            raise


def create_sample_data(app):
    """Create sample data for testing"""
    with app.app_context():
        try:
            # Check if sample data already exists
            if Project.query.count() > 0:
                print("ℹ️  Sample data already exists")
                return
            
            # Get admin user
            admin = User.query.filter_by(role='admin').first()
            if not admin:
                print("❌ No admin user found. Create admin user first.")
                return
            
            # Create sample project
            project = Project(
                name="Sample Web Scraping Project",
                description="A demonstration project for web scraping capabilities",
                industry="Technology",
                priority="high",
                status="active",
                owner_id=admin.id
            )
            project.set_tags(["demo", "technology", "web-scraping"])
            
            db.session.add(project)
            db.session.flush()  # Get project ID
            
            # Create sample website
            website = Website(
                project_id=project.id,
                url="https://example.com",
                name="Example Website",
                description="Sample website for testing scraping functionality",
                crawl_depth=2,
                follow_external_links=False,
                respect_robots_txt=True,
                rate_limit_delay=1.0,
                auth_type="none",
                status="active"
            )
            
            db.session.add(website)
            db.session.flush()  # Get website ID
            
            # Create sample extraction rule
            extraction_rule = ExtractionRule(
                project_id=project.id,
                name="Page Titles",
                description="Extract page titles using CSS selector",
                rule_type="css",
                selector="h1, h2, h3",
                attribute="text",
                transform="clean",
                required=False,
                multiple=True,
                is_active=True,
                priority=100
            )
            
            db.session.add(extraction_rule)
            db.session.commit()
            
            print("✅ Sample data created successfully")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating sample data: {e}")
            raise


def reset_database(app):
    """Drop and recreate all tables (WARNING: This deletes all data!)"""
    with app.app_context():
        try:
            # Drop FTS table first
            db.session.execute(text("DROP TABLE IF EXISTS pages_fts;"))
            
            # Drop all tables
            db.drop_all()
            
            print("✅ Database reset completed")
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            raise


def backup_database(app, backup_path=None):
    """Create a backup of the SQLite database"""
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"backup_scraper_{timestamp}.db"
    
    try:
        import shutil
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            print(f"✅ Database backed up to: {backup_path}")
        else:
            print(f"❌ Database file not found: {db_path}")
            
    except Exception as e:
        print(f"❌ Error backing up database: {e}")


def verify_database(app):
    """Verify database integrity and structure"""
    with app.app_context():
        try:
            # Check table counts
            tables = {
                'users': User.query.count(),
                'projects': Project.query.count(),
                'websites': Website.query.count(),
                'pages': Page.query.count(),
                'extraction_rules': ExtractionRule.query.count(),
                'snippets': Snippet.query.count(),
                'scheduled_jobs': ScheduledJob.query.count(),
                'exports': Export.query.count(),
                'audit_logs': AuditLog.query.count()
            }
            
            print("\n📊 Database Table Counts:")
            for table, count in tables.items():
                print(f"   {table}: {count}")
            
            # Check FTS table
            fts_result = db.session.execute(text("SELECT count(*) FROM pages_fts;")).scalar()
            print(f"   pages_fts: {fts_result}")
            
            # Check database file size
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if os.path.exists(db_path):
                size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
                print(f"\n💾 Database size: {size_mb} MB")
            
            print("✅ Database verification completed")
            
        except Exception as e:
            print(f"❌ Error verifying database: {e}")


def run_migration(app, migration_sql):
    """Run custom migration SQL"""
    with app.app_context():
        try:
            db.session.execute(text(migration_sql))
            db.session.commit()
            print("✅ Migration executed successfully")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {e}")
            raise


def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database setup and management')
    parser.add_argument('action', choices=['create', 'reset', 'backup', 'verify', 'admin', 'sample'], 
                       help='Action to perform')
    parser.add_argument('--email', default='admin@example.com', help='Admin email (for admin action)')
    parser.add_argument('--password', default='admin123', help='Admin password (for admin action)')
    parser.add_argument('--backup-path', help='Backup file path')
    
    args = parser.parse_args()
    
    # Create Flask app
    app = create_app()
    
    print(f"🚀 Executing database action: {args.action}")
    
    if args.action == 'create':
        create_tables(app)
        verify_database(app)
        
    elif args.action == 'reset':
        confirm = input("⚠️  This will delete ALL data. Type 'YES' to confirm: ")
        if confirm == 'YES':
            reset_database(app)
            create_tables(app)
            print("✅ Database reset and recreated")
        else:
            print("❌ Reset cancelled")
            
    elif args.action == 'backup':
        backup_database(app, args.backup_path)
        
    elif args.action == 'verify':
        verify_database(app)
        
    elif args.action == 'admin':
        create_admin_user(app, args.email, args.password)
        
    elif args.action == 'sample':
        create_sample_data(app)
        
    print("🎉 Database setup completed")


if __name__ == '__main__':
    main()