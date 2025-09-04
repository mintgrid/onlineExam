# Firebase Setup Guide

## 🔥 Firebase Migration Complete!

Your Online Exam Application has been successfully migrated from SQLite to **Firebase/Firestore** for persistent cloud storage.

## 📋 Firebase Configuration

Your Firebase project details:
```javascript
// Firebase Config
const firebaseConfig = {
  apiKey: "AIzaSyAjKS4No9kW4kQNUgFO8e4-VEZPyVK-Es4",
  authDomain: "onlineexam-f01cd.firebaseapp.com",
  projectId: "onlineexam-f01cd",
  storageBucket: "onlineexam-f01cd.firebasestorage.app",
  messagingSenderId: "1035809439592",
  appId: "1:1035809439592:web:549b343994e64f725360dd",
  measurementId: "G-ZL7ER12VC5"
};
```

## 🛠️ Setup Required

### 1. Get Firebase Service Account Key

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `onlineexam-f01cd`
3. Go to **Project Settings** → **Service Accounts**
4. Click **"Generate New Private Key"**
5. Download the JSON file

### 2. Configure Service Account

**Option A: For Local Development**
```bash
# Save the downloaded file as:
cp ~/Downloads/onlineexam-f01cd-firebase-adminsdk-xxxxx.json firebase-service-account.json
```

**Option B: For Production (Environment Variable)**
```bash
# Set environment variable:
export FIREBASE_SERVICE_ACCOUNT='{"type":"service_account","project_id":"onlineexam-f01cd",...}'
```

### 3. Enable Firestore Database

1. In Firebase Console, go to **Firestore Database**
2. Click **"Create Database"**
3. Choose **"Start in test mode"** (for now)
4. Select your preferred location (e.g., `us-central1`)

## 🗃️ Firestore Collections Structure

The application creates these collections:

```
📂 users/
  └── {userId}
      ├── username: string
      ├── email: string
      ├── password_hash: string
      ├── is_admin: boolean
      └── created_at: timestamp

📂 exams/
  └── {examId}
      ├── title: string
      ├── description: string
      ├── duration_minutes: number
      ├── created_by: string (userId)
      └── created_at: timestamp

📂 questions/
  └── {questionId}
      ├── exam_id: string
      ├── question_text: string
      ├── option_a: string
      ├── option_b: string
      ├── option_c: string
      ├── option_d: string
      ├── correct_answer: string
      └── marks: number

📂 examPermissions/
  └── {permissionId}
      ├── user_id: string
      ├── exam_id: string
      ├── start_time: timestamp
      ├── end_time: timestamp
      └── is_completed: boolean

📂 examResults/
  └── {resultId}
      ├── user_id: string
      ├── exam_id: string
      ├── score: number
      ├── total_marks: number
      ├── percentage: number
      ├── answers: object
      └── submitted_at: timestamp

📂 settings/
  └── {settingKey}
      ├── key: string
      ├── value: string
      └── updated_at: timestamp
```

## 🚀 Running the Application

### Local Development
```bash
# Make sure Firebase service account key is in place
python app.py
```

### Production Deployment
```bash
# Set environment variable for service account
export FIREBASE_SERVICE_ACCOUNT='{"your":"service-account-json"}'

# Deploy to Cloud Run/App Engine
gcloud run deploy --source .
```

## ⚡ Key Benefits of Firebase Migration

### ✅ **Persistent Data Storage**
- No more data loss on container restarts
- Cloud-based storage with automatic backups

### ✅ **Real-time Capabilities** 
- Live updates across admin/student interfaces
- Real-time exam monitoring

### ✅ **Automatic Scaling**
- Handles traffic spikes during exam periods
- Pay-only-for-what-you-use pricing

### ✅ **Built-in Security**
- Firebase security rules
- Automatic SSL/TLS encryption
- Data validation at database level

### ✅ **Global Distribution**
- Fast access worldwide
- Multiple data center redundancy

## 🔒 Security Rules (Firestore)

Update your Firestore security rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only access their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      // Admins can read all users
      allow read: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.is_admin == true;
    }
    
    // Exams - admins can CRUD, students can read assigned exams
    match /exams/{examId} {
      allow read, write: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.is_admin == true;
      allow read: if request.auth != null;
    }
    
    // Questions - same as exams
    match /questions/{questionId} {
      allow read, write: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.is_admin == true;
      allow read: if request.auth != null;
    }
    
    // Exam permissions - users can read their own
    match /examPermissions/{permissionId} {
      allow read, write: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.is_admin == true;
      allow read: if request.auth != null && resource.data.user_id == request.auth.uid;
    }
    
    // Exam results - users can read their own, admins can read all
    match /examResults/{resultId} {
      allow read, write: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.is_admin == true;
      allow read, write: if request.auth != null && resource.data.user_id == request.auth.uid;
    }
    
    // Settings - admin only
    match /settings/{settingId} {
      allow read, write: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.is_admin == true;
    }
  }
}
```

## 💰 Expected Costs

### Firebase Pricing (Pay-as-you-use):
- **Small school (100-500 users):** ~$0-10/month
- **Medium institution (500-2000 users):** ~$10-30/month  
- **Large organization (2000+ users):** ~$30-100/month

### Free Tier Includes:
- 50,000 reads/day
- 20,000 writes/day
- 20,000 deletes/day
- 1GB storage

## 🎯 Next Steps

1. ✅ **Set up Firebase service account key**
2. ✅ **Enable Firestore database**  
3. ✅ **Test the application locally**
4. ✅ **Configure Firestore security rules**
5. ✅ **Deploy to production**

## 🆘 Troubleshooting

### Common Issues:

**1. "Firebase not initialized"**
- Ensure `firebase-service-account.json` exists
- Or set `FIREBASE_SERVICE_ACCOUNT` environment variable

**2. "Permission denied"**
- Check Firestore security rules
- Ensure service account has proper permissions

**3. "Project not found"**
- Verify project ID in configuration
- Check Firebase project is active

Your application is now ready for **persistent, scalable, cloud-based storage**! 🎉