"""Utility functions for the Campfire Adelaide Dashboard"""
import re
import os
from datetime import datetime
from models import User, Mention


def parse_mentions(text, current_user_id, post_id=None, comment_id=None):
    """
    Parse @mentions from text and create Mention records
    Returns list of Mention objects
    """
    # Find all @mentions (alphanumeric usernames)
    mention_pattern = r'@(\w+)'
    mentioned_usernames = re.findall(mention_pattern, text)
    
    mentions = []
    for username in set(mentioned_usernames):  # Use set to avoid duplicates
        user = User.query.filter_by(username=username).first()
        if user and user.id != current_user_id:  # Don't mention yourself
            mention = Mention(
                post_id=post_id,
                comment_id=comment_id,
                mentioned_user_id=user.id,
                mentioner_user_id=current_user_id
            )
            mentions.append(mention)
    
    return mentions


def highlight_mentions(text):
    """
    Convert @mentions to HTML links
    """
    mention_pattern = r'@(\w+)'
    
    def replace_mention(match):
        username = match.group(1)
        user = User.query.filter_by(username=username).first()
        if user:
            return f'<a href="/user/{user.id}" class="mention">@{username}</a>'
        return match.group(0)
    
    return re.sub(mention_pattern, replace_mention, text)


def sanitize_html(text):
    """
    Basic HTML sanitization to prevent XSS attacks
    Escape HTML tags except for allowed formatting
    """
    import html
    # Escape all HTML
    text = html.escape(text)
    # Convert newlines to <br>
    text = text.replace('\n', '<br>')
    return text


def validate_url(url):
    """
    Validate if a string is a valid URL
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def get_site_settings():
    """
    Get current site settings (cached)
    """
    from models import SiteSettings
    settings = SiteSettings.query.first()
    if not settings:
        # Create default settings if none exist
        from models import db
        settings = SiteSettings()
        db.session.add(settings)
        db.session.commit()
    return settings


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def generate_unique_filename(original_filename):
    """Generate a unique filename with timestamp and random component"""
    import random
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}.{ext}"
    return filename


def create_audit_log(user_id, action_type, action_details, ip_address=None):
    """
    Create an audit log entry
    """
    from models import AuditLog, db
    import json
    
    log = AuditLog(
        user_id=user_id,
        action_type=action_type,
        action_details=json.dumps(action_details) if isinstance(action_details, dict) else action_details,
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()
    return log


def format_time_ago(dt):
    """Convert datetime to human-readable time ago format"""
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime('%b %d, %Y')
