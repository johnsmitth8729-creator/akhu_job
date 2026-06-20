from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from flask_login import login_required, current_user
from app.models import db, User, Vacancy, Application, Interview, SystemSetting, Faculty, Department
from app.routes.utils import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/<any(en, uz):lang_code>/admin')

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Gather statistics
    hr_count = User.query.filter_by(role='hr').count()
    vacancy_count = Vacancy.query.count()
    open_vacancies = Vacancy.query.filter_by(status='open').count()
    apps_count = Application.query.count()
    apps_received = Application.query.filter_by(status='received').count()
    apps_under_review = Application.query.filter_by(status='under_review').count()
    apps_interview = Application.query.filter_by(status='interview').count()
    apps_accepted = Application.query.filter_by(status='accepted').count()
    apps_rejected = Application.query.filter_by(status='rejected').count()
    
    interviews_count = Interview.query.count()
    
    # Recent Applications
    recent_applications = Application.query.order_by(Application.created_at.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        hr_count=hr_count,
        vacancy_count=vacancy_count,
        open_vacancies=open_vacancies,
        apps_count=apps_count,
        apps_received=apps_received,
        apps_under_review=apps_under_review,
        apps_interview=apps_interview,
        apps_accepted=apps_accepted,
        apps_rejected=apps_rejected,
        interviews_count=interviews_count,
        recent_applications=recent_applications
    )

# ----------------- HR USER MANAGEMENT -----------------
@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    users = User.query.filter_by(role='hr').all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/create', methods=['POST'])
@login_required
@admin_required
def user_create():
    username = request.form.get('username')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    
    if not all([username, password, full_name, email]):
        flash('All fields are required to create an HR user.', 'danger')
        return redirect(url_for('admin.users_list'))
        
    existing = User.query.filter_by(username=username).first()
    if existing:
        flash('Username already exists.', 'danger')
        return redirect(url_for('admin.users_list'))
        
    new_user = User(
        username=username,
        role='hr',
        full_name=full_name,
        email=email
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    flash(f'HR Recruiting user "{full_name}" created successfully.', 'success')
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/users/edit/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def user_edit(user_id):
    user = User.query.get_or_404(user_id)
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not all([full_name, email]):
        flash('Name and Email are required.', 'danger')
        return redirect(url_for('admin.users_list'))
        
    user.full_name = full_name
    user.email = email
    
    if password:
        user.set_password(password)
        
    db.session.commit()
    flash(f'User "{full_name}" updated successfully.', 'success')
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def user_delete(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'hr':
        flash('Cannot delete non-HR users.', 'danger')
        return redirect(url_for('admin.users_list'))
        
    name = user.full_name
    db.session.delete(user)
    db.session.commit()
    
    flash(f'HR User "{name}" deleted successfully.', 'success')
    return redirect(url_for('admin.users_list'))

# ----------------- SYSTEM SETTINGS MANAGEMENT -----------------
@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        # Email Settings
        SystemSetting.set_setting('email_smtp_host', request.form.get('email_smtp_host', '').strip())
        SystemSetting.set_setting('email_smtp_port', request.form.get('email_smtp_port', '587').strip())
        SystemSetting.set_setting('email_smtp_user', request.form.get('email_smtp_user', '').strip())
        SystemSetting.set_setting('email_smtp_password', request.form.get('email_smtp_password', '').strip())
        SystemSetting.set_setting('email_from_address', request.form.get('email_from_address', '').strip())
        SystemSetting.set_setting('email_use_tls', request.form.get('email_use_tls', 'True').strip())
        
        # General Settings
        SystemSetting.set_setting('university_name_en', request.form.get('university_name_en', '').strip())
        SystemSetting.set_setting('university_name_uz', request.form.get('university_name_uz', '').strip())
        
        flash('System settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))
        
    # Get current setting values
    settings_data = {
        'email_smtp_host': SystemSetting.get_setting('email_smtp_host', 'localhost'),
        'email_smtp_port': SystemSetting.get_setting('email_smtp_port', '587'),
        'email_smtp_user': SystemSetting.get_setting('email_smtp_user', ''),
        'email_smtp_password': SystemSetting.get_setting('email_smtp_password', ''),
        'email_from_address': SystemSetting.get_setting('email_from_address', 'no-reply@akhu.edu.uz'),
        'email_use_tls': SystemSetting.get_setting('email_use_tls', 'True'),
        'university_name_en': SystemSetting.get_setting('university_name_en', 'Al-Khwarizmi University'),
        'university_name_uz': SystemSetting.get_setting('university_name_uz', 'Al-Xorazmiy Universiteti')
    }
    
    return render_template('admin/settings.html', settings=settings_data)

# ----------------- VACANCIES / APPLICATIONS / INTERVIEWS OVERVIEWS -----------------
@admin_bp.route('/vacancies')
@login_required
@admin_required
def vacancies():
    vacancies_list = Vacancy.query.order_by(Vacancy.created_at.desc()).all()
    faculties = Faculty.query.all()
    departments = Department.query.all()
    return render_template(
        'admin/vacancies.html',
        vacancies=vacancies_list,
        faculties=faculties,
        departments=departments
    )

@admin_bp.route('/applications')
@login_required
@admin_required
def applications():
    applications_list = Application.query.order_by(Application.created_at.desc()).all()
    return render_template('admin/applications.html', applications=applications_list)

@admin_bp.route('/interviews')
@login_required
@admin_required
def interviews():
    interviews_list = Interview.query.order_by(Interview.date_time.desc()).all()
    return render_template('admin/interviews.html', interviews=interviews_list)

@admin_bp.route('/interviews/delete/<int:interview_id>', methods=['POST'])
@login_required
@admin_required
def interview_delete(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    if interview.application.status == 'interview':
        interview.application.status = 'under_review'
    db.session.delete(interview)
    db.session.commit()
    flash('Interview has been cancelled and deleted successfully.', 'success')
    return redirect(url_for('admin.interviews'))
