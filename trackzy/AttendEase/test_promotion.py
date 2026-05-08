#!/usr/bin/env python3
"""
Test script for student promotion functionality
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import app, db
from models import Student
from data_manager import data_manager

def main():
    with app.app_context():
        print('=== BEFORE PROMOTION ===')
        students = Student.query.all()
        for s in students:
            print(f'{s.name}: {s.class_id}')

        print('\n=== PROMOTING STUDENTS ===')
        result = data_manager.promote_students_academic_year()
        print(f'Final Year passed out: {result["final_year_passed_out"]}')
        print(f'3rd Year promoted: {result["third_year_promoted"]}')
        print(f'2nd Year promoted: {result["second_year_promoted"]}')

        print('\n=== AFTER PROMOTION ===')
        students = Student.query.all()
        for s in students:
            print(f'{s.name}: {s.class_id}')

if __name__ == '__main__':
    main()