from functools import wraps
from flask import session, redirect, url_for

def login_required(role=None):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificar si hay sesión activa
            if 'role' not in session:
                return redirect(url_for('user.login'))
            
            # Si tiene rol específico, verificarlo
            if role and session['role'] != role:
                return redirect(url_for('user.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return wrapper
