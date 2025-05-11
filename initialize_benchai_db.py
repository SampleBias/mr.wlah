#!/usr/bin/env python3
"""
Initialize BenchAI MongoDB Collections for Mr. Wlah

This script initializes the required collections for Mr. Wlah in the BenchAI
MongoDB database, including users, logs, transformations, and API usage tracking.
"""

import os
import sys
import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.server_api import ServerApi

def initialize_benchai_database():
    """Initialize collections in the BenchAI database for Mr. Wlah."""
    # Set the MongoDB connection URI for BenchAI
    uri = "mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=BenchAI"
    
    # Path to certificate file
    cert_path = os.path.join('certs', 'X509-cert-5870665680541743449.pem')
    
    # Check if certificate exists
    if not os.path.exists(cert_path):
        print(f"Error: X.509 certificate not found at {cert_path}")
        return False
    
    try:
        print(f"Connecting to BenchAI MongoDB...")
        
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
        
        # Use the benchai database
        db = client['benchai']
        
        # Get current collections
        existing_collections = db.list_collection_names()
        print(f"\nExisting collections: {existing_collections if existing_collections else 'None'}")
        
        # Create users collection if it doesn't exist
        if 'users' not in existing_collections:
            print("\nCreating 'users' collection...")
            users = db.users
            users.create_index([("auth0Id", ASCENDING)], unique=True)
            users.create_index([("email", ASCENDING)])
            users.create_index([("name", TEXT)])
            users.create_index([("lastLogin", DESCENDING)])
            print("✅ Created 'users' collection with indexes")
        else:
            print("\n'users' collection already exists")
        
        # Create logs collection if it doesn't exist
        if 'logs' not in existing_collections:
            print("Creating 'logs' collection...")
            logs = db.logs
            logs.create_index([("timestamp", DESCENDING)])
            logs.create_index([("level", ASCENDING)])
            logs.create_index([("userId", ASCENDING)])
            logs.create_index([("source", ASCENDING)])
            print("✅ Created 'logs' collection with indexes")
            
            # Add initial system log entry
            logs.insert_one({
                "timestamp": datetime.datetime.now(),
                "level": "INFO",
                "message": "Mr. Wlah logs collection initialized",
                "source": "system"
            })
            print("✅ Added initial log entry")
        else:
            print("'logs' collection already exists")
        
        # Create transformations collection if it doesn't exist
        if 'transformations' not in existing_collections:
            print("Creating 'transformations' collection...")
            transformations = db.transformations
            transformations.create_index([("userId", ASCENDING)])
            transformations.create_index([("createdAt", DESCENDING)])
            transformations.create_index([("tone", ASCENDING)])
            print("✅ Created 'transformations' collection with indexes")
        else:
            print("'transformations' collection already exists")
        
        # Create apiUsage collection if it doesn't exist
        if 'apiUsage' not in existing_collections:
            print("Creating 'apiUsage' collection...")
            api_usage = db.apiUsage
            api_usage.create_index([("userId", ASCENDING)])
            api_usage.create_index([("date", DESCENDING)])
            print("✅ Created 'apiUsage' collection with indexes")
        else:
            print("'apiUsage' collection already exists")
        
        # Insert system information
        if 'system' not in existing_collections:
            print("Creating 'system' collection...")
            db.system.insert_one({
                "name": "Mr. Wlah",
                "initialized": datetime.datetime.now(),
                "version": "1.0.0"
            })
            print("✅ Created 'system' collection with initial record")
        else:
            print("'system' collection already exists")
        
        # Add a sample user if the users collection is empty
        if 'users' in existing_collections and db.users.count_documents({}) == 0:
            print("\nAdding a sample user record...")
            db.users.insert_one({
                "auth0Id": "sample-user-id",
                "email": "sample@example.com",
                "name": "Sample User",
                "createdAt": datetime.datetime.now(),
                "lastLogin": datetime.datetime.now(),
                "usageCount": 0,
                "preferences": {
                    "defaultTone": "casual",
                    "saveHistory": True
                }
            })
            print("✅ Added sample user record")
        
        # Add a sample log entry for the user
        if 'logs' in existing_collections:
            print("Adding a sample user log entry...")
            db.logs.insert_one({
                "timestamp": datetime.datetime.now(),
                "level": "INFO",
                "userId": "sample-user-id",
                "message": "User logged in",
                "source": "auth"
            })
            print("✅ Added sample user log entry")
        
        # Display all collections after initialization
        final_collections = db.list_collection_names()
        print(f"\nFinal collections in database: {final_collections}")
        
        print("\n✅ Database initialization complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    success = initialize_benchai_database()
    sys.exit(0 if success else 1) 