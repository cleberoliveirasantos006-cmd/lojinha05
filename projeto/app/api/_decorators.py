from functools import wraps
from flask import jsonify
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            return jsonify(error="Acesso restrito ao administrador"), 403
        return f(*args, **kwargs)
    return wrapper


def super_admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin:
            return jsonify(error="Acesso restrito ao super-admin"), 403
        return f(*args, **kwargs)
    return wrapper