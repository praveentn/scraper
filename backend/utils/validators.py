# backend/utils/validators.py
import re


def validate_email(email):
    """Validate email format using regex"""
    if not email or not isinstance(email, str):
        return False
    
    # Simple but effective email regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email.strip()) is not None


def validate_password(password):
    """Validate password strength"""
    if not password or len(password) < 8:
        return False
    return True


def validate_url(url):
    """Validate URL format"""
    if not url or not isinstance(url, str):
        return False
        
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url.strip()) is not None