"""WTForms for input validation"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import (StringField, PasswordField, BooleanField, TextAreaField, 
                     SelectField, SubmitField, IntegerField, DateTimeField)
from wtforms.validators import DataRequired, Length, ValidationError, Regexp, Optional, NumberRange, URL
from models import User, Team, RegistrationCode


class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    """User registration form"""
    code = StringField('Registration Code', validators=[
        DataRequired(),
        Length(min=6, max=6),
        Regexp(r'^\d{6}$', message='Registration code must be 6 digits')
    ])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Check if username already exists"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_code(self, code):
        """Check if registration code is valid and unused"""
        reg_code = RegistrationCode.query.filter_by(code=code.data).first()
        if not reg_code:
            raise ValidationError('Invalid registration code.')
        if reg_code.is_used:
            raise ValidationError('This registration code has already been used.')


class PostForm(FlaskForm):
    """Post creation form with multi-image and video support"""
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=1, max=5000)])
    image = FileField('Image (Legacy)', validators=[FileAllowed(['png', 'jpg', 'jpeg'], 'Images only!')])
    images = MultipleFileField('Images (up to 10)', validators=[FileAllowed(['png', 'jpg', 'jpeg'], 'Images only!')])
    video = FileField('Video', validators=[FileAllowed(['mp4', 'webm', 'mov'], 'Videos only!')])
    is_global = BooleanField('Post to Global Timeline')
    submit = SubmitField('Create Post')


class ProfilePictureForm(FlaskForm):
    """Profile picture upload form"""
    profile_picture = FileField('Profile Picture', validators=[
        DataRequired(),
        FileAllowed(['png', 'jpg', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Upload')


class CreateUserForm(FlaskForm):
    """Admin form to create new users"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    is_admin = BooleanField('Admin User')
    team_id = SelectField('Team', coerce=int, validators=[])
    submit = SubmitField('Create User')
    
    def validate_username(self, username):
        """Check if username already exists"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')


class CreateTeamForm(FlaskForm):
    """Admin form to create new teams"""
    name = StringField('Team Name', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Create Team')
    
    def validate_name(self, name):
        """Check if team name already exists"""
        team = Team.query.filter_by(name=name.data).first()
        if team:
            raise ValidationError('Team name already exists. Please choose a different one.')


class AssignTeamForm(FlaskForm):
    """Admin form to assign users to teams"""
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    team_id = SelectField('Team', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign to Team')


class GenerateCodesForm(FlaskForm):
    """Admin form to generate registration codes"""
    count = SelectField('Number of Codes', 
                       choices=[(5, '5'), (10, '10'), (20, '20'), (50, '50')],
                       coerce=int,
                       validators=[DataRequired()])
    submit = SubmitField('Generate Codes')


class CommentForm(FlaskForm):
    """Form for adding comments to posts"""
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('Post Comment')


class VoteForm(FlaskForm):
    """Form for judge voting"""
    innovation_score = IntegerField('Innovation (1-10)', validators=[
        DataRequired(), 
        NumberRange(min=1, max=10, message='Score must be between 1 and 10')
    ])
    implementation_score = IntegerField('Implementation (1-10)', validators=[
        DataRequired(), 
        NumberRange(min=1, max=10, message='Score must be between 1 and 10')
    ])
    design_score = IntegerField('Design (1-10)', validators=[
        DataRequired(), 
        NumberRange(min=1, max=10, message='Score must be between 1 and 10')
    ])
    presentation_score = IntegerField('Presentation (1-10)', validators=[
        DataRequired(), 
        NumberRange(min=1, max=10, message='Score must be between 1 and 10')
    ])
    comments = TextAreaField('Comments (Optional)', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Submit Vote')


class AnnouncementForm(FlaskForm):
    """Form for creating announcements"""
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=200)])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=1, max=5000)])
    announcement_type = SelectField('Type', 
                                   choices=[('info', 'Info'), ('warning', 'Warning'), 
                                           ('success', 'Success'), ('important', 'Important')],
                                   validators=[DataRequired()])
    is_pinned = BooleanField('Pin Announcement')
    expires_at = DateTimeField('Expires At (Optional)', format='%Y-%m-%d %H:%M:%S', validators=[Optional()])
    submit = SubmitField('Create Announcement')


class ReportForm(FlaskForm):
    """Form for reporting posts or comments"""
    reason = SelectField('Reason', 
                        choices=[('spam', 'Spam'), ('inappropriate', 'Inappropriate'), 
                                ('offensive', 'Offensive'), ('other', 'Other')],
                        validators=[DataRequired()])
    details = TextAreaField('Details (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Submit Report')


class ProfileUpdateForm(FlaskForm):
    """Form for updating user profile"""
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['png', 'jpg', 'jpeg'], 'Images only!')
    ])
    github_url = StringField('GitHub URL', validators=[Optional(), URL()])
    linkedin_url = StringField('LinkedIn URL', validators=[Optional(), URL()])
    twitter_url = StringField('Twitter URL', validators=[Optional(), URL()])
    portfolio_url = StringField('Portfolio URL', validators=[Optional(), URL()])
    submit = SubmitField('Update Profile')


class TeamAvatarForm(FlaskForm):
    """Form for uploading team avatar"""
    avatar = FileField('Team Avatar', validators=[
        DataRequired(),
        FileAllowed(['png', 'jpg', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Upload Avatar')


class BrandingForm(FlaskForm):
    """Form for site branding settings"""
    site_name = StringField('Site Name', validators=[DataRequired(), Length(min=1, max=100)])
    logo = FileField('Logo', validators=[FileAllowed(['png', 'jpg', 'jpeg'], 'Images only!')])
    favicon = FileField('Favicon', validators=[FileAllowed(['png', 'ico'], 'PNG or ICO only!')])
    primary_color = StringField('Primary Color', validators=[
        DataRequired(), 
        Regexp(r'^#[0-9A-Fa-f]{6}$', message='Must be a valid hex color (e.g., #FF6B35)')
    ])
    secondary_color = StringField('Secondary Color', validators=[
        DataRequired(), 
        Regexp(r'^#[0-9A-Fa-f]{6}$', message='Must be a valid hex color (e.g., #004E89)')
    ])
    font_family = StringField('Font Family', validators=[DataRequired(), Length(min=1, max=100)])
    custom_css = TextAreaField('Custom CSS', validators=[Optional()])
    submit = SubmitField('Update Branding')


class ModerationActionForm(FlaskForm):
    """Form for moderation actions"""
    action = SelectField('Action', 
                        choices=[('hide', 'Hide Content'), ('delete', 'Delete Content'), 
                                ('warn', 'Warn User'), ('ban', 'Ban User')],
                        validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[DataRequired(), Length(min=1, max=500)])
    ban_duration = IntegerField('Ban Duration (days, 0 for permanent)', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Execute Action')
