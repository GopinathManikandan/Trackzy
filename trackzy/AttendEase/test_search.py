from app import app
from data_manager import data_manager
from models import Student, GraduatedStudent

with app.app_context():
    print("--- Active Students ---")
    active_all = Student.query.all()
    for s in active_all[:3]:
        print(f"ID: {s.student_id}, Name: {s.name}, Class: {s.class_id}")
    
    print("\n--- Graduated Students ---")
    grad_all = GraduatedStudent.query.all()
    for s in grad_all[:3]:
        print(f"ID: {s.student_id}, Name: {s.name}, Final Class: {s.final_class_id}")
    
    query = "6215" # Common prefix in roll numbers
    print(f"\n--- Searching for '{query}' ---")
    results = data_manager.search_any_students(query)
    print(f"Total results found: {len(results)}")
    for r in results:
        role = "Active" if hasattr(r, 'class_id') else "Graduated"
        print(f"[{role}] {r.name} ({r.student_id})")
