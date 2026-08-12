# =======================================================
# Al-Khwarizmi University Recruitment Portal
# Reports & Analytics Module
# Designed & Developed by: Omonbayev Jaloliddin
# Telegram: https://t.me/jaloliddin_omonbaev
# =======================================================

import io
import csv
import datetime
from sqlalchemy import func, desc, or_, and_
from app.models import db, Vacancy, Faculty, Department, Application, Interview, ContactRequest, User

def get_reports_data(start_date=None, end_date=None, faculty_id=None, department_id=None, vacancy_id=None, status=None, date_preset='all', lang_code='uz'):
    now = datetime.datetime.utcnow()
    
    # Resolve Date Preset if start_date/end_date not explicitly set or when preset is used
    if date_preset == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif date_preset == '7days':
        start_date = (now - datetime.timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif date_preset == '30days':
        start_date = (now - datetime.timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif date_preset == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif date_preset == 'this_year':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif date_preset == 'custom' and start_date:
        if isinstance(start_date, str) and start_date.strip():
            try:
                start_date = datetime.datetime.strptime(start_date.strip(), '%Y-%m-%d')
            except ValueError:
                start_date = None
        if isinstance(end_date, str) and end_date.strip():
            try:
                end_date = datetime.datetime.strptime(end_date.strip(), '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            except ValueError:
                end_date = None
    else:
        if date_preset != 'custom':
            start_date = None
            end_date = None

    # Base Application query with filters
    app_query = Application.query.join(Vacancy, Application.vacancy_id == Vacancy.id)
    
    if start_date:
        app_query = app_query.filter(Application.created_at >= start_date)
    if end_date:
        app_query = app_query.filter(Application.created_at <= end_date)
    if faculty_id:
        try:
            f_id = int(faculty_id)
            app_query = app_query.filter(Vacancy.faculty_id == f_id)
        except ValueError:
            pass
    if department_id:
        try:
            d_id = int(department_id)
            app_query = app_query.filter(Vacancy.department_id == d_id)
        except ValueError:
            pass
    if vacancy_id:
        try:
            v_id = int(vacancy_id)
            app_query = app_query.filter(Application.vacancy_id == v_id)
        except ValueError:
            pass
    if status and status != 'all':
        app_query = app_query.filter(Application.status == status)

    filtered_applications = app_query.order_by(Application.created_at.desc()).all()
    total_apps_count = len(filtered_applications)

    # Status counts for filtered apps
    apps_received = sum(1 for a in filtered_applications if a.status == 'received')
    apps_under_review = sum(1 for a in filtered_applications if a.status == 'under_review')
    apps_interview = sum(1 for a in filtered_applications if a.status == 'interview')
    apps_accepted = sum(1 for a in filtered_applications if a.status == 'accepted')
    apps_rejected = sum(1 for a in filtered_applications if a.status == 'rejected')

    acceptance_rate = round((apps_accepted / total_apps_count * 100), 1) if total_apps_count > 0 else 0
    rejection_rate = round((apps_rejected / total_apps_count * 100), 1) if total_apps_count > 0 else 0
    review_rate = round(((apps_under_review + apps_interview) / total_apps_count * 100), 1) if total_apps_count > 0 else 0

    # Overall vacancy counts
    vacancies_query = Vacancy.query
    if faculty_id:
        try:
            vacancies_query = vacancies_query.filter(Vacancy.faculty_id == int(faculty_id))
        except ValueError:
            pass
    if department_id:
        try:
            vacancies_query = vacancies_query.filter(Vacancy.department_id == int(department_id))
        except ValueError:
            pass
    all_vacancies = vacancies_query.order_by(Vacancy.created_at.desc()).all()
    total_vacancies = len(all_vacancies)
    open_vacancies = sum(1 for v in all_vacancies if v.status == 'open')
    closed_vacancies = sum(1 for v in all_vacancies if v.status == 'closed')

    # Vacancy Performance Breakdown
    vacancies_performance = []
    for v in all_vacancies:
        v_apps = [a for a in v.applications]
        if start_date:
            v_apps = [a for a in v_apps if a.created_at >= start_date]
        if end_date:
            v_apps = [a for a in v_apps if a.created_at <= end_date]
        
        v_total = len(v_apps)
        v_accepted = sum(1 for a in v_apps if a.status == 'accepted')
        v_rejected = sum(1 for a in v_apps if a.status == 'rejected')
        v_interview = sum(1 for a in v_apps if a.status == 'interview')
        v_under_review = sum(1 for a in v_apps if a.status == 'under_review')
        v_received = sum(1 for a in v_apps if a.status == 'received')
        v_rate = round((v_accepted / v_total * 100), 1) if v_total > 0 else 0

        vacancies_performance.append({
            'vacancy': v,
            'total_apps': v_total,
            'received': v_received,
            'under_review': v_under_review,
            'interview': v_interview,
            'accepted': v_accepted,
            'rejected': v_rejected,
            'acceptance_rate': v_rate
        })

    # Sort vacancies performance by total applicants descending
    vacancies_performance.sort(key=lambda x: x['total_apps'], reverse=True)

    # Faculty Breakdown
    faculties = Faculty.query.all()
    faculties_data = []
    for fac in faculties:
        fac_vacancies = [v for v in fac.vacancies]
        fac_apps_count = 0
        fac_accepted_count = 0
        for v in fac_vacancies:
            for a in v.applications:
                if (not start_date or a.created_at >= start_date) and (not end_date or a.created_at <= end_date):
                    fac_apps_count += 1
                    if a.status == 'accepted':
                        fac_accepted_count += 1
        faculties_data.append({
            'faculty': fac,
            'vacancies_count': len(fac_vacancies),
            'apps_count': fac_apps_count,
            'accepted_count': fac_accepted_count
        })

    # Department Breakdown
    departments = Department.query.all()
    departments_data = []
    for dept in departments:
        dept_vacancies = [v for v in dept.vacancies]
        dept_apps_count = 0
        dept_accepted_count = 0
        for v in dept_vacancies:
            for a in v.applications:
                if (not start_date or a.created_at >= start_date) and (not end_date or a.created_at <= end_date):
                    dept_apps_count += 1
                    if a.status == 'accepted':
                        dept_accepted_count += 1
        departments_data.append({
            'department': dept,
            'vacancies_count': len(dept_vacancies),
            'apps_count': dept_apps_count,
            'accepted_count': dept_accepted_count
        })

    # Interview stats
    interviews_query = Interview.query
    if start_date:
        interviews_query = interviews_query.filter(Interview.created_at >= start_date)
    if end_date:
        interviews_query = interviews_query.filter(Interview.created_at <= end_date)
    all_interviews = interviews_query.all()
    total_interviews = len(all_interviews)
    online_interviews = sum(1 for i in all_interviews if i.interview_type == 'online')
    onsite_interviews = sum(1 for i in all_interviews if i.interview_type == 'on_site')

    # Contact Requests stats
    contacts_query = ContactRequest.query
    if start_date:
        contacts_query = contacts_query.filter(ContactRequest.created_at >= start_date)
    if end_date:
        contacts_query = contacts_query.filter(ContactRequest.created_at <= end_date)
    all_contacts = contacts_query.order_by(ContactRequest.created_at.desc()).all()
    total_contacts = len(all_contacts)
    resolved_contacts = sum(1 for c in all_contacts if c.is_resolved)
    pending_contacts = total_contacts - resolved_contacts

    # Degree stats
    degree_counts = {}
    for a in filtered_applications:
        deg = (a.degree or 'Other').strip()
        degree_counts[deg] = degree_counts.get(deg, 0) + 1

    # Timeline Chart Data (Group by date for line/bar chart)
    timeline_dict = {}
    for a in filtered_applications:
        date_str = a.created_at.strftime('%Y-%m-%d')
        timeline_dict[date_str] = timeline_dict.get(date_str, 0) + 1

    # If timeline has items, sort by date
    sorted_timeline_dates = sorted(timeline_dict.keys())
    # If fewer than 7 days in custom/preset, fill missing days within the window if within 30 days
    timeline_labels = sorted_timeline_dates
    timeline_counts = [timeline_dict[d] for d in sorted_timeline_dates]

    # Status Chart Data
    status_labels_uz = ["Qabul qilindi (Yangi)", "Ko'rib chiqilmoqda", "Suhbat belgilandi", "Ishga qabul qilindi", "Rad etildi"]
    status_labels_en = ["Received (New)", "Under Review", "Interview Scheduled", "Accepted / Hired", "Rejected"]
    status_labels = status_labels_uz if lang_code == 'uz' else status_labels_en
    status_counts = [apps_received, apps_under_review, apps_interview, apps_accepted, apps_rejected]

    # Academic Units Chart (Combine Top Faculties & Departments)
    unit_labels = []
    unit_counts = []
    for f in faculties_data:
        if f['apps_count'] > 0:
            unit_labels.append(f['faculty'].get_name(lang_code))
            unit_counts.append(f['apps_count'])
    for d in departments_data:
        if d['apps_count'] > 0:
            unit_labels.append(d['department'].get_name(lang_code))
            unit_counts.append(d['apps_count'])

    # Format dates for string display in form inputs
    start_date_str = start_date.strftime('%Y-%m-%d') if start_date else ''
    end_date_str = end_date.strftime('%Y-%m-%d') if end_date else ''

    return {
        'total_apps_count': total_apps_count,
        'apps_received': apps_received,
        'apps_under_review': apps_under_review,
        'apps_interview': apps_interview,
        'apps_accepted': apps_accepted,
        'apps_rejected': apps_rejected,
        'acceptance_rate': acceptance_rate,
        'rejection_rate': rejection_rate,
        'review_rate': review_rate,
        'total_vacancies': total_vacancies,
        'open_vacancies': open_vacancies,
        'closed_vacancies': closed_vacancies,
        'total_interviews': total_interviews,
        'online_interviews': online_interviews,
        'onsite_interviews': onsite_interviews,
        'total_contacts': total_contacts,
        'resolved_contacts': resolved_contacts,
        'pending_contacts': pending_contacts,
        'filtered_applications': filtered_applications,
        'vacancies_performance': vacancies_performance,
        'faculties_data': faculties_data,
        'departments_data': departments_data,
        'all_contacts': all_contacts,
        'degree_counts': degree_counts,
        'faculties': faculties,
        'departments': departments,
        'all_vacancies': all_vacancies,
        # Filters state
        'date_preset': date_preset or 'all',
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        'selected_faculty_id': faculty_id,
        'selected_department_id': department_id,
        'selected_vacancy_id': vacancy_id,
        'selected_status': status or 'all',
        # Chart JSON objects
        'timeline_labels': timeline_labels,
        'timeline_counts': timeline_counts,
        'status_labels': status_labels,
        'status_counts': status_counts,
        'degree_labels': list(degree_counts.keys()),
        'degree_values': list(degree_counts.values()),
        'unit_labels': unit_labels,
        'unit_counts': unit_counts,
        'generated_at': now.strftime('%Y-%m-%d %H:%M:%S UTC')
    }


def generate_applications_csv(applications, lang_code='uz'):
    output = io.StringIO()
    # Write UTF-8 BOM so MS Excel opens Uzbek letters without encoding issues
    output.write('\ufeff')
    writer = csv.writer(output)

    if lang_code == 'uz':
        headers = [
            'Ariza raqami',
            'Nomzod F.I.SH',
            'Vakansiya / Lavozim',
            'Fakultet / Bo\'lim',
            'Ilmiy darajasi',
            'Oliy ta\'lim muassasasi',
            'Bitirgan yili',
            'Telefon raqami',
            'Elektron pochta',
            'Manzili',
            'Ariza topshirilgan sana',
            'Holati'
        ]
        status_map = {
            'received': 'Qabul qilindi',
            'under_review': 'Ko\'rib chiqilmoqda',
            'interview': 'Suhbat belgilandi',
            'accepted': 'Ishga qabul qilindi',
            'rejected': 'Rad etildi'
        }
    else:
        headers = [
            'Application Number',
            'Candidate Full Name',
            'Vacancy / Position',
            'Faculty / Department',
            'Academic Degree',
            'University',
            'Graduation Year',
            'Phone',
            'Email',
            'Address',
            'Application Date',
            'Status'
        ]
        status_map = {
            'received': 'Received',
            'under_review': 'Under Review',
            'interview': 'Interview Scheduled',
            'accepted': 'Accepted',
            'rejected': 'Rejected'
        }

    writer.writerow(headers)

    for app in applications:
        faculty_or_dept = ''
        if app.vacancy:
            if app.vacancy.faculty:
                faculty_or_dept = app.vacancy.faculty.get_name(lang_code)
            elif app.vacancy.department:
                faculty_or_dept = app.vacancy.department.get_name(lang_code)

        writer.writerow([
            app.application_number,
            app.full_name,
            app.vacancy.get_title(lang_code) if app.vacancy else '',
            faculty_or_dept,
            app.degree,
            app.university,
            app.graduation_year,
            app.phone,
            app.email,
            app.address.replace('\n', ' ').replace('\r', ' ') if app.address else '',
            app.created_at.strftime('%Y-%m-%d %H:%M') if app.created_at else '',
            status_map.get(app.status, app.status)
        ])

    output.seek(0)
    return output.getvalue()


def generate_vacancies_csv(vacancies_performance, lang_code='uz'):
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)

    if lang_code == 'uz':
        headers = [
            'Vakansiya ID',
            'Lavozim nomi',
            'Lavozim turi',
            'Fakultet / Bo\'lim',
            'Bandlik turi',
            'Maosh',
            'Oxirgi muddat (Deadline)',
            'Holati',
            'Jami arizalar',
            'Yangi',
            'Ko\'rib chiqilmoqda',
            'Suhbatda',
            'Qabul qilingan',
            'Rad etilgan',
            'Qabul qilish foizi (%)'
        ]
    else:
        headers = [
            'Vacancy ID',
            'Job Title',
            'Position Type',
            'Faculty / Department',
            'Employment Type',
            'Salary',
            'Deadline',
            'Status',
            'Total Applications',
            'Received',
            'Under Review',
            'Interview',
            'Accepted',
            'Rejected',
            'Acceptance Rate (%)'
        ]

    writer.writerow(headers)

    for vp in vacancies_performance:
        v = vp['vacancy']
        faculty_or_dept = ''
        if v.faculty:
            faculty_or_dept = v.faculty.get_name(lang_code)
        elif v.department:
            faculty_or_dept = v.department.get_name(lang_code)

        writer.writerow([
            v.id,
            v.get_title(lang_code),
            v.get_position_type(lang_code),
            faculty_or_dept,
            v.get_employment_type(lang_code),
            v.get_salary(lang_code),
            v.deadline.strftime('%Y-%m-%d') if v.deadline else '',
            v.status.upper(),
            vp['total_apps'],
            vp['received'],
            vp['under_review'],
            vp['interview'],
            vp['accepted'],
            vp['rejected'],
            f"{vp['acceptance_rate']}%"
        ])

    output.seek(0)
    return output.getvalue()
