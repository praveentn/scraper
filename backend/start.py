# backend/start.py
"""
Blitz Backend Startup Script
This script ensures all dependencies are installed and configurations are correct before starting the server.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def install_dependencies():
    """Install required Python packages"""
    try:
        print("📦 Installing dependencies...")
        
        # Check if requirements.txt exists
        if not os.path.exists('requirements.txt'):
            print("❌ requirements.txt not found")
            return False
        
        # Install packages
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def setup_environment():
    """Setup environment configuration"""
    try:
        # Check if .env file exists
        if not os.path.exists('.env'):
            print("⚠️  .env file not found, creating from template...")
            
            # Create basic .env file
            env_content = """# Basic .env configuration
SECRET_KEY=blitz-super-secret-key-change-this-in-production-2025
JWT_SECRET_KEY=blitz-super-secret-key-change-this-in-production-2025
FLASK_ENV=development
FLASK_PORT=5232
REACT_PORT=3232
DATABASE_URL=sqlite:///scraper.db
AZURE_OPENAI_API_KEY=openai-key-placeholder
AZURE_OPENAI_ENDPOINT=https://prave-mcngte2t-eastus2.cognitiveservices.azure.com/openai/deployments/gpt-4.1-nano/chat/completions?api-version=2025-01-01-preview
"""
            
            with open('.env', 'w') as f:
                f.write(env_content)
            
            print("✅ .env file created")
        else:
            print("✅ .env file found")
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Environment variables loaded")
        except ImportError:
            print("⚠️  python-dotenv not available, using system environment")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up environment: {e}")
        return False


def setup_database():
    """Setup database"""
    try:
        print("🗄️  Setting up database...")
        
        # Import and setup database
        from models import db
        from app import create_app
        
        app = create_app()
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create FTS5 virtual table
            from sqlalchemy import text
            try:
                db.session.execute(text("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
                        page_id,
                        title,
                        content,
                        url
                    );
                """))
                db.session.commit()
                print("✅ FTS5 search index created")
            except Exception as e:
                print(f"⚠️  FTS5 setup warning: {e}")
            
            # Create admin user if it doesn't exist
            from models import User
            admin = User.query.filter_by(email='admin@example.com').first()
            if not admin:
                admin = User(
                    email='admin@example.com',
                    first_name='Admin',
                    last_name='User',
                    role='admin',
                    is_active=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created (admin@example.com / admin123)")
            else:
                print("✅ Admin user already exists")
        
        print("✅ Database setup complete")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False


def start_server():
    """Start the Flask server"""
    try:
        print("🚀 Starting Blitz backend server...")
        
        from app import run_app
        run_app()
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False


def main():
    """Main startup function"""
    print("🌟 Blitz Web Scraping Platform - Backend Setup")
    print("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n⚠️  Continuing without installing dependencies...")
        print("   Please run: pip install -r requirements.txt")
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("\n⚠️  Database setup failed, but continuing...")
    
    print("\n" + "=" * 50)
    print("✅ Setup complete! Starting server...")
    print("=" * 50)
    
    # Start server
    start_server()


if __name__ == '__main__':
    main()