from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Connect to MongoDB
client = MongoClient(
    'mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=MrWlah',
    tls=True,
    tlsCertificateKeyFile='certs/X509-cert-5870665680541743449.pem',
    server_api=ServerApi('1')
)

db = client['benchai']
users_collection = db['users']

# Find the sample user
sample_user = users_collection.find_one({'auth0Id': 'sample-user-id'})

if sample_user:
    print(f"Found sample user: {sample_user.get('name')} ({sample_user.get('email')})")
    
    # Check if user has username
    if 'username' not in sample_user or not sample_user['username']:
        # Add a username
        username = 'sample_user'
        
        # Update the user
        users_collection.update_one(
            {'_id': sample_user['_id']},
            {'$set': {'username': username}}
        )
        
        print(f"Added username '{username}' to sample user")
    else:
        print(f"Sample user already has username: {sample_user['username']}")
else:
    print("Sample user not found") 