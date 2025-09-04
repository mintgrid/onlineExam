#!/usr/bin/env python3
"""
Initialize the Settings table in the database
"""

from app import app, db, Settings

if __name__ == '__main__':
    with app.app_context():
        # Create the Settings table
        db.create_all()
        print("Settings table created successfully!")
        
        # Verify the table exists by checking existing settings
        existing_settings = Settings.query.all()
        print(f"Found {len(existing_settings)} existing settings in the database")