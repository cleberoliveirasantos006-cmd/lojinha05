from flask import Flask, send_from_directory
from flask_cors import CORS
from app.config import Config
from app.extensions import db, migrate, login_manager


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.config.from_object(Config)

    CORS(app, supports_credentials=True, origins=["*"])

    db.init_app(app)
    migrate.init_app(app, db)          # mantido para uso local, mas não obrigatório
    login_manager.init_app(app)

    from app.auth.routes import auth_bp
    from app.api.profissionais import prof_bp
    from app.api.agendamentos import ag_bp
    from app.api.pedidos import ord_bp
    from app.api.cliente import cli_bp
    from app.api.admin import admin_bp

    for bp in (auth_bp, prof_bp, ag_bp, ord_bp, cli_bp, admin_bp):
        app.register_blueprint(bp)

    # ------------------------------------------------------------
    # Cria automaticamente as tabelas que ainda não existem no banco.
    # Substitui o "flask db upgrade" no Render (plano Free não tem Shell).
    # NÃO altera tabelas já existentes — só cria as que faltam.
    # ------------------------------------------------------------
    with app.app_context():
        from app import models  # garante que todos os modelos sejam registrados
        db.create_all()

    @app.route("/")
    def home():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/<path:filename>")
    def static_pages(filename):
        return send_from_directory(app.static_folder, filename)

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app
