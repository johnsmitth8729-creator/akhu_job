from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return abort(401)
        if current_user.role != 'admin':
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def hr_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return abort(401)
        # Admins have full access, so let admins view HR pages too
        if current_user.role not in ('hr', 'admin'):
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function
