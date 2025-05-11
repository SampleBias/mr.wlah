#!/usr/bin/env python3
"""
Test MongoDB Connection Script for Mr. Wlah

This script tests the connection to MongoDB using the specified connection details
and X.509 certificate authentication.
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test connection to MongoDB database."""
    print("Testing MongoDB Connection...")
    
    # Get MongoDB connection settings from environment variables
    mongo_uri = os.getenv('MONGODB_URI')
    mongo_db = os.getenv('MONGODB_DATABASE', 'mrwlah')
    
    if not mongo_uri:
        print("Error: MONGODB_URI not set in .env file")
        return False
    
    # Check if X.509 certificate exists
    cert_path = os.path.join('certs', 'X509-cert-5870665680541743449.pem')
    has_certificate = os.path.exists(cert_path)
    
    if not has_certificate:
        print(f"Error: X.509 certificate not found at {cert_path}")
        print("Please ensure you have placed the certificate file in the certs directory.")
        return False
    
    try:
        print(f"Connecting to: {mongo_uri}")
        print(f"Using certificate: {cert_path}")
        
        # Set up MongoDB client with X.509 certificate
        client = MongoClient(
            mongo_uri,
            tls=True,
            tlsCertificateKeyFile=cert_path,
            server_api=ServerApi('1')
        )
        
        # Test connection with ping
        client.admin.command('ping')
        print("✅ Connection successful!")
        
        # Get database
        db = client[mongo_db]
        
        # List collections
        collections = db.list_collection_names()
        print(f"\nDatabase: {mongo_db}")
        print(f"Collections: {len(collections)}")
        
        for i, collection in enumerate(collections, 1):
            count = db[collection].count_documents({})
            print(f"  {i}. {collection}: {count} document(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        
        # Provide troubleshooting tips
        print("\nTroubleshooting tips:")
        print("1. Check that your MongoDB URI is correct in the .env file")
        print("2. Verify that your X.509 certificate is valid and has the correct permissions")
        print("3. Ensure your IP address is whitelisted in MongoDB Atlas")
        print("4. Check that the authentication mechanism (MONGODB-X509) is supported by your cluster")
        
        return False


if __name__ == "__main__":
    success = test_mongodb_connection()
    sys.exit(0 if success else 1) 