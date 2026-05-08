import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import threading

def send_absence_email(recipient_emails, student_name, class_name, date_str, attendance_type='day', period=None):
    """
    Sends an email notification to recipients (student and parent) for absence.
    Runs in a background thread to avoid blocking the main application.
    """
    # Create and start a background thread
    thread = threading.Thread(
        target=_send_email_thread,
        args=(recipient_emails, student_name, class_name, date_str, attendance_type, period)
    )
    thread.daemon = True # Allow program to exit even if thread is running
    thread.start()
    return True # Return immediately to the user

def _send_email_thread(recipient_emails, student_name, class_name, date_str, attendance_type, period):
    # Ensure recipient_emails is a list
    if isinstance(recipient_emails, str):
        recipient_emails = [recipient_emails]
    
    # Filter out empty emails
    recipient_emails = [email for email in recipient_emails if email]
    
    if not recipient_emails:
        return

    # These will be configured by you later
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    
    # DEBUG: Check if credentials exist (without printing the actual password)
    if not sender_email:
        print("DEBUG: SENDER_EMAIL is missing from environment variables!")
    if not sender_password:
        print("DEBUG: SENDER_PASSWORD is missing from environment variables!")
    
    if not sender_email or not sender_password:
        print(f"Skipping email for {student_name}: Email credentials not configured.")
        return

    # Customize message based on type
    if attendance_type == 'day':
        alert_detail = "Today (Full Day)"
        status_text = "TODAY ABSENT"
    else:
        alert_detail = f"Period {period}"
        status_text = f"PERIOD {period} ABSENT"

    # Email Content
    subject = f"Absence Alert: {student_name} - {alert_detail}"
    body = f"""
    Dear Student/Parent,

    This is an automated notification from Trackzy.
    
    Student: {student_name}
    Class: {class_name}
    Date: {date_str}
    Status: {status_text}

    If you believe this is an error, please contact the department staff immediately.

    Regards,
    Trackzy Attendance System
    """

    try:
        # Set up the SMTP server (using Gmail defaults)
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.starttls()
        server.login(sender_email, sender_password)
        
        for email in recipient_emails:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"Trackzy Attendance <{sender_email}>"
            msg['To'] = email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Send
            server.send_message(msg)
            print(f"Successfully sent absence email to {email}")
        
        server.quit()
    except Exception as e:
        print(f"Error sending email for {student_name}: {e}")
