from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, limiter
from app.models import User, Store

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
@limiter.limit("5 per hour")
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip() or None

    if not username or len(password) < 4:
        return jsonify(error="Usuário e senha (mín. 4) obrigatórios"), 400
    if User.query.filter_by(username=username).first():
        return jsonify(error="Esse usuário já existe"), 409

    user = User(username=username, email=email, role="customer")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(id=user.id, username=user.username, role=user.role), 201


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify(error="Usuário ou senha incorretos"), 401

    login_user(user, remember=True)
    return jsonify(id=user.id, username=user.username,
                   role=user.role, store_id=user.store_id)


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify(ok=True)


@auth_bp.get("/me")
def me():
    if not current_user.is_authenticated:
        return jsonify(authenticated=False)
    return jsonify(authenticated=True, username=current_user.username,
                   role=current_user.role, store_id=current_user.store_id)


@auth_bp.post("/bootstrap-admin")
@limiter.limit("3 per hour")
def bootstrap_admin():
    token = request.headers.get("X-Bootstrap-Token", "")
    esperado = current_app.config.get("ADMIN_BOOTSTRAP_TOKEN", "")
    if not esperado or token != esperado:
        return jsonify(error="Acesso negado"), 403

    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = data.get("email")
    store_slug = data.get("store_slug")

    if not username or len(password) < 6:
        return jsonify(error="username e password (mín. 6) obrigatórios"), 400
    if User.query.filter_by(username=username).first():
        return jsonify(error="Usuário já existe"), 409

    store_id = None
    if store_slug:
        store = Store.query.filter_by(slug=store_slug).first()
        if not store:
            return jsonify(error="Loja não encontrada"), 404
        store_id = store.id

    admin = User(username=username, email=email, role="admin", store_id=store_id)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    return jsonify(id=admin.id, username=admin.username, role="admin"), 201
