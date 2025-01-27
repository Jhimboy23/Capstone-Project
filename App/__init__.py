import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS

db = SQLAlchemy()
DB_NAME = "database.db" 

def create_app():
    app = Flask(__name__)
    
    # Use environment variable for SECRET_KEY
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dfafdsfsfsa sadsad')
    
    # Set up the database URI for SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
# postgresql://demodatabase_5309_user:lpETIp3Oyydp0ihdfg3R6G2Ox4WgwM6Y@dpg-cub3sbogph6c73a37ub0-a.oregon-postgres.render.com/demodatabase_5309

    # Initialize the database with the app
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    # Enable CORS for the given resources
    CORS(app, resources={r"/sensor-data": {"origins": "*"}}, supports_credentials=True)

    # Import blueprints
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Import User model
    from .models import User

    # Ensure the database is created
    create_database(app)

    # Define user loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

def create_database(app):
    if not os.path.exists(DB_NAME):  # Check if the database exists
        with app.app_context():
            db.create_all()  # Create the database tables
        print('Created Database!')
