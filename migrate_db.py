"""Database migration script to add new features"""
import os
from app import app, db
from models import (User, Team, Post, RegistrationCode, Reaction, Comment, 
                    Mention, Vote, Announcement, PostMedia, Report, AuditLog, SiteSettings)


def migrate_database():
    """Run database migrations for new features"""
    with app.app_context():
        print("Starting database migration...")
        
        # Create all new tables
        db.create_all()
        print("✓ All tables created/updated")
        
        # Create default site settings if not exist
        site_settings = SiteSettings.query.first()
        if not site_settings:
            site_settings = SiteSettings(
                site_name='Campfire Adelaide Dashboard',
                primary_color='#FF6B35',
                secondary_color='#004E89',
                font_family='Inter'
            )
            db.session.add(site_settings)
            db.session.commit()
            print("✓ Default site settings created")
        else:
            print("ℹ Site settings already exist")
        
        # Create upload directories for new features
        upload_dirs = [
            os.path.join('static', 'uploads', 'profiles'),
            os.path.join('static', 'uploads', 'posts'),
            os.path.join('static', 'uploads', 'videos'),
            os.path.join('static', 'uploads', 'teams'),
            os.path.join('static', 'uploads', 'branding')
        ]
        for dir_path in upload_dirs:
            os.makedirs(dir_path, exist_ok=True)
        print("✓ Upload directories verified")
        
        print("\n" + "="*50)
        print("Database migration complete!")
        print("="*50)
        print("\nNew features added:")
        print("  - Reactions system")
        print("  - Comments system")
        print("  - @Mentions system")
        print("  - Voting system for judges")
        print("  - Announcements system")
        print("  - Multi-image and video posts")
        print("  - Content moderation")
        print("  - Audit logging")
        print("  - Dark mode support")
        print("  - Social links")
        print("  - Team avatars")
        print("  - Branding/theming system")


if __name__ == '__main__':
    migrate_database()
