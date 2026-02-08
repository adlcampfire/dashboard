"""WTForms for input validation"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError, Regexp
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
    """Post creation form"""
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=1, max=5000)])
    image = FileField('Image', validators=[FileAllowed(['png', 'jpg', 'jpeg'], 'Images only!')])
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
