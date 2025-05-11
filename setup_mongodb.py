#!/usr/bin/env python3
"""
MongoDB Setup Script for Mr. Wlah

This script helps set up the MongoDB connection and X.509 certificate.
It guides the user through the setup process and tests the connection.
"""

import os
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

def create_directory_if_not_exists(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
    return directory

def setup_certificate():
    """Set up the X.509 certificate."""
    cert_dir = create_directory_if_not_exists('certs')
    cert_path = os.path.join(cert_dir, 'X509-cert-5870665680541743449.pem')
    
    if os.path.exists(cert_path):
        print(f"Certificate already exists at: {cert_path}")
        return cert_path
    
    print("\n=== X.509 Certificate Setup ===")
    print("The MongoDB connection requires an X.509 certificate.")
    print(f"The certificate should be placed at: {cert_path}")
    
    cert_content = input("\nPaste the content of your X.509 certificate (or enter 'skip' to skip):\n")
    
    if cert_content.lower() == 'skip':
        print("Skipping certificate setup.")
        return None
    
    # Save certificate to file
    with open(cert_path, 'w') as f:
        f.write(cert_content)
    
    print(f"Certificate saved to: {cert_path}")
    return cert_path

def test_connection(cert_path):
    """Test the MongoDB connection."""
    # Load environment variables
    load_dotenv()
    
    # Get MongoDB connection settings
    mongo_uri = os.getenv('MONGODB_URI')
    mongo_db = os.getenv('MONGODB_DATABASE', 'mrwlah')
    
    if not mongo_uri:
        print("Error: MONGODB_URI not set in .env file")
        return False
    
    print("\n=== Testing MongoDB Connection ===")
    print(f"URI: {mongo_uri}")
    print(f"Database: {mongo_db}")
    print(f"Certificate: {cert_path}")
    
    try:
        # Set up MongoDB client with X.509 certificate
        client = MongoClient(
            mongo_uri,
            tls=True,
            tlsCertificateKeyFile=cert_path,
            server_api=ServerApi('1')
        )
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connection successful!")
        
        # Get database and list collections
        db = client[mongo_db]
        collections = db.list_collection_names()
        
        print(f"\nFound {len(collections)} collections in database '{mongo_db}':")
        for i, collection in enumerate(collections, 1):
            count = db[collection].count_documents({})
            print(f"  {i}. {collection}: {count} document(s)")
        
        return True
    
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

def update_env_file():
    """Update the .env file with MongoDB connection details."""
    env_path = '.env'
    
    if not os.path.exists(env_path):
        print(f"Error: {env_path} file not found")
        return False
    
    print("\n=== MongoDB Connection URI ===")
    print("Current MongoDB URI from .env file:")
    
    # Read current URI from .env file
    current_uri = None
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('MONGODB_URI='):
                current_uri = line.strip().split('=', 1)[1]
                print(f"  {current_uri}")
                break
    
    # Prompt for new URI
    new_uri = input("\nEnter new MongoDB URI (or press Enter to keep current):\n")
    
    if not new_uri:
        print("Keeping current MongoDB URI.")
        return True
    
    # Update .env file
    updated_content = []
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('MONGODB_URI='):
                updated_content.append(f'MONGODB_URI={new_uri}\n')
            else:
                updated_content.append(line)
    
    with open(env_path, 'w') as f:
        f.writelines(updated_content)
    
    print("Updated MongoDB URI in .env file.")
    return True

def main():
    """Main function."""
    print("=== MongoDB Setup for Mr. Wlah ===\n")
    
    # Step 1: Update .env file with MongoDB URI
    update_env_file()
    
    # Step 2: Set up X.509 certificate
    cert_path = setup_certificate()
    
    # Step 3: Test connection
    if cert_path and os.path.exists(cert_path):
        if test_connection(cert_path):
            print("\n✅ MongoDB setup completed successfully!")
        else:
            print("\n❌ MongoDB connection failed. Please check your settings and try again.")
    else:
        print("\n⚠️ Certificate not found. Cannot test connection.")
        print("Please place your X.509 certificate at certs/X509-cert-5870665680541743449.pem and run this script again.")

if __name__ == "__main__":
    main() 