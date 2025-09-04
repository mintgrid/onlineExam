"""
Firebase Firestore Models
Replacement for SQLAlchemy models with Firestore collections
"""

from firebase_config import firebase_db, COLLECTIONS
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string

class User:
    """User model for Firestore"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.username = data.get('username')
            self.email = data.get('email') 
            self.password_hash = data.get('password_hash')
            self.is_admin = data.get('is_admin', False)
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
        else:
            self.id = None
            self.username = None
            self.email = None
            self.password_hash = None
            self.is_admin = False
            self.created_at = None
            self.updated_at = None
    
    def save(self):
        """Save user to Firestore"""
        user_data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'is_admin': self.is_admin
        }
        
        if self.id:
            # Update existing user
            firebase_db.update_document(COLLECTIONS['USERS'], self.id, user_data)
        else:
            # Create new user
            self.id = firebase_db.add_document(COLLECTIONS['USERS'], user_data)
        
        return self.id
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        data = firebase_db.get_document(COLLECTIONS['USERS'], user_id)
        return User(data) if data else None
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        data = firebase_db.get_document_by_field(COLLECTIONS['USERS'], 'username', username)
        return User(data) if data else None
    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        data = firebase_db.get_document_by_field(COLLECTIONS['USERS'], 'email', email)
        return User(data) if data else None
    
    @staticmethod
    def get_all_students():
        """Get all student users"""
        docs = firebase_db.get_documents(
            COLLECTIONS['USERS'], 
            filters=[('is_admin', '==', False)]
        )
        # Sort in Python to avoid Firebase index requirements
        users = [User(doc) for doc in docs]
        return sorted(users, key=lambda x: x.created_at or '', reverse=True)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def delete(self):
        """Delete user"""
        if self.id:
            return firebase_db.delete_document(COLLECTIONS['USERS'], self.id)
        return False
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class Exam:
    """Exam model for Firestore"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.title = data.get('title')
            self.description = data.get('description')
            self.duration_minutes = data.get('duration_minutes', 60)
            self.created_by = data.get('created_by')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
        else:
            self.id = None
            self.title = None
            self.description = None
            self.duration_minutes = 60
            self.created_by = None
            self.created_at = None
            self.updated_at = None
    
    def save(self):
        """Save exam to Firestore"""
        exam_data = {
            'title': self.title,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'created_by': self.created_by
        }
        
        if self.id:
            firebase_db.update_document(COLLECTIONS['EXAMS'], self.id, exam_data)
        else:
            self.id = firebase_db.add_document(COLLECTIONS['EXAMS'], exam_data)
        
        return self.id
    
    @staticmethod
    def get_by_id(exam_id):
        """Get exam by ID"""
        data = firebase_db.get_document(COLLECTIONS['EXAMS'], exam_id)
        return Exam(data) if data else None
    
    @staticmethod
    def get_by_creator(creator_id):
        """Get exams created by a specific user"""
        docs = firebase_db.get_documents(
            COLLECTIONS['EXAMS'],
            filters=[('created_by', '==', creator_id)]
        )
        # Sort in Python to avoid Firebase index requirements
        exams = [Exam(doc) for doc in docs]
        return sorted(exams, key=lambda x: x.created_at or '', reverse=True)
    
    def get_questions(self):
        """Get questions for this exam"""
        return Question.get_by_exam_id(self.id)
    
    def get_permissions(self):
        """Get permissions for this exam"""
        return ExamPermission.get_by_exam_id(self.id)
    
    def get_results(self):
        """Get results for this exam"""
        return ExamResult.get_by_exam_id(self.id)
    
    def delete(self):
        """Delete exam and all related data"""
        if not self.id:
            return False
        
        # Delete related questions, permissions, and results
        questions = self.get_questions()
        permissions = self.get_permissions()
        results = self.get_results()
        
        operations = []
        
        # Add delete operations for questions
        for question in questions:
            operations.append({
                'type': 'delete',
                'collection': COLLECTIONS['QUESTIONS'],
                'doc_id': question.id
            })
        
        # Add delete operations for permissions
        for permission in permissions:
            operations.append({
                'type': 'delete',
                'collection': COLLECTIONS['EXAM_PERMISSIONS'],
                'doc_id': permission.id
            })
        
        # Add delete operations for results
        for result in results:
            operations.append({
                'type': 'delete',
                'collection': COLLECTIONS['EXAM_RESULTS'],
                'doc_id': result.id
            })
        
        # Add delete operation for exam
        operations.append({
            'type': 'delete',
            'collection': COLLECTIONS['EXAMS'],
            'doc_id': self.id
        })
        
        return firebase_db.batch_write(operations)

class Question:
    """Question model for Firestore"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.exam_id = data.get('exam_id')
            self.question_text = data.get('question_text')
            self.option_a = data.get('option_a')
            self.option_b = data.get('option_b')
            self.option_c = data.get('option_c')
            self.option_d = data.get('option_d')
            self.correct_answer = data.get('correct_answer')
            self.marks = data.get('marks', 1)
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
        else:
            self.id = None
            self.exam_id = None
            self.question_text = None
            self.option_a = None
            self.option_b = None
            self.option_c = None
            self.option_d = None
            self.correct_answer = None
            self.marks = 1
            self.created_at = None
            self.updated_at = None
    
    def save(self):
        """Save question to Firestore"""
        question_data = {
            'exam_id': self.exam_id,
            'question_text': self.question_text,
            'option_a': self.option_a,
            'option_b': self.option_b,
            'option_c': self.option_c,
            'option_d': self.option_d,
            'correct_answer': self.correct_answer,
            'marks': self.marks
        }
        
        if self.id:
            firebase_db.update_document(COLLECTIONS['QUESTIONS'], self.id, question_data)
        else:
            self.id = firebase_db.add_document(COLLECTIONS['QUESTIONS'], question_data)
        
        return self.id
    
    @staticmethod
    def get_by_id(question_id):
        """Get question by ID"""
        data = firebase_db.get_document(COLLECTIONS['QUESTIONS'], question_id)
        return Question(data) if data else None
    
    @staticmethod
    def get_by_exam_id(exam_id):
        """Get questions for a specific exam"""
        docs = firebase_db.get_documents(
            COLLECTIONS['QUESTIONS'],
            filters=[('exam_id', '==', exam_id)]
        )
        # Sort in Python to avoid Firebase index requirements
        questions = [Question(doc) for doc in docs]
        return sorted(questions, key=lambda x: x.created_at or '')  # Ascending order
    
    @staticmethod
    def get_all():
        """Get all questions"""
        docs = firebase_db.get_documents(COLLECTIONS['QUESTIONS'])
        # Sort in Python to avoid Firebase composite index requirements
        questions = [Question(doc) for doc in docs]
        return sorted(questions, key=lambda x: x.created_at or '')
    
    def delete(self):
        """Delete question"""
        if self.id:
            return firebase_db.delete_document(COLLECTIONS['QUESTIONS'], self.id)
        return False

class ExamPermission:
    """Exam Permission model for Firestore"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.user_id = data.get('user_id')
            self.exam_id = data.get('exam_id')
            self.start_time = data.get('start_time')
            self.end_time = data.get('end_time')
            self.is_completed = data.get('is_completed', False)
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
        else:
            self.id = None
            self.user_id = None
            self.exam_id = None
            self.start_time = None
            self.end_time = None
            self.is_completed = False
            self.created_at = None
            self.updated_at = None
    
    def save(self):
        """Save permission to Firestore"""
        permission_data = {
            'user_id': self.user_id,
            'exam_id': self.exam_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'is_completed': self.is_completed
        }
        
        if self.id:
            firebase_db.update_document(COLLECTIONS['EXAM_PERMISSIONS'], self.id, permission_data)
        else:
            self.id = firebase_db.add_document(COLLECTIONS['EXAM_PERMISSIONS'], permission_data)
        
        return self.id
    
    @staticmethod
    def get_by_id(permission_id):
        """Get permission by ID"""
        data = firebase_db.get_document(COLLECTIONS['EXAM_PERMISSIONS'], permission_id)
        return ExamPermission(data) if data else None
    
    @staticmethod
    def get_by_exam_id(exam_id):
        """Get permissions for a specific exam"""
        docs = firebase_db.get_documents(
            COLLECTIONS['EXAM_PERMISSIONS'],
            filters=[('exam_id', '==', exam_id)]
        )
        # Sort in Python to avoid Firebase index requirements
        permissions = [ExamPermission(doc) for doc in docs]
        return sorted(permissions, key=lambda x: x.created_at or '', reverse=True)
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get permissions for a specific user"""
        docs = firebase_db.get_documents(
            COLLECTIONS['EXAM_PERMISSIONS'],
            filters=[('user_id', '==', user_id)]
        )
        # Sort in Python to avoid Firebase index requirements
        permissions = [ExamPermission(doc) for doc in docs]
        return sorted(permissions, key=lambda x: x.created_at or '', reverse=True)
    
    @staticmethod
    def get_user_exam_permission(user_id, exam_id):
        """Get specific user exam permission"""
        docs = firebase_db.get_documents(
            COLLECTIONS['EXAM_PERMISSIONS'],
            filters=[('user_id', '==', user_id), ('exam_id', '==', exam_id)],
            limit=1
        )
        return ExamPermission(docs[0]) if docs else None
    
    @staticmethod
    def get_all():
        """Get all exam permissions"""
        docs = firebase_db.get_documents(COLLECTIONS['EXAM_PERMISSIONS'])
        # Sort in Python to avoid Firebase index requirements
        permissions = [ExamPermission(doc) for doc in docs]
        return sorted(permissions, key=lambda x: x.created_at or '', reverse=True)
    
    def delete(self):
        """Delete permission"""
        if self.id:
            return firebase_db.delete_document(COLLECTIONS['EXAM_PERMISSIONS'], self.id)
        return False

class ExamResult:
    """Exam Result model for Firestore"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.user_id = data.get('user_id')
            self.exam_id = data.get('exam_id')
            self.score = data.get('score', 0)
            self.total_marks = data.get('total_marks', 0)
            self.percentage = data.get('percentage', 0.0)
            self.answers = data.get('answers', {})
            self.submitted_at = data.get('submitted_at')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
        else:
            self.id = None
            self.user_id = None
            self.exam_id = None
            self.score = 0
            self.total_marks = 0
            self.percentage = 0.0
            self.answers = {}
            self.submitted_at = None
            self.created_at = None
            self.updated_at = None
    
    def save(self):
        """Save result to Firestore"""
        result_data = {
            'user_id': self.user_id,
            'exam_id': self.exam_id,
            'score': self.score,
            'total_marks': self.total_marks,
            'percentage': self.percentage,
            'answers': self.answers,
            'submitted_at': self.submitted_at
        }
        
        if self.id:
            firebase_db.update_document(COLLECTIONS['EXAM_RESULTS'], self.id, result_data)
        else:
            self.id = firebase_db.add_document(COLLECTIONS['EXAM_RESULTS'], result_data)
        
        return self.id
    
    @staticmethod
    def get_by_id(result_id):
        """Get result by ID"""
        data = firebase_db.get_document(COLLECTIONS['EXAM_RESULTS'], result_id)
        return ExamResult(data) if data else None
    
    @staticmethod
    def get_by_exam_id(exam_id):
        """Get results for a specific exam"""
        docs = firebase_db.get_documents(
            COLLECTIONS['EXAM_RESULTS'],
            filters=[('exam_id', '==', exam_id)]
        )
        # Sort in Python to avoid Firebase composite index requirements
        results = [ExamResult(doc) for doc in docs]
        return sorted(results, key=lambda x: x.submitted_at or '', reverse=True)
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get results for a specific user"""
        docs = firebase_db.get_documents(
            COLLECTIONS['EXAM_RESULTS'],
            filters=[('user_id', '==', user_id)]
        )
        # Sort in Python to avoid Firebase composite index requirements
        results = [ExamResult(doc) for doc in docs]
        return sorted(results, key=lambda x: x.submitted_at or '', reverse=True)
    
    @staticmethod
    def get_user_exam_result(user_id, exam_id):
        """Get specific user exam result"""
        docs = firebase_db.get_documents(
            COLLECTIONS['EXAM_RESULTS'],
            filters=[('user_id', '==', user_id), ('exam_id', '==', exam_id)],
            limit=1
        )
        return ExamResult(docs[0]) if docs else None
    
    @staticmethod
    def get_all():
        """Get all exam results"""
        docs = firebase_db.get_documents(COLLECTIONS['EXAM_RESULTS'])
        # Sort in Python to avoid Firebase composite index requirements
        results = [ExamResult(doc) for doc in docs]
        return sorted(results, key=lambda x: x.submitted_at or '', reverse=True)

class Settings:
    """Settings model for Firestore"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.key = data.get('key')
            self.value = data.get('value')
            self.updated_at = data.get('updated_at')
        else:
            self.id = None
            self.key = None
            self.value = None
            self.updated_at = None
    
    def save(self):
        """Save setting to Firestore"""
        setting_data = {
            'key': self.key,
            'value': self.value
        }
        
        if self.id:
            firebase_db.update_document(COLLECTIONS['SETTINGS'], self.id, setting_data)
        else:
            # Use key as document ID for settings
            self.id = self.key
            firebase_db.add_document(COLLECTIONS['SETTINGS'], setting_data, self.key)
        
        return self.id
    
    @staticmethod
    def get_by_key(key):
        """Get setting by key"""
        data = firebase_db.get_document(COLLECTIONS['SETTINGS'], key)
        return Settings(data) if data else None
    
    @staticmethod
    def get_all():
        """Get all settings"""
        docs = firebase_db.get_documents(COLLECTIONS['SETTINGS'])
        return [Settings(doc) for doc in docs]
    
    def delete(self):
        """Delete setting"""
        if self.id:
            return firebase_db.delete_document(COLLECTIONS['SETTINGS'], self.id)
        return False

# Helper functions for compatibility with existing code
def get_setting(key, default=None):
    """Get a setting value"""
    setting = Settings.get_by_key(key)
    return setting.value if setting else default

def set_setting(key, value):
    """Set a setting value"""
    setting = Settings.get_by_key(key)
    if setting:
        setting.value = value
    else:
        setting = Settings()
        setting.key = key
        setting.value = value
    
    return setting.save()

def generate_password():
    """Generate random password"""
    characters = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(characters) for _ in range(10))
    return password