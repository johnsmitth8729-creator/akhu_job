# =======================================================
# Al-Khwarizmi University Recruitment Portal
# Designed & Developed by: Omonbayev Jaloliddin
# Telegram: https://t.me/jaloliddin_omonbaev
# =======================================================

import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.models import db, User, SystemSetting

def seed_db():
    app = create_app()
    with app.app_context():
        # Create all tables if they don't exist
        print("Recreating database tables...")
        db.drop_all()
        db.create_all()
        
        print("Seeding default system settings...")
        settings = [
            ('email_smtp_host', 'localhost'),
            ('email_smtp_port', '587'),
            ('email_smtp_user', ''),
            ('email_smtp_password', ''),
            ('email_from_address', 'no-reply@akhu.edu.uz'),
            ('email_use_tls', 'True'),
            ('university_name_en', 'Al-Khwarizmi University'),
            ('university_name_uz', 'Al-Xorazmiy Universiteti')
        ]
        for key, val in settings:
            SystemSetting.set_setting(key, val)
            
        print("Seeding default users from environment configurations...")
        # Admin User
        admin_username = os.environ.get('ADMIN_USERNAME', 'jaloliddin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'Qwer1234@')
        admin_email = os.environ.get('ADMIN_EMAIL', 'jaloliddin@akhu.edu.uz')
        admin_fullname = os.environ.get('ADMIN_FULL_NAME', 'Jaloliddin Omonbayev')
        
        admin = User(
            username=admin_username,
            role='admin',
            full_name=admin_fullname,
            email=admin_email
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        
        # HR User
        hr_username = os.environ.get('HR_USERNAME', 'hr_staff')
        hr_password = os.environ.get('HR_PASSWORD', 'hr123')
        hr_email = os.environ.get('HR_EMAIL', 'hr@akhu.edu.uz')
        hr_fullname = os.environ.get('HR_FULL_NAME', 'HR Recruiter')
        
        hr = User(
            username=hr_username,
            role='hr',
            full_name=hr_fullname,
            email=hr_email
        )
        hr.set_password(hr_password)
        db.session.add(hr)
        
        db.session.commit()
        print("Database initialized successfully!")
        print(f"Admin User: {admin_username}")
        print(f"HR User: {hr_username}")

if __name__ == '__main__':
    seed_db()
