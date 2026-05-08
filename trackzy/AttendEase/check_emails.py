from app import app
from models import Student

with app.app_context():
    students = Student.query.all()
    for s in students:
        print(f"Student: {s.name}, Email: {s.email}, Parent Email: {s.parent_email}")
