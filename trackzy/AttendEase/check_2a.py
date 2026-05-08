from app import app
from models import Student

with app.app_context():
    print("Students in '2nd Year A':")
    students = Student.query.filter_by(class_id='2nd Year A').all()
    for s in students:
        print(f"  - Name: {s.name}, ID: {s.student_id}")
