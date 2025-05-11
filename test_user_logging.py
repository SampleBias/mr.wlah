#!/usr/bin/env python3
"""
Test User Logging for Mr. Wlah

This script tests adding user log entries to the benchai database.
"""

import os
import sys
import datetime
import random
from pymongo import MongoClient
from pymongo.server_api import ServerApi

def test_user_logging():
    """Test user activity logging functionality."""
    # Set the MongoDB connection URI for BenchAI
    uri = "mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=MrWlah"
    
    # Path to certificate file
    cert_path = os.path.join('certs', 'X509-cert-5870665680541743449.pem')
    
    # Check if certificate exists
    if not os.path.exists(cert_path):
        print(f"Error: X.509 certificate not found at {cert_path}")
        return False
    
    try:
        print("Connecting to BenchAI MongoDB...")
        
        # Set up MongoDB client with X.509 certificate
        client = MongoClient(
            uri,
            tls=True,
            tlsCertificateKeyFile=cert_path,
            server_api=ServerApi('1')
        )
        
        # Test connection with ping
        client.admin.command('ping')
        print("✅ Connection successful!")
        
        # Connect to the benchai database
        db = client['benchai']
        
        # Check for users collection
        if 'users' not in db.list_collection_names():
            print("❌ Users collection not found in benchai database")
            return False
            
        # Check for logs collection
        if 'logs' not in db.list_collection_names():
            print("❌ Logs collection not found in benchai database")
            return False
        
        # Find a user or create a test user
        test_user = db.users.find_one({"auth0Id": "sample-user-id"})
        
        if not test_user:
            print("Creating a test user...")
            test_user_id = db.users.insert_one({
                "auth0Id": "sample-user-id",
                "email": "test@example.com",
                "name": "Test User",
                "createdAt": datetime.datetime.now(),
                "lastLogin": datetime.datetime.now()
            }).inserted_id
            test_user = db.users.find_one({"_id": test_user_id})
            print("✅ Test user created")
        else:
            print(f"Using existing user: {test_user.get('name', 'Unknown')}")
        
        # Log some user activities
        activities = [
            "LOGIN",
            "TRANSFORM_TEXT",
            "DOWNLOAD_RESULT",
            "COPY_RESULT",
            "CHANGE_TONE",
            "UPLOAD_FILE",
            "LOGOUT"
        ]
        
        # Generate random user activities
        num_activities = 5
        print(f"\nAdding {num_activities} random user activities...")
        
        for i in range(num_activities):
            activity = random.choice(activities)
            
            # Create details based on activity type
            details = None
            if activity == "TRANSFORM_TEXT":
                details = {
                    "tone": random.choice(["casual", "professional", "scientific", "educational"]),
                    "text_length": random.randint(50, 500),
                    "preserve_font": random.choice([True, False])
                }
            elif activity == "UPLOAD_FILE":
                details = {
                    "file_type": random.choice(["txt", "pdf", "docx"]),
                    "file_size": random.randint(1024, 10240)
                }
            
            # Log the activity
            log_entry = {
                "timestamp": datetime.datetime.now(),
                "userId": test_user.get("auth0Id"),
                "action": activity,
                "level": "INFO",
                "source": "test_script"
            }
            
            if details:
                log_entry["details"] = details
            
            db.logs.insert_one(log_entry)
            
            if details:
                detail_str = f" - {details}"
            else:
                detail_str = ""
                
            print(f"  {i+1}. Logged: {activity}{detail_str}")
        
        # Get the latest logs for this user
        print("\nRetrieving latest logs for the user...")
        latest_logs = list(db.logs.find(
            {"userId": test_user.get("auth0Id")}
        ).sort("timestamp", -1).limit(10))
        
        print(f"Found {len(latest_logs)} log entries:")
        for i, log in enumerate(latest_logs, 1):
            timestamp = log.get('timestamp').strftime('%Y-%m-%d %H:%M:%S')
            action = log.get('action', 'Unknown')
            
            print(f"  {i}. [{timestamp}] {action}")
        
        print("\n✅ User logging test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing user logging: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_user_logging()
    sys.exit(0 if success else 1) 