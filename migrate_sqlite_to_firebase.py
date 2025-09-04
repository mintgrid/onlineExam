#!/usr/bin/env python3
"""
SQLite to Firebase Migration Script
Migrates all data from SQLite database to Firebase Firestore collections
"""

import sqlite3
import sys
import os
from datetime import datetime, timezone
from firebase_models import User, Exam, Question, ExamPermission, ExamResult, Settings
from firebase_config import firebase_db, COLLECTIONS

def convert_datetime(dt_string):
    """Convert SQLite datetime string to timezone-aware datetime"""
    if not dt_string:
        return None
    try:
        # Parse SQLite datetime format
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except:
        return None

def migrate_users():
    """Migrate users from SQLite to Firebase"""
    print("🔄 Migrating users...")
    
    conn = sqlite3.connect('instance/exam_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM user')
    users = cursor.fetchall()
    
    migrated = 0
    for row in users:
        # Check if user already exists in Firebase
        existing_user = User.get_by_username(row['username'])
        if existing_user:
            print(f"   ⚠️  User '{row['username']}' already exists in Firebase, skipping...")
            continue
        
        # Create new Firebase user
        user = User()
        user.username = row['username']
        user.email = row['email']
        user.password_hash = row['password_hash']
        user.is_admin = bool(row['is_admin'])
        
        user_id = user.save()
        if user_id:
            print(f"   ✅ Migrated user: {row['username']}")
            migrated += 1
        else:
            print(f"   ❌ Failed to migrate user: {row['username']}")
    
    conn.close()
    print(f"   📊 Users migrated: {migrated}")
    return migrated

def migrate_settings():
    """Migrate settings from SQLite to Firebase"""
    print("🔄 Migrating settings...")
    
    conn = sqlite3.connect('instance/exam_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM settings')
    settings = cursor.fetchall()
    
    migrated = 0
    for row in settings:
        # Check if setting already exists
        existing_setting = Settings.get_by_key(row['key'])
        if existing_setting:
            print(f"   ⚠️  Setting '{row['key']}' already exists, updating...")
            existing_setting.value = row['value']
            existing_setting.save()
        else:
            setting = Settings()
            setting.key = row['key']
            setting.value = row['value']
            
            setting_id = setting.save()
            if setting_id:
                print(f"   ✅ Migrated setting: {row['key']}")
                migrated += 1
            else:
                print(f"   ❌ Failed to migrate setting: {row['key']}")
    
    conn.close()
    print(f"   📊 Settings migrated: {migrated}")
    return migrated

def migrate_exams():
    """Migrate exams from SQLite to Firebase"""
    print("🔄 Migrating exams...")
    
    conn = sqlite3.connect('instance/exam_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all exams with creator information
    cursor.execute('''
        SELECT e.*, u.username as creator_username 
        FROM exam e 
        LEFT JOIN user u ON e.created_by = u.id
    ''')
    exams = cursor.fetchall()
    
    migrated = 0
    exam_id_mapping = {}  # SQLite ID -> Firebase ID mapping
    
    for row in exams:
        # Find creator in Firebase by username
        creator = User.get_by_username(row['creator_username'])
        if not creator:
            print(f"   ❌ Creator '{row['creator_username']}' not found in Firebase for exam '{row['title']}'")
            continue
        
        exam = Exam()
        exam.title = row['title']
        exam.description = row['description']
        exam.duration_minutes = row['duration_minutes']
        exam.created_by = creator.id
        
        exam_id = exam.save()
        if exam_id:
            exam_id_mapping[row['id']] = exam_id
            print(f"   ✅ Migrated exam: {row['title']}")
            migrated += 1
        else:
            print(f"   ❌ Failed to migrate exam: {row['title']}")
    
    conn.close()
    print(f"   📊 Exams migrated: {migrated}")
    return migrated, exam_id_mapping

def migrate_questions(exam_id_mapping):
    """Migrate questions from SQLite to Firebase"""
    print("🔄 Migrating questions...")
    
    conn = sqlite3.connect('instance/exam_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM question')
    questions = cursor.fetchall()
    
    migrated = 0
    for row in questions:
        # Map SQLite exam_id to Firebase exam_id
        firebase_exam_id = exam_id_mapping.get(row['exam_id'])
        if not firebase_exam_id:
            print(f"   ❌ Exam ID {row['exam_id']} not found in mapping for question")
            continue
        
        question = Question()
        question.exam_id = firebase_exam_id
        question.question_text = row['question_text']
        question.option_a = row['option_a']
        question.option_b = row['option_b']
        question.option_c = row['option_c']
        question.option_d = row['option_d']
        question.correct_answer = row['correct_answer']
        question.marks = row['marks']
        
        question_id = question.save()
        if question_id:
            print(f"   ✅ Migrated question: {row['question_text'][:50]}...")
            migrated += 1
        else:
            print(f"   ❌ Failed to migrate question")
    
    conn.close()
    print(f"   📊 Questions migrated: {migrated}")
    return migrated

def migrate_exam_permissions(exam_id_mapping):
    """Migrate exam permissions from SQLite to Firebase"""
    print("🔄 Migrating exam permissions...")
    
    conn = sqlite3.connect('instance/exam_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get permissions with user information
    cursor.execute('''
        SELECT ep.*, u.username 
        FROM exam_permission ep
        LEFT JOIN user u ON ep.user_id = u.id
    ''')
    permissions = cursor.fetchall()
    
    migrated = 0
    for row in permissions:
        # Find user in Firebase
        user = User.get_by_username(row['username'])
        if not user:
            print(f"   ❌ User '{row['username']}' not found in Firebase for permission")
            continue
        
        # Map SQLite exam_id to Firebase exam_id
        firebase_exam_id = exam_id_mapping.get(row['exam_id'])
        if not firebase_exam_id:
            print(f"   ❌ Exam ID {row['exam_id']} not found in mapping for permission")
            continue
        
        permission = ExamPermission()
        permission.user_id = user.id
        permission.exam_id = firebase_exam_id
        permission.start_time = convert_datetime(row['start_time'])
        permission.end_time = convert_datetime(row['end_time'])
        permission.is_completed = bool(row['is_completed'])
        
        permission_id = permission.save()
        if permission_id:
            print(f"   ✅ Migrated permission for user: {row['username']}")
            migrated += 1
        else:
            print(f"   ❌ Failed to migrate permission for user: {row['username']}")
    
    conn.close()
    print(f"   📊 Permissions migrated: {migrated}")
    return migrated

def migrate_exam_results(exam_id_mapping):
    """Migrate exam results from SQLite to Firebase"""
    print("🔄 Migrating exam results...")
    
    conn = sqlite3.connect('instance/exam_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get results with user information
    cursor.execute('''
        SELECT er.*, u.username 
        FROM exam_result er
        LEFT JOIN user u ON er.user_id = u.id
    ''')
    results = cursor.fetchall()
    
    migrated = 0
    for row in results:
        # Find user in Firebase
        user = User.get_by_username(row['username'])
        if not user:
            print(f"   ❌ User '{row['username']}' not found in Firebase for result")
            continue
        
        # Map SQLite exam_id to Firebase exam_id
        firebase_exam_id = exam_id_mapping.get(row['exam_id'])
        if not firebase_exam_id:
            print(f"   ❌ Exam ID {row['exam_id']} not found in mapping for result")
            continue
        
        result = ExamResult()
        result.user_id = user.id
        result.exam_id = firebase_exam_id
        result.score = row['score']
        result.total_marks = row['total_marks']
        result.percentage = row['percentage']
        result.answers = eval(row['answers']) if row['answers'] else {}  # Convert string to dict
        result.submitted_at = convert_datetime(row['submitted_at'])
        
        result_id = result.save()
        if result_id:
            print(f"   ✅ Migrated result for user: {row['username']}")
            migrated += 1
        else:
            print(f"   ❌ Failed to migrate result for user: {row['username']}")
    
    conn.close()
    print(f"   📊 Results migrated: {migrated}")
    return migrated

def main():
    """Main migration function"""
    print("🚀 Starting SQLite to Firebase Migration...")
    print("=" * 50)
    
    # Check if SQLite database exists
    if not os.path.exists('instance/exam_system.db'):
        print("❌ SQLite database not found at 'instance/exam_system.db'")
        sys.exit(1)
    
    # Check Firebase connection
    try:
        firebase_db.get_documents(COLLECTIONS['USERS'], limit=1)
        print("✅ Firebase connection verified")
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        sys.exit(1)
    
    # Run migrations in order (maintaining referential integrity)
    total_migrated = 0
    
    try:
        # 1. Migrate users first (needed for foreign keys)
        total_migrated += migrate_users()
        
        # 2. Migrate settings
        total_migrated += migrate_settings()
        
        # 3. Migrate exams (returns mapping for foreign keys)
        exams_migrated, exam_id_mapping = migrate_exams()
        total_migrated += exams_migrated
        
        # 4. Migrate questions (depends on exams)
        total_migrated += migrate_questions(exam_id_mapping)
        
        # 5. Migrate exam permissions (depends on users and exams)
        total_migrated += migrate_exam_permissions(exam_id_mapping)
        
        # 6. Migrate exam results (depends on users and exams)
        total_migrated += migrate_exam_results(exam_id_mapping)
        
        print("=" * 50)
        print(f"🎉 Migration completed successfully!")
        print(f"📊 Total records migrated: {total_migrated}")
        print(f"🔥 Your data is now in Firebase Firestore!")
        
    except Exception as e:
        print(f"❌ Migration failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()