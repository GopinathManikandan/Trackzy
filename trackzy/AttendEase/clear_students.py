import os
import json
from app import app
from models import db, Student, AttendanceRecord, User

def clear_student_data():
    with app.app_context():
        try:
            print("Clearing students table...")
            db.session.query(Student).delete()
            
            print("Clearing attendance_records table...")
            db.session.query(AttendanceRecord).delete()

            print("Clearing student users from users table...")
            User.query.filter_by(role='student').delete()
            
            db.session.commit()
            print("Database tables cleared.")
            
            # Clear JSON files to prevent re-migration
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            
            students_json = os.path.join(data_dir, 'students.json')
            if os.path.exists(students_json):
                with open(students_json, 'w') as f:
                    json.dump([], f)
                print("data/students.json cleared.")
                
            attendance_json = os.path.join(data_dir, 'attendance.json')
            if os.path.exists(attendance_json):
                with open(attendance_json, 'w') as f:
                    json.dump([], f)
                print("data/attendance.json cleared.")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error clearing data: {e}")

if __name__ == "__main__":
    clear_student_data()
