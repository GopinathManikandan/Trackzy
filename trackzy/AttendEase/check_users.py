from app import app
from models import db, User, Student, Class

with app.app_context():
    print("--- Database Summary ---")
    print(f"Users: {User.query.count()}")
    print(f"Students: {Student.query.count()}")
    print(f"Classes: {Class.query.count()}")
    
    print("\n--- Users in DB ---")
    users = User.query.all()
    for u in users:
        print(f"ID: {u.user_id}, Username: {u.username}, Role: {u.role}, Password: {u.password}")
    
    if not any(u.role == 'hod' for u in users):
        print("\nCreating default HOD user...")
        hod = User(
            user_id='admin',
            username='admin',
            password='adminpassword',
            role='hod',
            name='Administrator'
        )
        db.session.add(hod)
        db.session.commit()
        print("Default HOD user created: admin / adminpassword")
