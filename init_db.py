"""Initialize database and create default admin account"""
import os
import random
import string
from app import app, db
from models import User, Team, RegistrationCode


def init_database():
    """Initialize the database and create default data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Check if default admin already exists
        admin = User.query.filter_by(username='bennyboy635').first()
        if not admin:
            # Create default admin account
            admin = User(username='bennyboy635', is_admin=True)
            admin.set_password('changemeasap')
            db.session.add(admin)
            db.session.commit()
            print("✓ Default admin account created (bennyboy635/changemeasap)")
        else:
            print("ℹ Default admin account already exists")
        
        # Generate initial registration codes if none exist
        existing_codes = RegistrationCode.query.count()
        if existing_codes == 0:
            print("Generating 10 initial registration codes...")
            codes = []
            for _ in range(10):
                # Generate unique 6-digit code
                while True:
                    code = ''.join(random.choices(string.digits, k=6))
                    if code not in codes and not RegistrationCode.query.filter_by(code=code).first():
                        break
                
                reg_code = RegistrationCode(code=code)
                db.session.add(reg_code)
                codes.append(code)
                print(f"  - {code}")
            
            db.session.commit()
            print("✓ Registration codes generated")
        else:
            print(f"ℹ {existing_codes} registration codes already exist")
        
        # Create upload directories if they don't exist
        upload_dirs = [
            os.path.join('static', 'uploads', 'profiles'),
            os.path.join('static', 'uploads', 'posts')
        ]
        for dir_path in upload_dirs:
            os.makedirs(dir_path, exist_ok=True)
        print("✓ Upload directories verified")
        
        print("\n" + "="*50)
        print("Database initialization complete!")
        print("="*50)
        print("\nDefault Admin Credentials:")
        print("  Username: bennyboy635")
        print("  Password: changemeasap")
        print("\nPlease change the default password after first login!")


if __name__ == '__main__':
    init_database()
