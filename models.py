"""Database models for Campfire Adelaide Dashboard"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication and profile management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_judge = db.Column(db.Boolean, default=False, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    theme_preference = db.Column(db.String(20), default='light', nullable=False)
    is_banned = db.Column(db.Boolean, default=False, nullable=False)
    ban_reason = db.Column(db.Text, nullable=True)
    banned_until = db.Column(db.DateTime, nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    twitter_url = db.Column(db.String(255), nullable=True)
    portfolio_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    team = db.relationship('Team', back_populates='members')
    posts = db.relationship('Post', back_populates='user', cascade='all, delete-orphan')
    registration_code = db.relationship('RegistrationCode', back_populates='user', uselist=False)
    comments = db.relationship('Comment', back_populates='user', cascade='all, delete-orphan')
    reactions = db.relationship('Reaction', back_populates='user', cascade='all, delete-orphan')
    votes = db.relationship('Vote', back_populates='judge', cascade='all, delete-orphan')
    reports_made = db.relationship('Report', foreign_keys='Report.reported_by_user_id', back_populates='reporter', cascade='all, delete-orphan')
    mentions_made = db.relationship('Mention', foreign_keys='Mention.mentioner_user_id', back_populates='mentioner', cascade='all, delete-orphan')
    mentions_received = db.relationship('Mention', foreign_keys='Mention.mentioned_user_id', back_populates='mentioned_user', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Team(db.Model):
    """Team model for hackathon teams"""
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    avatar_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    members = db.relationship('User', back_populates='team')
    posts = db.relationship('Post', back_populates='team', cascade='all, delete-orphan')
    votes = db.relationship('Vote', back_populates='team', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Team {self.name}>'


class Post(db.Model):
    """Post model for timeline posts"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    is_global = db.Column(db.Boolean, default=False, nullable=False)
    is_hidden = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='posts')
    team = db.relationship('Team', back_populates='posts')
    reactions = db.relationship('Reaction', back_populates='post', cascade='all, delete-orphan')
    comments = db.relationship('Comment', back_populates='post', cascade='all, delete-orphan')
    mentions = db.relationship('Mention', back_populates='post', cascade='all, delete-orphan')
    media = db.relationship('PostMedia', back_populates='post', cascade='all, delete-orphan')
    reports = db.relationship('Report', back_populates='post', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Post {self.id} by {self.user_id}>'


class RegistrationCode(db.Model):
    """Registration code model for user registration"""
    __tablename__ = 'registration_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(6), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    used_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='registration_code')
    
    def __repr__(self):
        return f'<RegistrationCode {self.code}>'


class Reaction(db.Model):
    """Reaction model for post reactions (emoji reactions)"""
    __tablename__ = 'reactions'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)  # like, love, celebrate, idea, fire, applause
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    post = db.relationship('Post', back_populates='reactions')
    user = db.relationship('User', back_populates='reactions')
    
    # Unique constraint: one reaction type per user per post
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', 'reaction_type', name='unique_reaction'),)
    
    def __repr__(self):
        return f'<Reaction {self.reaction_type} by {self.user_id} on {self.post_id}>'


class Comment(db.Model):
    """Comment model for post comments"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    post = db.relationship('Post', back_populates='comments')
    user = db.relationship('User', back_populates='comments')
    mentions = db.relationship('Mention', back_populates='comment', cascade='all, delete-orphan')
    reports = db.relationship('Report', back_populates='comment', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Comment {self.id} by {self.user_id} on post {self.post_id}>'


class Mention(db.Model):
    """Mention model for @mentions in posts and comments"""
    __tablename__ = 'mentions'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    mentioned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mentioner_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    post = db.relationship('Post', back_populates='mentions')
    comment = db.relationship('Comment', back_populates='mentions')
    mentioned_user = db.relationship('User', foreign_keys=[mentioned_user_id], back_populates='mentions_received')
    mentioner = db.relationship('User', foreign_keys=[mentioner_user_id], back_populates='mentions_made')
    
    def __repr__(self):
        return f'<Mention @{self.mentioned_user_id} by {self.mentioner_user_id}>'


class Vote(db.Model):
    """Vote model for judge voting on team submissions"""
    __tablename__ = 'votes'
    
    id = db.Column(db.Integer, primary_key=True)
    judge_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    innovation_score = db.Column(db.Integer, nullable=False)  # 1-10
    implementation_score = db.Column(db.Integer, nullable=False)  # 1-10
    design_score = db.Column(db.Integer, nullable=False)  # 1-10
    presentation_score = db.Column(db.Integer, nullable=False)  # 1-10
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    judge = db.relationship('User', back_populates='votes')
    team = db.relationship('Team', back_populates='votes')
    
    # Unique constraint: one vote per judge per team
    __table_args__ = (db.UniqueConstraint('judge_id', 'team_id', name='unique_vote'),)
    
    def calculate_total_score(self):
        """Calculate weighted total score"""
        return (
            self.innovation_score * 0.30 +
            self.implementation_score * 0.30 +
            self.design_score * 0.20 +
            self.presentation_score * 0.20
        ) * 10  # Scale to 100
    
    def __repr__(self):
        return f'<Vote by judge {self.judge_id} for team {self.team_id}>'


class Announcement(db.Model):
    """Announcement model for site-wide announcements"""
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    announcement_type = db.Column(db.String(20), nullable=False)  # info, warning, success, important
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
    created_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    admin = db.relationship('User', foreign_keys=[created_by_admin_id])
    
    def __repr__(self):
        return f'<Announcement {self.title}>'


class PostMedia(db.Model):
    """PostMedia model for multi-image and video uploads"""
    __tablename__ = 'post_media'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)  # image or video
    file_path = db.Column(db.String(255), nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    post = db.relationship('Post', back_populates='media')
    
    def __repr__(self):
        return f'<PostMedia {self.media_type} for post {self.post_id}>'


class Report(db.Model):
    """Report model for content moderation"""
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    reported_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(50), nullable=False)  # spam, inappropriate, offensive, other
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    post = db.relationship('Post', back_populates='reports')
    comment = db.relationship('Comment', back_populates='reports')
    reporter = db.relationship('User', back_populates='reports_made')
    
    def __repr__(self):
        return f'<Report {self.id} - {self.reason}>'


class AuditLog(db.Model):
    """AuditLog model for tracking user and admin actions"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action_type = db.Column(db.String(50), nullable=False)
    action_details = db.Column(db.Text, nullable=True)  # JSON string
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action_type} by {self.user_id}>'


class SiteSettings(db.Model):
    """SiteSettings model for site-wide branding and customization (singleton)"""
    __tablename__ = 'site_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default='Campfire Adelaide Dashboard', nullable=False)
    logo_path = db.Column(db.String(255), nullable=True)
    favicon_path = db.Column(db.String(255), nullable=True)
    primary_color = db.Column(db.String(7), default='#FF6B35', nullable=False)
    secondary_color = db.Column(db.String(7), default='#004E89', nullable=False)
    font_family = db.Column(db.String(100), default='Inter', nullable=False)
    custom_css = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    admin = db.relationship('User', foreign_keys=[updated_by_admin_id])
    
    def __repr__(self):
        return f'<SiteSettings {self.site_name}>'
