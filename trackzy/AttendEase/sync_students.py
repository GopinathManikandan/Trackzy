from app import app
from data_manager import data_manager

with app.app_context():
    print("Synchronizing student accounts...")
    count = data_manager.sync_student_accounts()
    print(f"Successfully created {count} new student portal accounts!")
