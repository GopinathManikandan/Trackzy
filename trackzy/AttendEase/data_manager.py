import os
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from models import db, User, Class, Student, AttendanceRecord, GraduatedStudent, Announcement
import csv

class DataManager:
    def __init__(self):
        # No more data_dir needed as we use SQL
        pass

    # User management methods
    def get_user_by_username(self, username: str) -> Optional[User]:
        return User.query.filter_by(username=username).first()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return User.query.filter_by(user_id=user_id).first()

    def get_users_by_role(self, role: str) -> List[User]:
        return User.query.filter_by(role=role).all()

    def get_user_name_by_id(self, user_id: str) -> str:
        user = self.get_user_by_id(user_id)
        return user.name if user else "Unknown"

    def create_staff_user(self, username: str, password: str, name: str, assigned_classes: List[str] = None) -> bool:
        """Create a new staff user"""
        if self.get_user_by_username(username):
            return False  # Username already exists
        
        if assigned_classes is None:
            assigned_classes = ["1st Year A","1st Year B","2nd Year A", "2nd Year B", "3rd Year A", "3rd Year B", "Final Year"]
        
        user = User(
            user_id=username,  # Use username as user_id
            username=username,
            password=password,
            role='staff',
            name=name,
            assigned_classes=assigned_classes
        )
        db.session.add(user)
        db.session.commit()
        return True

    def delete_staff_user(self, username: str) -> bool:
        """Delete a staff user"""
        user = self.get_user_by_username(username)
        if not user or user.role != 'staff':
            return False
        
        db.session.delete(user)
        db.session.commit()
        return True

    def update_staff_classes(self, username: str, assigned_classes: List[str]) -> bool:
        """Update assigned classes for a staff user"""
        user = self.get_user_by_username(username)
        if not user or user.role != 'staff':
            return False
        
        user.assigned_classes = assigned_classes
        db.session.commit()
        return True

    def get_all_staff_users(self) -> List[User]:
        """Get all staff users"""
        return User.query.filter_by(role='staff').all()

    # Class management methods
    def get_all_classes(self) -> List[Class]:
        return Class.query.order_by(Class.semester.asc(), Class.section.asc()).all()

    def get_class_by_id(self, class_id: str) -> Optional[Class]:
        return Class.query.filter_by(class_id=class_id).first()

    def get_classes_by_ids(self, class_ids: List[str]) -> List[Class]:
        return Class.query.filter(Class.class_id.in_(class_ids)).order_by(Class.semester.asc(), Class.section.asc()).all()

    def add_class(self, class_id: str, class_name: str, department: str = 'AI&DS', semester: int = 1, section: str = None) -> bool:
        if self.get_class_by_id(class_id):
            return False
        new_class = Class(
            class_id=class_id,
            class_name=class_name,
            department=department,
            semester=semester,
            section=section
        )
        db.session.add(new_class)
        db.session.commit()
        return True

    def delete_class(self, class_id: str) -> bool:
        """Delete a class if it has no students"""
        class_obj = self.get_class_by_id(class_id)
        if not class_obj:
            return False
        
        # Check if students exist in this class
        students_count = Student.query.filter_by(class_id=class_id).count()
        if students_count > 0:
            return False
        
        db.session.delete(class_obj)
        db.session.commit()
        return True

    def update_class(self, class_id: str, updates: Dict) -> bool:
        """Update class details"""
        class_obj = self.get_class_by_id(class_id)
        if not class_obj:
            return False
        
        if 'class_name' in updates:
            class_obj.class_name = updates['class_name']
        if 'semester' in updates:
            class_obj.semester = updates['semester']
        if 'section' in updates:
            class_obj.section = updates['section']
        
        db.session.commit()
        return True

    # Announcement management methods
    def get_announcements_for_class(self, class_id: str) -> List[Announcement]:
        """Get announcements for a specific class or 'all'"""
        return Announcement.query.filter(
            (Announcement.class_id == class_id) | (Announcement.class_id == 'all')
        ).order_by(Announcement.created_at.desc()).all()

    def get_staff_announcements(self, staff_id: str) -> List[Announcement]:
        """Get announcements posted by a specific staff member"""
        return Announcement.query.filter_by(staff_id=staff_id).order_by(Announcement.created_at.desc()).all()

    def delete_announcement(self, announcement_id: int, staff_id: str) -> bool:
        """Delete an announcement if it belongs to the staff member"""
        announcement = Announcement.query.filter_by(id=announcement_id, staff_id=staff_id).first()
        if announcement:
            db.session.delete(announcement)
            db.session.commit()
            return True
        return False

    def add_announcement(self, content: str, class_id: str, staff_id: str, staff_name: str) -> bool:
        """Add a new announcement with IST timestamp"""
        # Calculate IST (GMT + 5:30)
        from datetime import datetime, timedelta
        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        
        new_announcement = Announcement(
            content=content,
            class_id=class_id,
            staff_id=staff_id,
            staff_name=staff_name,
            created_at=ist_now
        )
        db.session.add(new_announcement)
        db.session.commit()
        return True

    # Student management methods
    def get_students_by_class(self, class_id: str) -> List[Student]:
        return Student.query.filter_by(class_id=class_id).all()

    def get_student_by_id(self, student_id: str) -> Optional[Student]:
        return Student.query.filter_by(student_id=student_id).first()

    def get_student_by_user_id(self, user_id: str) -> Optional[Student]:
        """Map a logged-in student user ID to a Student record."""
        return self.get_student_by_id(user_id)

    def get_student_attendance(self, student_id: str) -> List[AttendanceRecord]:
        return self.get_student_attendance_history(student_id)

    def get_any_student_by_id(self, student_id: str) -> Optional[Any]:
        """Get a student from either active or graduated table"""
        student = Student.query.filter_by(student_id=student_id).first()
        if student:
            return student
        return GraduatedStudent.query.filter_by(student_id=student_id).first()

    def search_students(self, query: str) -> List[Student]:
        search = f"%{query}%"
        return Student.query.filter(
            (Student.name.ilike(search)) | 
            (Student.student_id.ilike(search))
        ).all()

    def search_any_students(self, query: str) -> List[Any]:
        """Search in both active and graduated students"""
        search = f"%{query}%"
        active = Student.query.filter(
            (Student.name.ilike(search)) | 
            (Student.student_id.ilike(search))
        ).all()
        
        graduated = GraduatedStudent.query.filter(
            (GraduatedStudent.name.ilike(search)) | 
            (GraduatedStudent.student_id.ilike(search))
        ).all()
        
        return active + graduated

    def sync_student_accounts(self) -> int:
        """Create or update user accounts for all students"""
        students = Student.query.all()
        count = 0
        for s in students:
            # Check if user already exists
            existing_user = User.query.filter_by(user_id=s.student_id).first()
            if not existing_user:
                # Username = Exact Name, Password = Student ID
                base_username = s.name.strip()
                username = base_username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username} {counter}"
                    counter += 1

                new_user = User(
                    user_id=s.student_id,
                    username=username,
                    password=s.student_id,
                    role='student',
                    name=s.name,
                    assigned_classes=[]
                )
                db.session.add(new_user)
                count += 1
            else:
                # Update existing user to use exact name without underscores
                base_username = s.name.strip()
                username = base_username
                counter = 1
                # Only update if current username is different from exact name
                if existing_user.username != username:
                    while User.query.filter_by(username=username).filter(User.user_id != s.student_id).first():
                        username = f"{base_username} {counter}"
                        counter += 1
                    existing_user.username = username
                    existing_user.name = s.name
                    count += 1

        db.session.commit()
        return count
    def add_student(self, student_data: Dict) -> (bool, str):
        try:
            student_id = student_data.get('student_id')
            if not student_id:
                return False, "Missing student_id"
                
            existing_student = self.get_student_by_id(student_id)
            if existing_student:
                # Update existing student instead of failing
                for key, value in student_data.items():
                    if hasattr(existing_student, key):
                        setattr(existing_student, key, value)
            else:
                new_student = Student(**student_data)
                db.session.add(new_student)
            
            # Create or update user account
            existing_user = User.query.filter_by(user_id=student_id).first()
            if not existing_user:
                # Username = Name (ensure unique), Password = Roll Number
                base_username = student_data.get('name', 'Student')
                username = base_username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username} {counter}"
                    counter += 1
                
                new_user = User(
                    user_id=student_id,
                    username=username,
                    password=student_data.get('roll_number', student_id),
                    role='student',
                    name=student_data.get('name'),
                    assigned_classes=[]
                )
                db.session.add(new_user)
            else:
                # User exists, update name and credentials
                existing_user.name = student_data.get('name')
                
                # Check if we need to update username and ensure it stays unique
                base_username = student_data.get('name', 'Student')
                if existing_user.username != base_username:
                    username = base_username
                    counter = 1
                    while User.query.filter_by(username=username).filter(User.user_id != student_id).first():
                        username = f"{base_username} {counter}"
                        counter += 1
                    existing_user.username = username
                
                existing_user.password = student_data.get('roll_number', student_id)
                existing_user.role = 'student'
            
            db.session.commit()
            return True, "Success"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    def update_student(self, student_id: str, updates: Dict) -> bool:
        student = self.get_student_by_id(student_id)
        if not student:
            return False
        
        for key, value in updates.items():
            if hasattr(student, key):
                setattr(student, key, value)
        
        db.session.commit()
        return True

    def delete_student(self, student_id: str) -> bool:
        student = self.get_student_by_id(student_id)
        if not student:
            return False
        
        db.session.delete(student)
        db.session.commit()
        return True

    def delete_students_by_class(self, class_id: str) -> int:
        """Delete all students from a specific class"""
        students = Student.query.filter_by(class_id=class_id).all()
        count = len(students)
        for student in students:
            db.session.delete(student)
        db.session.commit()
        return count

    def import_students_from_csv(self, csv_filepath: str):
        count = 0
        try:
            with open(csv_filepath, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    student_id = row.get('student_id')
                    if not student_id: continue
                    
                    # Create or update
                    student = self.get_student_by_id(student_id)
                    if not student:
                        student = Student(student_id=student_id)
                        db.session.add(student)
                    
                    student.roll_number = student_id
                    student.name = (row.get('name', '') or row.get('student_name', '')).strip()
                    student.class_id = row.get('class_id', '')
                    student.department = row.get('department', 'AI&DS')
                    student.email = row.get('email', '')
                    student.phone = row.get('phone', '')
                    student.parent_email = row.get('parent_email', '')
                    student.parent_phone = row.get('parent_phone', '')
                    
                    # Also create/update user account
                    existing_user = User.query.filter_by(user_id=student_id).first()
                    if not existing_user:
                        new_user = User(
                            user_id=student_id,
                            username=student.name, # Username is student name
                            password=student_id,   # Password is roll number/ID
                            role='student',
                            name=student.name,
                            assigned_classes=[]
                        )
                        db.session.add(new_user)
                    else:
                        existing_user.username = student.name
                        existing_user.password = student_id
                        existing_user.name = student.name
                    
                    count += 1
            
            db.session.commit()
            return count
        except Exception as e:
            print(f"Error importing students: {e}")
            db.session.rollback()
            return 0

    # Attendance management methods
    def save_attendance_records(self, records: List[AttendanceRecord]):
        # Records passed here are usually model objects already
        for record in records:
            db.session.add(record)
        db.session.commit()

    def get_attendance_records(self, class_id: str = None, date_str: str = None, 
                             attendance_type: str = None, period: int = None) -> List[AttendanceRecord]:
        query = AttendanceRecord.query
        if class_id:
            query = query.filter_by(class_id=class_id)
        if date_str:
            query = query.filter_by(date=date_str)
        if attendance_type:
            query = query.filter_by(attendance_type=attendance_type)
            if attendance_type == 'period' and period:
                query = query.filter_by(period=period)
            elif attendance_type == 'day':
                query = query.filter_by(period=1)
        
        return query.all()

    def is_attendance_locked(self, class_id: str, date_str: str, attendance_type: str, period: int = None) -> bool:
        records = self.get_attendance_records(class_id, date_str, attendance_type, period)
        return any(r.locked for r in records)

    def lock_attendance(self, class_id: str, date_str: str, attendance_type: str, period: int = None):
        records = self.get_attendance_records(class_id, date_str, attendance_type, period)
        for record in records:
            record.locked = True
        db.session.commit()

    def update_attendance_record(self, record_id: str, updates: Dict):
        record = AttendanceRecord.query.filter_by(record_id=record_id).first()
        if record:
            for key, value in updates.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            db.session.commit()

    def get_class_attendance_summary(self, class_id: str, date_str: str, attendance_type: str = 'day', period: int = None) -> Dict:
        records = self.get_attendance_records(class_id, date_str, attendance_type, period)
        students = self.get_students_by_class(class_id)
        
        summary = {
            'total_students': len(students),
            'present': 0,
            'absent': 0,
            'late': 0,
            'percentage': 0.0,
            'locked': False,
            'marked_by_user': 'N/A',
            'trend': 0.0
        }
        
        if records:
            # Only count students that are actually in the class currently
            student_ids = {s.student_id for s in students}
            present_students = [r for r in records if r.status == 'present' and r.student_id in student_ids]
            late_students = [r for r in records if r.status == 'present' and r.is_late and r.student_id in student_ids]

            summary['present'] = len(present_students)
            summary['late'] = len(late_students)
            summary['absent'] = max(0, summary['total_students'] - summary['present'])
            summary['percentage'] = (summary['present'] / summary['total_students']) * 100 if summary['total_students'] > 0 else 0
            summary['locked'] = any(r.locked for r in records)
            summary['marked_by_user'] = self.get_user_name_by_id(records[0].marked_by)            
            # Calculate trend (compare with yesterday)
            try:
                yesterday = (datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
                yesterday_records = self.get_attendance_records(class_id, yesterday, attendance_type, period)
                if yesterday_records:
                    yesterday_present = len([r for r in yesterday_records if r.status == 'present'])
                    yesterday_percentage = (yesterday_present / len(students)) * 100 if students else 0
                    summary['trend'] = summary['percentage'] - yesterday_percentage
            except:
                summary['trend'] = 0.0
        
        return summary

    def get_student_attendance_history(self, student_id: str, start_date: str = None, end_date: str = None) -> List[AttendanceRecord]:
        query = AttendanceRecord.query.filter_by(student_id=student_id)
        if start_date:
            query = query.filter(AttendanceRecord.date >= start_date)
        if end_date:
            query = query.filter(AttendanceRecord.date <= end_date)
        
        return query.order_by(AttendanceRecord.date.desc()).all()

    def mark_attendance(self, class_id: str, attendance_data: List[Dict], marked_by: str, date_str: str = None, attendance_type: str = 'day', period: int = 1) -> bool:
        if not attendance_data or not class_id or not marked_by:
            return False

        date_str = date_str or datetime.now().strftime('%Y-%m-%d')
        records = []

        for item in attendance_data:
            student_id = item.get('student_id')
            status = item.get('status', 'absent')
            is_late = item.get('is_late', False)
            if not student_id:
                continue

            existing = AttendanceRecord.query.filter_by(
                class_id=class_id,
                date=date_str,
                attendance_type=attendance_type,
                period=period,
                student_id=student_id
            ).first()

            if existing:
                existing.status = status
                existing.is_late = is_late
                existing.marked_by = marked_by
                existing.locked = False
                records.append(existing)
            else:
                record = AttendanceRecord(
                    record_id=str(uuid.uuid4()),
                    class_id=class_id,
                    date=date_str,
                    attendance_type=attendance_type,
                    period=period,
                    student_id=student_id,
                    status=status,
                    is_late=is_late,
                    marked_by=marked_by,
                    locked=False
                )
                records.append(record)

        if records:
            self.save_attendance_records(records)
            return True
        return False

    def mark_latecomer_attendance(self, student_ids: List[str], class_id: str, date_str: str, marked_by: str, attendance_type: str = 'day', period: int = 1) -> bool:
        if not student_ids or not class_id or not marked_by or not date_str:
            return False

        for student_id in student_ids:
            existing = AttendanceRecord.query.filter_by(
                class_id=class_id,
                date=date_str,
                attendance_type=attendance_type,
                period=period,
                student_id=student_id
            ).first()

            if existing:
                existing.status = 'present'
                existing.is_late = True
                existing.marked_by = marked_by
                existing.locked = False
            else:
                record = AttendanceRecord(
                    record_id=str(uuid.uuid4()),
                    class_id=class_id,
                    date=date_str,
                    attendance_type=attendance_type,
                    period=period,
                    student_id=student_id,
                    status='present',
                    is_late=True,
                    marked_by=marked_by,
                    locked=False
                )
                db.session.add(record)

        db.session.commit()
        return True

    def get_attendance_report(self, class_id: str, start_date: str = None, end_date: str = None) -> Dict:
        query = AttendanceRecord.query.filter_by(class_id=class_id)
        if start_date:
            query = query.filter(AttendanceRecord.date >= start_date)
        if end_date:
            query = query.filter(AttendanceRecord.date <= end_date)

        records = query.all()
        total = len(records)
        present = len([r for r in records if r.status == 'present'])
        absent = len([r for r in records if r.status == 'absent'])

        return {
            'class_id': class_id,
            'date_range': {'start': start_date, 'end': end_date},
            'total_records': total,
            'present': present,
            'absent': absent,
            'percentage': (present / total) * 100 if total > 0 else 0
        }

    def get_overall_attendance_report(self, start_date: str = None, end_date: str = None) -> Dict:
        query = AttendanceRecord.query
        if start_date:
            query = query.filter(AttendanceRecord.date >= start_date)
        if end_date:
            query = query.filter(AttendanceRecord.date <= end_date)

        records = query.all()
        total = len(records)
        present = len([r for r in records if r.status == 'present'])
        absent = len([r for r in records if r.status == 'absent'])

        return {
            'date_range': {'start': start_date, 'end': end_date},
            'total_records': total,
            'present': present,
            'absent': absent,
            'percentage': (present / total) * 100 if total > 0 else 0
        }

    def promote_students(self, from_class_id: str, to_class_id: str, student_ids: List[str]) -> bool:
        if not from_class_id or not to_class_id or not student_ids:
            return False

        students = Student.query.filter(Student.student_id.in_(student_ids), Student.class_id == from_class_id).all()
        if not students:
            return False

        for student in students:
            student.class_id = to_class_id

        db.session.commit()
        return True

    def get_department_attendance_summary(self, date_str: str, attendance_type: str = 'day', period: int = None) -> Dict:
        all_classes = self.get_all_classes()
        summary = {
            'classes': [],
            'total_students': 0,
            'total_present': 0,
            'overall_percentage': 0.0
        }
        
        for class_obj in all_classes:
            class_summary = self.get_class_attendance_summary(class_obj.class_id, date_str, attendance_type, period)
            class_summary['class_name'] = class_obj.class_name
            class_summary['class_id'] = class_obj.class_id
            summary['classes'].append(class_summary)
            summary['total_students'] += class_summary['total_students']
            summary['total_present'] += class_summary['present']
        
        if summary['total_students'] > 0:
            summary['overall_percentage'] = (summary['total_present'] / summary['total_students']) * 100
        
        return summary

    def promote_students_academic_year(self) -> Dict[str, int]:
        """
        Promote students to the next academic year:
        - Final Year students pass out (are removed)
        - 3rd Year students move to Final Year
        - 2nd Year students move to 3rd Year (maintaining sections)
        
        Returns a dictionary with counts of affected students
        """
        result = {
            'final_year_passed_out': 0,
            'third_year_promoted': 0,
            'second_year_promoted': 0
        }
        
        try:
            # 1. Move Final Year students to Graduated Students table (they pass out)
            final_year_students = Student.query.filter_by(class_id='Final Year').all()
            result['final_year_passed_out'] = len(final_year_students)
            
            for student in final_year_students:
                # Check if already graduated to avoid UNIQUE constraint violation
                existing_graduated = GraduatedStudent.query.filter_by(student_id=student.student_id).first()
                
                if not existing_graduated:
                    # Create graduated student record
                    graduated_student = GraduatedStudent(
                        student_id=student.student_id,
                        roll_number=student.roll_number,
                        name=student.name,
                        final_class_id=student.class_id,
                        email=student.email,
                        phone=student.phone,
                        department=student.department,
                        parent_email=student.parent_email,
                        parent_phone=student.parent_phone,
                        graduation_year=datetime.now().strftime('%Y')
                    )
                    db.session.add(graduated_student)
                else:
                    # If already in graduated table, just update the graduation year if needed
                    # but definitely don't try to add a new record with the same student_id
                    existing_graduated.graduation_year = datetime.now().strftime('%Y')
                
                # Remove from active students
                db.session.delete(student)
            
            # 2. Promote 3rd Year students to Final Year
            third_year_students = Student.query.filter(Student.class_id.in_(['3rd Year', '3rd Year A', '3rd Year B'])).all()
            result['third_year_promoted'] = len(third_year_students)
            
            for student in third_year_students:
                student.class_id = 'Final Year'
            
            # 3. Promote 2nd Year students to 3rd Year (maintaining sections)
            # 2nd Year A → 3rd Year A
            second_year_a_students = Student.query.filter_by(class_id='2nd Year A').all()
            for student in second_year_a_students:
                student.class_id = '3rd Year A'
            
            # 2nd Year B → 3rd Year B
            second_year_b_students = Student.query.filter_by(class_id='2nd Year B').all()
            for student in second_year_b_students:
                student.class_id = '3rd Year B'
            
            result['second_year_promoted'] = len(second_year_a_students) + len(second_year_b_students)
            
            # Commit all changes
            db.session.commit()
            
            return result
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error during student promotion: {str(e)}")

    # Graduated Students management methods
    def get_graduated_students(self) -> List[GraduatedStudent]:
        """Get all graduated students"""
        return GraduatedStudent.query.order_by(GraduatedStudent.graduation_date.desc()).all()

    def get_graduated_student_by_id(self, student_id: str) -> Optional[GraduatedStudent]:
        """Get a specific graduated student by ID"""
        return GraduatedStudent.query.filter_by(student_id=student_id).first()

    def search_graduated_students(self, query: str) -> List[GraduatedStudent]:
        """Search graduated students by name or roll number"""
        search_filter = f"%{query}%"
        return GraduatedStudent.query.filter(
            (GraduatedStudent.name.ilike(search_filter)) |
            (GraduatedStudent.roll_number.ilike(search_filter)) |
            (GraduatedStudent.student_id.ilike(search_filter))
        ).order_by(GraduatedStudent.graduation_date.desc()).all()

    def get_graduated_students_by_year(self, year: str) -> List[GraduatedStudent]:
        """Get graduated students by graduation year"""
        return GraduatedStudent.query.filter_by(graduation_year=year).order_by(GraduatedStudent.name).all()

# Global instance
data_manager = DataManager()
