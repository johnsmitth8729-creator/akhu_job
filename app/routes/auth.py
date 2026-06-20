from flask import Blueprint, render_template, redirect, url_for, flash, request, g
from flask_login import login_user, logout_user, current_user, login_required
from app.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/<any(en, uz):lang_code>')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect based on role
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'hr':
            return redirect(url_for('hr.dashboard'))
            
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=remember)
        
        # Next URL check
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
            
        # Role-based dashboard redirect
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'hr':
            return redirect(url_for('hr.dashboard'))
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.home'))
