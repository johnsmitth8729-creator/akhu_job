import os
import random
import datetime
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, current_app, abort, jsonify, Response
from werkzeug.utils import secure_filename
from app.models import db, Faculty, Department, Vacancy, Application, ApplicationDocument, ContactRequest, SystemSetting, Interview
from app import csrf
from app.routes.notifications import send_email_notification

main_bp = Blueprint('main', __name__, url_prefix='/<any(en, uz):lang_code>')
public_bp = Blueprint('public', __name__)

@main_bp.route('/')
def home():
    # Fetch counts for the homepage hero stats
    open_positions_count = Vacancy.query.filter_by(status='open').count()
    faculties_count = Faculty.query.count()
    applications_count = Application.query.count()
    interviews_count = Interview.query.count()
    
    # We only show the 3 latest vacancies on the homepage
    latest_vacancies = Vacancy.query.filter_by(status='open').order_by(Vacancy.created_at.desc()).limit(3).all()
    
    return render_template(
        'home.html',
        vacancies=latest_vacancies,
        open_positions_count=open_positions_count,
        faculties_count=faculties_count,
        applications_count=applications_count,
        interviews_count=interviews_count
    )

@main_bp.route('/vacancies')
def vacancies_list():
    faculties = Faculty.query.all()
    departments = Department.query.all()
    
    # Query parameters for filtering
    search_query = request.args.get('search', '').strip()
    faculty_id = request.args.get('faculty', '')
    department_id = request.args.get('department', '')
    position_type = request.args.get('position_type', '')
    
    # Base query for active vacancies
    query = Vacancy.query.filter_by(status='open')
    
    # Apply filters
    if search_query:
        # Search title across all 3 languages
        query = query.filter(
            (Vacancy.title_en.ilike(f'%{search_query}%')) |
            (Vacancy.title_uz.ilike(f'%{search_query}%'))
        )
    if faculty_id:
        query = query.filter_by(faculty_id=int(faculty_id))
    if department_id:
        query = query.filter_by(department_id=int(department_id))
    if position_type:
        query = query.filter(
            (Vacancy.position_type_en == position_type) |
            (Vacancy.position_type_uz == position_type)
        )
        
    vacancies = query.order_by(Vacancy.created_at.desc()).all()
    
    return render_template(
        'vacancies.html',
        vacancies=vacancies,
        faculties=faculties,
        departments=departments,
        search_query=search_query,
        selected_faculty=faculty_id,
        selected_department=department_id,
        selected_position=position_type
    )

@main_bp.route('/vacancy/<int:vacancy_id>')
def vacancy_details(vacancy_id):
    vacancy = Vacancy.query.get_or_404(vacancy_id)
    if vacancy.status == 'closed':
        flash('This vacancy has been closed.', 'warning')
    return render_template('vacancy_details.html', vacancy=vacancy)

@main_bp.route('/apply/<int:vacancy_id>', methods=['GET', 'POST'])
def apply(vacancy_id):
    vacancy = Vacancy.query.get_or_404(vacancy_id)
    if vacancy.status == 'closed':
        flash('This vacancy is closed and no longer accepting applications.', 'danger')
        return redirect(url_for('main.vacancy_details', vacancy_id=vacancy_id))
        
    if request.method == 'POST':
        # Retrieve Personal details
        full_name = request.form.get('full_name')
        birth_date_str = request.form.get('birth_date')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        
        # Retrieve Education details
        degree = request.form.get('degree')
        university = request.form.get('university')
        graduation_year_str = request.form.get('graduation_year')
        
        # Basic validation
        if not all([full_name, birth_date_str, phone, email, address, degree, university, graduation_year_str]):
            flash('Please fill out all required fields.', 'danger')
            return redirect(url_for('main.apply', vacancy_id=vacancy_id))
            
        try:
            birth_date = datetime.datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            graduation_year = int(graduation_year_str)
        except ValueError:
            flash('Invalid date or graduation year format.', 'danger')
            return redirect(url_for('main.apply', vacancy_id=vacancy_id))
            
        # File checks
        allowed_func = current_app.config['ALLOWED_FILE_FUNC']
        doc_files = {}
        required_docs = ['passport', 'resume', 'diploma']
        optional_docs = ['certificates', 'additional']
        
        # Verify required uploads exist
        for key in required_docs:
            if key not in request.files or request.files[key].filename == '':
                flash(f'Please upload the required document: {key.capitalize()}', 'danger')
                return redirect(url_for('main.apply', vacancy_id=vacancy_id))
                
        # Check size and extensions of all files
        for key in required_docs + optional_docs:
            if key in request.files and request.files[key].filename != '':
                file = request.files[key]
                
                # Check extension
                if not allowed_func(file.filename):
                    flash(f'File type not allowed for {key}. Supported: PDF, DOC, DOCX, JPG, JPEG, PNG.', 'danger')
                    return redirect(url_for('main.apply', vacancy_id=vacancy_id))
                
                # Check file size (since Flask accepts it, double check size before saving)
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)  # Reset pointer
                
                if file_size > current_app.config['MAX_CONTENT_LENGTH']:
                    flash(f'File size exceeds 20 MB limit for {key}.', 'danger')
                    return redirect(url_for('main.apply', vacancy_id=vacancy_id))
                    
                doc_files[key] = (file, file_size)

        # Generate unique tracking code (application number)
        # E.g. AKHU-2026-8910
        year = datetime.datetime.now().year
        while True:
            rand_code = random.randint(1000, 9999)
            app_number = f"AKHU-{year}-{rand_code}"
            existing = Application.query.filter_by(application_number=app_number).first()
            if not existing:
                break
                
        # Save Application record
        application = Application(
            application_number=app_number,
            vacancy_id=vacancy_id,
            full_name=full_name,
            birth_date=birth_date,
            phone=phone,
            email=email,
            address=address,
            degree=degree,
            university=university,
            graduation_year=graduation_year,
            status='received'
        )
        db.session.add(application)
        db.session.flush() # Populate application.id
        
        # Save documents
        for doc_type, (file, file_size) in doc_files.items():
            filename = secure_filename(file.filename)
            # Add timestamp prefix to avoid name collisions
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            unique_filename = f"{timestamp}_{application.id}_{doc_type}_{filename}"
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save file
            file.save(save_path)
            
            # Record document in DB
            doc_record = ApplicationDocument(
                application_id=application.id,
                doc_type=doc_type,
                file_path=os.path.join('uploads', unique_filename), # relative path for routing
                file_name=filename,
                file_size=file_size
            )
            db.session.add(doc_record)
            
        db.session.commit()
        
        # Trigger Email Notification
        email_subject = "Application Received - Al-Khwarizmi University"
        email_body = f"""
        Dear {full_name},
        
        Thank you for applying for the position of "{vacancy.get_title(g.lang_code)}" at Al-Khwarizmi University.
        
        Your application has been received successfully.
        Tracking Details:
        - Application Number: {app_number}
        - Registered Email: {email}
        
        You can check the status of your application at any time here:
        {request.url_root}{g.lang_code}/status
        
        Sincerely,
        HR Department
        Al-Khwarizmi University
        """
        send_email_notification(email, email_subject, email_body)
        
        flash(f'Your application has been submitted successfully! Use code {app_number} to track your application status.', 'success')
        return redirect(url_for('main.status_tracker', app_num=app_number, email_addr=email))
        
    return render_template('apply.html', vacancy=vacancy)

@main_bp.route('/status', methods=['GET', 'POST'])
def status_tracker():
    app_num = request.args.get('app_num', '') or request.form.get('app_num', '').strip()
    email_addr = request.args.get('email_addr', '') or request.form.get('email_addr', '').strip()
    
    application = None
    searched = False
    
    if request.method == 'POST' or (app_num and email_addr):
        searched = True
        application = Application.query.filter_by(
            application_number=app_num,
            email=email_addr
        ).first()
        
        if not application:
            flash('No application found matching the tracking details.', 'danger')
            
    return render_template(
        'status.html',
        application=application,
        searched=searched,
        app_num=app_num,
        email_addr=email_addr
    )

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        
        if not all([name, email, phone, message]):
            flash('Please fill out all contact fields.', 'danger')
            return redirect(url_for('main.contact'))
            
        # Record contact request in DB
        req = ContactRequest(
            name=name,
            email=email,
            phone=phone,
            message=message
        )
        db.session.add(req)
        db.session.commit()
        
        flash('Your contact request has been sent successfully. Our team will get back to you shortly.', 'success')
        return redirect(url_for('main.contact'))
        
    return render_template('contact.html')

# Endpoint to load departments dynamically via JS based on selected Faculty
@main_bp.route('/api/departments/<int:faculty_id>')
def api_departments(faculty_id):
    departments = Department.query.all()
    # Return translated names based on current language
    result = []
    for dept in departments:
        name = getattr(dept, f'name_{g.lang_code}', dept.name_en)
        result.append({'id': dept.id, 'name': name})
    return jsonify(result)


@public_bp.route('/robots.txt')
def robots_txt():
    content = """User-agent: *
Disallow: /en/admin/
Disallow: /uz/admin/
Disallow: /en/hr_recruiting/
Disallow: /uz/hr_recruiting/
Sitemap: https://akhu.uz/sitemap.xml

# Platform Developer Attribution:
# Developed and Designed by Omonbayev Jaloliddin (Telegram: https://t.me/jaloliddin_omonbaev)
# Created for Al-Khwarizmi University Recruitment Portal
"""
    return Response(content, mimetype='text/plain')

@public_bp.route('/sitemap.xml')
def sitemap_xml():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<!--
    Sitemap for Al-Khwarizmi University Recruitment Portal
    Platform Creator & Developer: Omonbayev Jaloliddin (Telegram: https://t.me/jaloliddin_omonbaev)
-->
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://akhu.uz/en/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://akhu.uz/uz/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://akhu.uz/en/vacancies</loc>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://akhu.uz/uz/vacancies</loc>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://akhu.uz/en/contact</loc>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
    <url>
        <loc>https://akhu.uz/uz/contact</loc>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
</urlset>"""
    return Response(content, mimetype='application/xml')
