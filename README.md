# 🔥 Campfire Adelaide Dashboard

A comprehensive Flask-based dashboard for managing hackathon teams and activities. This application provides authentication, team management, timeline features, and file uploads for hackathon participants.

## Features

### Authentication & User Management
- Default admin account (bennyboy635/changemeasap)
- User registration with 6-digit numeric codes
- Role-based access (Admins and Users)
- Secure password hashing with Werkzeug

### Team Management
- Create and manage hackathon teams
- Assign users to teams
- View team member lists

### Timeline Features
- **Team Timeline**: Share posts with team members
- **Global Timeline**: View posts from all teams
- Post with description and image uploads
- Automatic timestamp organization

### Profile Features
- Upload and update profile pictures
- View personal post history
- Profile information display

### Admin Dashboard
- Create and manage users
- Create and manage teams
- Generate and manage registration codes
- View system statistics

## Requirements

- Python 3.8+
- SQLite (or PostgreSQL for production)
- Modern web browser

## Installation

### 1. Clone the Repository

```bash
git clone https://github.dev/adlcampfire/dashboard
cd dashboard
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
python init_db.py
```

This will:
- Create database tables
- Create default admin account (admin/changemeasap)
- Generate 10 initial registration codes
- Create upload directories

### 5. Run the Application

#### Development Mode (with debug enabled):
```bash
export FLASK_DEBUG=True
python app.py
```

#### Production Mode (debug disabled):
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Default Credentials

**Admin Account:**
- Username: `admin`
- Password: `changemeasap`

**⚠️ IMPORTANT: Change the default password immediately after first login!**

## Usage

### For Admins

1. **Login** with admin credentials
2. **Create Teams** in the Teams section
3. **Generate Registration Codes** for participants
4. **Create Users** or share registration codes with participants
5. **Assign Users to Teams**
6. **Monitor** activity through the dashboard

### For Users

1. **Register** using a 6-digit registration code
2. **Login** with your username and password
3. **Join a Team** (admin will assign you)
4. **Create Posts** with descriptions and images
5. **View Team Timeline** to see your team's posts
6. **View Global Timeline** to see all teams' posts
7. **Update Profile Picture** in your profile

## Project Structure

```
dashboard/
├── app.py                 # Main Flask application
├── models.py              # Database models (User, Team, Post, RegistrationCode)
├── forms.py               # WTForms for validation
├── init_db.py            # Database initialization script
├── requirements.txt       # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   ├── js/
│   │   └── main.js       # Frontend JavaScript
│   └── uploads/
│       ├── profiles/     # Profile pictures
│       └── posts/        # Post images
├── templates/
│   ├── base.html         # Base template
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── error.html        # Error page
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── users.html
│   │   ├── teams.html
│   │   └── codes.html
│   └── user/
│       ├── dashboard.html
│       ├── team_timeline.html
│       ├── global_timeline.html
│       ├── profile.html
│       └── create_post.html
└── README.md
```

## Configuration

### Environment Variables

You can configure the application using environment variables:

```bash
# Secret key for session management
export SECRET_KEY='your-secret-key-here'

# Database URL (default: SQLite)
export DATABASE_URL='sqlite:///campfire.db'
# For PostgreSQL:
# export DATABASE_URL='postgresql://user:password@localhost/dbname'

# Flask Debug Mode (default: False)
export FLASK_DEBUG=True  # Only for development
```

### Production Deployment

For production deployment:

1. Set `SECRET_KEY` to a strong random value
2. Use PostgreSQL instead of SQLite
3. Ensure `FLASK_DEBUG` is not set or set to False
4. Use a production WSGI server (e.g., Gunicorn)
5. Set up proper file storage (e.g., S3)
6. Enable HTTPS
7. Configure proper backup strategies

Example with Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Security Features

- Password hashing using Werkzeug
- CSRF protection with Flask-WTF
- File upload validation (only PNG, JPG, JPEG)
- Login required decorators
- Admin-only route protection
- Secure session management
- File size limits (16MB max)

## File Upload Specifications

### Profile Pictures
- Accepted formats: PNG, JPG, JPEG
- Maximum size: 16MB
- Stored in: `static/uploads/profiles/`

### Post Images
- Accepted formats: PNG, JPG, JPEG
- Maximum size: 16MB
- Stored in: `static/uploads/posts/`

## Database Schema

### User Model
- id (Primary Key)
- username (Unique)
- password_hash
- is_admin (Boolean)
- team_id (Foreign Key)
- profile_picture
- created_at

### Team Model
- id (Primary Key)
- name (Unique)
- created_at

### Post Model
- id (Primary Key)
- user_id (Foreign Key)
- team_id (Foreign Key)
- description
- image_path
- is_global (Boolean)
- created_at

### RegistrationCode Model
- id (Primary Key)
- code (6 digits, Unique)
- is_used (Boolean)
- used_by_user_id (Foreign Key)
- created_at

## API Endpoints

### Authentication
- `GET/POST /login` - Login page
- `GET/POST /register` - Registration page
- `GET /logout` - Logout

### Admin Routes
- `GET /admin` - Admin dashboard
- `GET/POST /admin/users` - Manage users
- `POST /admin/users/assign` - Assign user to team
- `GET/POST /admin/teams` - Manage teams
- `GET/POST /admin/codes` - Manage registration codes
- `GET /admin/codes/reset/<id>` - Reset registration code

### User Routes
- `GET /dashboard` - User dashboard
- `GET/POST /profile` - User profile
- `GET /timeline/team` - Team timeline
- `GET /timeline/global` - Global timeline
- `GET/POST /post/create` - Create new post

## Troubleshooting

### Database Issues

If you encounter database issues:

```bash
# Remove existing database
rm campfire.db

# Reinitialize
python init_db.py
```

### Upload Directory Permissions

Ensure upload directories have proper write permissions:

```bash
chmod -R 755 static/uploads/
```

### Port Already in Use

If port 5000 is already in use:

```bash
# Change port in app.py or use environment variable
export FLASK_RUN_PORT=5001
python app.py
```

## Development

### Running in Debug Mode

Debug mode is enabled by default in `app.py`. For production, set `debug=False`.

### Adding New Features

1. Update models in `models.py`
2. Create/update forms in `forms.py`
3. Add routes in `app.py`
4. Create templates in `templates/`
5. Update styles in `static/css/style.css`

## License

This project is licensed under the MIT License.

## Support

For issues or questions:
1. Check this README
2. Review error messages in the browser
3. Check application logs
4. Contact the development team

## Contributors

- Campfire Adelaide Team

## Changelog

### Version 1.0.0 (2026-02-08)
- Initial release
- Authentication and user management
- Team management
- Timeline features (team and global)
- Profile pictures
- Admin dashboard
- File upload functionality

---

**Note:** This is a hackathon management tool. Ensure proper security measures are in place before deploying to production.