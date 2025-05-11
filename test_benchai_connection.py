#!/usr/bin/env python3
"""
Test BenchAI MongoDB Connection

This script tests the connection to the BenchAI MongoDB database using
the provided connection string and X.509 certificate.
"""

import os
import sys
from pymongo import MongoClient
from pymongo.server_api import ServerApi

def main():
    """Test connection to BenchAI MongoDB."""
    # Set the MongoDB connection URI for BenchAI
    uri = "mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=BenchAI"
    
    # Check if certificate directory exists and create it if needed
    cert_dir = 'certs'
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
        print(f"Created directory: {cert_dir}")
    
    # Path to certificate file
    cert_path = os.path.join(cert_dir, 'X509-cert-5870665680541743449.pem')
    
    # Check if certificate exists
    if not os.path.exists(cert_path):
        print(f"Error: X.509 certificate not found at {cert_path}")
        print("Please create this file with your certificate contents first.")
        return 1
    
    try:
        print(f"Connecting to BenchAI MongoDB...")
        print(f"URI: {uri}")
        print(f"Certificate: {cert_path}")
        
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
        
        # Get databases list
        database_names = client.list_database_names()
        print(f"\nAvailable databases: {', '.join(database_names)}")
        
        # Connect to the BenchAI database
        db = client['BenchAI']
        
        # List collections in the database
        collections = db.list_collection_names()
        if collections:
            print(f"\nCollections in BenchAI database: {len(collections)}")
            for i, collection_name in enumerate(collections, 1):
                count = db[collection_name].count_documents({})
                print(f"  {i}. {collection_name}: {count} document(s)")
        else:
            print("\nNo collections found in BenchAI database.")
        
        # Also try testDB as mentioned in the example
        test_db = client['testDB']
        test_collections = test_db.list_collection_names()
        if test_collections:
            print(f"\nCollections in testDB: {len(test_collections)}")
            for i, collection_name in enumerate(test_collections, 1):
                count = test_db[collection_name].count_documents({})
                print(f"  {i}. {collection_name}: {count} document(s)")
                
                # If the collection is testCol as in the example, show specific count
                if collection_name == 'testCol':
                    print(f"    Document count in testCol: {count}")
        else:
            print("\nNo collections found in testDB.")
            
        return 0
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Verify that your X.509 certificate is valid")
        print("2. Ensure your IP address is whitelisted in MongoDB Atlas")
        print("3. Check that the certificate has the correct permissions")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 