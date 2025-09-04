import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    # Use SQLite for local development if no DATABASE_URL is provided
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        # Create instance directory if it doesn't exist
        os.makedirs(os.path.join(app.instance_path), exist_ok=True)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(app.instance_path, 'school.db')}"
    # Configure engine options based on database type
    if "postgresql" in app.config["SQLALCHEMY_DATABASE_URI"]:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
    else:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Mail configuration
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", "587"))
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@solmaior.com")
    
    # Upload configuration
    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
    
    # Create upload directory
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'  # type: ignore
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes import register_blueprints
    register_blueprints(app)
    
    # Register template filters
    from utils import register_template_filters
    register_template_filters(app)
    
    with app.app_context():
        from models import User, Student, Teacher, Room, Course, Enrollment, Schedule, Payment, Material, ExperimentalClass
        db.create_all()
        
        # Create default admin user if not exists
        admin = User.query.filter_by(email='admin@solmaior.com').first()
        if not admin:
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                email='admin@solmaior.com',
                password_hash=generate_password_hash('admin123'),
                user_type='admin',
                full_name='Administrador Sistema',
                phone='(11) 99999-9999',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            logging.info("Admin user created: admin@solmaior.com / admin123")
    
    return app

app = create_app()
