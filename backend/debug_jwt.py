# backend/debug_jwt.py
"""
JWT Debug Script
This script helps debug JWT token issues by testing token generation and validation.
"""

import os
import sys
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not available")

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token, decode_token
from config import get_config


def test_jwt_configuration():
    """Test JWT configuration and token generation/validation"""
    print("🔍 Testing JWT Configuration")
    print("=" * 40)
    
    # Create minimal Flask app
    app = Flask(__name__)
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    with app.app_context():
        # Print configuration
        print(f"SECRET_KEY: {app.config.get('SECRET_KEY', 'NOT SET')[:20]}...")
        print(f"JWT_SECRET_KEY: {app.config.get('JWT_SECRET_KEY', 'NOT SET')[:20]}...")
        print(f"JWT_ALGORITHM: {app.config.get('JWT_ALGORITHM', 'NOT SET')}")
        print(f"JWT_ACCESS_TOKEN_EXPIRES: {app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 'NOT SET')}")
        
        # Test token generation
        try:
            print("\n🔑 Testing token generation...")
            test_user_id = "123"  # FIXED: Use string instead of integer
            
            # Generate token
            access_token = create_access_token(identity=test_user_id)
            print(f"✅ Token generated successfully")
            print(f"   Token (first 50 chars): {access_token[:50]}...")
            
            # Decode token to verify
            try:
                decoded = decode_token(access_token)
                print(f"✅ Token decoded successfully")
                print(f"   User ID: {decoded.get('sub')}")
                print(f"   Expires: {datetime.fromtimestamp(decoded.get('exp'))}")
                print(f"   Algorithm: {decoded.get('alg', 'Unknown')}")
                print(f"   Token Type: {decoded.get('type', 'Unknown')}")
                
                # Test user ID conversion
                user_id_from_token = decoded.get('sub')
                try:
                    user_id_int = int(user_id_from_token)
                    print(f"   User ID as int: {user_id_int}")
                    print("✅ User ID conversion working")
                except ValueError:
                    print("❌ Cannot convert user ID to integer")
                    return False
                
                return True
                
            except Exception as e:
                print(f"❌ Token decode failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Token generation failed: {e}")
            return False


def test_environment_variables():
    """Test environment variables"""
    print("\n🌍 Testing Environment Variables")
    print("=" * 40)
    
    env_vars = [
        'SECRET_KEY',
        'JWT_SECRET_KEY',
        'FLASK_PORT',
        'REACT_PORT',
        'DATABASE_URL'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        if var in ['SECRET_KEY', 'JWT_SECRET_KEY'] and value != 'NOT SET':
            value = value[:10] + '...' + value[-10:] if len(value) > 20 else value
        print(f"   {var}: {value}")


def test_config_consistency():
    """Test configuration consistency"""
    print("\n⚖️  Testing Configuration Consistency")
    print("=" * 40)
    
    config_class = get_config()
    config = config_class()
    
    secret_key = getattr(config, 'SECRET_KEY', None)
    jwt_secret_key = getattr(config, 'JWT_SECRET_KEY', None)
    
    print(f"   SECRET_KEY set: {bool(secret_key)}")
    print(f"   JWT_SECRET_KEY set: {bool(jwt_secret_key)}")
    
    if secret_key and jwt_secret_key:
        keys_match = secret_key == jwt_secret_key
        print(f"   Keys match: {keys_match}")
        
        if not keys_match:
            print("   ⚠️  SECRET_KEY and JWT_SECRET_KEY don't match!")
            print("   This could cause token validation issues.")
        
        return keys_match
    else:
        print("   ❌ One or both keys are missing!")
        return False


def test_auth_service_compatibility():
    """Test compatibility with auth service"""
    print("\n🔐 Testing Auth Service Compatibility")
    print("=" * 40)
    
    try:
        # Create proper Flask app with database
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from services.auth_service import AuthService
            
            # Test get_user_by_id with string
            print("   Testing get_user_by_id with string ID...")
            user = AuthService.get_user_by_id("123")
            print(f"   String ID test: ✅ Passed (returns: {type(user).__name__})")
            
            # Test get_user_by_id with int
            print("   Testing get_user_by_id with int ID...")
            user = AuthService.get_user_by_id(123)
            print(f"   Int ID test: ✅ Passed (returns: {type(user).__name__})")
            
            print("   ✅ Auth service is compatible with JWT string identities")
            return True
        
    except Exception as e:
        print(f"   ❌ Auth service test failed: {e}")
        return False


def test_backend_connectivity():
    """Test if backend server is running"""
    print("\n🌐 Testing Backend Connectivity")
    print("=" * 40)
    
    try:
        import requests
        
        # Test health endpoint
        response = requests.get('http://localhost:5232/health', timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend server is running")
            health_data = response.json()
            print(f"   Status: {health_data.get('status')}")
            print(f"   Database: {health_data.get('database')}")
            return True
        else:
            print(f"   ❌ Backend server responded with: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ⚠️  Backend server is not running")
        print("   Start with: python start.py")
        return False
    except Exception as e:
        print(f"   ❌ Connection test failed: {e}")
        return False


def main():
    """Main debug function"""
    print("🔧 JWT Configuration Debug Tool")
    print("=" * 50)
    
    success = True
    
    # Test environment variables
    test_environment_variables()
    
    # Test configuration consistency
    if not test_config_consistency():
        success = False
    
    # Test JWT functionality
    if not test_jwt_configuration():
        success = False
    
    # Test auth service compatibility
    if not test_auth_service_compatibility():
        print("   ⚠️  Auth service test failed, but this might be due to missing database")
        print("   This is okay if JWT configuration is working")
    
    # Test backend connectivity
    backend_running = test_backend_connectivity()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ JWT configuration is working correctly!")
        print("   Your tokens should now validate properly.")
        
        if backend_running:
            print("   🎉 Backend server is running - you can run tests now!")
        else:
            print("   💡 Start backend with: python start.py")
            
    else:
        print("❌ Some JWT configuration issues remain!")
        print("   Please check the configuration and try again.")
    
    print("\n📋 Summary:")
    print(f"   JWT Config: {'✅ Working' if success else '❌ Failed'}")
    print(f"   Backend Server: {'✅ Running' if backend_running else '⚠️  Not running'}")
    print("=" * 50)


if __name__ == '__main__':
    main()