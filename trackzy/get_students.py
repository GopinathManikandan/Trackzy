import sys
import os
sys.path.append('AttendEase')
from app import app
from models import db, User

with app.app_context():
    students = User.query.filter_by(role='student').limit(5).all()
    if not students:
        print("No student accounts found in database.")
    else:
        for s in students:
            print(f"Username: {s.username}, Password: {s.password}")
