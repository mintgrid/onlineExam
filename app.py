from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import os
import secrets
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exam_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@examapp.com')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    exam_permissions = db.relationship('ExamPermission', backref='user', lazy=True)
    exam_results = db.relationship('ExamResult', backref='user', lazy=True)

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, default=60)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    questions = db.relationship('Question', backref='exam', lazy=True, cascade='all, delete-orphan')
    permissions = db.relationship('ExamPermission', backref='exam', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('ExamResult', backref='exam', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500))
    option_b = db.Column(db.String(500))
    option_c = db.Column(db.String(500))
    option_d = db.Column(db.String(500))
    correct_answer = db.Column(db.String(1), nullable=False)
    marks = db.Column(db.Integer, default=1)

class ExamPermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class ExamResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    score = db.Column(db.Integer)
    total_marks = db.Column(db.Integer)
    percentage = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    answers = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_password():
    characters = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(characters) for _ in range(10))
    return password

def send_user_credentials(email, username, password):
    try:
        msg = Message('Your Exam Portal Login Credentials',
                      recipients=[email])
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">Welcome to Online Exam Portal</h2>
            <p>Your login credentials are:</p>
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <p><strong>Username:</strong> {username}</p>
                <p><strong>Password:</strong> {password}</p>
            </div>
            <p style="margin-top: 20px;">Please login at: <a href="http://localhost:5000/login">Exam Portal</a></p>
            <p style="color: #7f8c8d; font-size: 12px;">Please change your password after first login.</p>
        </div>
        '''
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_exam_completion_notification(admin_email, user_name, exam_title, score, total):
    try:
        msg = Message('Exam Completed Notification',
                      recipients=[admin_email])
        percentage = (score / total * 100) if total > 0 else 0
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">Exam Completion Report</h2>
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <p><strong>Student Name:</strong> {user_name}</p>
                <p><strong>Exam:</strong> {exam_title}</p>
                <p><strong>Score:</strong> {score}/{total}</p>
                <p><strong>Percentage:</strong> {percentage:.2f}%</p>
                <p><strong>Completed At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
        '''
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
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
    
    exams = Exam.query.filter_by(created_by=current_user.id).all()
    users = User.query.filter_by(is_admin=False).all()
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
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('create_user'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('create_user'))
        
        password = generate_password()
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        
        if send_user_credentials(email, username, password):
            flash('User created successfully. Login credentials sent to email.', 'success')
        else:
            flash(f'User created. Password: {password} (Email sending failed)', 'warning')
        
        return redirect(url_for('admin_dashboard'))
    
    return render_template('create_user.html')

@app.route('/admin/create_exam', methods=['GET', 'POST'])
@login_required
def create_exam():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        exam = Exam(
            title=request.form.get('title'),
            description=request.form.get('description'),
            duration_minutes=int(request.form.get('duration', 60)),
            created_by=current_user.id
        )
        db.session.add(exam)
        db.session.commit()
        
        flash('Exam created successfully', 'success')
        return redirect(url_for('manage_questions', exam_id=exam.id))
    
    return render_template('create_exam.html')

@app.route('/admin/exam/<int:exam_id>/questions', methods=['GET', 'POST'])
@login_required
def manage_questions(exam_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    exam = Exam.query.get_or_404(exam_id)
    
    if request.method == 'POST':
        question = Question(
            exam_id=exam_id,
            question_text=request.form.get('question_text'),
            option_a=request.form.get('option_a'),
            option_b=request.form.get('option_b'),
            option_c=request.form.get('option_c'),
            option_d=request.form.get('option_d'),
            correct_answer=request.form.get('correct_answer'),
            marks=int(request.form.get('marks', 1))
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully', 'success')
        return redirect(url_for('manage_questions', exam_id=exam_id))
    
    questions = Question.query.filter_by(exam_id=exam_id).all()
    return render_template('manage_questions.html', exam=exam, questions=questions)

@app.route('/admin/assign_exam', methods=['GET', 'POST'])
@login_required
def assign_exam():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        exam_id = request.form.get('exam_id')
        start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')
        
        permission = ExamPermission(
            user_id=user_id,
            exam_id=exam_id,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(permission)
        db.session.commit()
        
        user = User.query.get(user_id)
        exam = Exam.query.get(exam_id)
        
        try:
            msg = Message('Exam Assignment Notification',
                          recipients=[user.email])
            msg.html = f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">New Exam Assigned</h2>
                <p>You have been assigned a new exam:</p>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                    <p><strong>Exam:</strong> {exam.title}</p>
                    <p><strong>Available from:</strong> {start_time.strftime('%Y-%m-%d %H:%M')}</p>
                    <p><strong>Available until:</strong> {end_time.strftime('%Y-%m-%d %H:%M')}</p>
                </div>
                <p style="margin-top: 20px;">Login to take the exam: <a href="http://localhost:5000/login">Exam Portal</a></p>
            </div>
            '''
            mail.send(msg)
            flash('Exam assigned successfully and notification sent', 'success')
        except:
            flash('Exam assigned successfully (email notification failed)', 'warning')
        
        return redirect(url_for('admin_dashboard'))
    
    users = User.query.filter_by(is_admin=False).all()
    exams = Exam.query.filter_by(created_by=current_user.id).all()
    return render_template('assign_exam.html', users=users, exams=exams)

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    permissions = ExamPermission.query.filter_by(user_id=current_user.id).all()
    available_exams = []
    completed_exams = []
    
    # Group permissions by exam_id to avoid duplicates
    exam_permissions = {}
    
    for perm in permissions:
        if perm.is_completed:
            completed_exams.append(perm)
        elif perm.start_time <= now <= perm.end_time:
            # Only show one active permission per exam
            if perm.exam_id not in exam_permissions:
                exam_permissions[perm.exam_id] = perm
    
    available_exams = list(exam_permissions.values())
    
    return render_template('user_dashboard.html', 
                         available_exams=available_exams,
                         completed_exams=completed_exams)

@app.route('/exam/<int:exam_id>/take')
@login_required
def take_exam(exam_id):
    if current_user.is_admin:
        flash('Admins cannot take exams', 'error')
        return redirect(url_for('admin_dashboard'))
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Find an active permission within the current time window
    permission = ExamPermission.query.filter(
        ExamPermission.user_id == current_user.id,
        ExamPermission.exam_id == exam_id,
        ExamPermission.is_completed == False,
        ExamPermission.start_time <= now,
        ExamPermission.end_time >= now
    ).first()
    
    if not permission:
        flash('This exam is not available at this time or you do not have permission', 'error')
        return redirect(url_for('user_dashboard'))
    
    exam = Exam.query.get_or_404(exam_id)
    questions = Question.query.filter_by(exam_id=exam_id).all()
    
    time_remaining = min(
        (permission.end_time - now).total_seconds(),
        exam.duration_minutes * 60
    )
    
    return render_template('take_exam.html', 
                         exam=exam, 
                         questions=questions,
                         time_remaining=int(time_remaining))

@app.route('/exam/<int:exam_id>/submit', methods=['POST'])
@login_required
def submit_exam(exam_id):
    if current_user.is_admin:
        return jsonify({'error': 'Admins cannot submit exams'}), 403
    
    permission = ExamPermission.query.filter_by(
        user_id=current_user.id,
        exam_id=exam_id,
        is_completed=False
    ).first()
    
    if not permission:
        return jsonify({'error': 'Invalid exam submission'}), 403
    
    exam = Exam.query.get_or_404(exam_id)
    questions = Question.query.filter_by(exam_id=exam_id).all()
    
    score = 0
    total_marks = 0
    answers = {}
    
    for question in questions:
        user_answer = request.form.get(f'question_{question.id}')
        answers[str(question.id)] = user_answer
        total_marks += question.marks
        
        if user_answer == question.correct_answer:
            score += question.marks
    
    percentage = (score / total_marks * 100) if total_marks > 0 else 0
    
    result = ExamResult(
        user_id=current_user.id,
        exam_id=exam_id,
        score=score,
        total_marks=total_marks,
        percentage=percentage,
        answers=str(answers)
    )
    db.session.add(result)
    
    permission.is_completed = True
    db.session.commit()
    
    admin = User.query.get(exam.created_by)
    if admin:
        send_exam_completion_notification(
            admin.email,
            current_user.username,
            exam.title,
            score,
            total_marks
        )
    
    flash(f'Exam submitted successfully! Your score: {score}/{total_marks} ({percentage:.2f}%)', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/admin/assignments')
@login_required
def view_assignments():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    # Get all assignments for exams created by current admin
    exams = Exam.query.filter_by(created_by=current_user.id).all()
    exam_ids = [exam.id for exam in exams]
    
    assignments = ExamPermission.query.filter(ExamPermission.exam_id.in_(exam_ids)).all()
    
    # Separate active and completed assignments
    active_assignments = []
    completed_assignments = []
    
    for assignment in assignments:
        if assignment.is_completed:
            completed_assignments.append(assignment)
        else:
            active_assignments.append(assignment)
    
    return render_template('manage_assignments.html', 
                         active_assignments=active_assignments,
                         completed_assignments=completed_assignments)

@app.route('/admin/assignment/<int:assignment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_assignment(assignment_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    assignment = ExamPermission.query.get_or_404(assignment_id)
    
    # Verify this assignment belongs to an exam created by current admin
    exam = Exam.query.get(assignment.exam_id)
    if exam.created_by != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        assignment.start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        assignment.end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')
        db.session.commit()
        flash('Assignment updated successfully', 'success')
        return redirect(url_for('view_assignments'))
    
    return render_template('edit_assignment.html', assignment=assignment)

@app.route('/admin/assignment/<int:assignment_id>/delete', methods=['POST'])
@login_required
def delete_assignment(assignment_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    assignment = ExamPermission.query.get_or_404(assignment_id)
    
    # Verify this assignment belongs to an exam created by current admin
    exam = Exam.query.get(assignment.exam_id)
    if exam.created_by != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    db.session.delete(assignment)
    db.session.commit()
    
    return jsonify({'message': 'Assignment deleted successfully'}), 200

@app.route('/admin/results')
@login_required
def view_results():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    exams = Exam.query.filter_by(created_by=current_user.id).all()
    exam_ids = [exam.id for exam in exams]
    results = ExamResult.query.filter(ExamResult.exam_id.in_(exam_ids)).all()
    
    return render_template('view_results.html', results=results)

@app.route('/create_test_users')
def create_test_users():
    with app.app_context():
        users_created = []
        
        # Create test student users
        test_users = [
            {'username': 'student1', 'email': 'student1@example.com', 'password': 'student123'},
            {'username': 'student2', 'email': 'student2@example.com', 'password': 'student456'},
            {'username': 'john', 'email': 'john@example.com', 'password': 'john123'},
            {'username': 'jane', 'email': 'jane@example.com', 'password': 'jane123'}
        ]
        
        for user_data in test_users:
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if not existing_user:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=generate_password_hash(user_data['password']),
                    is_admin=False
                )
                db.session.add(user)
                users_created.append(f"{user_data['username']} (password: {user_data['password']})")
        
        if users_created:
            db.session.commit()
            return jsonify({
                'message': 'Test users created successfully',
                'users': users_created
            }), 200
        else:
            return jsonify({'message': 'All test users already exist'}), 200

@app.route('/init_db')
def init_db():
    with app.app_context():
        db.create_all()
        
        admin = User.query.filter_by(username='admin').first()
        admin2 = User.query.filter_by(username='admin2').first()
        
        created_users = []
        
        if not admin:
            admin = User(
                username='admin',
                email='admin@examapp.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            created_users.append('admin (password: admin123)')
        
        if not admin2:
            admin2 = User(
                username='admin2',
                email='admin2@examapp.com',
                password_hash=generate_password_hash('admin456'),
                is_admin=True
            )
            db.session.add(admin2)
            created_users.append('admin2 (password: admin456)')
        
        if created_users:
            db.session.commit()
            return jsonify({'message': f'Database initialized. Admin users created: {", ".join(created_users)}'}), 200
        return jsonify({'message': 'Database already initialized'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5003)