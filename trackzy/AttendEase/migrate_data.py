import json
import os
from app import app
from models import db, User, Class, Student, AttendanceRecord
from datetime import datetime

def migrate():
    # Get the directory where this script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')

    with app.app_context():
        print(f"Starting migration from {data_dir}...")
        
        # 1. Migrate Users
        users_path = os.path.join(data_dir, 'users.json')
        if os.path.exists(users_path):
            with open(users_path, 'r') as f:
                users = json.load(f)
                # Only delete if we are force migrating, otherwise check existence
                # User.query.delete() 
                for u in users:
                    if not User.query.filter_by(user_id=u['user_id']).first():
                        user = User(
                            user_id=u['user_id'],
                            username=u['username'],
                            password=u['password'],
                            role=u['role'],
                            name=u['name'],
                            assigned_classes=u.get('assigned_classes', [])
                        )
                        db.session.add(user)
            print("Users migrated.")

        # 2. Migrate Classes
        classes_path = os.path.join(data_dir, 'classes.json')
        if os.path.exists(classes_path):
            with open(classes_path, 'r') as f:
                classes = json.load(f)
                for c in classes:
                    if not Class.query.filter_by(class_id=c['class_id']).first():
                        cls = Class(
                            class_id=c['class_id'],
                            class_name=c['class_name'],
                            department=c['department'],
                            semester=c.get('semester'),
                            section=c.get('section')
                        )
                        db.session.add(cls)
            print("Classes migrated.")

        # 3. Migrate Students
        students_path = os.path.join(data_dir, 'students.json')
        if os.path.exists(students_path):
            with open(students_path, 'r') as f:
                students = json.load(f)
                for s in students:
                    if not Student.query.filter_by(student_id=s['student_id']).first():
                        student = Student(
                            student_id=s['student_id'],
                            roll_number=s.get('roll_number', s['student_id']),
                            name=s['name'],
                            class_id=s['class_id'],
                            email=s.get('email', ''),
                            phone=s.get('phone', ''),
                            department=s.get('department', 'AI&DS'),
                            parent_email=s.get('parent_email', ''),
                            parent_phone=s.get('parent_phone', '')
                        )
                        db.session.add(student)
            print("Students migrated.")

        # 4. Migrate Attendance
        attendance_path = os.path.join(data_dir, 'attendance.json')
        if os.path.exists(attendance_path):
            with open(attendance_path, 'r') as f:
                attendance = json.load(f)
                for a in attendance:
                    if not AttendanceRecord.query.filter_by(record_id=a['record_id']).first():
                        # Handle created_at date
                        created_at = datetime.now()
                        if 'created_at' in a:
                            try:
                                created_at = datetime.fromisoformat(a['created_at'])
                            except:
                                pass

                        record = AttendanceRecord(
                            record_id=a['record_id'],
                            class_id=a['class_id'],
                            date=a['date'],
                            attendance_type=a['attendance_type'],
                            period=a.get('period'),
                            student_id=a['student_id'],
                            status=a['status'],
                            is_late=a.get('is_late', False),
                            marked_by=a.get('marked_by', ''),
                            locked=a.get('locked', False),
                            submitted_as_type=a.get('submitted_as_type', 'period'),
                            created_at=created_at
                        )
                        db.session.add(record)
            print("Attendance records migrated.")

        db.session.commit()
        print("Migration completed successfully!")

if __name__ == '__main__':
    migrate()
