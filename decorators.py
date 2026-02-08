"""Decorators for rate limiting and audit logging"""
from functools import wraps
from flask import request, abort, flash, redirect, url_for
from flask_login import current_user
from datetime import datetime, timedelta
from utils import create_audit_log

# In-memory rate limiting storage (for simplicity - production should use Redis)
rate_limit_storage = {}


def clear_old_rate_limits():
    """Clear rate limits older than 1 hour"""
    now = datetime.utcnow()
    keys_to_delete = []
    for key, data in rate_limit_storage.items():
        if (now - data['first_request']).total_seconds() > 3600:
            keys_to_delete.append(key)
    for key in keys_to_delete:
        del rate_limit_storage[key]


def rate_limit(max_requests, window_minutes, action_name):
    """
    Rate limiting decorator
    
    Args:
        max_requests: Maximum number of requests allowed
        window_minutes: Time window in minutes
        action_name: Name of the action for display
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Admins bypass rate limits
            if current_user.is_authenticated and current_user.is_admin:
                return f(*args, **kwargs)
            
            # Get user identifier
            if current_user.is_authenticated:
                identifier = f"user_{current_user.id}_{action_name}"
            else:
                identifier = f"ip_{request.remote_addr}_{action_name}"
            
            # Clean old entries
            clear_old_rate_limits()
            
            # Check rate limit
            now = datetime.utcnow()
            if identifier in rate_limit_storage:
                data = rate_limit_storage[identifier]
                time_passed = (now - data['first_request']).total_seconds() / 60  # minutes
                
                if time_passed < window_minutes:
                    if data['count'] >= max_requests:
                        # Rate limit exceeded
                        wait_time = int(window_minutes - time_passed)
                        flash(f'Rate limit exceeded. Please wait {wait_time} minutes before trying again.', 'error')
                        return redirect(request.referrer or url_for('index'))
                    else:
                        data['count'] += 1
                else:
                    # Reset window
                    rate_limit_storage[identifier] = {
                        'count': 1,
                        'first_request': now
                    }
            else:
                # First request
                rate_limit_storage[identifier] = {
                    'count': 1,
                    'first_request': now
                }
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def audit_log(action_type):
    """
    Audit logging decorator
    
    Args:
        action_type: Type of action being performed
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the function first
            result = f(*args, **kwargs)
            
            # Log the action if user is authenticated
            if current_user.is_authenticated:
                try:
                    details = {
                        'endpoint': request.endpoint,
                        'method': request.method,
                        'url': request.url
                    }
                    create_audit_log(
                        user_id=current_user.id,
                        action_type=action_type,
                        action_details=details,
                        ip_address=request.remote_addr
                    )
                except Exception as e:
                    # Don't fail the request if audit logging fails
                    print(f"Audit log error: {e}")
            
            return result
        return decorated_function
    return decorator


def judge_required(f):
    """Decorator to require judge or admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not (current_user.is_judge or current_user.is_admin):
            flash('You must be a judge to access this page.', 'error')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
