from flask import Flask, render_template, send_from_directory
from app.models import db
from app.routes import api_bp
from config import config
import os


def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(config[config_name])
    
    # Ensure instance folder exists
    instance_path = app.config.get('LOCAL_STORAGE_PATH')
    if instance_path:
        os.makedirs(instance_path, exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Main routes
    @app.route('/')
    def index():
        """Dashboard - case list"""
        return render_template('index.html')
    
    @app.route('/cases/new')
    def new_case():
        """Create new case page"""
        return render_template('new_case.html')
    
    @app.route('/cases/<int:case_id>')
    def case_detail(case_id):
        """Case detail page"""
        return render_template('case_detail.html', case_id=case_id)
    
    @app.route('/storage/<path:filename>')
    def serve_storage(filename):
        """Serve files from local storage"""
        storage_path = app.config.get('LOCAL_STORAGE_PATH')
        return send_from_directory(storage_path, filename)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
