import os
import random
import string
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from models import (db, User, Team, Post, RegistrationCode, Reaction, Comment, 
                    Mention, Vote, Announcement, PostMedia, Report, AuditLog, SiteSettings)
from forms import (LoginForm, RegistrationForm, PostForm, ProfilePictureForm,
                   CreateUserForm, CreateTeamForm, AssignTeamForm, GenerateCodesForm,
                   CommentForm, VoteForm, AnnouncementForm, ReportForm, ProfileUpdateForm,
                   TeamAvatarForm, BrandingForm, ModerationActionForm)
from utils import (parse_mentions, highlight_mentions, sanitize_html, validate_url,
                   get_site_settings, allowed_file, generate_unique_filename, 
                   create_audit_log, format_time_ago)
from decorators import rate_limit, audit_log, judge_required

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}
MAX_IMAGES_PER_POST = 10

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///campfire.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size for videos
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """Check if file extension is allowed for images"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_upload(file, folder, allowed_extensions=None):
    """
    Save uploaded file and return the filename
    
    Args:
        file: The file object to save
        folder: Subfolder within UPLOAD_FOLDER
        allowed_extensions: Set of allowed file extensions (defaults to ALLOWED_IMAGE_EXTENSIONS)
    
    Returns:
        str: The filename if successful, None otherwise
    """
    if not file or not file.filename:
        return None
    
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS
    
    if '.' not in file.filename:
        return None
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return None
    
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    file.save(filepath)
    return filename


def time_ago(dt):
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


app.jinja_env.filters['time_ago'] = time_ago


@app.context_processor
def inject_global_data():
    """Inject data into all templates"""
    settings = get_site_settings()
    
    active_announcements = Announcement.query.filter(
        (Announcement.expires_at == None) | (Announcement.expires_at > datetime.utcnow())
    ).order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).all()
    
    return {
        'site_settings': settings,
        'active_announcements': active_announcements
    }


@app.route('/')
def index():
    """Home page - redirect to appropriate dashboard"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if user.is_banned:
                if user.banned_until and user.banned_until > datetime.utcnow():
                    flash(f'Your account is banned until {user.banned_until.strftime("%Y-%m-%d %H:%M")}. Reason: {user.ban_reason}', 'error')
                elif not user.banned_until:
                    flash(f'Your account has been permanently banned. Reason: {user.ban_reason}', 'error')
                else:
                    user.is_banned = False
                    user.banned_until = None
                    user.ban_reason = None
                    db.session.commit()
            
            if not user.is_banned:
                login_user(user, remember=form.remember_me.data)
                
                create_audit_log(
                    user_id=user.id,
                    action_type='login',
                    action_details={'username': user.username},
                    ip_address=request.remote_addr
                )
                
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('index')
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(next_page)
        else:
            flash('Invalid username or password', 'error')
            create_audit_log(
                user_id=None,
                action_type='failed_login',
                action_details={'username': form.username.data},
                ip_address=request.remote_addr
            )
    
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        reg_code = RegistrationCode.query.filter_by(code=form.code.data).first()
        
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        
        reg_code.is_used = True
        reg_code.used_by_user_id = user.id
        
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """Logout current user"""
    create_audit_log(
        user_id=current_user.id,
        action_type='logout',
        action_details={'username': current_user.username},
        ip_address=request.remote_addr
    )
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    users_count = User.query.count()
    teams_count = Team.query.count()
    posts_count = Post.query.count()
    codes_unused = RegistrationCode.query.filter_by(is_used=False).count()
    
    return render_template('admin/dashboard.html',
                         users_count=users_count,
                         teams_count=teams_count,
                         posts_count=posts_count,
                         codes_unused=codes_unused)


@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_users():
    """Manage users"""
    form = CreateUserForm()
    assign_form = AssignTeamForm()
    
    teams = Team.query.all()
    form.team_id.choices = [(0, 'No Team')] + [(t.id, t.name) for t in teams]
    assign_form.team_id.choices = [(t.id, t.name) for t in teams]
    
    users = User.query.all()
    assign_form.user_id.choices = [(u.id, u.username) for u in users]
    
    if form.validate_on_submit() and form.submit.data:
        user = User(username=form.username.data, is_admin=form.is_admin.data)
        user.set_password(form.password.data)
        if form.team_id.data and form.team_id.data > 0:
            user.team_id = form.team_id.data
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.username} created successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/users.html', users=users, form=form, assign_form=assign_form)


@app.route('/admin/users/assign', methods=['POST'])
@login_required
@admin_required
def admin_assign_team():
    """Assign user to team"""
    form = AssignTeamForm()
    
    # Populate choices
    teams = Team.query.all()
    users = User.query.all()
    form.team_id.choices = [(t.id, t.name) for t in teams]
    form.user_id.choices = [(u.id, u.username) for u in users]
    
    if form.validate_on_submit():
        user = User.query.get(form.user_id.data)
        if user:
            user.team_id = form.team_id.data
            db.session.commit()
            flash(f'User {user.username} assigned to team successfully!', 'success')
        else:
            flash('User not found.', 'error')
    
    return redirect(url_for('admin_users'))


@app.route('/admin/teams', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_teams():
    """Manage teams"""
    form = CreateTeamForm()
    
    if form.validate_on_submit():
        team = Team(name=form.name.data)
        db.session.add(team)
        db.session.commit()
        flash(f'Team {team.name} created successfully!', 'success')
        return redirect(url_for('admin_teams'))
    
    teams = Team.query.all()
    return render_template('admin/teams.html', teams=teams, form=form)


@app.route('/admin/codes', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_codes():
    """Manage registration codes"""
    form = GenerateCodesForm()
    
    if form.validate_on_submit():
        count = form.count.data
        generated = []
        for _ in range(count):
            # Generate unique 6-digit code
            while True:
                code = ''.join(random.choices(string.digits, k=6))
                if not RegistrationCode.query.filter_by(code=code).first():
                    break
            
            reg_code = RegistrationCode(code=code)
            db.session.add(reg_code)
            generated.append(code)
        
        db.session.commit()
        flash(f'Generated {count} registration codes successfully!', 'success')
        return redirect(url_for('admin_codes'))
    
    codes = RegistrationCode.query.order_by(RegistrationCode.created_at.desc()).all()
    return render_template('admin/codes.html', codes=codes, form=form)


@app.route('/admin/codes/reset/<int:code_id>')
@login_required
@admin_required
def admin_reset_code(code_id):
    """Reset a registration code"""
    code = RegistrationCode.query.get_or_404(code_id)
    code.is_used = False
    code.used_by_user_id = None
    db.session.commit()
    flash(f'Registration code {code.code} has been reset.', 'success')
    return redirect(url_for('admin_codes'))


# User routes
@app.route('/dashboard')
@login_required
def user_dashboard():
    """User dashboard"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    return render_template('user/dashboard.html')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile"""
    form = ProfileUpdateForm()
    
    if form.validate_on_submit():
        updated = False
        
        # Update profile picture
        if form.profile_picture.data:
            filename = save_upload(form.profile_picture.data, 'profiles')
            if filename:
                current_user.profile_picture = filename
                updated = True
        
        # Update social links
        if form.github_url.data:
            current_user.github_url = form.github_url.data
            updated = True
        if form.linkedin_url.data:
            current_user.linkedin_url = form.linkedin_url.data
            updated = True
        if form.twitter_url.data:
            current_user.twitter_url = form.twitter_url.data
            updated = True
        if form.portfolio_url.data:
            current_user.portfolio_url = form.portfolio_url.data
            updated = True
        
        if updated:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('No changes made.', 'info')
    
    posts = Post.query.filter_by(user_id=current_user.id, deleted_at=None).order_by(Post.created_at.desc()).all()
    return render_template('user/profile.html', form=form, posts=posts)


@app.route('/timeline/team')
@login_required
def team_timeline():
    """Team timeline"""
    if not current_user.team_id:
        flash('You are not assigned to a team yet.', 'warning')
        return redirect(url_for('user_dashboard'))
    
    posts = Post.query.filter_by(team_id=current_user.team_id, deleted_at=None).order_by(Post.created_at.desc()).all()
    return render_template('user/team_timeline.html', posts=posts)


@app.route('/timeline/global')
@login_required
def global_timeline():
    """Global timeline"""
    posts = Post.query.filter_by(is_global=True, deleted_at=None).order_by(Post.created_at.desc()).all()
    return render_template('user/global_timeline.html', posts=posts)


@app.route('/post/create', methods=['GET', 'POST'])
@login_required
@limiter.limit("10 per hour")
def create_post():
    """Create a new post with multi-media support"""
    if not current_user.team_id:
        flash('You must be assigned to a team to create posts.', 'warning')
        return redirect(url_for('user_dashboard'))
    
    form = PostForm()
    
    if form.validate_on_submit():
        # Create post
        post = Post(
            user_id=current_user.id,
            team_id=current_user.team_id,
            description=form.description.data,
            is_global=form.is_global.data
        )
        db.session.add(post)
        db.session.flush()  # Get post ID
        
        # Handle multiple images (up to MAX_IMAGES_PER_POST)
        if form.images.data:
            image_count = 0
            for image_file in form.images.data:
                if image_count >= MAX_IMAGES_PER_POST:
                    flash(f'Maximum {MAX_IMAGES_PER_POST} images allowed per post.', 'warning')
                    break
                
                if image_file and allowed_file(image_file.filename):
                    filename = save_upload(image_file, 'posts')
                    if filename:
                        media = PostMedia(
                            post_id=post.id,
                            media_type='image',
                            file_path=filename,
                            display_order=image_count
                        )
                        db.session.add(media)
                        image_count += 1
        
        # Handle video upload (only if no images)
        elif form.video.data:
            filename = save_upload(form.video.data, 'videos', allowed_extensions=ALLOWED_VIDEO_EXTENSIONS)
            if filename:
                media = PostMedia(
                    post_id=post.id,
                    media_type='video',
                    file_path=filename,
                    display_order=0
                )
                db.session.add(media)
        
        # Legacy single image support
        elif form.image.data:
            image_filename = save_upload(form.image.data, 'posts')
            post.image_path = image_filename
        
        db.session.commit()
        
        create_audit_log(
            user_id=current_user.id,
            action_type='post_created',
            action_details={'post_id': post.id},
            ip_address=request.remote_addr
        )
        
        flash('Post created successfully!', 'success')
        
        if form.is_global.data:
            return redirect(url_for('global_timeline'))
        else:
            return redirect(url_for('team_timeline'))
    
    return render_template('user/create_post.html', form=form)


# API Routes for AJAX interactions

@app.route('/api/reaction/<int:post_id>', methods=['POST'])
@login_required
@rate_limit(100, 60, 'reactions')
def toggle_reaction(post_id):
    """Toggle reaction on a post"""
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    reaction_type = data.get('reaction_type')
    
    if not reaction_type or reaction_type not in ['like', 'love', 'celebrate', 'idea', 'fire', 'applause']:
        return jsonify({'success': False, 'message': 'Invalid reaction type'}), 400
    
    # Check if reaction exists
    existing_reaction = Reaction.query.filter_by(
        post_id=post_id,
        user_id=current_user.id,
        reaction_type=reaction_type
    ).first()
    
    if existing_reaction:
        # Remove reaction
        db.session.delete(existing_reaction)
        db.session.commit()
        action = 'removed'
    else:
        # Add reaction
        reaction = Reaction(
            post_id=post_id,
            user_id=current_user.id,
            reaction_type=reaction_type
        )
        db.session.add(reaction)
        db.session.commit()
        action = 'added'
    
    # Get updated reaction counts
    reactions_data = {}
    for rtype in ['like', 'love', 'celebrate', 'idea', 'fire', 'applause']:
        count = Reaction.query.filter_by(post_id=post_id, reaction_type=rtype).count()
        user_reacted = Reaction.query.filter_by(
            post_id=post_id,
            user_id=current_user.id,
            reaction_type=rtype
        ).first() is not None
        reactions_data[rtype] = {
            'count': count,
            'user_reacted': user_reacted
        }
    
    return jsonify({
        'success': True,
        'action': action,
        'reactions': reactions_data
    })


@app.route('/api/comment/<int:post_id>', methods=['POST'])
@login_required
@rate_limit(30, 60, 'comments')
def add_comment(post_id):
    """Add a comment to a post"""
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400
    
    if len(content) > 1000:
        return jsonify({'success': False, 'message': 'Comment too long (max 1000 characters)'}), 400
    
    # Sanitize content before storing
    content_sanitized = sanitize_html(content)
    
    # Create comment with sanitized content
    comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        content=content_sanitized  # Store sanitized content
    )
    db.session.add(comment)
    db.session.flush()
    
    # Parse mentions from original content
    mentions = parse_mentions(content, current_user.id, comment_id=comment.id)
    for mention in mentions:
        db.session.add(mention)
    
    db.session.commit()
    
    # Return comment data
    comment_data = {
        'id': comment.id,
        'content': content_sanitized,
        'content_html': highlight_mentions(content_sanitized),
        'time_ago': format_time_ago(comment.created_at),
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'profile_picture': f'/static/uploads/profiles/{current_user.profile_picture}' if current_user.profile_picture else None
        },
        'can_delete': True  # Current user can delete their own comment
    }
    
    return jsonify({'success': True, 'comment': comment_data})


@app.route('/api/comment/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """Delete a comment"""
    comment = Comment.query.get_or_404(comment_id)
    
    # Check permissions
    if comment.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Soft delete
    comment.deleted = True
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/api/comments/<int:post_id>')
@login_required
def get_comments(post_id):
    """Get comments for a post"""
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id, deleted=False).order_by(Comment.created_at).all()
    
    comments_data = []
    for comment in comments:
        content_sanitized = sanitize_html(comment.content)
        comments_data.append({
            'id': comment.id,
            'content': comment.content,
            'content_html': highlight_mentions(content_sanitized),
            'time_ago': format_time_ago(comment.created_at),
            'user': {
                'id': comment.user.id,
                'username': comment.user.username,
                'profile_picture': f'/static/uploads/profiles/{comment.user.profile_picture}' if comment.user.profile_picture else None
            },
            'can_delete': comment.user_id == current_user.id or current_user.is_admin
        })
    
    return jsonify({'success': True, 'comments': comments_data})


@app.route('/api/users/search')
@login_required
def search_users():
    """Search users for mentions"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 1:
        users = User.query.limit(10).all()
    else:
        users = User.query.filter(User.username.ilike(f'%{query}%')).limit(10).all()
    
    users_data = [{
        'id': user.id,
        'username': user.username,
        'profile_picture': f'/static/uploads/profiles/{user.profile_picture}' if user.profile_picture else None
    } for user in users]
    
    return jsonify({'success': True, 'users': users_data})


@app.route('/api/theme', methods=['POST'])
@login_required
def save_theme():
    """Save user theme preference"""
    data = request.get_json()
    theme = data.get('theme', 'light')
    
    if theme not in ['light', 'dark']:
        return jsonify({'success': False, 'message': 'Invalid theme'}), 400
    
    current_user.theme_preference = theme
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/post/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    """Soft delete a post"""
    post = Post.query.get_or_404(post_id)
    
    # Check permissions
    if post.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Soft delete
    post.deleted_at = datetime.utcnow()
    db.session.commit()
    
    create_audit_log(
        user_id=current_user.id,
        action_type='post_deleted',
        action_details={'post_id': post_id},
        ip_address=request.remote_addr
    )
    
    flash('Post deleted successfully.', 'success')
    return redirect(request.referrer or url_for('user_dashboard'))


# Announcements routes
@app.route('/admin/announcements', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_announcements():
    """Manage announcements"""
    form = AnnouncementForm()
    
    if form.validate_on_submit():
        announcement = Announcement(
            title=form.title.data,
            content=form.content.data,
            announcement_type=form.announcement_type.data,
            is_pinned=form.is_pinned.data,
            expires_at=form.expires_at.data,
            created_by_admin_id=current_user.id
        )
        db.session.add(announcement)
        db.session.commit()
        
        create_audit_log(
            user_id=current_user.id,
            action_type='announcement_created',
            action_details={'title': announcement.title},
            ip_address=request.remote_addr
        )
        
        flash('Announcement created successfully!', 'success')
        return redirect(url_for('admin_announcements'))
    
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin/announcements.html', form=form, announcements=announcements)


@app.route('/announcements')
@login_required
def view_announcements():
    """View all announcements"""
    announcements = Announcement.query.filter(
        (Announcement.expires_at == None) | (Announcement.expires_at > datetime.utcnow())
    ).order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).all()
    return render_template('user/announcements.html', announcements=announcements)


# Judge voting routes
@app.route('/judge/teams')
@login_required
@judge_required
def judge_teams():
    """Judge dashboard - view all teams"""
    teams = Team.query.all()
    
    # Get voting status for each team
    teams_data = []
    for team in teams:
        existing_vote = Vote.query.filter_by(
            judge_id=current_user.id,
            team_id=team.id
        ).first()
        teams_data.append({
            'team': team,
            'voted': existing_vote is not None,
            'vote': existing_vote
        })
    
    return render_template('judge/teams.html', teams_data=teams_data)


@app.route('/judge/vote/<int:team_id>', methods=['GET', 'POST'])
@login_required
@judge_required
def judge_vote(team_id):
    """Submit or view vote for a team"""
    team = Team.query.get_or_404(team_id)
    
    # Check if already voted
    existing_vote = Vote.query.filter_by(
        judge_id=current_user.id,
        team_id=team_id
    ).first()
    
    form = VoteForm()
    
    if form.validate_on_submit():
        if existing_vote:
            flash('You have already voted for this team.', 'warning')
            return redirect(url_for('judge_teams'))
        
        vote = Vote(
            judge_id=current_user.id,
            team_id=team_id,
            innovation_score=form.innovation_score.data,
            implementation_score=form.implementation_score.data,
            design_score=form.design_score.data,
            presentation_score=form.presentation_score.data,
            comments=form.comments.data
        )
        db.session.add(vote)
        db.session.commit()
        
        create_audit_log(
            user_id=current_user.id,
            action_type='vote_submitted',
            action_details={'team_id': team_id},
            ip_address=request.remote_addr
        )
        
        flash('Vote submitted successfully!', 'success')
        return redirect(url_for('judge_teams'))
    
    # Get team posts for reference
    posts = Post.query.filter_by(team_id=team_id, deleted_at=None).order_by(Post.created_at.desc()).all()
    
    return render_template('judge/vote.html', team=team, form=form, existing_vote=existing_vote, posts=posts)


@app.route('/admin/results')
@login_required
@admin_required
def admin_results():
    """View voting results"""
    teams = Team.query.all()
    
    results = []
    for team in teams:
        votes = Vote.query.filter_by(team_id=team.id).all()
        if votes:
            total_score = sum(vote.calculate_total_score() for vote in votes) / len(votes)
        else:
            total_score = 0
        
        results.append({
            'team': team,
            'votes': votes,
            'average_score': total_score,
            'vote_count': len(votes)
        })
    
    # Sort by average score
    results.sort(key=lambda x: x['average_score'], reverse=True)
    
    return render_template('admin/results.html', results=results)


@app.route('/admin/results/export')
@login_required
@admin_required
def admin_results_export():
    """Export results as CSV"""
    import csv
    from io import StringIO
    from flask import make_response
    
    teams = Team.query.all()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Team', 'Judge', 'Innovation', 'Implementation', 'Design', 'Presentation', 'Total Score', 'Comments'])
    
    for team in teams:
        votes = Vote.query.filter_by(team_id=team.id).all()
        for vote in votes:
            writer.writerow([
                team.name,
                vote.judge.username,
                vote.innovation_score,
                vote.implementation_score,
                vote.design_score,
                vote.presentation_score,
                vote.calculate_total_score(),
                vote.comments or ''
            ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=voting_results_{datetime.utcnow().strftime("%Y%m%d")}.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    return response


# Content moderation routes
@app.route('/api/report/<string:content_type>/<int:content_id>', methods=['POST'])
@login_required
def report_content(content_type, content_id):
    """Report a post or comment"""
    data = request.get_json()
    reason = data.get('reason')
    details = data.get('details', '')
    
    if content_type not in ['post', 'comment']:
        return jsonify({'success': False, 'message': 'Invalid content type'}), 400
    
    if not reason or reason not in ['spam', 'inappropriate', 'offensive', 'harassment', 'other']:
        return jsonify({'success': False, 'message': 'Invalid reason'}), 400
    
    # Create report
    report = Report(
        post_id=content_id if content_type == 'post' else None,
        comment_id=content_id if content_type == 'comment' else None,
        reported_by_user_id=current_user.id,
        reason=reason,
        details=details
    )
    db.session.add(report)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Report submitted successfully'})


@app.route('/admin/moderation')
@login_required
@admin_required
def admin_moderation():
    """Moderation queue"""
    status = request.args.get('status', 'pending')
    
    query = Report.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    reports = query.order_by(Report.created_at.desc()).all()
    
    return render_template('admin/moderation.html', reports=reports, current_status=status)


@app.route('/admin/moderation/<int:report_id>', methods=['POST'])
@login_required
@admin_required
def admin_moderation_action(report_id):
    """Take action on a report"""
    report = Report.query.get_or_404(report_id)
    action = request.form.get('action')
    reason = request.form.get('reason', '')
    
    if action == 'hide':
        # Hide the content
        if report.post_id:
            post = Post.query.get(report.post_id)
            post.is_hidden = True
        elif report.comment_id:
            comment = Comment.query.get(report.comment_id)
            comment.deleted = True
        
        report.status = 'resolved'
        flash('Content hidden successfully.', 'success')
    
    elif action == 'delete':
        # Soft delete the content
        if report.post_id:
            post = Post.query.get(report.post_id)
            post.deleted_at = datetime.utcnow()
        elif report.comment_id:
            comment = Comment.query.get(report.comment_id)
            comment.deleted = True
        
        report.status = 'resolved'
        flash('Content deleted successfully.', 'success')
    
    elif action == 'ban':
        # Ban the user
        ban_duration = int(request.form.get('ban_duration', 0))
        
        if report.post_id:
            post = Post.query.get(report.post_id)
            user_to_ban = post.user
        elif report.comment_id:
            comment = Comment.query.get(report.comment_id)
            user_to_ban = comment.user
        
        user_to_ban.is_banned = True
        user_to_ban.ban_reason = reason
        if ban_duration > 0:
            user_to_ban.banned_until = datetime.utcnow() + timedelta(days=ban_duration)
        
        report.status = 'resolved'
        flash(f'User banned successfully.', 'success')
    
    elif action == 'dismiss':
        report.status = 'dismissed'
        flash('Report dismissed.', 'info')
    
    db.session.commit()
    
    create_audit_log(
        user_id=current_user.id,
        action_type='moderation_action',
        action_details={'report_id': report_id, 'action': action},
        ip_address=request.remote_addr
    )
    
    return redirect(url_for('admin_moderation'))


# Audit log routes
@app.route('/admin/audit-logs')
@login_required
@admin_required
def admin_audit_logs():
    """View audit logs"""
    page = request.args.get('page', 1, type=int)
    action_type = request.args.get('action_type', '')
    user_id = request.args.get('user_id', type=int)
    
    query = AuditLog.query
    
    if action_type:
        query = query.filter_by(action_type=action_type)
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    logs = query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=50, error_out=False)
    
    # Get unique action types for filter
    action_types = db.session.query(AuditLog.action_type).distinct().all()
    action_types = [at[0] for at in action_types]
    
    return render_template('admin/audit_logs.html', logs=logs, action_types=action_types)


@app.route('/admin/audit-logs/export')
@login_required
@admin_required
def admin_audit_logs_export():
    """Export audit logs as CSV"""
    import csv
    from io import StringIO
    from flask import make_response
    
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).all()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'User', 'Action Type', 'Details', 'IP Address'])
    
    for log in logs:
        username = log.user.username if log.user else 'System'
        writer.writerow([
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            username,
            log.action_type,
            log.action_details or '',
            log.ip_address or ''
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=audit_logs_{datetime.utcnow().strftime("%Y%m%d")}.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    return response


# Team avatar routes
@app.route('/admin/team/<int:team_id>/avatar', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_team_avatar(team_id):
    """Upload team avatar"""
    team = Team.query.get_or_404(team_id)
    form = TeamAvatarForm()
    
    if form.validate_on_submit():
        filename = save_upload(form.avatar.data, 'team_avatars')
        if filename:
            team.avatar_path = filename
            db.session.commit()
            flash('Team avatar uploaded successfully!', 'success')
            return redirect(url_for('admin_teams'))
        else:
            flash('Failed to upload avatar.', 'error')
    
    return render_template('admin/team_avatar.html', team=team, form=form)


# Site settings routes
@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_settings():
    """Site branding settings"""
    settings = get_site_settings()
    form = BrandingForm(obj=settings)
    
    if form.validate_on_submit():
        settings.site_name = form.site_name.data
        settings.primary_color = form.primary_color.data
        settings.secondary_color = form.secondary_color.data
        settings.font_family = form.font_family.data
        settings.custom_css = form.custom_css.data
        settings.updated_by_admin_id = current_user.id
        
        # Handle logo upload
        if form.logo.data:
            filename = save_upload(form.logo.data, 'branding')
            if filename:
                settings.logo_path = filename
        
        # Handle favicon upload
        if form.favicon.data:
            filename = save_upload(form.favicon.data, 'branding')
            if filename:
                settings.favicon_path = filename
        
        db.session.commit()
        
        create_audit_log(
            user_id=current_user.id,
            action_type='settings_updated',
            action_details={'site_name': settings.site_name},
            ip_address=request.remote_addr
        )
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    return render_template('admin/settings.html', form=form, settings=settings)


# Error handlers
@app.errorhandler(403)
def forbidden(e):
    """Handle 403 Forbidden errors"""
    return render_template('error.html', error='403 - Forbidden', message='You do not have permission to access this page.'), 403


@app.errorhandler(404)
def not_found(e):
    """Handle 404 Not Found errors"""
    return render_template('error.html', error='404 - Not Found', message='The page you are looking for does not exist.'), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 Internal Server errors"""
    db.session.rollback()
    return render_template('error.html', error='500 - Internal Server Error', message='Something went wrong. Please try again later.'), 500


if __name__ == '__main__':
    # Debug mode should be disabled in production
    # Set debug=True only for development via environment variable
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
