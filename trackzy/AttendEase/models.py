from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'staff', 'hod', 'admin'
    name = db.Column(db.String(100), nullable=False)
    assigned_classes = db.Column(db.JSON, default=[]) # List of class_ids
    profile_pic = db.Column(db.String(200), nullable=True)

class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.String(50), unique=True, nullable=False)
    class_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer)
    section = db.Column(db.String(10))

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    roll_number = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100), default="AI&DS")
    parent_email = db.Column(db.String(100))
    parent_phone = db.Column(db.String(20))

    def to_dict(self):
        return {
            'student_id': self.student_id,
            'roll_number': self.roll_number,
            'name': self.name,
            'class_id': self.class_id,
            'email': self.email,
            'phone': self.phone,
            'department': self.department,
            'parent_email': self.parent_email,
            'parent_phone': self.parent_phone,
        }

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.String(100), unique=True, nullable=False)
    class_id = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(20), nullable=False) # YYYY-MM-DD
    attendance_type = db.Column(db.String(20), nullable=False) # 'day' or 'period'
    period = db.Column(db.Integer)
    student_id = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False) # 'present', 'absent'
    is_late = db.Column(db.Boolean, default=False)
    marked_by = db.Column(db.String(50), nullable=False)
    locked = db.Column(db.Boolean, default=False)
    submitted_as_type = db.Column(db.String(20), default="period")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GraduatedStudent(db.Model):
    __tablename__ = 'graduated_students'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    roll_number = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    final_class_id = db.Column(db.String(50), nullable=False) # The class they graduated from
    graduation_date = db.Column(db.DateTime, default=datetime.utcnow)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100), default="AI&DS")
    parent_email = db.Column(db.String(100))
    parent_phone = db.Column(db.String(20))
    final_cgpa = db.Column(db.Float) # Optional field for CGPA
    graduation_year = db.Column(db.String(10)) # e.g., "2024-2025"

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(50), nullable=False)
    sender_name = db.Column(db.String(100), nullable=False)
    receiver_id = db.Column(db.String(50), nullable=False)
    receiver_name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    submitted_as_type = db.Column(db.String(20), default="period")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    class_id = db.Column(db.String(50), nullable=False) # 'all' or specific class_id
    staff_id = db.Column(db.String(50), nullable=False)
    staff_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
