#!/usr/bin/env python3
"""
Populate SQLite Database with Comprehensive Test Data
Creates complete dataset including students, exams, questions, permissions, results, and settings
"""

import sqlite3
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash
import json

def populate_test_data():
    """Populate SQLite database with comprehensive test data"""
    print("🚀 Populating SQLite Database with Complete Test Data...")
    
    conn = sqlite3.connect('instance/exam_system.db')
    cursor = conn.cursor()
    
    # 1. Add Student Users
    print("\n👥 Adding Student Users...")
    students = [
        ('john', 'john@example.com', 'john123'),
        ('jane', 'jane@example.com', 'jane123'),
        ('student1', 'student1@example.com', 'student123'),
        ('student2', 'student2@example.com', 'student456'),
        ('alice', 'alice@example.com', 'alice789'),
        ('bob', 'bob@example.com', 'bob321'),
        ('carol', 'carol@example.com', 'carol654'),
        ('dave', 'dave@example.com', 'dave987')
    ]
    
    for username, email, password in students:
        password_hash = generate_password_hash(password)
        try:
            cursor.execute('''
                INSERT INTO user (username, email, password_hash, is_admin, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, False, datetime.now(timezone.utc).isoformat()))
            print(f"   ✅ Added student: {username}")
        except sqlite3.IntegrityError:
            print(f"   ⚠️  Student {username} already exists, skipping...")
    
    # 2. Add Settings
    print("\n⚙️ Adding Application Settings...")
    settings = [
        ('MAIL_SERVER', 'smtp.gmail.com'),
        ('MAIL_PORT', '587'),
        ('MAIL_USE_TLS', 'true'),
        ('MAIL_USERNAME', 'admin@examapp.com'),
        ('MAIL_PASSWORD', 'app-password-here'),
        ('MAIL_DEFAULT_SENDER', 'noreply@examapp.com'),
        ('APP_VERSION', '2.0.0'),
        ('MAINTENANCE_MODE', 'false'),
        ('MAX_EXAM_DURATION', '180'),
        ('DEFAULT_PASSING_SCORE', '60')
    ]
    
    for key, value in settings:
        try:
            cursor.execute('''
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, datetime.now(timezone.utc).isoformat()))
            print(f"   ✅ Added setting: {key} = {value}")
        except sqlite3.IntegrityError:
            print(f"   ⚠️  Setting {key} already exists, skipping...")
    
    # 3. Add Exams
    print("\n📝 Adding Sample Exams...")
    exams = [
        ('Python Programming Basics', 'Introduction to Python programming concepts', 60, 1),
        ('Web Development Fundamentals', 'HTML, CSS, and JavaScript basics', 90, 1),
        ('Database Management', 'SQL and database design principles', 120, 2),
        ('Mathematics Quiz', 'Basic mathematics and algebra', 45, 1),
        ('Science Test', 'General science knowledge', 75, 2)
    ]
    
    exam_ids = []
    for title, description, duration, created_by in exams:
        try:
            cursor.execute('''
                INSERT INTO exam (title, description, duration_minutes, created_by, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, description, duration, created_by, datetime.now(timezone.utc).isoformat()))
            exam_id = cursor.lastrowid
            exam_ids.append(exam_id)
            print(f"   ✅ Added exam: {title} (ID: {exam_id})")
        except Exception as e:
            print(f"   ❌ Error adding exam {title}: {e}")
    
    # 4. Add Questions
    print("\n❓ Adding Questions to Exams...")
    
    # Questions for Python Programming Basics (exam_id = first exam)
    if exam_ids:
        python_questions = [
            ("What is Python?", "A snake", "A programming language", "A movie", "A game", "B", 2),
            ("Which keyword is used to define a function in Python?", "func", "def", "function", "define", "B", 2),
            ("What is the output of print(2 + 3)?", "23", "5", "error", "none", "B", 1),
            ("Which data type is used to store text in Python?", "int", "float", "str", "bool", "C", 2),
            ("How do you create a list in Python?", "[]", "{}", "()", "<>", "A", 1)
        ]
        
        for question_text, opt_a, opt_b, opt_c, opt_d, correct, marks in python_questions:
            cursor.execute('''
                INSERT INTO question (exam_id, question_text, option_a, option_b, option_c, option_d, correct_answer, marks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (exam_ids[0], question_text, opt_a, opt_b, opt_c, opt_d, correct, marks))
        print(f"   ✅ Added 5 questions to Python Programming exam")
        
        # Questions for Web Development (exam_id = second exam)
        if len(exam_ids) > 1:
            web_questions = [
                ("What does HTML stand for?", "Hyper Text Markup Language", "Home Tool Markup Language", "Hyperlinks and Text Markup Language", "None of the above", "A", 2),
                ("Which CSS property is used to change text color?", "text-color", "font-color", "color", "text-style", "C", 1),
                ("What does JS stand for?", "JavaStyle", "JavaScript", "JustScript", "JavaSource", "B", 1),
                ("Which HTML tag is used for the largest heading?", "<h6>", "<heading>", "<h1>", "<header>", "C", 2)
            ]
            
            for question_text, opt_a, opt_b, opt_c, opt_d, correct, marks in web_questions:
                cursor.execute('''
                    INSERT INTO question (exam_id, question_text, option_a, option_b, option_c, option_d, correct_answer, marks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (exam_ids[1], question_text, opt_a, opt_b, opt_c, opt_d, correct, marks))
            print(f"   ✅ Added 4 questions to Web Development exam")
        
        # Questions for Mathematics Quiz
        if len(exam_ids) > 3:
            math_questions = [
                ("What is 15 + 27?", "42", "41", "43", "40", "A", 1),
                ("What is the square root of 64?", "6", "7", "8", "9", "C", 2),
                ("What is 12 × 8?", "84", "96", "104", "92", "B", 2)
            ]
            
            for question_text, opt_a, opt_b, opt_c, opt_d, correct, marks in math_questions:
                cursor.execute('''
                    INSERT INTO question (exam_id, question_text, option_a, option_b, option_c, option_d, correct_answer, marks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (exam_ids[3], question_text, opt_a, opt_b, opt_c, opt_d, correct, marks))
            print(f"   ✅ Added 3 questions to Mathematics exam")
    
    # 5. Add Exam Permissions (Assignments)
    print("\n🔐 Adding Exam Permissions...")
    
    # Get student user IDs
    cursor.execute('SELECT id, username FROM user WHERE is_admin = 0')
    students_data = cursor.fetchall()
    
    if exam_ids and students_data:
        now = datetime.now(timezone.utc)
        permissions = []
        
        # Create various permission scenarios
        for i, (student_id, username) in enumerate(students_data[:6]):  # First 6 students
            for j, exam_id in enumerate(exam_ids[:3]):  # First 3 exams
                if i + j < 8:  # Create varied permissions
                    if (i + j) % 3 == 0:  # Current active exam
                        start_time = now - timedelta(hours=1)
                        end_time = now + timedelta(hours=2)
                        is_completed = False
                    elif (i + j) % 3 == 1:  # Recently completed exam
                        start_time = now - timedelta(days=2)
                        end_time = now - timedelta(hours=1)
                        is_completed = True
                    else:  # Future exam
                        start_time = now + timedelta(hours=2)
                        end_time = now + timedelta(days=1)
                        is_completed = False
                    
                    permissions.append((
                        student_id, exam_id, 
                        start_time.isoformat(), 
                        end_time.isoformat(), 
                        is_completed,
                        now.isoformat()
                    ))
        
        for user_id, exam_id, start_time, end_time, is_completed, created_at in permissions:
            cursor.execute('''
                INSERT INTO exam_permission (user_id, exam_id, start_time, end_time, is_completed, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, exam_id, start_time, end_time, is_completed, created_at))
        
        print(f"   ✅ Added {len(permissions)} exam permissions")
    
    # 6. Add Exam Results
    print("\n📊 Adding Exam Results...")
    
    # Get completed permissions
    cursor.execute('''
        SELECT ep.user_id, ep.exam_id, u.username 
        FROM exam_permission ep 
        JOIN user u ON ep.user_id = u.id 
        WHERE ep.is_completed = 1
    ''')
    completed_permissions = cursor.fetchall()
    
    for user_id, exam_id, username in completed_permissions:
        # Get exam questions to calculate total marks
        cursor.execute('SELECT SUM(marks) FROM question WHERE exam_id = ?', (exam_id,))
        total_marks_result = cursor.fetchone()
        total_marks = total_marks_result[0] if total_marks_result[0] else 10
        
        # Generate realistic scores (60-95% range)
        import random
        score_percentage = random.uniform(0.6, 0.95)
        score = int(total_marks * score_percentage)
        percentage = (score / total_marks) * 100
        
        # Create sample answers
        answers = {f"question_{i}": random.choice(["A", "B", "C", "D"]) for i in range(1, 6)}
        
        cursor.execute('''
            INSERT INTO exam_result (user_id, exam_id, score, total_marks, percentage, answers, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, exam_id, score, total_marks, percentage, 
            json.dumps(answers),
            (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))).isoformat()
        ))
        
        print(f"   ✅ Added result: {username} scored {score}/{total_marks} ({percentage:.1f}%)")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("🎉 SQLITE DATABASE POPULATED SUCCESSFULLY!")
    print("=" * 60)
    print("📊 Test Data Summary:")
    print(f"   👥 Students: {len(students)} users")
    print(f"   ⚙️  Settings: {len(settings)} configuration items")
    print(f"   📝 Exams: {len(exams)} exams")
    print(f"   ❓ Questions: Multiple questions per exam")
    print(f"   🔐 Permissions: Multiple exam assignments")
    print(f"   📊 Results: Sample exam results")
    print("\n✅ Ready for Firebase migration!")

def verify_data():
    """Verify the populated data"""
    print("\n🔍 Verifying Populated Data...")
    
    conn = sqlite3.connect('instance/exam_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    tables = ['user', 'settings', 'exam', 'question', 'exam_permission', 'exam_result']
    
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"   📋 {table}: {count} records")
    
    conn.close()
    print("✅ Data verification complete!")

def main():
    """Main function"""
    populate_test_data()
    verify_data()

if __name__ == "__main__":
    main()