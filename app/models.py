# =======================================================
# Al-Khwarizmi University Recruitment Portal
# Designed & Developed by: Omonbayev Jaloliddin
# Telegram: https://t.me/jaloliddin_omonbaev
# =======================================================

import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'hr'
    full_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @property
    def is_admin(self):
        return self.role == 'admin'
        
    @property
    def is_hr(self):
        return self.role == 'hr'


class Faculty(db.Model):
    __tablename__ = 'faculties'
    
    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(128), nullable=False)
    name_uz = db.Column(db.String(128), nullable=False)
    
    vacancies = db.relationship('Vacancy', backref='faculty', lazy=True)

    def get_name(self, lang):
        return getattr(self, f'name_{lang}', self.name_en)


class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(128), nullable=False)
    name_uz = db.Column(db.String(128), nullable=False)
    
    vacancies = db.relationship('Vacancy', backref='department', lazy=True)

    def get_name(self, lang):
        return getattr(self, f'name_{lang}', self.name_en)


class Vacancy(db.Model):
    __tablename__ = 'vacancies'
    
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculties.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    
    # 2-Language Content
    title_en = db.Column(db.String(128), nullable=False)
    title_uz = db.Column(db.String(128), nullable=False)
    
    position_type_en = db.Column(db.String(64), nullable=False)  # e.g. Professor, Assistant, Lecturer
    position_type_uz = db.Column(db.String(64), nullable=False)
    
    description_en = db.Column(db.Text, nullable=False)
    description_uz = db.Column(db.Text, nullable=False)
    
    requirements_en = db.Column(db.Text, nullable=False)
    requirements_uz = db.Column(db.Text, nullable=False)
    
    responsibilities_en = db.Column(db.Text, nullable=False)
    responsibilities_uz = db.Column(db.Text, nullable=False)
    
    salary_en = db.Column(db.String(64), nullable=False)
    salary_uz = db.Column(db.String(64), nullable=False)
    
    employment_type_en = db.Column(db.String(64), nullable=False)  # e.g. Full-time, Part-time
    employment_type_uz = db.Column(db.String(64), nullable=False)
    
    deadline = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='open')  # 'open', 'closed'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    applications = db.relationship('Application', backref='vacancy', lazy=True)
    
    def get_title(self, lang):
        return getattr(self, f'title_{lang}', self.title_en)
        
    def get_position_type(self, lang):
        return getattr(self, f'position_type_{lang}', self.position_type_en)
        
    def get_description(self, lang):
        return getattr(self, f'description_{lang}', self.description_en)
        
    def get_requirements(self, lang):
        return getattr(self, f'requirements_{lang}', self.requirements_en)
        
    def get_responsibilities(self, lang):
        return getattr(self, f'responsibilities_{lang}', self.responsibilities_en)
        
    def get_salary(self, lang):
        return getattr(self, f'salary_{lang}', self.salary_en)
        
    def get_employment_type(self, lang):
        return getattr(self, f'employment_type_{lang}', self.employment_type_en)


class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    application_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    vacancy_id = db.Column(db.Integer, db.ForeignKey('vacancies.id'), nullable=False)
    
    # Personal Info
    full_name = db.Column(db.String(128), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.Text, nullable=False)
    
    # Education Info
    degree = db.Column(db.String(64), nullable=False)  # Bachelor, Master, PhD, etc.
    university = db.Column(db.String(128), nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    
    # Process tracking
    status = db.Column(db.String(32), default='received')  # 'received', 'under_review', 'interview', 'accepted', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    documents = db.relationship('ApplicationDocument', backref='application', cascade='all, delete-orphan', lazy=True)
    interviews = db.relationship('Interview', backref='application', cascade='all, delete-orphan', lazy=True)


class ApplicationDocument(db.Model):
    __tablename__ = 'application_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    doc_type = db.Column(db.String(32), nullable=False)  # 'passport', 'resume', 'diploma', 'certificates', 'additional'
    file_path = db.Column(db.String(256), nullable=False)
    file_name = db.Column(db.String(128), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # size in bytes


class Interview(db.Model):
    __tablename__ = 'interviews'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    interview_type = db.Column(db.String(32), nullable=False)  # 'on_site', 'online'
    date_time = db.Column(db.DateTime, nullable=False)
    location_or_link = db.Column(db.String(256), nullable=False)  # Room name/street or Zoom Link
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ContactRequest(db.Model):
    __tablename__ = 'contact_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(32), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # 'email', 'telegram'
    recipient = db.Column(db.String(256), nullable=False)
    subject = db.Column(db.String(128), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)


class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    
    @classmethod
    def get_setting(cls, key, default=None):
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default
        
    @classmethod
    def set_setting(cls, key, value):
        setting = cls.query.filter_by(key=key).first()
        if not setting:
            setting = cls(key=key, value=value)
            db.session.add(setting)
        else:
            setting.value = value
        db.session.commit()
