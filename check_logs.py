#!/usr/bin/env python3
"""
Check Logs in BenchAI Database

This script checks and displays the logs collection in the BenchAI database.
"""

import os
import sys
import datetime
from pymongo import MongoClient
from pymongo.server_api import ServerApi

def check_logs():
    """Check and display logs from the benchai database."""
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
        
        # Check if the logs collection exists
        if 'logs' not in db.list_collection_names():
            print("❌ Logs collection not found in benchai database")
            return False
        
        # Get logs
        logs = list(db.logs.find().sort('timestamp', -1))
        
        if not logs:
            print("No logs found in the logs collection")
            
            # Add a test log entry
            print("Adding a test log entry...")
            db.logs.insert_one({
                "timestamp": datetime.datetime.now(),
                "level": "INFO",
                "message": "Test log entry",
                "source": "check_logs.py"
            })
            print("✅ Test log entry added")
            
            # Get logs again
            logs = list(db.logs.find().sort('timestamp', -1))
        
        # Display logs
        print(f"\nFound {len(logs)} log entries:")
        
        for i, log in enumerate(logs, 1):
            timestamp = log.get('timestamp').strftime('%Y-%m-%d %H:%M:%S') if 'timestamp' in log else 'Unknown'
            level = log.get('level', 'UNKNOWN')
            message = log.get('message', 'No message')
            source = log.get('source', 'Unknown')
            user_id = log.get('userId', 'None')
            
            print(f"{i}. [{timestamp}] {level} - {message}")
            print(f"   Source: {source}, User ID: {user_id}")
            
            if i < len(logs):
                print("")  # Add empty line between logs
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking logs: {str(e)}")
        return False

if __name__ == "__main__":
    success = check_logs()
    sys.exit(0 if success else 1) 