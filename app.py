"""
Online Exam Application with Firebase/Firestore Backend
Migrated from SQLAlchemy to Firebase for persistent cloud storage
"""

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
import os
import json

# Import Firebase models and configuration
from firebase_models import User, Exam, Question, ExamPermission, ExamResult, Settings, get_setting, set_setting, generate_password
from firebase_config import firebase_db, COLLECTIONS
import firebase_admin

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@examapp.com')

login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# User class for Flask-Login compatibility
class FlaskUser(UserMixin):
    def __init__(self, user_data):
        self.id = user_data.id
        self.username = user_data.username
        self.email = user_data.email
        self.is_admin = user_data.is_admin
        self.password_hash = user_data.password_hash

@login_manager.user_loader
def load_user(user_id):
    user_data = User.get_by_id(user_id)
    return FlaskUser(user_data) if user_data else None

def update_mail_config():
    """Update Flask-Mail configuration from Firestore settings"""
    try:
        mail_username = get_setting('MAIL_USERNAME', app.config.get('MAIL_USERNAME'))
        mail_password = get_setting('MAIL_PASSWORD', app.config.get('MAIL_PASSWORD'))
        mail_server = get_setting('MAIL_SERVER', app.config.get('MAIL_SERVER', 'smtp.gmail.com'))
        mail_port = int(get_setting('MAIL_PORT', app.config.get('MAIL_PORT', 587)))
        mail_use_tls = get_setting('MAIL_USE_TLS', 'true').lower() == 'true'
        mail_default_sender = get_setting('MAIL_DEFAULT_SENDER', app.config.get('MAIL_DEFAULT_SENDER'))
        
        # Update app config
        app.config['MAIL_USERNAME'] = mail_username
        app.config['MAIL_PASSWORD'] = mail_password
        app.config['MAIL_SERVER'] = mail_server
        app.config['MAIL_PORT'] = mail_port
        app.config['MAIL_USE_TLS'] = mail_use_tls
        app.config['MAIL_DEFAULT_SENDER'] = mail_default_sender
        
        # Reinitialize mail instance
        mail.init_app(app)
    except Exception as e:
        print(f"Error updating mail config: {e}")

def send_user_credentials(email, username, password):
    try:
        # Update mail configuration from Firestore settings
        update_mail_config()
        
        msg = Message('Your Exam Portal Login Credentials',
                      recipients=[email])
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">Welcome to Online Exam Portal</h2>
            <p>Your account has been created successfully. Here are your login credentials:</p>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Username:</strong> {username}</p>
                <p><strong>Password:</strong> {password}</p>
                <p><strong>Login URL:</strong> <a href="http://localhost:5003/login">Login Here</a></p>
            </div>
            <p>Please keep these credentials safe and change your password after first login.</p>
            <p>Best regards,<br>Online Exam Portal Team</p>
        </div>
        '''
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_exam_completion_notification(admin_email, user_name, exam_title, score, total):
    try:
        # Update mail configuration from Firestore settings
        update_mail_config()
        
        msg = Message('Exam Completed Notification',
                      recipients=[admin_email])
        percentage = (score / total * 100) if total > 0 else 0
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">Exam Completion Notification</h2>
            <p>A student has completed an exam:</p>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Student:</strong> {user_name}</p>
                <p><strong>Exam:</strong> {exam_title}</p>
                <p><strong>Score:</strong> {score}/{total} ({percentage:.1f}%)</p>
                <p><strong>Completed At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <p>Please review the results in the admin dashboard.</p>
        </div>
        '''
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

def initialize_database():
    """Initialize Firestore with default admin users"""
    try:
        print("Initializing Firebase/Firestore database...")
        
        # Check if admin users exist
        admin = User.get_by_username('admin')
        if not admin:
            admin = User()
            admin.username = 'admin'
            admin.email = 'admin@examapp.com'
            admin.password_hash = generate_password_hash('admin123')
            admin.is_admin = True
            admin.save()
            print("Created default admin user: admin/admin123")
        
        admin2 = User.get_by_username('admin2')
        if not admin2:
            admin2 = User()
            admin2.username = 'admin2'
            admin2.email = 'admin2@examapp.com'
            admin2.password_hash = generate_password_hash('admin456')
            admin2.is_admin = True
            admin2.save()
            print("Created default admin user: admin2/admin456")
        
        print("Firebase database initialization completed successfully")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise e

# Global flag to track lazy initialization
_database_initialized = False

def ensure_database_initialized():
    """Lazy database initialization for faster startup"""
    global _database_initialized
    if not _database_initialized:
        try:
            initialize_database()
            _database_initialized = True
        except Exception as e:
            print(f"Database initialization failed: {e}")
            # Don't raise exception to allow app to continue starting

# Routes
@app.route('/')
def index():
    # Lazy initialization on first route access
    ensure_database_initialized()
    return render_template('index.html')

@app.route('/startup')
def startup_check():
    """Quick startup check endpoint for Cloud Run"""
    return jsonify({
        'status': 'ready',
        'message': 'Application started successfully',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200

@app.route('/debug')
def debug_firebase():
    """Firebase diagnostic endpoint for Cloud Run debugging"""
    debug_info = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'environment': {
            'K_SERVICE': os.environ.get('K_SERVICE'),  # Cloud Run service name
            'PORT': os.environ.get('PORT'),
            'GOOGLE_CLOUD_PROJECT': os.environ.get('GOOGLE_CLOUD_PROJECT'),
            'FIREBASE_SERVICE_ACCOUNT_SET': bool(os.environ.get('FIREBASE_SERVICE_ACCOUNT')),
        },
        'firebase': {
            'admin_apps': len(firebase_admin._apps) if 'firebase_admin' in globals() else 0,
            'db_initialized': firebase_db.db is not None,
        }
    }
    
    # Test Firebase connection
    try:
        if firebase_db.db:
            # Quick test query
            firebase_db.get_documents(COLLECTIONS['USERS'], limit=1)
            debug_info['firebase']['connection_test'] = 'success'
        else:
            debug_info['firebase']['connection_test'] = 'db_not_initialized'
    except Exception as e:
        debug_info['firebase']['connection_test'] = f'failed: {str(e)}'
    
    return jsonify(debug_info), 200

@app.route('/health')
def health_check():
    """Health check endpoint for Google Cloud monitoring"""
    # Ensure database is initialized on first health check
    ensure_database_initialized()
    
    try:
        # Check Firebase connectivity by getting a user
        firebase_db.get_documents(COLLECTIONS['USERS'], limit=1)
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'database': db_status,
        'backend': 'firebase',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200 if db_status == 'healthy' else 503

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.get_by_username(username)
        
        if user and user.check_password(password):
            flask_user = FlaskUser(user)
            login_user(flask_user)
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('user_dashboard'))
    
    exams = Exam.get_by_creator(current_user.id)
    users = User.get_all_students()
    
    # Performance optimization: Batch load all related data
    if exams:
        exam_ids = [exam.id for exam in exams]
        
        # Get all permissions, results, questions in batch
        all_permissions = ExamPermission.get_all()
        all_results = ExamResult.get_all()
        all_questions = Question.get_all()
        all_users = {user.id: user for user in User.get_all_students()}
        
        # Group by exam_id for faster lookups
        permissions_by_exam = {}
        results_by_exam = {}
        questions_by_exam = {}
        
        for perm in all_permissions:
            if perm.exam_id in exam_ids:
                if perm.exam_id not in permissions_by_exam:
                    permissions_by_exam[perm.exam_id] = []
                perm.user = all_users.get(perm.user_id)  # Enrich with user data
                permissions_by_exam[perm.exam_id].append(perm)
        
        for result in all_results:
            if result.exam_id in exam_ids:
                if result.exam_id not in results_by_exam:
                    results_by_exam[result.exam_id] = []
                results_by_exam[result.exam_id].append(result)
        
        for question in all_questions:
            if question.exam_id in exam_ids:
                if question.exam_id not in questions_by_exam:
                    questions_by_exam[question.exam_id] = []
                questions_by_exam[question.exam_id].append(question)
        
        # Assign to exams and enrich permissions with exam data
        for exam in exams:
            exam.permissions = permissions_by_exam.get(exam.id, [])
            exam.results = results_by_exam.get(exam.id, [])
            exam.questions = questions_by_exam.get(exam.id, [])
            
            # Enrich permissions with exam data
            for perm in exam.permissions:
                perm.exam = exam
    
    return render_template('admin_dashboard.html', exams=exams, users=users)

@app.route('/admin/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        # Check if user already exists
        if User.get_by_username(username):
            flash('Username already exists', 'error')
            return redirect(url_for('create_user'))
        
        if User.get_by_email(email):
            flash('Email already exists', 'error')
            return redirect(url_for('create_user'))
        
        # Generate random password
        password = generate_password()
        
        # Create new user
        user = User()
        user.username = username
        user.email = email
        user.password_hash = generate_password_hash(password)
        user.is_admin = False
        
        user_id = user.save()
        
        if user_id:
            # Send credentials via email
            send_user_credentials(email, username, password)
            flash(f'User created successfully. Credentials sent to {email}', 'success')
        else:
            flash('Error creating user', 'error')
        
        return redirect(url_for('create_user'))
    
    return render_template('create_user.html')

@app.route('/admin/create_exam', methods=['GET', 'POST'])
@login_required
def create_exam():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Validate required fields
        title = request.form.get('title')
        description = request.form.get('description', '')
        # Check for both 'duration' and 'duration_minutes' field names for compatibility
        duration_str = request.form.get('duration') or request.form.get('duration_minutes')
        
        if not title:
            flash('Exam title is required', 'error')
            return redirect(url_for('create_exam'))
        
        if not duration_str:
            flash('Exam duration is required', 'error')
            return redirect(url_for('create_exam'))
        
        try:
            duration_minutes = int(duration_str)
            if duration_minutes < 5 or duration_minutes > 300:
                flash('Duration must be between 5 and 300 minutes', 'error')
                return redirect(url_for('create_exam'))
        except (ValueError, TypeError):
            flash('Invalid duration value', 'error')
            return redirect(url_for('create_exam'))
        
        exam = Exam()
        exam.title = title
        exam.description = description
        exam.duration_minutes = duration_minutes
        exam.created_by = current_user.id
        
        exam_id = exam.save()
        
        if exam_id:
            flash('Exam created successfully', 'success')
            return redirect(url_for('manage_questions', exam_id=exam_id))
        else:
            flash('Error creating exam', 'error')
    
    return render_template('create_exam.html')

@app.route('/admin/exam/<exam_id>/questions', methods=['GET', 'POST'])
@login_required
def manage_questions(exam_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    exam = Exam.get_by_id(exam_id)
    if not exam or exam.created_by != current_user.id:
        flash('Exam not found or access denied', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        question = Question()
        question.exam_id = exam_id
        question.question_text = request.form.get('question_text')
        question.option_a = request.form.get('option_a')
        question.option_b = request.form.get('option_b')
        question.option_c = request.form.get('option_c')
        question.option_d = request.form.get('option_d')
        question.correct_answer = request.form.get('correct_answer')
        question.marks = int(request.form.get('marks', 1))
        
        if question.save():
            flash('Question added successfully', 'success')
        else:
            flash('Error adding question', 'error')
        
        return redirect(url_for('manage_questions', exam_id=exam_id))
    
    questions = Question.get_by_exam_id(exam_id)
    return render_template('manage_questions.html', exam=exam, questions=questions)

@app.route('/admin/exam/<exam_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_exam(exam_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    exam = Exam.get_by_id(exam_id)
    if not exam or exam.created_by != current_user.id:
        flash('Exam not found or access denied', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        # Validate required fields
        title = request.form.get('title')
        description = request.form.get('description', '')
        # Check for both 'duration' and 'duration_minutes' field names for compatibility
        duration_str = request.form.get('duration') or request.form.get('duration_minutes')
        
        if not title:
            flash('Exam title is required', 'error')
            return redirect(url_for('edit_exam', exam_id=exam_id))
        
        if not duration_str:
            flash('Exam duration is required', 'error')
            return redirect(url_for('edit_exam', exam_id=exam_id))
        
        try:
            duration_minutes = int(duration_str)
            if duration_minutes < 5 or duration_minutes > 300:
                flash('Duration must be between 5 and 300 minutes', 'error')
                return redirect(url_for('edit_exam', exam_id=exam_id))
        except (ValueError, TypeError):
            flash('Invalid duration value', 'error')
            return redirect(url_for('edit_exam', exam_id=exam_id))
        
        exam.title = title
        exam.description = description
        exam.duration_minutes = duration_minutes
        
        if exam.save():
            flash('Exam updated successfully', 'success')
        else:
            flash('Error updating exam', 'error')
        
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_exam.html', exam=exam)

@app.route('/admin/exam/<exam_id>/delete', methods=['POST'])
@login_required
def delete_exam(exam_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    exam = Exam.get_by_id(exam_id)
    if not exam or exam.created_by != current_user.id:
        return jsonify({'error': 'Exam not found or access denied'}), 403
    
    if exam.delete():
        return jsonify({'message': 'Exam deleted successfully'}), 200
    else:
        return jsonify({'error': 'Error deleting exam'}), 500

@app.route('/admin/question/<question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    question = Question.get_by_id(question_id)
    if not question:
        flash('Question not found', 'error')
        return redirect(url_for('admin_dashboard'))
    
    exam = Exam.get_by_id(question.exam_id)
    if not exam or exam.created_by != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        question.question_text = request.form.get('question_text')
        question.option_a = request.form.get('option_a')
        question.option_b = request.form.get('option_b')
        question.option_c = request.form.get('option_c')
        question.option_d = request.form.get('option_d')
        question.correct_answer = request.form.get('correct_answer')
        question.marks = int(request.form.get('marks', 1))
        
        if question.save():
            flash('Question updated successfully', 'success')
        else:
            flash('Error updating question', 'error')
        
        return redirect(url_for('manage_questions', exam_id=question.exam_id))
    
    return render_template('edit_question.html', question=question, exam=exam)

@app.route('/admin/question/<question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    question = Question.get_by_id(question_id)
    if not question:
        return jsonify({'error': 'Question not found'}), 404
    
    exam = Exam.get_by_id(question.exam_id)
    if not exam or exam.created_by != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    exam_id = question.exam_id
    if question.delete():
        return jsonify({'message': 'Question deleted successfully', 'exam_id': exam_id}), 200
    else:
        return jsonify({'error': 'Error deleting question'}), 500

@app.route('/admin/assign_exam', methods=['GET', 'POST'])
@login_required
def assign_exam():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        exam_id = request.form.get('exam_id')
        user_id = request.form.get('user_id')
        start_time = datetime.fromisoformat(request.form.get('start_time')).replace(tzinfo=timezone.utc)
        end_time = datetime.fromisoformat(request.form.get('end_time')).replace(tzinfo=timezone.utc)
        
        # Check if permission already exists
        existing_permission = ExamPermission.get_user_exam_permission(user_id, exam_id)
        if existing_permission:
            flash('Permission already exists for this user and exam', 'error')
            return redirect(url_for('assign_exam'))
        
        permission = ExamPermission()
        permission.user_id = user_id
        permission.exam_id = exam_id
        permission.start_time = start_time
        permission.end_time = end_time
        permission.is_completed = False
        
        if permission.save():
            user = User.get_by_id(user_id)
            exam = Exam.get_by_id(exam_id)
            flash(f'Exam "{exam.title}" assigned to {user.username}', 'success')
        else:
            flash('Error assigning exam', 'error')
        
        return redirect(url_for('assign_exam'))
    
    exams = Exam.get_by_creator(current_user.id)
    users = User.get_all_students()
    return render_template('assign_exam.html', exams=exams, users=users)

@app.route('/admin/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        user = User.get_by_id(current_user.id)
        
        if not user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('change_password'))
        
        if not new_password or len(new_password) < 6:
            flash('New password must be at least 6 characters long', 'error')
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('change_password'))
        
        if user.check_password(new_password):
            flash('New password must be different from current password', 'error')
            return redirect(url_for('change_password'))
        
        user.set_password(new_password)
        if user.save():
            flash('Password changed successfully!', 'success')
        else:
            flash('Error changing password', 'error')
        
        return redirect(url_for('admin_dashboard'))
    
    return render_template('change_password.html')

@app.route('/admin/notification_settings', methods=['GET', 'POST'])
@login_required
def notification_settings():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        mail_server = request.form.get('mail_server', 'smtp.gmail.com')
        mail_port = request.form.get('mail_port', '587')
        mail_username = request.form.get('mail_username', '')
        mail_password = request.form.get('mail_password', '')
        mail_use_tls = 'mail_use_tls' in request.form
        mail_default_sender = request.form.get('mail_default_sender', '')
        
        if not mail_username:
            flash('Email username is required', 'error')
            return redirect(url_for('notification_settings'))
        
        if not mail_password:
            flash('Email password is required', 'error')
            return redirect(url_for('notification_settings'))
        
        try:
            port_num = int(mail_port)
            if port_num < 1 or port_num > 65535:
                raise ValueError()
        except ValueError:
            flash('Invalid port number', 'error')
            return redirect(url_for('notification_settings'))
        
        try:
            set_setting('MAIL_SERVER', mail_server)
            set_setting('MAIL_PORT', mail_port)
            set_setting('MAIL_USERNAME', mail_username)
            set_setting('MAIL_PASSWORD', mail_password)
            set_setting('MAIL_USE_TLS', 'true' if mail_use_tls else 'false')
            set_setting('MAIL_DEFAULT_SENDER', mail_default_sender or mail_username)
            
            update_mail_config()
            flash('Notification settings updated successfully!', 'success')
        except Exception as e:
            flash(f'Error saving settings: {str(e)}', 'error')
        
        return redirect(url_for('notification_settings'))
    
    current_settings = {
        'mail_server': get_setting('MAIL_SERVER', 'smtp.gmail.com'),
        'mail_port': get_setting('MAIL_PORT', '587'),
        'mail_username': get_setting('MAIL_USERNAME', ''),
        'mail_password': get_setting('MAIL_PASSWORD', ''),
        'mail_use_tls': get_setting('MAIL_USE_TLS', 'true').lower() == 'true',
        'mail_default_sender': get_setting('MAIL_DEFAULT_SENDER', '')
    }
    
    return render_template('notification_settings.html', settings=current_settings)

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get user's exam permissions
    permissions = ExamPermission.get_by_user_id(current_user.id)
    
    available_exams = []
    completed_exams = []
    
    current_time = datetime.now(timezone.utc)
    
    for permission in permissions:
        exam = Exam.get_by_id(permission.exam_id)
        if exam:
            # Load questions for this exam to get accurate question count
            exam.questions = Question.get_by_exam_id(exam.id)
            permission.exam = exam
            
            if permission.is_completed:
                # Also load exam results for completed exams
                exam.results = ExamResult.get_by_exam_id(exam.id)
                completed_exams.append(permission)
            elif permission.start_time <= current_time <= permission.end_time:
                available_exams.append(permission)
    
    return render_template('user_dashboard.html', 
                         available_exams=available_exams, 
                         completed_exams=completed_exams)

@app.route('/exam/<exam_id>/take')
@login_required
def take_exam(exam_id):
    if current_user.is_admin:
        flash('Admins cannot take exams', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Check permission
    permission = ExamPermission.get_user_exam_permission(current_user.id, exam_id)
    if not permission:
        flash('You do not have permission to take this exam', 'error')
        return redirect(url_for('user_dashboard'))
    
    current_time = datetime.now(timezone.utc)
    if current_time < permission.start_time or current_time > permission.end_time:
        flash('This exam is not available at this time', 'error')
        return redirect(url_for('user_dashboard'))
    
    if permission.is_completed:
        flash('You have already completed this exam', 'error')
        return redirect(url_for('user_dashboard'))
    
    exam = Exam.get_by_id(exam_id)
    questions = Question.get_by_exam_id(exam_id)
    
    # Calculate time remaining for the exam
    # For the exam timer, we use the full exam duration regardless of permission window
    # This gives students the full allocated time for the exam
    time_remaining_seconds = exam.duration_minutes * 60
    
    # However, we should also check if the permission window ends before the exam duration
    # to prevent students from taking more time than the permission allows
    time_until_permission_end = int((permission.end_time - current_time).total_seconds())
    
    # Use the minimum of exam duration and time until permission ends
    time_remaining = min(time_remaining_seconds, time_until_permission_end)
    
    # Ensure time remaining is not negative
    time_remaining = max(0, time_remaining)
    
    return render_template('take_exam.html', exam=exam, questions=questions, permission=permission, time_remaining=time_remaining)

@app.route('/exam/<exam_id>/submit', methods=['POST'])
@login_required
def submit_exam(exam_id):
    if current_user.is_admin:
        return jsonify({'error': 'Admins cannot take exams'}), 403
    
    permission = ExamPermission.get_user_exam_permission(current_user.id, exam_id)
    if not permission or permission.is_completed:
        return jsonify({'error': 'Invalid exam submission'}), 403
    
    # Get answers from form
    answers = {}
    for key, value in request.form.items():
        if key.startswith('question_'):
            question_id = key.replace('question_', '')
            answers[question_id] = value
    
    # Calculate score
    questions = Question.get_by_exam_id(exam_id)
    score = 0
    total_marks = 0
    
    for question in questions:
        total_marks += question.marks
        if question.id in answers and answers[question.id] == question.correct_answer:
            score += question.marks
    
    percentage = (score / total_marks * 100) if total_marks > 0 else 0
    
    # Save result
    result = ExamResult()
    result.user_id = current_user.id
    result.exam_id = exam_id
    result.score = score
    result.total_marks = total_marks
    result.percentage = percentage
    result.answers = answers
    result.submitted_at = datetime.now(timezone.utc)
    
    if result.save():
        # Mark permission as completed
        permission.is_completed = True
        permission.save()
        
        # Send notification to admin
        exam = Exam.get_by_id(exam_id)
        admin = User.get_by_id(exam.created_by)
        send_exam_completion_notification(
            admin.email,
            current_user.username,
            exam.title,
            score,
            total_marks
        )
        
        flash(f'Exam submitted successfully! Your score: {score}/{total_marks} ({percentage:.2f}%)', 'success')
    else:
        flash('Error submitting exam', 'error')
    
    return redirect(url_for('user_dashboard'))

@app.route('/admin/view_results')
@login_required
def view_results():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Get all exam results
    results = ExamResult.get_all()
    
    # Enrich results with exam and user details
    for result in results:
        result.exam = Exam.get_by_id(result.exam_id)
        result.user = User.get_by_id(result.user_id)
    
    return render_template('view_results.html', results=results)

@app.route('/admin/view_assignments')
@login_required
def view_assignments():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Get all exam permissions/assignments
    permissions = ExamPermission.get_all()
    
    # Enrich permissions with exam and user details
    for permission in permissions:
        permission.exam = Exam.get_by_id(permission.exam_id)
        permission.user = User.get_by_id(permission.user_id)
    
    return render_template('manage_assignments.html', assignments=permissions)

@app.route('/admin/edit_assignment/<assignment_id>', methods=['GET', 'POST'])
@login_required
def edit_assignment(assignment_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Get the assignment
    assignment = ExamPermission.get_by_id(assignment_id)
    if not assignment:
        flash('Assignment not found', 'error')
        return redirect(url_for('view_assignments'))
    
    # Enrich with exam and user data
    assignment.exam = Exam.get_by_id(assignment.exam_id)
    assignment.user = User.get_by_id(assignment.user_id)
    
    if request.method == 'POST':
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        
        if not start_time_str or not end_time_str:
            flash('Both start time and end time are required', 'error')
            return redirect(url_for('edit_assignment', assignment_id=assignment_id))
        
        try:
            # Parse the datetime strings
            start_time = datetime.fromisoformat(start_time_str.replace('T', ' '))
            end_time = datetime.fromisoformat(end_time_str.replace('T', ' '))
            
            # Convert to UTC
            start_time = start_time.replace(tzinfo=timezone.utc)
            end_time = end_time.replace(tzinfo=timezone.utc)
            
            if end_time <= start_time:
                flash('End time must be after start time', 'error')
                return redirect(url_for('edit_assignment', assignment_id=assignment_id))
            
            # Update the assignment
            assignment.start_time = start_time
            assignment.end_time = end_time
            assignment.save()
            
            flash('Assignment updated successfully!', 'success')
            return redirect(url_for('view_assignments'))
            
        except ValueError as e:
            flash(f'Invalid date format: {str(e)}', 'error')
            return redirect(url_for('edit_assignment', assignment_id=assignment_id))
    
    return render_template('edit_assignment.html', assignment=assignment)

@app.route('/admin/user/<user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get the user to delete
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Prevent deletion of admin users (safety measure)
    if user.is_admin:
        return jsonify({'error': 'Cannot delete admin users'}), 403
    
    # Prevent deletion of current user
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 403
    
    try:
        # Delete related data first (cascade deletion)
        
        # 1. Delete exam results for this user
        exam_results = ExamResult.get_by_user_id(user_id)
        for result in exam_results:
            result.delete()
        
        # 2. Delete exam permissions (assignments) for this user
        permissions = ExamPermission.get_by_user_id(user_id)
        for permission in permissions:
            permission.delete()
        
        # 3. Finally delete the user
        if user.delete():
            return jsonify({'message': f'User {user.username} deleted successfully'}), 200
        else:
            return jsonify({'error': 'Error deleting user from database'}), 500
            
    except Exception as e:
        print(f"Error deleting user {user_id}: {str(e)}")
        return jsonify({'error': f'Error deleting user: {str(e)}'}), 500

if __name__ == '__main__':
    # Get port from environment variable (Cloud Run uses PORT env var)
    port = int(os.environ.get('PORT', 8080))
    
    # Use lazy initialization to speed up startup
    print("Starting application... (Firebase will initialize on first request)")
    
    # Optionally initialize database now (uncomment for immediate init)
    # ensure_database_initialized()
    
    # Use production settings for Cloud Run
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)