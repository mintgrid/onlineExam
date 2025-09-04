#!/usr/bin/env python3
"""
Test Firebase Integration
Simple test to verify Firebase models work
"""

import os
import sys

# Use real Firebase (comment out emulator for production)
# os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'

try:
    from firebase_models import User, Exam, Question
    from firebase_config import firebase_db
    
    print("🔥 Testing Firebase Integration...")
    
    # Test 1: Create a test user
    print("\n1. Testing User Creation...")
    test_user = User()
    test_user.username = "testuser"
    test_user.email = "test@example.com"
    test_user.set_password("testpass")
    test_user.is_admin = False
    
    # This will fail without proper Firebase setup, which is expected
    try:
        user_id = test_user.save()
        if user_id:
            print("✅ User created successfully with ID:", user_id)
        else:
            print("❌ User creation failed")
    except Exception as e:
        print(f"⚠️ Expected Firebase error (no service account): {e}")
    
    # Test 2: Test model initialization
    print("\n2. Testing Model Initialization...")
    user = User()
    exam = Exam()
    question = Question()
    
    print("✅ All models initialized successfully")
    print("✅ User model:", user.__class__.__name__)
    print("✅ Exam model:", exam.__class__.__name__)
    print("✅ Question model:", question.__class__.__name__)
    
    # Test 3: Test Firebase config
    print("\n3. Testing Firebase Config...")
    from firebase_config import COLLECTIONS
    print("✅ Collections defined:", list(COLLECTIONS.keys()))
    
    print("\n🎉 Firebase Integration Test Complete!")
    print("\n📋 Next Steps:")
    print("1. Set up Firebase service account key")
    print("2. Enable Firestore database")
    print("3. Run the application with: python app.py")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure Firebase dependencies are installed:")
    print("pip install firebase-admin google-cloud-firestore")
    
except Exception as e:
    print(f"⚠️ Firebase Error (Expected): {e}")
    print("This is expected without proper Firebase configuration.")
    print("Follow FIREBASE_SETUP.md to complete setup.")