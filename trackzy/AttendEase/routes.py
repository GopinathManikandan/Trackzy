import os
from flask import render_template, request, redirect, url_for, session, flash, jsonify, make_response
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import or_
import uuid
import json
from app import app
from data_manager import data_manager
from models import db, User, Class, Student, AttendanceRecord, GraduatedStudent, Message
from notifications import send_absence_email

@app.route('/')
def index():
    """Home page - redirect to login if not authenticated"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    if user.role == 'staff':
        return redirect(url_for('staff_dashboard'))
    elif user.role == 'hod' or user.role == 'admin':
        return redirect(url_for('hod_dashboard'))
    elif user.role == 'student':
        return redirect(url_for('student_dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        selected_role = request.form.get('role', '').strip()
        
        if not username or not password or not selected_role:
            flash('Please enter username, password, and select your role', 'error')
            return render_template('login.html')
        
        user = data_manager.get_user_by_username(username)
        
        # If user not found by username, try finding by user_id (common for students to use roll number)
        if not user:
            user = data_manager.get_user_by_id(username)
            
        # Check password and role (allow 'admin' role to login as 'hod')
        role_matches = (user.role == selected_role) or (selected_role == 'hod' and user.role == 'admin')
        
        if user and user.password == password and role_matches:
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['user_role'] = user.role
            session['user_name'] = user.name
            
            app.logger.info(f"User {username} logged in successfully as {user.role}")
            flash(f'Welcome, {user.name}!', 'success')
            return redirect(url_for('index'))
        else:
            if not user:
                app.logger.warning(f"Login failed: User {username} not found")
            elif user.password != password:
                app.logger.warning(f"Login failed: Incorrect password for user {username}")
            elif not role_matches:
                app.logger.warning(f"Login failed: Role mismatch for user {username}. DB role: {user.role}, Selected role: {selected_role}")
            
            flash('Invalid credentials or role mismatch', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/staff_dashboard')
def staff_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'staff':
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    # Get only classes assigned to this staff member
    classes = data_manager.get_classes_by_ids(user.assigned_classes) if user.assigned_classes else []
    
    # Generate class summaries for today
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    class_summaries = []
    
    for class_obj in classes:
        summary = data_manager.get_class_attendance_summary(class_obj.class_id, today)
        summary['class'] = class_obj  # Add the class object to the summary
        class_summaries.append(summary)
    
    # Calculate average percentage
    avg_percentage = sum(s['percentage'] for s in class_summaries) / len(class_summaries) if class_summaries else 0
    
    all_classes = data_manager.get_all_classes()
    staff_announcements = data_manager.get_staff_announcements(user.user_id)
    
    return render_template('staff_dashboard.html', user=user, classes=classes,
                         class_summaries=class_summaries, today=today, avg_percentage=avg_percentage,
                         all_classes=all_classes, staff_announcements=staff_announcements)

@app.route('/post_announcement', methods=['POST'])
def post_announcement():
    if 'user_id' not in session or session.get('user_role') != 'staff':
        return redirect(url_for('login'))

    content = request.form.get('content')
    class_id = request.form.get('class_id')

    if not content or not class_id:
        flash('Content and Target Class are required.', 'error')
        return redirect(url_for('staff_dashboard'))

    success = data_manager.add_announcement(
        content=content,
        class_id=class_id,
        staff_id=session['user_id'],
        staff_name=session.get('user_name', 'Staff')
    )

    if success:
        flash('Announcement posted successfully!', 'success')
    else:
        flash('Failed to post announcement.', 'error')

    return redirect(url_for('staff_dashboard'))

@app.route('/delete_announcement/<int:announcement_id>', methods=['POST'])
def delete_announcement_route(announcement_id):
    if 'user_id' not in session or session.get('user_role') != 'staff':
        return redirect(url_for('login'))
    
    success = data_manager.delete_announcement(announcement_id, session['user_id'])
    if success:
        flash('Announcement deleted.', 'success')
    else:
        flash('Failed to delete announcement.', 'error')
    
    return redirect(url_for('staff_dashboard'))

@app.route('/hod_dashboard')
def hod_dashboard():
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    classes = data_manager.get_all_classes()
    all_staff = data_manager.get_all_staff_users()
    today = datetime.now().strftime('%Y-%m-%d')
    dept_summary = data_manager.get_department_attendance_summary(today)
    return render_template('hod_dashboard.html', user=user, classes=classes, all_staff=all_staff, today=today, dept_summary=dept_summary)

@app.route('/create_class', methods=['POST'])
def create_class():
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))

    class_id = request.form.get('class_id', '').strip()
    class_name = request.form.get('class_name', '').strip()
    semester = request.form.get('semester', '').strip()
    section = request.form.get('section', '').strip()

    if not class_id or not class_name or not semester:
        flash('Please provide class ID, class name, and semester.', 'error')
        return redirect(url_for('hod_dashboard'))

    try:
        semester_value = int(semester)
    except ValueError:
        flash('Semester must be a valid number.', 'error')
        return redirect(url_for('hod_dashboard'))

    success = data_manager.add_class(
        class_id=class_id,
        class_name=class_name,
        semester=semester_value,
        section=section or None
    )

    if success:
        flash('Class created successfully.', 'success')
    else:
        flash('A class with that ID already exists.', 'error')

    return redirect(url_for('hod_dashboard'))

@app.route('/delete_class/<class_id>', methods=['POST'])
def delete_class(class_id):
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))
    
    success = data_manager.delete_class(class_id)
    if success:
        flash(f'Class {class_id} deleted successfully.', 'success')
    else:
        flash(f'Failed to delete class {class_id}. Make sure it is empty.', 'error')
    
    return redirect(url_for('hod_dashboard'))

@app.route('/update_class', methods=['POST'])
def update_class():
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))

    class_id = request.form.get('class_id')
    class_name = request.form.get('class_name')
    semester = request.form.get('semester')
    section = request.form.get('section')

    if not class_id or not class_name:
        flash('Class ID and Name are required.', 'error')
        return redirect(url_for('hod_dashboard'))

    updates = {
        'class_name': class_name,
        'semester': int(semester) if semester else None,
        'section': section
    }

    success = data_manager.update_class(class_id, updates)
    if success:
        flash(f'Class {class_id} updated successfully.', 'success')
    else:
        flash(f'Failed to update class {class_id}.', 'error')

    return redirect(url_for('hod_dashboard'))

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    student = data_manager.get_student_by_user_id(session['user_id'])
    if not student:
        flash('Student profile not found.', 'error')
        return redirect(url_for('login'))
    
    # Get filters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    attendance_type = request.args.get('attendance_type', 'all')
    period = request.args.get('period')
    status_filter = request.args.get('status', 'all')
    show_all = request.args.get('show_all') == 'true'

    # Get raw attendance records
    attendance_records = data_manager.get_student_attendance(student.student_id)

    # Apply filters
    filtered_history = attendance_records
    is_today_view = False
    display_date = None
    
    # Logic for "Only Latest Day" default view
    if not (start_date or end_date or attendance_type != 'all' or status_filter != 'all' or show_all):
        if attendance_records:
            latest_date = max(r.date for r in attendance_records)
            filtered_history = [r for r in attendance_records if r.date == latest_date]
            # Sort: Day first, then periods 1-8
            day_att = [r for r in filtered_history if r.attendance_type == 'day']
            period_att = sorted([r for r in filtered_history if r.attendance_type == 'period'], key=lambda x: x.period or 0)
            filtered_history = day_att + period_att
            is_today_view = True
            display_date = latest_date
    else:
        # Standard filtering logic
        if start_date:
            filtered_history = [r for r in filtered_history if str(r.date) >= start_date]
        if end_date:
            filtered_history = [r for r in filtered_history if str(r.date) <= end_date]
        if attendance_type != 'all':
            filtered_history = [r for r in filtered_history if r.attendance_type == attendance_type]
            if attendance_type == 'period' and period:
                filtered_history = [r for r in filtered_history if str(r.period) == str(period)]
        if status_filter != 'all':
            if status_filter == 'late':
                filtered_history = [r for r in filtered_history if r.status == 'present' and r.is_late]
            else:
                filtered_history = [r for r in filtered_history if r.status == status_filter]
        
        # Sort filtered history by date desc, then by type/period
        filtered_history.sort(key=lambda x: (x.date, 0 if x.attendance_type == 'day' else x.period or 0), reverse=True)

    # Calculate statistics based on full history for overall view
    total_days = len(attendance_records)
    present_days = sum(1 for r in attendance_records if r.status == 'present')
    absent_days = total_days - present_days
    late_count = sum(1 for r in attendance_records if r.status == 'present' and r.is_late)
    percentage = (present_days / total_days * 100) if total_days > 0 else 0

    stats = {
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'late_count': late_count,
        'percentage': percentage,
        'filtered_count': len(filtered_history),
        'filtered_present': sum(1 for r in filtered_history if r.status == 'present'),
        'filtered_absent': sum(1 for r in filtered_history if r.status == 'absent'),
        'filtered_late': sum(1 for r in filtered_history if r.status == 'present' and r.is_late)
    }

    class_obj = data_manager.get_class_by_id(student.class_id)
    announcements = data_manager.get_announcements_for_class(student.class_id)

    return render_template('student_dashboard.html',
                         user=user,
                         student=student,
                         class_obj=class_obj,
                         history=filtered_history,
                         stats=stats,
                         start_date=start_date,
                         end_date=end_date,
                         attendance_type=attendance_type,
                         period=period,
                         status_filter=status_filter,
                         is_today_view=is_today_view,
                         display_date=display_date,
                         announcements=announcements)
@app.route('/mark_attendance/<class_id>', methods=['GET', 'POST'])
def mark_attendance(class_id):
    if 'user_id' not in session or session.get('user_role') != 'staff':
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    class_obj = data_manager.get_class_by_id(class_id)
    if not class_obj:
        flash('Class not found.', 'error')
        return redirect(url_for('staff_dashboard'))
    
    # Get query/form parameters
    date_str = request.values.get('date', datetime.now().strftime('%Y-%m-%d'))
    attendance_type = request.values.get('attendance_type', request.values.get('type', 'day'))
    period = request.values.get('period', 1)
    
    # Check if attendance is already locked for this specific period/date
    is_locked = data_manager.is_attendance_locked(
        class_id, 
        date_str, 
        attendance_type, 
        int(period) if period else 1
    )
    
    if request.method == 'POST':
        if is_locked:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Attendance is already locked for this period.'})
            flash('Attendance for this period has already been marked and locked.', 'warning')
            return redirect(url_for('staff_dashboard'))

        attendance_data = request.get_json(silent=True)
        if attendance_data is None:
            attendance_data = []
            students = data_manager.get_students_by_class(class_id)
            for student in students:
                status = 'present' if request.form.get(f'student_{student.student_id}') == 'present' else 'absent'
                attendance_data.append({
                    'student_id': student.student_id,
                    'status': status,
                    'is_late': False
                })
            date_str = request.form.get('date', date_str)
            attendance_type = request.form.get('attendance_type', attendance_type)
            period = request.form.get('period', period)

        success = False
        if attendance_data:
            success = data_manager.mark_attendance(
                class_id,
                attendance_data,
                session['user_id'],
                date_str,
                attendance_type,
                int(period) if period else 1
            )

            if success:
                # Lock attendance after successful first submission
                data_manager.lock_attendance(
                    class_id, 
                    date_str, 
                    attendance_type, 
                    int(period) if period else 1
                )
                
                if not request.is_json:
                    absent_students = [item for item in attendance_data if item.get('status') == 'absent']
                    for item in absent_students:
                        student = data_manager.get_student_by_id(item.get('student_id'))
                        if student:
                            recipients = [student.email, student.parent_email]
                            send_absence_email(
                                recipients, 
                                student.name, 
                                class_obj.class_name, 
                                date_str,
                                attendance_type=attendance_type,
                                period=period
                            )
        if request.is_json:
            return jsonify({'success': success})

        if success:
            flash('Attendance submitted successfully. Absence notifications were sent where applicable.', 'success')
            return redirect(url_for('staff_dashboard'))
        else:
            flash('Failed to submit attendance. Please try again.', 'error')

        return redirect(url_for('mark_attendance', class_id=class_id, date=date_str, type=attendance_type, period=period))
    
    students = data_manager.get_students_by_class(class_id)
    
    # Get existing attendance records for this date/time to pre-populate the form
    attendance_records = data_manager.get_attendance_records(class_id=class_id, date_str=date_str, 
                                                             attendance_type=attendance_type, 
                                                             period=int(period) if period else None)
    # Build attendance status dictionary
    attendance_status = {}
    for record in attendance_records:
        attendance_status[record.student_id] = record.status
    
    return render_template('mark_attendance.html', user=user, class_obj=class_obj, students=students, 
                         date_str=date_str, attendance_type=attendance_type, period=period, 
                         attendance_status=attendance_status, locked=is_locked)

@app.route('/class_details/<class_id>')
def class_details(class_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    class_obj = data_manager.get_class_by_id(class_id)
    if not class_obj:
        flash('Class not found.', 'error')
        return redirect(url_for('index'))
    
    students = data_manager.get_students_by_class(class_id)
    
    # Get filters
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    attendance_type = request.args.get('type', 'day')
    period = request.args.get('period', 1, type=int)
    
    attendance_summary = data_manager.get_class_attendance_summary(class_id, date_str, attendance_type, period)
    
    # Get attendance records for selected date/type/period
    attendance_records = data_manager.get_attendance_records(class_id=class_id, date_str=date_str, 
                                                             attendance_type=attendance_type, period=period)
    
    # Create student_attendance dict
    student_attendance = {}
    for student in students:
        # Find attendance record for this student
        record = next((r for r in attendance_records if r.student_id == student.student_id), None)
        if record:
            student_attendance[student.student_id] = {
                'status': record.status,
                'is_late': record.is_late,
                'student': student,
                'time': record.created_at.strftime('%H:%M') if record.created_at else 'N/A'
            }
        else:
            student_attendance[student.student_id] = {
                'status': 'absent',
                'is_late': False,
                'student': student,
                'time': 'N/A'
            }
    
    # Calculate weekly trend (last 7 days)
    weekly_trend = []
    for i in range(6, -1, -1):  # Last 7 days including the selected date
        try:
            base_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            base_date = datetime.now()
            
        iter_date_str = (base_date - timedelta(days=i)).strftime('%Y-%m-%d')
        day_summary = data_manager.get_class_attendance_summary(class_id, iter_date_str, attendance_type, period)
        weekly_trend.append({
            'date': iter_date_str,
            'percentage': day_summary['percentage'],
            'present': day_summary['present'],
            'total': day_summary['total_students']
        })
    
    return render_template('class_details.html', user=user, class_obj=class_obj, students=students, 
                         attendance_summary=attendance_summary, student_attendance=student_attendance, 
                         weekly_trend=weekly_trend, date_str=date_str, 
                         attendance_type=attendance_type, period=period)

@app.route('/student_details/<student_id>')
def student_details(student_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    student = data_manager.get_student_by_id(student_id)
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('index'))
    
    # Get filters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    attendance_type = request.args.get('attendance_type', 'all')
    period = request.args.get('period')
    status_filter = request.args.get('status', 'all')
    
    class_obj = data_manager.get_class_by_id(student.class_id)
    attendance_records = data_manager.get_student_attendance(student_id)
    
    # Apply filters
    filtered_records = attendance_records
    if start_date:
        filtered_records = [r for r in filtered_records if str(r.date) >= start_date]
    if end_date:
        filtered_records = [r for r in filtered_records if str(r.date) <= end_date]
    if attendance_type != 'all':
        filtered_records = [r for r in filtered_records if r.attendance_type == attendance_type]
        if attendance_type == 'period' and period:
            filtered_records = [r for r in filtered_records if str(r.period) == str(period)]
    if status_filter != 'all':
        filtered_records = [r for r in filtered_records if r.status == status_filter]
    
    # Sort filtered history by date desc, then by type/period
    filtered_records.sort(key=lambda x: (x.date, 0 if x.attendance_type == 'day' else x.period or 0), reverse=True)

    # Prepare daily summary for charts (using filtered records)
    daily_summary = []
    for record in filtered_records:
        daily_summary.append({
            'date': str(record.date),
            'status': record.status,
            'is_late': bool(record.is_late)
        })
    
    # Calculate attendance statistics based on FULL history
    total_days = len(attendance_records)
    present_days = sum(1 for r in attendance_records if r.status == 'present')
    absent_days = total_days - present_days
    late_count = sum(1 for r in attendance_records if r.status == 'present' and r.is_late)
    percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    stats = {
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'late_count': late_count,
        'percentage': percentage,
        'filtered_count': len(filtered_records),
        'filtered_present': sum(1 for r in filtered_records if r.status == 'present'),
        'filtered_absent': sum(1 for r in filtered_records if r.status == 'absent'),
        'filtered_late': sum(1 for r in filtered_records if r.status == 'present' and r.is_late)
    }
    
    return render_template('student_details.html', user=user, student=student, class_obj=class_obj, 
                         attendance_records=filtered_records, stats=stats, daily_summary=daily_summary,
                         start_date=start_date, end_date=end_date, attendance_type=attendance_type,
                         period=period, status_filter=status_filter)

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    classes = data_manager.get_all_classes()
    
    # Get parameters from query string
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    class_id = request.args.get('class_id')
    attendance_type = request.args.get('type', 'day')
    period = request.args.get('period', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    report_classes = []
    report_students = []
    total_students = 0
    total_present = 0
    
    # Get report data
    if class_id:
        # Filter for a specific class - show student list
        class_obj = data_manager.get_class_by_id(class_id)
        if class_obj:
            summary = data_manager.get_class_attendance_summary(class_id, date_str, attendance_type, period)
            total_students = summary['total_students']
            total_present = summary['present']
            
            # Get detailed student list for this class
            students = data_manager.get_students_by_class(class_id)
            records = data_manager.get_attendance_records(class_id=class_id, date_str=date_str, attendance_type=attendance_type, period=period)
            record_map = {r.student_id: r for r in records}
            
            for student in students:
                record = record_map.get(student.student_id)
                status = record.status if record else 'absent'
                is_late = record.is_late if record else False
                
                # Apply status filter
                if status_filter == 'all' or \
                   (status_filter == 'present' and status == 'present') or \
                   (status_filter == 'absent' and status == 'absent') or \
                   (status_filter == 'late' and is_late):
                    report_students.append({
                        'student_id': student.student_id,
                        'name': student.name,
                        'roll_number': student.roll_number,
                        'status': status,
                        'is_late': is_late,
                        'class_name': class_obj.class_name,
                        'marked_by': data_manager.get_user_name_by_id(record.marked_by) if record else 'N/A'
                    })
    else:
        # Get report data for all classes
        if status_filter == 'all':
            # Show class-wise summary
            for class_obj in classes:
                summary = data_manager.get_class_attendance_summary(class_obj.class_id, date_str, attendance_type, period)
                report_classes.append({
                    'class_id': class_obj.class_id,
                    'class_name': class_obj.class_name,
                    'total_students': summary['total_students'],
                    'present': summary['present'],
                    'absent': summary['total_students'] - summary['present'],
                    'late': summary.get('late', 0),
                    'percentage': summary['percentage']
                })
                total_students += summary['total_students']
                total_present += summary['present']
        else:
            # Show all students across the department matching the status filter
            for class_obj in classes:
                students = data_manager.get_students_by_class(class_obj.class_id)
                records = data_manager.get_attendance_records(class_id=class_obj.class_id, date_str=date_str, attendance_type=attendance_type, period=period)
                record_map = {r.student_id: r for r in records}
                
                class_summary = data_manager.get_class_attendance_summary(class_obj.class_id, date_str, attendance_type, period)
                total_students += class_summary['total_students']
                total_present += class_summary['present']
                
                for student in students:
                    record = record_map.get(student.student_id)
                    status = record.status if record else 'absent'
                    is_late = record.is_late if record else False
                    
                    if (status_filter == 'present' and status == 'present') or \
                       (status_filter == 'absent' and status == 'absent') or \
                       (status_filter == 'late' and is_late):
                        report_students.append({
                            'student_id': student.student_id,
                            'name': student.name,
                            'roll_number': student.roll_number,
                            'status': status,
                            'is_late': is_late,
                            'class_name': class_obj.class_name,
                            'marked_by': data_manager.get_user_name_by_id(record.marked_by) if record else 'N/A'
                        })
    
    report_data = {
        'classes': report_classes,
        'students': report_students,
        'total_students': total_students,
        'total_present': total_present,
        'overall_percentage': (total_present / total_students * 100) if total_students > 0 else 0,
        'attendance_type': attendance_type,
        'period': period,
        'status_filter': status_filter
    }
    
    return render_template('reports.html', user=user, classes=classes, report_data=report_data, date_str=date_str, selected_class_id=class_id)

@app.route('/get_report_data')
def get_report_data():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    class_id = request.args.get('class_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if class_id:
        report_data = data_manager.get_attendance_report(class_id, start_date, end_date)
    else:
        report_data = data_manager.get_overall_attendance_report(start_date, end_date)
    
    return jsonify(report_data)

@app.route('/promotion')
def promotion():
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    classes = data_manager.get_all_classes()
    return render_template('promotion.html', user=user, classes=classes)

@app.route('/promote_students', methods=['POST'])
def promote_students():
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))
    
    data = request.get_json(silent=True)
    if data is None:
        from_class_id = request.form.get('from_class')
        to_class_id = request.form.get('to_class')
        student_ids = [s.student_id for s in data_manager.get_students_by_class(from_class_id)] if from_class_id else []
    else:
        from_class_id = data.get('from_class_id')
        to_class_id = data.get('to_class_id')
        student_ids = data.get('student_ids', [])
    
    if not from_class_id or not to_class_id or not student_ids:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Invalid data provided'})
        flash('Invalid promotion request. Please select both source and destination classes.', 'error')
        return redirect(url_for('promotion'))
    
    success = data_manager.promote_students(from_class_id, to_class_id, student_ids)
    if request.is_json:
        return jsonify({'success': success})
    flash('Student promotion completed successfully.' if success else 'Promotion failed.', 'success' if success else 'error')
    return redirect(url_for('promotion'))

@app.route('/chat')
def staff_chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    staff_users = [staff for staff in data_manager.get_all_staff_users() if staff.user_id != user.user_id]
    staff_list = []
    for staff in staff_users:
        unread_count = Message.query.filter_by(sender_id=staff.user_id, receiver_id=user.user_id, is_read=False).count()
        staff_list.append({
            'user_id': staff.user_id,
            'username': staff.username,
            'name': staff.name,
            'unread_count': unread_count
        })

    selected_partner_id = request.args.get('with')
    chat_partner = None
    messages = []
    if selected_partner_id:
        chat_partner = data_manager.get_user_by_id(selected_partner_id)
        if chat_partner and chat_partner.user_id != user.user_id:
            messages = Message.query.filter(
                or_(
                    (Message.sender_id == user.user_id) & (Message.receiver_id == chat_partner.user_id),
                    (Message.sender_id == chat_partner.user_id) & (Message.receiver_id == user.user_id)
                )
            ).order_by(Message.timestamp.asc()).all()

            Message.query.filter_by(sender_id=chat_partner.user_id, receiver_id=user.user_id, is_read=False).update({'is_read': True})
            db.session.commit()
        else:
            flash('Selected staff member not found.', 'error')
            return redirect(url_for('staff_chat'))

    return render_template('chat.html', user=user, staff_list=staff_list, chat_partner=chat_partner, messages=messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user:
        return jsonify({'success': False, 'error': 'Invalid user'}), 400
    
    data = request.get_json(silent=True) or {}
    receiver_id = data.get('receiver_id')
    message_text = (data.get('message') or '').strip()

    if not receiver_id or not message_text:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

    receiver = data_manager.get_user_by_id(receiver_id)
    if not receiver or receiver.user_id == user.user_id:
        return jsonify({'success': False, 'error': 'Recipient not found'}), 404

    message = Message(
        sender_id=user.user_id,
        sender_name=user.name,
        receiver_id=receiver.user_id,
        receiver_name=receiver.name,
        message=message_text,
        is_read=False
    )
    db.session.add(message)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': {
            'sender_name': user.name,
            'message': message_text,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@app.route('/latecomer_attendance')
def latecomer_attendance():
    if 'user_id' not in session or session.get('user_role') != 'staff':
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    
    # Check if class_id is provided in query params
    class_id = request.args.get('class_id')
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    attendance_type = request.args.get('type', 'day')
    period = request.args.get('period', 1)
    
    if class_id:
        # Specific class mode
        class_obj = data_manager.get_class_by_id(class_id)
        if not class_obj:
            flash('Class not found.', 'error')
            return redirect(url_for('staff_dashboard'))
        
        # Get absent students for this class/date
        attendance_records = data_manager.get_attendance_records(class_id=class_id, date_str=date_str, attendance_type=attendance_type, period=int(period) if period else 1)
        present_student_ids = {r.student_id for r in attendance_records if r.status == 'present'}
        all_students = data_manager.get_students_by_class(class_id)
        absent_students = [s for s in all_students if s.student_id not in present_student_ids]
        
        return render_template('latecomer_attendance.html', user=user, class_obj=class_obj, 
                             absent_students=absent_students, date_str=date_str, 
                             attendance_type=attendance_type, period=period)
    else:
        # Class selection mode
        classes = data_manager.get_all_classes()
        return render_template('latecomer_attendance.html', user=user, classes=classes)

@app.route('/mark_latecomer', methods=['POST'])
def mark_latecomer():
    if 'user_id' not in session or session.get('user_role') != 'staff':
        return redirect(url_for('login'))
    
    data = request.get_json(silent=True)
    if data is None:
        student_ids = request.form.getlist('latecomers')
        class_id = request.form.get('class_id')
        date_str = request.form.get('date')
        attendance_type = request.form.get('attendance_type', 'day')
        period = request.form.get('period', 1)
    else:
        student_ids = data.get('student_ids', [])
        class_id = data.get('class_id')
        date_str = data.get('date')
        attendance_type = data.get('attendance_type', 'day')
        period = data.get('period', 1)
    
    if not student_ids or not class_id or not date_str:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Invalid data'})
        flash('Invalid latecomer request. Please select students to mark.', 'error')
        return redirect(url_for('staff_dashboard'))
    
    success = data_manager.mark_latecomer_attendance(
        student_ids,
        class_id,
        date_str,
        session['user_id'],
        attendance_type,
        int(period) if period else 1
    )
    if request.is_json:
        return jsonify({'success': success})
    flash('Latecomer attendance updated successfully.' if success else 'Failed to update latecomer attendance.', 'success' if success else 'error')
    return redirect(url_for('staff_dashboard'))

@app.route('/api/students/search')
def search_students():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('q', '')
    students = data_manager.search_students(query)
    results = []
    for s in students:
        class_obj = data_manager.get_class_by_id(s.class_id)
        results.append({
            'id': s.student_id,
            'name': s.name,
            'roll_number': s.roll_number,
            'class_name': class_obj.class_name if class_obj else 'N/A'
        })
    return jsonify(results)

@app.route('/api/classes/<class_id>/attendance/<date>')
def get_class_attendance(class_id, date):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    records = data_manager.get_attendance_records(class_id=class_id, date_str=date)
    attendance_data = [{
        'student_id': r.student_id,
        'status': r.status,
        'is_late': r.is_late,
        'marked_by': r.marked_by,
        'locked': r.locked
    } for r in records]
    
    return jsonify(attendance_data)

@app.route('/upload_students', methods=['POST'])
def upload_students():
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))
    
    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('hod_dashboard'))
    
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.csv'):
        flash('Please upload a valid CSV file', 'error')
        return redirect(url_for('hod_dashboard'))
    
    try:
        import csv
        import io
        
        # Read CSV content - try different encodings
        try:
            content = file.stream.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            file.stream.seek(0)
            content = file.stream.read().decode("latin-1")
        except Exception as e:
            app.logger.error(f"File read error: {e}")
            flash(f"Error reading file: {e}", 'error')
            return redirect(url_for('hod_dashboard'))
        
        # Check file size (rough estimate: 1000 rows * 200 chars per row = 200KB)
        if len(content) > 1000000:  # 1MB limit
            flash('File too large. Please upload a smaller CSV file (max 1MB).', 'error')
            return redirect(url_for('hod_dashboard'))
        
        stream = io.StringIO(content, newline=None)
        
        # Try to detect delimiter
        sample = content[:2048]
        try:
            dialect = csv.Sniffer().sniff(sample)
            csv_reader = csv.DictReader(stream, dialect=dialect)
        except Exception as e:
            app.logger.warning(f"CSV Sniffing failed: {e}. Falling back to default comma delimiter.")
            stream.seek(0)
            csv_reader = csv.DictReader(stream)
        
        # Normalize headers: lowercase and strip whitespace
        if not csv_reader.fieldnames:
            flash('CSV file appears to be empty or missing headers.', 'error')
            return redirect(url_for('hod_dashboard'))
        
        normalized_fieldnames = {f.strip().lower(): f for f in csv_reader.fieldnames if f}
        
        # Get all valid class_ids for validation (case-insensitive)
        all_classes = data_manager.get_all_classes()
        valid_class_ids = {cls.class_id.lower() for cls in all_classes}
        class_id_map = {cls.class_id.lower(): cls.class_id for cls in all_classes}
        
        uploaded_count = 0
        errors = []
        seen_ids = set()
        duplicate_ids_count = 0
        sci_notation_count = 0
        processed_rows = 0
        max_rows = 1500
        
        # Mapping helper
        def get_val(row, aliases):
            for alias in aliases:
                if alias in normalized_fieldnames:
                    return row.get(normalized_fieldnames[alias], '').strip()
            return ''
        
        def normalize_text(value):
            return ' '.join(str(value).replace('\t', ' ').replace('\r', ' ').split()) if value else ''
        
        for row_num, row in enumerate(csv_reader, start=2):
            if processed_rows >= max_rows:
                errors.append(f"Stopped at row {row_num}: Max {max_rows} rows reached")
                break
            
            processed_rows += 1
            if not any(row.values()): continue
            
            try:
                # Map headers with aliases
                student_id = normalize_text(get_val(row, ['student_id', 'id', 'roll_number', 'rollno', 'student id', 'roll number']))
                name = normalize_text(get_val(row, ['name', 'student_name', 'full_name', 'student name', 'full name']))
                class_id = normalize_text(get_val(row, ['class_id', 'class', 'year_section', 'class id', 'year section']))
                department = normalize_text(get_val(row, ['department', 'dept', 'branch'])) or 'AI&DS'
                email = normalize_text(get_val(row, ['email', 'email_id', 'student_email', 'e-mail', 'student email']))
                phone = normalize_text(get_val(row, ['phone', 'mobile', 'phone_number', 'contact', 'mobile number']))
                parent_email = normalize_text(get_val(row, ['parent_email', 'father_email', 'mother_email', 'parent email', 'father email', 'mother email']))
                parent_phone = normalize_text(get_val(row, ['parent_phone', 'father_phone', 'mother_phone', 'parent_contact', 'parent phone', 'father phone', 'mother phone']))
                
                if 'E+' in student_id.upper() or '.0000' in student_id:
                    sci_notation_count += 1

                if not student_id or not name or not class_id:
                    errors.append(f"Row {row_num}: Missing core data (ID, Name, or Class)")
                    continue
                
                if student_id in seen_ids:
                    duplicate_ids_count += 1
                else:
                    seen_ids.add(student_id)

                if class_id.lower() not in valid_class_ids:
                    errors.append(f"Row {row_num}: Class '{class_id}' not found in system")
                    continue
                
                class_id = class_id_map[class_id.lower()]
                
                student_data = {
                    'student_id': student_id,
                    'roll_number': student_id,
                    'name': name,
                    'class_id': class_id,
                    'department': department,
                    'email': email,
                    'phone': phone,
                    'parent_email': parent_email,
                    'parent_phone': parent_phone
                }
                
                success, error_msg = data_manager.add_student(student_data)
                if success:
                    uploaded_count += 1
                else:
                    errors.append(f"Row {row_num}: {error_msg}")
                    
            except Exception as e:
                app.logger.error(f"Error processing CSV row {row_num}: {e}")
                errors.append(f"Row {row_num}: System error")
        
        if uploaded_count > 0:
            flash(f'Processed {uploaded_count} student records.', 'success')
        if duplicate_ids_count > 0:
            flash(f'Updated {duplicate_ids_count} duplicate IDs.', 'warning')
        if sci_notation_count > 0:
            flash(f'{sci_notation_count} IDs had scientific notation format.', 'error')
        if errors:
            for error in errors[:5]: flash(error, 'warning')
                
    except Exception as e:
        app.logger.error(f"CSV Upload Fatal Error: {e}", exc_info=True)
        flash(f"A fatal error occurred during upload: {str(e)}", 'error')
    
    return redirect(url_for('hod_dashboard'))
    
    return redirect(url_for('hod_dashboard'))

@app.route('/delete_students_by_class', methods=['POST'])
def delete_students_by_class():
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))
    
    class_id = request.form.get('class_id')
    if not class_id:
        flash('No class selected', 'error')
        return redirect(url_for('hod_dashboard'))
    
    try:
        deleted_count = data_manager.delete_students_by_class(class_id)
        flash(f'Successfully deleted {deleted_count} students from class {class_id}', 'success')
    except Exception as e:
        flash(f'Error deleting students: {str(e)}', 'error')
    
    return redirect(url_for('hod_dashboard'))

@app.route('/delete_student', methods=['POST'])
def delete_student():
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))
    
    student_id = request.form.get('student_id') or request.args.get('student_id')
    if not student_id:
        flash('No student ID provided', 'error')
        return redirect(url_for('hod_dashboard'))
    
    try:
        if data_manager.delete_student(student_id):
            flash(f'Successfully deleted student {student_id}', 'success')
        else:
            flash(f'Failed to delete student {student_id}', 'error')
    except Exception as e:
        flash(f'Error deleting student: {str(e)}', 'error')
    
    return redirect(url_for('hod_dashboard'))

@app.route('/update_student', methods=['POST'])
def update_student():
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))
    
    student_id = request.form.get('student_id', '').strip()
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    parent_email = request.form.get('parent_email', '').strip()
    parent_phone = request.form.get('parent_phone', '').strip()
    
    if not student_id or not name:
        flash('Student ID and name are required.', 'error')
        return redirect(url_for('student_details', student_id=student_id))
    
    updates = {
        'name': name,
        'department': department,
        'email': email,
        'phone': phone,
        'parent_email': parent_email,
        'parent_phone': parent_phone
    }
    
    try:
        success = data_manager.update_student(student_id, updates)
        if success:
            flash('Student details updated successfully.', 'success')
        else:
            flash('Failed to update student details.', 'error')
    except Exception as e:
        flash(f'Error updating student: {str(e)}', 'error')
    
    return redirect(url_for('student_details', student_id=student_id))

@app.route('/delete_staff', methods=['POST'])
def delete_staff():
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))
    
    username = request.form.get('username')
    if not username:
        flash('No staff username provided', 'error')
        return redirect(url_for('hod_dashboard'))
    
    try:
        if data_manager.delete_staff_user(username):
            flash(f'Successfully deleted staff account for {username}', 'success')
        else:
            flash(f'Failed to delete staff account for {username}', 'error')
    except Exception as e:
        flash(f'Error deleting staff account: {str(e)}', 'error')
    
    return redirect(url_for('hod_dashboard'))

@app.route('/create_staff', methods=['POST'])
def create_staff():
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    name = request.form.get('name', '').strip()
    assigned_classes = request.form.getlist('assigned_classes')
    
    if not username or not password or not name:
        flash('Please provide username, password, and name.', 'error')
        return redirect(url_for('hod_dashboard'))
    
    try:
        success = data_manager.create_staff_user(
            username=username,
            password=password,
            name=name,
            assigned_classes=assigned_classes if assigned_classes else None
        )
        
        if success:
            flash(f'Staff account created successfully for {username}', 'success')
        else:
            flash('Username already exists. Please choose a different username.', 'error')
    except Exception as e:
        flash(f'Error creating staff account: {str(e)}', 'error')
    
    return redirect(url_for('hod_dashboard'))

@app.route('/update_staff_classes', methods=['POST'])
def update_staff_classes():
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))
    
    username = request.form.get('username', '').strip()
    assigned_classes = request.form.getlist('assigned_classes')
    
    if not username:
        flash('No staff username provided', 'error')
        return redirect(url_for('hod_dashboard'))
    
    try:
        success = data_manager.update_staff_classes(
            username=username,
            assigned_classes=assigned_classes
        )
        
        if success:
            flash(f'Successfully updated classes for {username}', 'success')
        else:
            flash(f'Failed to update classes for {username}', 'error')
    except Exception as e:
        flash(f'Error updating staff classes: {str(e)}', 'error')
    
    return redirect(url_for('hod_dashboard'))

@app.route('/add_student', methods=['POST'])
def add_student():
    if 'user_id' not in session or session.get('user_role') not in ['hod', 'admin']:
        return redirect(url_for('login'))
    
    student_id = request.form.get('student_id', '').strip()
    name = request.form.get('name', '').strip()
    class_id = request.form.get('class_id', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    parent_email = request.form.get('parent_email', '').strip()
    parent_phone = request.form.get('parent_phone', '').strip()
    
    if not student_id or not name or not class_id:
        flash('Please provide student ID, name, and class.', 'error')
        return redirect(url_for('hod_dashboard'))
    
    student_data = {
        'student_id': student_id,
        'roll_number': student_id,  # Same as student_id
        'name': name,
        'class_id': class_id,
        'department': 'AI&DS',
        'email': email,
        'phone': phone,
        'parent_email': parent_email,
        'parent_phone': parent_phone
    }
    
    try:
        success, error_msg = data_manager.add_student(student_data)
        
        if success:
            flash(f'Student {name} added successfully.', 'success')
        else:
            flash(f'Error adding student: {error_msg}', 'error')
    except Exception as e:
        flash(f'Error adding student: {str(e)}', 'error')
    
    return redirect(url_for('hod_dashboard'))

@app.route('/download_student_report_excel')
def download_student_report_excel():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
    
    student = data_manager.get_student_by_user_id(session['user_id'])
    if not student:
        return redirect(url_for('login'))

    # Get the same filters as dashboard
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    attendance_type = request.args.get('attendance_type', 'all')
    period = request.args.get('period')
    status_filter = request.args.get('status', 'all')
    show_all = request.args.get('show_all') == 'true'

    # Get and filter data
    records = data_manager.get_student_attendance(student.student_id)
    filtered = records

    if not (start_date or end_date or attendance_type != 'all' or status_filter != 'all' or show_all):
        if records:
            latest_date = max(r.date for r in records)
            filtered = [r for r in records if r.date == latest_date]
    else:
        if start_date: filtered = [r for r in filtered if str(r.date) >= start_date]
        if end_date: filtered = [r for r in filtered if str(r.date) <= end_date]
        if attendance_type != 'all':
            filtered = [r for r in filtered if r.attendance_type == attendance_type]
            if attendance_type == 'period' and period:
                filtered = [r for r in filtered if str(r.period) == str(period)]
        if status_filter != 'all':
            if status_filter == 'late':
                filtered = [r for r in filtered if r.status == 'present' and r.is_late]
            else:
                filtered = [r for r in filtered if r.status == status_filter]

    # Create Excel
    import pandas as pd
    import io
    
    data = []
    for r in filtered:
        basis = f"Period {r.period}" if r.attendance_type == 'period' else "Full Day"
        remarks = "Late Arrival" if r.is_late else "On Time"
        data.append({
            'Date': r.date,
            'Basis': basis,
            'Status': r.status.capitalize(),
            'Remarks': remarks
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Attendance')
    
    output.seek(0)
    
    from flask import send_file
    filename = f"Attendance_Report_{student.name.replace(' ', '_')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/download_student_report_jpg')
def download_student_report_jpg():
    # Since server-side image generation is complex (requires wkhtmltoimage/selenium), 
    # we'll use a client-side approach or redirect to a "printable" view that JS can capture.
    # For now, we provide the printable template view.
    return redirect(url_for('student_dashboard', is_report='true'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500
