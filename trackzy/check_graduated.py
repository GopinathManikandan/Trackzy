import sys
import os
sys.path.append('AttendEase')
from app import app
from models import GraduatedStudent

with app.app_context():
    g = GraduatedStudent.query.filter_by(student_id='621522243004').first()
    if g:
        print(f"Found student {g.student_id} ({g.name}) in GraduatedStudent table.")
    else:
        print(f"Student 621522243004 not found in GraduatedStudent table.")
