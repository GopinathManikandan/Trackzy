from app import app
from models import Student, AttendanceRecord

with app.app_context():
    student_count = Student.query.count()
    attendance_count = AttendanceRecord.query.count()
    print(f"Students in DB: {student_count}")
    print(f"Attendance Records in DB: {attendance_count}")
