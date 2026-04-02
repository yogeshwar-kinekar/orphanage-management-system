# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate # Optional
from config import Config
from datetime import datetime
import logging # Import logging

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login' # Route function name for login page
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info' # Bootstrap class for flash message
csrf = CSRFProtect()
migrate = Migrate() # Optional

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure logging
    logging.basicConfig(level=logging.INFO) # Log info and above
    app.logger.setLevel(logging.INFO)

    # Log database URI on startup (be careful with passwords in logs)
    # Use a safer way to log config in production if needed
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    app.logger.info(f"Connecting to database: {db_uri.split('@')[1] if '@' in db_uri else db_uri}")


    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db) # Optional: Initialize Flask-Migrate

    # Import models here to avoid circular imports
    # and ensure they are known to SQLAlchemy/Migrate
    from app import models

    # Register Blueprints or import routes
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    app.logger.info("Flask app created successfully.")

    # Create database tables if they don't exist
    # In a production setup, use Flask-Migrate instead
    with app.app_context():
        try:
            # db.drop_all() # Uncomment to reset tables during development
            db.create_all()
            app.logger.info("Database tables checked/created.")
             # --- Add Initial Admin User ---
            from app.models import Admin
            from werkzeug.security import generate_password_hash
            # Check if admin exists
            if not Admin.query.filter_by(username='admin').first():
                hashed_password = generate_password_hash('password', method='pbkdf2:sha256') # CHANGE 'password'
                admin_user = Admin(username='admin', password_hash=hashed_password)
                db.session.add(admin_user)
                db.session.commit()
                app.logger.info("Default admin user created.")
        except Exception as e:
             app.logger.error(f"Error during DB initialization or admin user creation: {e}")


    return app