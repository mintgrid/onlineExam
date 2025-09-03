import requests
from datetime import datetime, timedelta

# Create session for admin
session = requests.Session()

# Login as admin
login_data = {'username': 'admin', 'password': 'admin123'}
session.post('http://localhost:5001/login', data=login_data)

print("Creating sample exam and assignments...")

# Create a sample exam
exam_data = {
    'title': 'Python Programming Test',
    'description': 'Basic Python programming concepts',
    'duration': 30
}

exam_response = session.post('http://localhost:5001/admin/create_exam', data=exam_data)
print(f"Exam creation response: {exam_response.status_code}")

# Get the exam ID (we'll assume it's exam ID 1)
# Add some questions to the exam
question_data = {
    'question_text': 'What is Python?',
    'option_a': 'A snake',
    'option_b': 'A programming language',
    'option_c': 'A movie',
    'option_d': 'A game',
    'correct_answer': 'B',
    'marks': 2
}

question_response = session.post('http://localhost:5001/admin/exam/1/questions', data=question_data)
print(f"Question creation response: {question_response.status_code}")

# Create assignments
now = datetime.now()
assignments = [
    {
        'user_id': 1,  # student1
        'exam_id': 1,
        'start_time': (now + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
        'end_time': (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
    },
    {
        'user_id': 2,  # student2
        'exam_id': 1,
        'start_time': (now - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
        'end_time': (now + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    }
]

for assignment in assignments:
    response = session.post('http://localhost:5001/admin/assign_exam', data=assignment)
    print(f"Assignment creation response: {response.status_code}")

print("Sample data creation completed!")
print("You can now view assignments in the admin dashboard.")