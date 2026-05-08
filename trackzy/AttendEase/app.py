import os
import logging
from flask import Flask
from datetime import datetime
from dotenv import load_dotenv
from models import db

# Load environment variables from .env file
load_dotenv()

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Database Configuration
db_url = os.environ.get("DATABASE_URL", "sqlite:///attendance.db")

# Fix for Render/Heroku connection strings that use postgres:// instead of postgresql://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with app
db.init_app(app)

# Custom Jinja2 filter for strptime
@app.template_filter('strptime')
def strptime_filter(value, format):
    if isinstance(value, str):
        return datetime.strptime(value, format)
    return value

@app.template_filter('chat_time')
def chat_time_filter(dt):
    if not dt: return ""
    # Convert UTC to IST (+5:30)
    from datetime import timedelta
    ist_time = dt + timedelta(hours=5, minutes=30)
    return ist_time.strftime('%I:%M %p')

@app.template_filter('chat_date')
def chat_date_filter(dt):
    if not dt: return ""
    # Convert UTC to IST (+5:30)
    from datetime import timedelta, date
    ist_dt = dt + timedelta(hours=5, minutes=30)
    ist_date = ist_dt.date()
    today = (datetime.utcnow() + timedelta(hours=5, minutes=30)).date()
    
    if ist_date == today:
        return "Today"
    elif ist_date == today - timedelta(days=1):
        return "Yesterday"
    else:
        return ist_date.strftime('%B %d, %Y')

# Import routes after app creation to avoid circular imports
from routes import *

# Create tables if they don't exist
with app.app_context():
    db.create_all()
    
    # Check if we need to seed data (if no users exist)
    from models import User
    if User.query.count() == 0:
        app.logger.info("Database is empty. Running initial migration...")
        try:
            from migrate_data import migrate
            migrate()
        except Exception as e:
            app.logger.error(f"Error during initial migration: {e}")
