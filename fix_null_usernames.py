#!/usr/bin/env python3
"""
Fix null usernames in MongoDB users collection.
This script finds users with null usernames and assigns them unique names.
"""

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import datetime
import uuid
import random
import os
import sys

# Connect to MongoDB
client = MongoClient(
    'mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=MrWlah',
    tls=True,
    tlsCertificateKeyFile='certs/X509-cert-5870665680541743449.pem',
    server_api=ServerApi('1')
)

db = client['benchai']
users_collection = db['users']

def fix_null_usernames():
    """Find and fix all users with null usernames"""
    print("Finding users with null usernames...")
    
    # Find all users with null or undefined username
    null_username_query = {'$or': [
        {'username': None},
        {'username': {'$exists': False}}
    ]}
    
    users_with_null = list(users_collection.find(null_username_query))
    
    if not users_with_null:
        print("No users found with null usernames. Nothing to fix.")
        return
    
    print(f"Found {len(users_with_null)} user(s) with null usernames.")
    
    # Fix each user
    for user in users_with_null:
        user_id = user.get('_id')
        name = user.get('name', 'Unknown')
        email = user.get('email', '')
        
        # Generate a unique username
        if email:
            # Try to use email as the basis for username
            username_base = email.split('@')[0].replace('.', '').lower()
        elif name and name != 'Unknown':
            # If no email, use name
            username_base = name.replace(' ', '').lower()
        else:
            # Last resort, generate a random username
            username_base = f"user_{uuid.uuid4().hex[:8]}"
        
        # Add a random number to ensure uniqueness
        username = f"{username_base}_{random.randint(1000, 9999)}"
        
        print(f"Assigning username '{username}' to user {name} (ID: {user_id})")
        
        # Update the user
        users_collection.update_one(
            {'_id': user_id},
            {'$set': {'username': username}}
        )
    
    print("\nUsername fix complete.")
    print("Verifying fix...")
    
    # Verify the fix worked
    remaining_null = users_collection.count_documents(null_username_query)
    if remaining_null == 0:
        print("✅ All users now have usernames!")
    else:
        print(f"⚠️ {remaining_null} user(s) still have null usernames. May need to run again.")

if __name__ == "__main__":
    try:
        fix_null_usernames()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 