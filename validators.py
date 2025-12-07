"""
Input validation utilities
"""
import re
from html import escape


def validate_password(password):
    """
    Validate password strength.
    
    Requirements:
    - At least 8 characters
    - Contains uppercase and lowercase letters
    - Contains at least one digit
    - Contains at least one special character
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain an uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain a lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain a digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain a special character"
    
    return True, ""


def validate_username(username):
    """
    Validate username format.
    
    Requirements:
    - 3-30 characters
    - Only letters, numbers, and underscores
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if len(username) < 3 or len(username) > 30:
        return False, "Username must be 3-30 characters"
    
    if not re.match(r'^[a-z0-9_]+$', username):
        return False, "Username can only contain lowercase letters, numbers, and underscores"
    
    return True, ""


def sanitize_input(text, max_length=None):
    """
    Sanitize user input to prevent XSS.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # Enforce max length
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    # Escape HTML
    text = escape(text)
    
    return text


def validate_trade_params(shares, action, privacy):
    """
    Validate trading parameters.
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if shares <= 0:
        return False, "Shares must be greater than 0"
    
    if shares > 10000:
        return False, "Maximum 10,000 shares per transaction"
    
    if action not in ['buy', 'sell']:
        return False, "Action must be 'buy' or 'sell'"
    
    if privacy not in ['public', 'followers', 'private']:
        return False, "Privacy must be 'public', 'followers', or 'private'"
    
    return True, ""
