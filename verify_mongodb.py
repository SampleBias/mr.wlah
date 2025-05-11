#!/usr/bin/env python3
"""
Verify MongoDB Connection for Mr. Wlah

A simple script to verify the MongoDB connection using the
current .env settings and certificate.
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

def main():
    """Verify MongoDB connection."""
    # Load environment variables
    load_dotenv()
    
    # Get MongoDB connection settings
    mongo_uri = os.getenv('MONGODB_URI')
    mongo_db = os.getenv('MONGODB_DATABASE', 'mrwlah')
    
    if not mongo_uri:
        print("Error: MONGODB_URI not set in .env file")
        return 1
    
    # Check if X.509 certificate exists
    cert_path = os.path.join('certs', 'X509-cert-5870665680541743449.pem')
    
    if not os.path.exists(cert_path):
        print(f"Error: X.509 certificate not found at {cert_path}")
        return 1
    
    print(f"MongoDB URI: {mongo_uri}")
    print(f"Database: {mongo_db}")
    print(f"Certificate: {cert_path}")
    
    try:
        print("\nConnecting to MongoDB...")
        
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
        
        # Get database
        db = client[mongo_db]
        
        # Count collections
        collections = db.list_collection_names()
        print(f"\nDatabase '{mongo_db}' has {len(collections)} collections:")
        
        # Display collection info
        for collection in collections:
            count = db[collection].count_documents({})
            print(f"  - {collection}: {count} documents")
        
        return 0
    
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 