import sys
import os
sys.path.append('AttendEase')
from app import app
from models import User

with app.app_context():
    users = User.query.all()
    for u in users:
        print(f"Role: {u.role}, Username: {u.username}, Password: {u.password}, Name: {u.name}")
