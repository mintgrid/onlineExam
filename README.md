# Online Exam Portal

A modern, responsive online examination system built with Flask and SQLite, featuring Material Design-inspired UI.

## Features

### Admin Features
- Create and manage user accounts
- Create exams with multiple-choice questions
- Assign exams to users with time restrictions
- View detailed exam results and analytics
- Automatic email notifications

### User Features
- Secure login system
- Take assigned exams within specified time windows
- Real-time timer during exams
- Instant result calculation
- View exam history and scores

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Email Settings

Copy the `.env.example` file to `.env` and update with your email credentials:

```bash
cp .env.example .env
```

Edit `.env` with your email configuration:
- For Gmail, you'll need to use an app-specific password
- Enable 2-factor authentication in your Gmail account
- Generate an app password from Google Account settings

### 3. Initialize the Database

Start the Flask application:

```bash
python app.py
```

Go directly to the initialization URL:
```
http://localhost:5003/init_db
```

This creates the database and an admin account:
- Username: `admin`
- Password: `admin123`

### 4. Access the Application

1. Go to `http://localhost:5003`
2. Click "Login to Portal"
3. Use the admin credentials to log in

## Usage Guide

### Admin Workflow

1. **Login** with admin credentials
2. **Create Users**: Admin Dashboard → Create User
3. **Create Exams**: Admin Dashboard → Create Exam
4. **Add Questions**: After creating an exam, add multiple-choice questions
5. **Assign Exams**: Admin Dashboard → Assign Exam (select user, exam, and time window)
6. **View Results**: Admin Dashboard → View Results

### User Workflow

1. **Receive Credentials** via email after admin creates account
2. **Login** with provided credentials
3. **View Available Exams** on the dashboard
4. **Take Exam** within the assigned time window
5. **Submit Exam** and view immediate results
6. **View History** of completed exams on dashboard

## Email Notifications

The system sends automatic emails for:
- New user account creation (with login credentials)
- Exam assignment notifications to users
- Exam completion notifications to admin

## UI Features

- **Material Design** inspired interface
- **Responsive Design** works on desktop, tablet, and mobile
- **Glass Morphism** effects for modern look
- **Smooth Animations** and transitions
- **Real-time Timer** during exams
- **Color-coded** status indicators

## Security Features

- Password hashing using Werkzeug
- Session-based authentication
- CSRF protection
- Time-restricted exam access
- Automatic exam submission on timeout

## Database Schema

- **Users**: Stores admin and student accounts
- **Exams**: Exam details and settings
- **Questions**: Multiple-choice questions for each exam
- **ExamPermissions**: Time-based access control
- **ExamResults**: Stores submission data and scores

## Troubleshooting

### Email not sending?
- Check your `.env` file configuration
- For Gmail, ensure you're using an app-specific password
- Verify your internet connection
- Check spam folder for emails

### Database issues?
- Delete `exam_system.db` and reinitialize
- Ensure write permissions in the project directory

### Login problems?
- Clear browser cookies
- Restart the Flask application
- Check if the database is initialized

## Development

To run in debug mode:
```bash
python app.py
```

The application will be available at `http://localhost:5003`

## License

This project is for educational purposes.