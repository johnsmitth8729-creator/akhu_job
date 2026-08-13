import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, Response
from flask_login import login_required, current_user
from app.models import db, User, Vacancy, Application, Interview, SystemSetting, Faculty, Department
from app.routes.utils import admin_required
from app.routes.reports_helper import get_reports_data, generate_applications_csv, generate_vacancies_csv

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
    page = request.args.get('page', 1, type=int)
    year = request.args.get('year', str(datetime.date.today().year))
    status = request.args.get('status', 'all')
    
    query = Vacancy.query
    if year and year != 'all':
        try:
            yr = int(year)
            query = query.filter(Vacancy.created_at >= datetime.date(yr, 1, 1), Vacancy.created_at <= datetime.date(yr, 12, 31))
        except ValueError:
            pass
    if status and status != 'all':
        query = query.filter(Vacancy.status == status)
        
    pagination = query.order_by(Vacancy.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    vacs = pagination.items
    
    faculties = Faculty.query.all()
    departments = Department.query.all()
    available_years = list(range(2026, datetime.date.today().year + 1))
    
    return render_template(
        'admin/vacancies.html',
        vacancies=vacs,
        pagination=pagination,
        faculties=faculties,
        departments=departments,
        selected_year=year,
        selected_status=status,
        available_years=available_years
    )

@admin_bp.route('/applications')
@login_required
@admin_required
def applications():
    page = request.args.get('page', 1, type=int)
    year = request.args.get('year', str(datetime.date.today().year))
    status = request.args.get('status', 'all')
    
    query = Application.query
    if year and year != 'all':
        try:
            yr = int(year)
            start_date = datetime.datetime(yr, 1, 1, 0, 0, 0)
            end_date = datetime.datetime(yr, 12, 31, 23, 59, 59)
            query = query.filter(Application.created_at >= start_date, Application.created_at <= end_date)
        except ValueError:
            pass
    if status and status != 'all':
        query = query.filter(Application.status == status)
        
    pagination = query.order_by(Application.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    apps = pagination.items
    
    available_years = list(range(2026, datetime.date.today().year + 1))
    
    return render_template(
        'admin/applications.html',
        applications=apps,
        pagination=pagination,
        selected_year=year,
        selected_status=status,
        available_years=available_years
    )

@admin_bp.route('/interviews')
@login_required
@admin_required
def interviews():
    page = request.args.get('page', 1, type=int)
    year = request.args.get('year', str(datetime.date.today().year))
    
    query = Interview.query
    if year and year != 'all':
        try:
            yr = int(year)
            query = query.filter(Interview.date_time >= datetime.datetime(yr, 1, 1), Interview.date_time <= datetime.datetime(yr, 12, 31, 23, 59, 59))
        except ValueError:
            pass
            
    pagination = query.order_by(Interview.date_time.desc()).paginate(page=page, per_page=10, error_out=False)
    interviews_list = pagination.items
    
    available_years = list(range(2026, datetime.date.today().year + 1))
    
    return render_template(
        'admin/interviews.html',
        interviews=interviews_list,
        pagination=pagination,
        selected_year=year,
        available_years=available_years
    )

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

# ----------------- REPORTS & ANALYTICS -----------------
@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    date_preset = request.args.get('date_preset', 'all')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    faculty_id = request.args.get('faculty_id', '')
    department_id = request.args.get('department_id', '')
    vacancy_id = request.args.get('vacancy_id', '')
    status = request.args.get('status', 'all')

    data = get_reports_data(
        start_date=start_date,
        end_date=end_date,
        faculty_id=faculty_id,
        department_id=department_id,
        vacancy_id=vacancy_id,
        status=status,
        date_preset=date_preset,
        lang_code=g.lang_code
    )

    return render_template('admin/reports.html', **data)

@admin_bp.route('/reports/export/applications')
@login_required
@admin_required
def export_applications_csv():
    date_preset = request.args.get('date_preset', 'all')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    faculty_id = request.args.get('faculty_id', '')
    department_id = request.args.get('department_id', '')
    vacancy_id = request.args.get('vacancy_id', '')
    status = request.args.get('status', 'all')

    data = get_reports_data(
        start_date=start_date,
        end_date=end_date,
        faculty_id=faculty_id,
        department_id=department_id,
        vacancy_id=vacancy_id,
        status=status,
        date_preset=date_preset,
        lang_code=g.lang_code
    )

    csv_data = generate_applications_csv(data['filtered_applications'], lang_code=g.lang_code)
    filename = f"akhu_applications_report_{datetime.date.today().strftime('%Y%m%d')}.csv"
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

@admin_bp.route('/reports/export/vacancies')
@login_required
@admin_required
def export_vacancies_csv():
    date_preset = request.args.get('date_preset', 'all')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    faculty_id = request.args.get('faculty_id', '')
    department_id = request.args.get('department_id', '')
    vacancy_id = request.args.get('vacancy_id', '')
    status = request.args.get('status', 'all')

    data = get_reports_data(
        start_date=start_date,
        end_date=end_date,
        faculty_id=faculty_id,
        department_id=department_id,
        vacancy_id=vacancy_id,
        status=status,
        date_preset=date_preset,
        lang_code=g.lang_code
    )

    csv_data = generate_vacancies_csv(data['vacancies_performance'], lang_code=g.lang_code)
    filename = f"akhu_vacancies_performance_report_{datetime.date.today().strftime('%Y%m%d')}.csv"
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


