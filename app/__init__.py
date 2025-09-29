from flask import Flask
from app.utilidad.extensions import db
from app.routes.user_routes import registrar_ausencias_global

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)

    # Importar Blueprints después de inicializar db
    from .routes.user_routes import user_bp
    app.register_blueprint(user_bp)

    # 👇 Aquí creas las tablas ANTES de llamar registrar_ausencias_global
    with app.app_context():
        db.create_all()  # Esto crea todas las tablas según tus modelos
        registrar_ausencias_global()  # Ahora sí puedes consultar datos

    return app
