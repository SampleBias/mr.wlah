#!/usr/bin/env python3
"""
Database Initialization Script for Mr. Wlah

This script initializes the MongoDB database and necessary collections for Mr. Wlah.
It sets up indexes, default values, and prepares the database for use.
"""

import os
import sys
import datetime
import argparse
import re
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.server_api import ServerApi

# Load environment variables
load_dotenv()

def initialize_database(verbose=False, force=False):
    """Initialize the MongoDB database and collections."""
    # MongoDB connection settings
    mongo_uri = os.getenv('MONGODB_URI')
    mongo_db = os.getenv('MONGODB_DATABASE', 'mrwlah')
    
    if not mongo_uri:
        print("Error: MONGODB_URI not set in .env file")
        return False
    
    # Check if X.509 certificate exists
    cert_path = os.path.join('certs', 'X509-cert-5870665680541743449.pem')
    has_certificate = os.path.exists(cert_path)
    
    try:
        # Connect to MongoDB with X.509 authentication
        if has_certificate:
            if verbose:
                print(f"Using X.509 certificate at {cert_path}")
            
            # Make sure the URI is in the correct format for X.509 authentication
            if 'authMechanism=MONGODB-X509' not in mongo_uri:
                # Replace or add authMechanism parameter
                if '?' in mongo_uri:
                    mongo_uri = re.sub(r'authMechanism=[^&]*', '', mongo_uri)
                    if mongo_uri.endswith('&'):
                        mongo_uri += 'authMechanism=MONGODB-X509'
                    else:
                        mongo_uri += '&authMechanism=MONGODB-X509'
                else:
                    mongo_uri += '?authMechanism=MONGODB-X509'
            
            # Set up MongoDB client with X.509 certificate
            mongo_client = MongoClient(
                mongo_uri,
                tls=True,
                tlsCertificateKeyFile=cert_path,
                server_api=ServerApi('1')
            )
        else:
            # Regular connection without X.509
            mongo_client = MongoClient(mongo_uri, server_api=ServerApi('1'))
        
        # Test connection
        mongo_client.admin.command('ping')
        if verbose:
            print("MongoDB connection successful")
        
        # Get database
        db = mongo_client[mongo_db]
        
        # Check if database already initialized
        if db.list_collection_names() and not force:
            print(f"Database '{mongo_db}' already contains collections. Use --force to reinitialize.")
            return True
        
        # Create collections
        if verbose:
            print(f"Creating collections in database '{mongo_db}'")
        
        # Create users collection
        users = db.users
        users.create_index([("auth0Id", ASCENDING)], unique=True)
        users.create_index([("email", ASCENDING)])
        users.create_index([("name", TEXT)])
        users.create_index([("lastLogin", DESCENDING)])
        if verbose:
            print("Created 'users' collection with indexes")
        
        # Create transformations collection
        transformations = db.transformations
        transformations.create_index([("userId", ASCENDING)])
        transformations.create_index([("createdAt", DESCENDING)])
        transformations.create_index([("tone", ASCENDING)])
        if verbose:
            print("Created 'transformations' collection with indexes")
        
        # Create API usage collection
        api_usage = db.apiUsage
        api_usage.create_index([("userId", ASCENDING)])
        api_usage.create_index([("date", DESCENDING)])
        if verbose:
            print("Created 'apiUsage' collection with indexes")
        
        # Create logs collection
        logs = db.logs
        logs.create_index([("timestamp", DESCENDING)])
        logs.create_index([("level", ASCENDING)])
        logs.create_index([("userId", ASCENDING)])
        if verbose:
            print("Created 'logs' collection with indexes")
        
        # Insert initialization record
        db.system.insert_one({
            "name": "Mr. Wlah",
            "initialized": datetime.datetime.now(),
            "version": "1.0.0"
        })
        
        print(f"Successfully initialized database '{mongo_db}'")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False


def add_system_log(message, level="INFO"):
    """Add a system log entry to the database."""
    try:
        # MongoDB connection settings
        mongo_uri = os.getenv('MONGODB_URI')
        mongo_db = os.getenv('MONGODB_DATABASE', 'mrwlah')
        
        if not mongo_uri:
            print(f"System Log ({level}): {message}")
            return False
        
        # Check if X.509 certificate exists
        cert_path = os.path.join('certs', 'X509-cert-5870665680541743449.pem')
        has_certificate = os.path.exists(cert_path)
        
        # Connect to MongoDB with X.509 authentication
        if has_certificate:
            # Make sure the URI is in the correct format for X.509 authentication
            if 'authMechanism=MONGODB-X509' not in mongo_uri:
                # Replace or add authMechanism parameter
                if '?' in mongo_uri:
                    mongo_uri = re.sub(r'authMechanism=[^&]*', '', mongo_uri)
                    if mongo_uri.endswith('&'):
                        mongo_uri += 'authMechanism=MONGODB-X509'
                    else:
                        mongo_uri += '&authMechanism=MONGODB-X509'
                else:
                    mongo_uri += '?authMechanism=MONGODB-X509'
            
            # Set up MongoDB client with X.509 certificate
            mongo_client = MongoClient(
                mongo_uri,
                tls=True,
                tlsCertificateKeyFile=cert_path,
                server_api=ServerApi('1')
            )
        else:
            # Regular connection without X.509
            mongo_client = MongoClient(mongo_uri, server_api=ServerApi('1'))
        
        db = mongo_client[mongo_db]
        
        # Add log entry
        db.logs.insert_one({
            "timestamp": datetime.datetime.now(),
            "level": level,
            "message": message,
            "source": "system"
        })
        
        # Print log message
        print(f"System Log ({level}): {message}")
        return True
        
    except Exception as e:
        print(f"Error adding system log: {str(e)}")
        print(f"Log message was: {level} - {message}")
        return False


def log_user_activity(user_id, action, details=None):
    """Log user activity to the database."""
    try:
        # MongoDB connection settings
        mongo_uri = os.getenv('MONGODB_URI')
        mongo_db = os.getenv('MONGODB_DATABASE', 'mrwlah')
        
        if not mongo_uri:
            print(f"User Activity: {user_id} - {action}")
            return False

        # Check if X.509 certificate exists
        cert_path = os.path.join('certs', 'X509-cert-5870665680541743449.pem')
        has_certificate = os.path.exists(cert_path)
        
        # Connect to MongoDB with X.509 authentication
        if has_certificate:
            # Make sure the URI is in the correct format for X.509 authentication
            if 'authMechanism=MONGODB-X509' not in mongo_uri:
                # Replace or add authMechanism parameter
                if '?' in mongo_uri:
                    mongo_uri = re.sub(r'authMechanism=[^&]*', '', mongo_uri)
                    if mongo_uri.endswith('&'):
                        mongo_uri += 'authMechanism=MONGODB-X509'
                    else:
                        mongo_uri += '&authMechanism=MONGODB-X509'
                else:
                    mongo_uri += '?authMechanism=MONGODB-X509'
            
            # Set up MongoDB client with X.509 certificate
            mongo_client = MongoClient(
                mongo_uri,
                tls=True,
                tlsCertificateKeyFile=cert_path,
                server_api=ServerApi('1')
            )
        else:
            # Regular connection without X.509
            mongo_client = MongoClient(mongo_uri, server_api=ServerApi('1'))
        
        db = mongo_client[mongo_db]
        
        # Add log entry
        log_entry = {
            "timestamp": datetime.datetime.now(),
            "userId": user_id,
            "action": action,
            "level": "INFO"
        }
        
        if details:
            log_entry["details"] = details
        
        db.logs.insert_one(log_entry)
        
        # Print log message
        print(f"User Activity: {user_id} - {action}")
        return True
        
    except Exception as e:
        print(f"Error logging user activity: {str(e)}")
        print(f"Activity was: {user_id} - {action}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize Mr. Wlah MongoDB database")
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--force', '-f', action='store_true', help='Force reinitialization')
    args = parser.parse_args()
    
    success = initialize_database(verbose=args.verbose, force=args.force)
    
    if success:
        add_system_log("Database initialization completed successfully")
    else:
        add_system_log("Database initialization failed", level="ERROR")
    
    sys.exit(0 if success else 1) 