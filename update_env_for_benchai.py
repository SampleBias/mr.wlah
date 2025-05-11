#!/usr/bin/env python3
"""
Update .env File for BenchAI MongoDB

This script updates the .env file to use the BenchAI MongoDB database.
"""

import os
import re

def update_env_file():
    """Update the .env file with BenchAI MongoDB settings."""
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print(f"Error: {env_file} not found")
        return False
    
    # Read the current .env file
    with open(env_file, 'r') as f:
        env_content = f.readlines()
    
    # The new MongoDB URI and database name
    new_uri = "mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=MrWlah"
    new_db = "benchai"
    
    # Track if we found and updated the settings
    uri_updated = False
    db_updated = False
    
    # Update the MongoDB settings
    updated_content = []
    for line in env_content:
        if line.startswith('MONGODB_URI='):
            updated_content.append(f'MONGODB_URI={new_uri}\n')
            uri_updated = True
        elif line.startswith('MONGODB_DATABASE='):
            updated_content.append(f'MONGODB_DATABASE={new_db}\n')
            db_updated = True
        else:
            updated_content.append(line)
    
    # If we didn't find the settings, add them
    if not uri_updated:
        updated_content.append(f'MONGODB_URI={new_uri}\n')
    if not db_updated:
        updated_content.append(f'MONGODB_DATABASE={new_db}\n')
    
    # Write the updated content back to the .env file
    with open(env_file, 'w') as f:
        f.writelines(updated_content)
    
    print(f"✅ Updated {env_file} with BenchAI MongoDB settings:")
    print(f"   MONGODB_URI={new_uri}")
    print(f"   MONGODB_DATABASE={new_db}")
    
    return True

if __name__ == "__main__":
    update_env_file() 