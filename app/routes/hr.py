import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from flask_login import login_required, current_user
from app.models import db, Vacancy, Faculty, Department, Application, Interview, ContactRequest
from app.routes.utils import hr_required
from app.routes.notifications import send_email_notification

hr_bp = Blueprint('hr', __name__, url_prefix='/<any(en, uz):lang_code>/hr_recruiting')

@hr_bp.route('/')
@login_required
@hr_required
def dashboard():
    # Gather statistics
    vacancies_count = Vacancy.query.count()
    active_vacancies = Vacancy.query.filter_by(status='open').count()
    total_apps = Application.query.count()
    pending_apps = Application.query.filter_by(status='received').count()
    under_review_apps = Application.query.filter_by(status='under_review').count()
    interviews_scheduled = Interview.query.count()
    unresolved_contacts = ContactRequest.query.filter_by(is_resolved=False).count()
    
    # Recent applications for HR review
    recent_apps = Application.query.order_by(Application.created_at.desc()).limit(8).all()
    
    return render_template(
        'hr/dashboard.html',
        vacancies_count=vacancies_count,
        active_vacancies=active_vacancies,
        total_apps=total_apps,
        pending_apps=pending_apps,
        under_review_apps=under_review_apps,
        interviews_scheduled=interviews_scheduled,
        unresolved_contacts=unresolved_contacts,
        recent_apps=recent_apps
    )

# ----------------- VACANCY CRUD -----------------
@hr_bp.route('/vacancies')
@login_required
@hr_required
def vacancies_list():
    vacancies = Vacancy.query.order_by(Vacancy.created_at.desc()).all()
    faculties = Faculty.query.all()
    departments = Department.query.all()
    return render_template(
        'hr/vacancies.html',
        vacancies=vacancies,
        faculties=faculties,
        departments=departments
    )

@hr_bp.route('/vacancies/create', methods=['GET', 'POST'])
@login_required
@hr_required
def vacancy_create():
    if request.method == 'POST':
        faculty_id = request.form.get('faculty_id') or None
        department_id = request.form.get('department_id') or None
        deadline_str = request.form.get('deadline')
        
        # Gather multilingual fields
        title_en = request.form.get('title_en')
        title_uz = request.form.get('title_uz')
        
        position_type_en = request.form.get('position_type_en')
        position_type_uz = request.form.get('position_type_uz')
        
        description_en = request.form.get('description_en')
        description_uz = request.form.get('description_uz')
        
        requirements_en = request.form.get('requirements_en')
        requirements_uz = request.form.get('requirements_uz')
        
        responsibilities_en = request.form.get('responsibilities_en')
        responsibilities_uz = request.form.get('responsibilities_uz')
        
        salary_en = request.form.get('salary_en')
        salary_uz = request.form.get('salary_uz')
        
        employment_type_en = request.form.get('employment_type_en')
        employment_type_uz = request.form.get('employment_type_uz')
        
        # Verify required
        if not all([deadline_str, 
                    title_en, title_uz, 
                    position_type_en, position_type_uz, 
                    description_en, description_uz, 
                    requirements_en, requirements_uz,
                    responsibilities_en, responsibilities_uz,
                    salary_en, salary_uz,
                    employment_type_en, employment_type_uz]):
            if g.lang_code == 'uz':
                flash('Iltimos, barcha maydonlarni ingliz va o\'zbek tillarida to\'ldiring.', 'danger')
            else:
                flash('Please fill out all fields in English and Uzbek.', 'danger')
            return redirect(url_for('hr.vacancy_create'))

        if faculty_id and department_id:
            if g.lang_code == 'uz':
                flash('Fakultet va Bo\'limni bir vaqtda tanlash mumkin emas. Faqat bittasini tanlang.', 'danger')
            else:
                flash('You cannot select both Faculty and Department at the same time. Please choose only one.', 'danger')
            return redirect(url_for('hr.vacancy_create'))

        if not faculty_id and not department_id:
            if g.lang_code == 'uz':
                flash('Iltimos, Fakultet yoki Bo\'limdan kamida bittasini tanlang.', 'danger')
            else:
                flash('Please select at least one: Academic Faculty or Department.', 'danger')
            return redirect(url_for('hr.vacancy_create'))
            
        try:
            deadline = datetime.datetime.strptime(deadline_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid deadline date format.', 'danger')
            return redirect(url_for('hr.vacancy_create'))
            
        new_vacancy = Vacancy(
            faculty_id=int(faculty_id) if faculty_id else None,
            department_id=int(department_id) if department_id else None,
            deadline=deadline,
            title_en=title_en,
            title_uz=title_uz,
            position_type_en=position_type_en,
            position_type_uz=position_type_uz,
            description_en=description_en,
            description_uz=description_uz,
            requirements_en=requirements_en,
            requirements_uz=requirements_uz,
            responsibilities_en=responsibilities_en,
            responsibilities_uz=responsibilities_uz,
            salary_en=salary_en,
            salary_uz=salary_uz,
            employment_type_en=employment_type_en,
            employment_type_uz=employment_type_uz,
            status='open'
        )
        db.session.add(new_vacancy)
        db.session.commit()
        
        flash('Vacancy created successfully.', 'success')
        return redirect(url_for('hr.vacancies_list'))
        
    faculties = Faculty.query.all()
    departments = Department.query.all()
    return render_template('hr/vacancy_form.html', faculties=faculties, departments=departments, vacancy=None)

@hr_bp.route('/vacancies/edit/<int:vacancy_id>', methods=['GET', 'POST'])
@login_required
@hr_required
def vacancy_edit(vacancy_id):
    vacancy = Vacancy.query.get_or_404(vacancy_id)
    
    if request.method == 'POST':
        faculty_id = request.form.get('faculty_id') or None
        department_id = request.form.get('department_id') or None
        deadline_str = request.form.get('deadline')
        status = request.form.get('status')
        
        # Multilingual fields
        title_en = request.form.get('title_en')
        title_uz = request.form.get('title_uz')
        
        position_type_en = request.form.get('position_type_en')
        position_type_uz = request.form.get('position_type_uz')
        
        description_en = request.form.get('description_en')
        description_uz = request.form.get('description_uz')
        
        requirements_en = request.form.get('requirements_en')
        requirements_uz = request.form.get('requirements_uz')
        
        responsibilities_en = request.form.get('responsibilities_en')
        responsibilities_uz = request.form.get('responsibilities_uz')
        
        salary_en = request.form.get('salary_en')
        salary_uz = request.form.get('salary_uz')
        
        employment_type_en = request.form.get('employment_type_en')
        employment_type_uz = request.form.get('employment_type_uz')
        
        if not all([deadline_str, status,
                    title_en, title_uz, 
                    position_type_en, position_type_uz, 
                    description_en, description_uz, 
                    requirements_en, requirements_uz,
                    responsibilities_en, responsibilities_uz,
                    salary_en, salary_uz,
                    employment_type_en, employment_type_uz]):
            if g.lang_code == 'uz':
                flash('Iltimos, barcha majburiy maydonlarni to\'ldiring.', 'danger')
            else:
                flash('All required fields must be filled in.', 'danger')
            return redirect(url_for('hr.vacancy_edit', vacancy_id=vacancy_id))

        if faculty_id and department_id:
            if g.lang_code == 'uz':
                flash('Fakultet va Bo\'limni bir vaqtda tanlash mumkin emas. Faqat bittasini tanlang.', 'danger')
            else:
                flash('You cannot select both Faculty and Department at the same time. Please choose only one.', 'danger')
            return redirect(url_for('hr.vacancy_edit', vacancy_id=vacancy_id))

        if not faculty_id and not department_id:
            if g.lang_code == 'uz':
                flash('Iltimos, Fakultet yoki Bo\'limdan kamida bittasini tanlang.', 'danger')
            else:
                flash('Please select at least one: Academic Faculty or Department.', 'danger')
            return redirect(url_for('hr.vacancy_edit', vacancy_id=vacancy_id))
            
        try:
            deadline = datetime.datetime.strptime(deadline_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid deadline date format.', 'danger')
            return redirect(url_for('hr.vacancy_edit', vacancy_id=vacancy_id))
            
        # Update vacancy
        vacancy.faculty_id = int(faculty_id) if faculty_id else None
        vacancy.department_id = int(department_id) if department_id else None
        vacancy.deadline = deadline
        vacancy.status = status
        
        vacancy.title_en = title_en
        vacancy.title_uz = title_uz
        
        vacancy.position_type_en = position_type_en
        vacancy.position_type_uz = position_type_uz
        
        vacancy.description_en = description_en
        vacancy.description_uz = description_uz
        
        vacancy.requirements_en = requirements_en
        vacancy.requirements_uz = requirements_uz
        
        vacancy.responsibilities_en = responsibilities_en
        vacancy.responsibilities_uz = responsibilities_uz
        
        vacancy.salary_en = salary_en
        vacancy.salary_uz = salary_uz
        
        vacancy.employment_type_en = employment_type_en
        vacancy.employment_type_uz = employment_type_uz
        
        db.session.commit()
        flash('Vacancy updated successfully.', 'success')
        return redirect(url_for('hr.vacancies_list'))
        
    faculties = Faculty.query.all()
    departments = Department.query.all()
    return render_template('hr/vacancy_form.html', faculties=faculties, departments=departments, vacancy=vacancy)

@hr_bp.route('/vacancies/close/<int:vacancy_id>', methods=['POST'])
@login_required
@hr_required
def vacancy_close(vacancy_id):
    vacancy = Vacancy.query.get_or_404(vacancy_id)
    vacancy.status = 'closed'
    db.session.commit()
    flash('Vacancy status set to closed.', 'info')
    return redirect(url_for('hr.vacancies_list'))

# ----------------- APPLICATION & WORKFLOW MANAGEMENT -----------------
@hr_bp.route('/applications')
@login_required
@hr_required
def applications_list():
    apps = Application.query.order_by(Application.created_at.desc()).all()
    return render_template('hr/applications.html', applications=apps)

@hr_bp.route('/applications/<int:app_id>')
@login_required
@hr_required
def application_details(app_id):
    app_record = Application.query.get_or_404(app_id)
    return render_template('hr/application_details.html', app=app_record)

@hr_bp.route('/applications/status/<int:app_id>', methods=['POST'])
@login_required
@hr_required
def application_status_change(app_id):
    app_record = Application.query.get_or_404(app_id)
    new_status = request.form.get('status')
    
    valid_statuses = ['received', 'under_review', 'interview', 'accepted', 'rejected']
    if new_status not in valid_statuses:
        flash('Invalid application status.', 'danger')
        return redirect(url_for('hr.application_details', app_id=app_id))
        
    old_status = app_record.status
    app_record.status = new_status
    db.session.commit()
    
    # Send Notification Email if state is Accepted or Rejected
    if new_status in ['accepted', 'rejected'] and old_status != new_status:
        subject = f"Application Status Update - Al-Khwarizmi University"
        
        if new_status == 'accepted':
            body = f"""
            Dear {app_record.full_name},
            
            We are pleased to inform you that your application (No: {app_record.application_number}) for the vacancy of "{app_record.vacancy.get_title(g.lang_code)}" at Al-Khwarizmi University has been ACCEPTED.
            
            Our HR team will contact you shortly to discuss the next steps, contract details, and orientation.
            
            Congratulations!
            
            Sincerely,
            HR Recruitment Team
            Al-Khwarizmi University
            """
        else: # rejected
            body = f"""
            Dear {app_record.full_name},
            
            Thank you for your interest in the vacancy of "{app_record.vacancy.get_title(g.lang_code)}" at Al-Khwarizmi University and for taking the time to apply.
            
            We have reviewed your application (No: {app_record.application_number}) and documents. Regrettably, we have decided to proceed with other candidates whose profiles more closely align with the specific requirements of this position.
            
            We appreciate your interest in our university and wish you success in your future professional endeavors.
            
            Sincerely,
            HR Recruitment Team
            Al-Khwarizmi University
            """
            
        send_email_notification(app_record.email, subject, body)
        
    flash(f'Application status updated to {new_status.replace("_", " ").capitalize()}.', 'success')
    return redirect(url_for('hr.application_details', app_id=app_id))

# ----------------- INTERVIEW SCHEDULING -----------------
@hr_bp.route('/interviews/schedule', methods=['POST'])
@login_required
@hr_required
def interview_schedule():
    app_id = request.form.get('application_id')
    interview_type = request.form.get('interview_type') # 'on_site', 'online'
    date_time_str = request.form.get('date_time')
    location_or_link = request.form.get('location_or_link')
    notes = request.form.get('notes', '')
    
    if not all([app_id, interview_type, date_time_str, location_or_link]):
        flash('Please fill out all required fields to schedule an interview.', 'danger')
        return redirect(url_for('hr.application_details', app_id=app_id))
        
    app_record = Application.query.get_or_404(int(app_id))
    
    try:
        # Expected format: 2026-06-18T10:30
        date_time = datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date/time format. Use YYYY-MM-DDTHH:MM.', 'danger')
        return redirect(url_for('hr.application_details', app_id=app_id))
        
    # Create Interview record
    interview = Interview(
        application_id=app_record.id,
        interview_type=interview_type,
        date_time=date_time,
        location_or_link=location_or_link,
        notes=notes
    )
    db.session.add(interview)
    
    # Update application status
    app_record.status = 'interview'
    db.session.commit()
    
    # Send email notification to candidate
    formatted_time = date_time.strftime('%Y-%m-%d at %H:%M')
    location_label = "Zoom Link" if interview_type == 'online' else "University Location"
    
    email_subject = "Interview Invitation - Al-Khwarizmi University"
    email_body = f"""
    Dear {app_record.full_name},
    
    We are pleased to invite you for an interview regarding your application (No: {app_record.application_number}) for the position of "{app_record.vacancy.get_title(g.lang_code)}".
    
    Interview Details:
    - Type: {interview_type.replace('_', '-').capitalize()} Interview
    - Date & Time: {formatted_time} (Tashkent Time)
    - {location_label}: {location_or_link}
    
    Notes:
    {notes if notes else 'None'}
    
    Please confirm your availability by replying to this email.
    
    Sincerely,
    HR Recruitment Team
    Al-Khwarizmi University
    """
    send_email_notification(app_record.email, email_subject, email_body)
    
    flash('Interview scheduled successfully and email invitation sent.', 'success')
    return redirect(url_for('hr.application_details', app_id=app_record.id))

# ----------------- CONTACT REQUESTS -----------------
@hr_bp.route('/contact_requests')
@login_required
@hr_required
def contact_requests():
    requests_list = ContactRequest.query.order_by(ContactRequest.created_at.desc()).all()
    return render_template('hr/contact_requests.html', requests=requests_list)

@hr_bp.route('/contact_requests/resolve/<int:req_id>', methods=['POST'])
@login_required
@hr_required
def contact_resolve(req_id):
    req = ContactRequest.query.get_or_404(req_id)
    req.is_resolved = True
    db.session.commit()
    flash('Contact request marked as resolved.', 'success')
    return redirect(url_for('hr.contact_requests'))



# ----------------- FACULTY & DEPARTMENT MANAGEMENT -----------------
@hr_bp.route('/faculties-departments', methods=['GET', 'POST'])
@login_required
@hr_required
def faculties_departments():
    faculties = Faculty.query.all()
    departments = Department.query.all()
    return render_template(
        'hr/faculties_departments.html',
        faculties=faculties,
        departments=departments
    )

@hr_bp.route('/faculties/create', methods=['POST'])
@login_required
@hr_required
def faculty_create():
    name_en = request.form.get('name_en')
    name_uz = request.form.get('name_uz')
    
    if not all([name_en, name_uz]):
        flash('Faculty names are required in English and Uzbek.', 'danger')
        return redirect(url_for('hr.faculties_departments'))
        
    faculty = Faculty(name_en=name_en, name_uz=name_uz)
    db.session.add(faculty)
    db.session.commit()
    
    flash(f'Faculty "{name_en}" added successfully.', 'success')
    return redirect(url_for('hr.faculties_departments'))

@hr_bp.route('/departments/create', methods=['POST'])
@login_required
@hr_required
def department_create():
    name_en = request.form.get('name_en')
    name_uz = request.form.get('name_uz')
    
    if not all([name_en, name_uz]):
        flash('Department names in English and Uzbek are required.', 'danger')
        return redirect(url_for('hr.faculties_departments'))
        
    department = Department(
        name_en=name_en,
        name_uz=name_uz
    )
    db.session.add(department)
    db.session.commit()
    
    flash(f'Department "{name_en}" added successfully.', 'success')
    return redirect(url_for('hr.faculties_departments'))

@hr_bp.route('/faculties/delete/<int:faculty_id>', methods=['POST'])
@login_required
@hr_required
def faculty_delete(faculty_id):
    faculty = Faculty.query.get_or_404(faculty_id)
    if faculty.vacancies:
        flash('Cannot delete faculty because it contains departments or vacancies.', 'danger')
        return redirect(url_for('hr.faculties_departments'))
    db.session.delete(faculty)
    db.session.commit()
    flash('Faculty deleted successfully.', 'success')
    return redirect(url_for('hr.faculties_departments'))

@hr_bp.route('/departments/delete/<int:dept_id>', methods=['POST'])
@login_required
@hr_required
def department_delete(dept_id):
    dept = Department.query.get_or_404(dept_id)
    if dept.vacancies:
        flash('Cannot delete department because it contains vacancies.', 'danger')
        return redirect(url_for('hr.faculties_departments'))
    db.session.delete(dept)
    db.session.commit()
    flash('Department deleted successfully.', 'success')
    return redirect(url_for('hr.faculties_departments'))

