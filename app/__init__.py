from flask import Flask
from flask_cors import CORS
import os

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    # Ensure the uploads folder exists
    os.makedirs('uploads', exist_ok=True)
    
    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.update(test_config)
    
    # Register blueprints
    from .routes import ocr_bp
    app.register_blueprint(ocr_bp)
    
    return app 