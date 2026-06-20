# =======================================================
# Al-Khwarizmi University Recruitment Portal
# Designed & Developed by: Omonbayev Jaloliddin
# =======================================================

import os
import io
import unittest
import datetime

# Override the database URL environment variable before importing/creating the app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from app.models import db, User, Faculty, Department, Vacancy, Application, ContactRequest, SystemSetting

class PortalTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        # Enable testing configurations
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        # Recreate tables and seed database
        db.create_all()
        self.seed_test_db()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def seed_test_db(self):
        # Settings
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
            
        # Admin User
        admin = User(
            username='jaloliddin',
            role='admin',
            full_name='Jaloliddin Omonbayev',
            email='jaloliddin@akhu.edu.uz'
        )
        admin.set_password('Qwer1234@')
        db.session.add(admin)
        
        # HR User
        hr = User(
            username='hr_staff',
            role='hr',
            full_name='HR Recruiter',
            email='hr@akhu.edu.uz'
        )
        hr.set_password('hr123')
        db.session.add(hr)
        
        # Faculty & Department
        self.test_fac = Faculty(name_en='Computer Science', name_uz='Kompyuter ilmlari')
        self.test_dept = Department(name_en='Software Engineering', name_uz='Dasturiy injiniring')
        db.session.add(self.test_fac)
        db.session.add(self.test_dept)
        
        db.session.commit()

    def login_client(self, username, password):
        return self.client.post('/en/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def test_file_validation_rules(self):
        """Verify that security rules correctly filter uploads"""
        allowed_func = self.app.config['ALLOWED_FILE_FUNC']
        
        # Safe extensions
        self.assertTrue(allowed_func('resume.pdf'))
        self.assertTrue(allowed_func('passport.jpg'))
        self.assertTrue(allowed_func('diploma.docx'))
        self.assertTrue(allowed_func('cert.png'))
        self.assertTrue(allowed_func('extra.doc'))
        
        # Blocked / Dangerous extensions
        self.assertFalse(allowed_func('script.exe'))
        self.assertFalse(allowed_func('payload.bat'))
        self.assertFalse(allowed_func('command.cmd'))
        self.assertFalse(allowed_func('setup.sh'))
        self.assertFalse(allowed_func('virus.scr'))

    def test_database_models_exist(self):
        """Check database schema and confirm tables map correctly"""
        self.assertIsNotNone(User.query.first())
        self.assertIsNotNone(SystemSetting.query.first())
        self.assertEqual(Faculty.query.count(), 1)
        self.assertEqual(Department.query.count(), 1)
        self.assertEqual(Vacancy.query.count(), 0)
        self.assertEqual(Application.query.count(), 0)
        self.assertEqual(ContactRequest.query.count(), 0)

    def test_language_redirect(self):
        """Verify root path / redirects to /en/"""
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/en/'))

    def test_public_routes(self):
        """Verify that public endpoints return successful responses"""
        # Home
        response = self.client.get('/en/')
        self.assertEqual(response.status_code, 200)
        
        # Status tracker
        response = self.client.get('/en/status')
        self.assertEqual(response.status_code, 200)
        
        # Contact
        response = self.client.get('/en/contact')
        self.assertEqual(response.status_code, 200)
        
        # Login page
        response = self.client.get('/en/login')
        self.assertEqual(response.status_code, 200)

    def test_authentication_flow(self):
        """Test login success, redirect role based, and logout"""
        # Admin login
        response = self.login_client('jaloliddin', 'Qwer1234@')
        self.assertIn(b'Jaloliddin Omonbayev', response.data)
        self.assertIn(b'Dashboard Statistics', response.data)
        
        # Logout
        response = self.client.get('/en/logout', follow_redirects=True)
        self.assertIn(b'You have been logged out successfully.', response.data)
        
        # HR login
        response = self.login_client('hr_staff', 'hr123')
        self.assertIn(b'HR Recruiter', response.data)
        self.assertIn(b'Overview Statistics', response.data)

    def test_admin_settings_update(self):
        """Verify that SMTP credentials and university details can be updated"""
        # Log in as admin
        self.login_client('jaloliddin', 'Qwer1234@')
        
        # Update settings
        response = self.client.post('/en/admin/settings', data={
            'email_smtp_host': 'smtp.gmail.com',
            'email_smtp_port': '465',
            'email_smtp_user': 'test@gmail.com',
            'email_smtp_password': 'secret_password',
            'email_from_address': 'notifications@akhu.edu.uz',
            'email_use_tls': 'True',
            'university_name_en': 'New Al-Khwarizmi Uni',
            'university_name_uz': 'Yangi Al-Xorazmiy Uni'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'System settings updated successfully.', response.data)
        
        # Verify db updates
        self.assertEqual(SystemSetting.get_setting('email_smtp_host'), 'smtp.gmail.com')
        self.assertEqual(SystemSetting.get_setting('university_name_en'), 'New Al-Khwarizmi Uni')

    def test_vacancy_creation_and_validation(self):
        """Test vacancy creation rules: Faculty/Department selection is mandatory"""
        # Log in as HR
        self.login_client('hr_staff', 'hr123')
        
        # 1. Try creating a vacancy without BOTH faculty and department (Should fail)
        response = self.client.post('/en/hr_recruiting/vacancies/create', data={
            'deadline': '2026-12-31',
            'title_en': 'Lecturer in Software Engineering',
            'title_uz': 'Dasturiy injiniring o\'qituvchisi',
            'position_type_en': 'Lecturer',
            'position_type_uz': 'O\'qituvchi',
            'employment_type_en': 'Full-time',
            'employment_type_uz': 'To\'liq',
            'salary_en': 'Negotiable',
            'salary_uz': 'Kelishilgan',
            'description_en': 'Teach programming courses.',
            'description_uz': 'Dasturlashdan dars berish.',
            'requirements_en': 'MSc in CS.',
            'requirements_uz': 'Katta tajriba.',
            'responsibilities_en': 'Deliver lectures.',
            'responsibilities_uz': 'Darslarni tashkil qilish.'
        }, follow_redirects=True)
        
        self.assertIn(b'Please select at least academic Faculty or Department.', response.data)
        self.assertEqual(Vacancy.query.count(), 0)

        # 2. Create vacancy with ONLY Faculty (Should succeed)
        response = self.client.post('/en/hr_recruiting/vacancies/create', data={
            'faculty_id': str(self.test_fac.id),
            'deadline': '2026-12-31',
            'title_en': 'Professor in AI',
            'title_uz': 'AI bo\'yicha professor',
            'position_type_en': 'Professor',
            'position_type_uz': 'Professor',
            'employment_type_en': 'Full-time',
            'employment_type_uz': 'To\'liq',
            'salary_en': 'Negotiable',
            'salary_uz': 'Kelishilgan',
            'description_en': 'Research in AI.',
            'description_uz': 'AI sohasida tadqiqot.',
            'requirements_en': 'PhD.',
            'requirements_uz': 'Ilmiy daraja.',
            'responsibilities_en': 'Lead research.',
            'responsibilities_uz': 'Tadqiqot olib borish.'
        }, follow_redirects=True)
        
        self.assertEqual(Vacancy.query.count(), 1)
        vacancy = Vacancy.query.first()
        self.assertEqual(vacancy.faculty_id, self.test_fac.id)
        self.assertIsNone(vacancy.department_id)

    def test_application_submission_and_tracking(self):
        """Submit a candidate dossier application and test tracking via code"""
        # Create a test vacancy
        vac = Vacancy(
            faculty_id=self.test_fac.id,
            deadline=datetime.date(2026, 12, 31),
            title_en='Test Position',
            title_uz='Test Lavozim',
            position_type_en='Lecturer',
            position_type_uz='O\'qituvchi',
            employment_type_en='Part-time',
            employment_type_uz='Yarim bandlik',
            salary_en='Negotiable',
            salary_uz='Kelishilgan',
            description_en='Details',
            description_uz='Tafsilotlar',
            requirements_en='Reqs',
            requirements_uz='Talablar',
            responsibilities_en='Resps',
            responsibilities_uz='Vazifalar',
            status='open'
        )
        db.session.add(vac)
        db.session.commit()
        
        # Prepare mock file uploads
        passport_file = (io.BytesIO(b"passport content"), "passport.pdf")
        resume_file = (io.BytesIO(b"resume content"), "resume.docx")
        diploma_file = (io.BytesIO(b"diploma content"), "diploma.pdf")
        
        # Submit application to the correct endpoint /en/apply/<vacancy_id>
        response = self.client.post(f'/en/apply/{vac.id}', data={
            'full_name': 'Ali Valiyev',
            'birth_date': '1995-05-15',
            'phone': '+998901234567',
            'email': 'ali@gmail.com',
            'address': 'Tashkent, Uzbekistan',
            'degree': 'Master',
            'university': 'AKHU',
            'graduation_year': '2018',
            'passport': passport_file,
            'resume': resume_file,
            'diploma': diploma_file
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Your application has been submitted successfully!', response.data)
        
        # Verify db entry
        self.assertEqual(Application.query.count(), 1)
        app_record = Application.query.first()
        self.assertEqual(app_record.full_name, 'Ali Valiyev')
        self.assertEqual(app_record.status, 'received')
        
        # Verify application status can be tracked via status page
        response = self.client.post('/en/status', data={
            'app_num': app_record.application_number,
            'email_addr': 'ali@gmail.com'
        }, follow_redirects=True)
        self.assertIn(b'Ali Valiyev', response.data)
        self.assertIn(b'Received', response.data)

if __name__ == '__main__':
    unittest.main()
