from pymongo import MongoClient
from pymongo.server_api import ServerApi
import datetime

# Connect to MongoDB
client = MongoClient(
    'mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=MrWlah',
    tls=True,
    tlsCertificateKeyFile='certs/X509-cert-5870665680541743449.pem',
    server_api=ServerApi('1')
)

db = client['benchai']
users = db.users

# Find the first user
user = users.find_one({})
if user:
    print("Found user:", user)
    
    # Update the user to add user_id field if not present
    if 'user_id' not in user and 'auth0Id' in user:
        users.update_one(
            {'_id': user['_id']},
            {'$set': {'user_id': user['auth0Id']}}
        )
        print(f"Updated user {user['_id']} to add user_id field")
    
    # Verify the update
    updated_user = users.find_one({'_id': user['_id']})
    print("\nUpdated user data:")
    print(f"_id: {updated_user['_id']}")
    print(f"auth0Id: {updated_user.get('auth0Id', 'N/A')}")
    print(f"user_id: {updated_user.get('user_id', 'N/A')}")
    print(f"email: {updated_user.get('email', 'N/A')}")
    print(f"name: {updated_user.get('name', 'N/A')}")
    
    # Check other relevant fields
    print(f"subscription: {updated_user.get('subscription', 'FREE')}")
    print(f"usageCount: {updated_user.get('usageCount', 0)}")
    
    # Add lastActive field if missing
    if 'lastActive' not in updated_user:
        users.update_one(
            {'_id': user['_id']},
            {'$set': {'lastActive': datetime.datetime.utcnow()}}
        )
        print("Added lastActive field")
else:
    print("No users found in database")
    
    # Create a sample user if none exists
    new_user = {
        'auth0Id': 'sample-auth0-id',
        'user_id': 'sample-auth0-id',
        'email': 'sample@example.com',
        'name': 'Sample User',
        'createdAt': datetime.datetime.utcnow(),
        'lastLogin': datetime.datetime.utcnow(),
        'lastActive': datetime.datetime.utcnow(),
        'subscription': 'FREE',
        'usageCount': 0
    }
    
    result = users.insert_one(new_user)
    print(f"Created sample user with ID: {result.inserted_id}") 