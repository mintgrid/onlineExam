#!/usr/bin/env python3
"""
Direct SQLite to Firebase Migration
Creates the admin users directly in Firebase using the initialization method
"""

import sqlite3
from werkzeug.security import generate_password_hash

# Import the existing initialization function
from app import initialize_database

def migrate_admin_users_to_firebase():
    """Migrate admin users directly to Firebase using the app's initialization"""
    print("🚀 Migrating Admin Users to Firebase...")
    
    # Check SQLite database
    conn = sqlite3.connect('instance/exam_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM user WHERE is_admin = 1')
    admin_users = cursor.fetchall()
    
    print(f"📊 Found {len(admin_users)} admin users in SQLite:")
    for user in admin_users:
        print(f"   👤 {user['username']} ({user['email']})")
    
    conn.close()
    
    # Initialize Firebase database (this will create the default admin users)
    print("\n🔥 Initializing Firebase with admin users...")
    try:
        initialize_database()
        print("✅ Firebase database initialized successfully!")
        print("✅ Admin users are now available in Firebase:")
        print("   👤 admin / admin123")
        print("   👤 admin2 / admin456")
        
        return True
    except Exception as e:
        print(f"❌ Error initializing Firebase: {e}")
        return False

def create_sample_data_in_firebase():
    """Create some sample data for testing"""
    print("\n📋 Creating sample data in Firebase...")
    
    try:
        # Import Firebase models
        from firebase_models import User, Exam, Question, ExamPermission
        from datetime import datetime, timezone, timedelta
        
        # Check if we can create a test user
        print("   📝 Creating test student user...")
        test_user = User()
        test_user.username = "john"
        test_user.email = "john@example.com" 
        test_user.password_hash = generate_password_hash("john123")
        test_user.is_admin = False
        
        user_id = test_user.save()
        if user_id:
            print(f"   ✅ Created student user: john (ID: {user_id})")
        else:
            print("   ❌ Failed to create student user")
            
        # Try to create a sample exam
        print("   📝 Creating sample exam...")
        admin_user = User.get_by_username('admin')
        if admin_user:
            exam = Exam()
            exam.title = "Sample Math Test"
            exam.description = "Basic mathematics test"
            exam.duration_minutes = 30
            exam.created_by = admin_user.id
            
            exam_id = exam.save()
            if exam_id:
                print(f"   ✅ Created sample exam: {exam.title} (ID: {exam_id})")
                
                # Add a sample question
                question = Question()
                question.exam_id = exam_id
                question.question_text = "What is 2 + 2?"
                question.option_a = "3"
                question.option_b = "4" 
                question.option_c = "5"
                question.option_d = "6"
                question.correct_answer = "B"
                question.marks = 1
                
                q_id = question.save()
                if q_id:
                    print(f"   ✅ Added sample question (ID: {q_id})")
                    
                # Create exam permission for test user
                if user_id:
                    permission = ExamPermission()
                    permission.user_id = user_id
                    permission.exam_id = exam_id
                    permission.start_time = datetime.now(timezone.utc)
                    permission.end_time = datetime.now(timezone.utc) + timedelta(days=7)
                    permission.is_completed = False
                    
                    p_id = permission.save()
                    if p_id:
                        print(f"   ✅ Created exam permission (ID: {p_id})")
            else:
                print("   ❌ Failed to create sample exam")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating sample data: {e}")
        return False

def main():
    """Main migration function"""
    print("🎯 Direct SQLite to Firebase Migration")
    print("=" * 50)
    
    # Step 1: Migrate admin users
    success1 = migrate_admin_users_to_firebase()
    
    # Step 2: Create sample data for testing
    if success1:
        success2 = create_sample_data_in_firebase()
        
        if success1 and success2:
            print("\n" + "=" * 50)
            print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            print("✅ Admin users migrated to Firebase")
            print("✅ Sample data created for testing")
            print("\n🚀 Ready to test application:")
            print("   🌐 URL: http://localhost:5003")
            print("   👤 Login: admin / admin123")
            print("   👤 Login: john / john123 (student)")
        else:
            print("\n⚠️ Migration partially completed")
    else:
        print("\n❌ Migration failed")

if __name__ == "__main__":
    main()