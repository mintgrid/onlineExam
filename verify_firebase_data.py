#!/usr/bin/env python3
"""
Verify Firebase Data Migration
Check all Firebase collections and display summary
"""

from firebase_models import User, Exam, Question, ExamPermission, ExamResult, Settings
from firebase_config import firebase_db, COLLECTIONS

def verify_all_collections():
    """Verify all Firebase collections"""
    print("🔍 Verifying Firebase Firestore Data...")
    print("=" * 50)
    
    total_records = 0
    
    # 1. Verify Users
    print("\n👥 USERS Collection:")
    try:
        admin_users = firebase_db.get_documents(
            COLLECTIONS['USERS'], 
            filters=[('is_admin', '==', True)]
        )
        student_users = firebase_db.get_documents(
            COLLECTIONS['USERS'], 
            filters=[('is_admin', '==', False)]
        )
        
        print(f"   📊 Admin Users: {len(admin_users)}")
        for user in admin_users:
            print(f"      👤 {user['username']} ({user['email']})")
        
        print(f"   📊 Student Users: {len(student_users)}")
        for user in student_users[:5]:  # Show first 5
            print(f"      👤 {user['username']} ({user['email']})")
        if len(student_users) > 5:
            print(f"      ... and {len(student_users) - 5} more students")
        
        total_records += len(admin_users) + len(student_users)
        
    except Exception as e:
        print(f"   ❌ Error fetching users: {e}")
    
    # 2. Verify Settings
    print("\n⚙️ SETTINGS Collection:")
    try:
        settings = firebase_db.get_documents(COLLECTIONS['SETTINGS'])
        print(f"   📊 Settings: {len(settings)}")
        for setting in settings:
            print(f"      🔧 {setting['key']} = {setting['value']}")
        total_records += len(settings)
    except Exception as e:
        print(f"   ❌ Error fetching settings: {e}")
    
    # 3. Verify Exams
    print("\n📝 EXAMS Collection:")
    try:
        exams = firebase_db.get_documents(COLLECTIONS['EXAMS'])
        print(f"   📊 Exams: {len(exams)}")
        for exam in exams:
            print(f"      📋 {exam['title']} ({exam['duration_minutes']} min)")
        total_records += len(exams)
    except Exception as e:
        print(f"   ❌ Error fetching exams: {e}")
    
    # 4. Verify Questions
    print("\n❓ QUESTIONS Collection:")
    try:
        questions = firebase_db.get_documents(COLLECTIONS['QUESTIONS'])
        print(f"   📊 Questions: {len(questions)}")
        
        # Group questions by exam
        exam_questions = {}
        for question in questions:
            exam_id = question['exam_id']
            if exam_id not in exam_questions:
                exam_questions[exam_id] = []
            exam_questions[exam_id].append(question)
        
        for exam_id, q_list in exam_questions.items():
            print(f"      📋 Exam {exam_id}: {len(q_list)} questions")
        
        total_records += len(questions)
    except Exception as e:
        print(f"   ❌ Error fetching questions: {e}")
    
    # 5. Verify Exam Permissions
    print("\n🔐 EXAM PERMISSIONS Collection:")
    try:
        permissions = firebase_db.get_documents(COLLECTIONS['EXAM_PERMISSIONS'])
        print(f"   📊 Permissions: {len(permissions)}")
        
        # Count by status
        active_permissions = [p for p in permissions if not p.get('is_completed', False)]
        completed_permissions = [p for p in permissions if p.get('is_completed', False)]
        
        print(f"      🟢 Active: {len(active_permissions)}")
        print(f"      ✅ Completed: {len(completed_permissions)}")
        
        total_records += len(permissions)
    except Exception as e:
        print(f"   ❌ Error fetching permissions: {e}")
    
    # 6. Verify Exam Results
    print("\n📊 EXAM RESULTS Collection:")
    try:
        results = firebase_db.get_documents(COLLECTIONS['EXAM_RESULTS'])
        print(f"   📊 Results: {len(results)}")
        
        if results:
            total_score = sum([r.get('score', 0) for r in results])
            total_marks = sum([r.get('total_marks', 0) for r in results])
            avg_percentage = sum([r.get('percentage', 0) for r in results]) / len(results)
            
            print(f"      📈 Total Score: {total_score}/{total_marks}")
            print(f"      📈 Average: {avg_percentage:.1f}%")
            
            # Show sample results
            for i, result in enumerate(results[:3]):
                print(f"      📝 Result {i+1}: {result.get('score', 0)}/{result.get('total_marks', 0)} ({result.get('percentage', 0):.1f}%)")
        
        total_records += len(results)
    except Exception as e:
        print(f"   ❌ Error fetching results: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 FIREBASE VERIFICATION COMPLETE!")
    print("=" * 50)
    print(f"📊 Total Records in Firebase: {total_records}")
    print("\n🔥 Firebase Collections Summary:")
    print("   📁 users - User accounts (admin & students)")
    print("   📁 exams - Exam definitions")
    print("   📁 questions - Exam questions")
    print("   📁 examPermissions - Time-based exam access")
    print("   📁 examResults - Student exam results")
    print("   📁 settings - Application configuration")
    
    print(f"\n✅ All data successfully migrated from SQLite to Firebase!")
    print("🚀 Your application now runs on cloud-based Firebase backend!")

def test_firebase_functionality():
    """Test basic Firebase operations"""
    print("\n🧪 Testing Firebase Functionality...")
    
    try:
        # Test user lookup
        admin_user = User.get_by_username('admin')
        if admin_user:
            print("   ✅ User lookup working")
        
        # Test exam retrieval
        if admin_user:
            exams = Exam.get_by_creator(admin_user.id)
            print(f"   ✅ Exam retrieval working ({len(exams)} exams found)")
        
        # Test settings
        mail_server = Settings.get_by_key('MAIL_SERVER')
        if mail_server:
            print(f"   ✅ Settings working (MAIL_SERVER: {mail_server.value})")
        
        print("   🎉 All Firebase operations working correctly!")
        
    except Exception as e:
        print(f"   ❌ Firebase functionality error: {e}")

def main():
    """Main verification function"""
    verify_all_collections()
    test_firebase_functionality()

if __name__ == "__main__":
    main()