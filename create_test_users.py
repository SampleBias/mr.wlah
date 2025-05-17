from pymongo import MongoClient
from pymongo.server_api import ServerApi
import datetime
import random
import uuid

# Connect to MongoDB
client = MongoClient(
    'mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=MrWlah',
    tls=True,
    tlsCertificateKeyFile='certs/X509-cert-5870665680541743449.pem',
    server_api=ServerApi('1')
)

db = client['benchai']
users_collection = db['users']

# Sample user data
test_users = [
    {
        'auth0Id': f"auth0|{uuid.uuid4()}",
        'name': 'John Smith',
        'email': 'john.smith@example.com',
        'subscription': 'BASIC',
        'usageCount': 7,
        'username': 'johnsmith'
    },
    {
        'auth0Id': f"auth0|{uuid.uuid4()}",
        'name': 'Sarah Johnson',
        'email': 'sarah.j@example.com',
        'subscription': 'PRO',
        'usageCount': 15,
        'username': 'sarahj'
    },
    {
        'auth0Id': f"auth0|{uuid.uuid4()}",
        'name': 'Michael Davis',
        'email': 'michael.d@example.com',
        'subscription': 'FREE',
        'usageCount': 2,
        'username': 'mdavis'
    },
    {
        'auth0Id': f"auth0|{uuid.uuid4()}",
        'name': 'Emma Wilson',
        'email': 'emma.w@example.com',
        'subscription': 'UNLIMITED',
        'usageCount': 32,
        'username': 'ewilson'
    },
    {
        'auth0Id': f"auth0|{uuid.uuid4()}",
        'name': 'James Taylor',
        'email': 'james.taylor@example.com',
        'subscription': 'FREE',
        'usageCount': 1,
        'username': 'jtaylor'
    }
]

# Check the existing users
existing_users = list(users_collection.find())
print(f"Found {len(existing_users)} existing users in the database")

# See if there's a unique index on username
indexes = users_collection.index_information()
print(f"Collection indexes: {indexes}")
print("Checking for required fields in existing users...")

# If a username index exists, check existing users and add username if missing
if any('username' in idx for idx in indexes.values()):
    print("Username index found - checking existing users for usernames")
    for user in existing_users:
        if 'username' not in user or not user['username']:
            # Generate a username
            if 'email' in user and user['email']:
                username = user['email'].split('@')[0].replace('.', '')
            else:
                username = f"user{str(uuid.uuid4())[:8]}"
                
            # Add a random number to make it unique
            username = f"{username}{random.randint(1000, 9999)}"
            
            # Update the user
            print(f"Adding username '{username}' to user {user.get('name', 'Unknown')}")
            users_collection.update_one(
                {'_id': user['_id']},
                {'$set': {'username': username}}
            )

# Add timestamps and ensure user_id field exists
for user in test_users:
    # Create a random timestamp within the last 7 days
    days_ago = random.randint(0, 7)
    hours_ago = random.randint(0, 24)
    minutes_ago = random.randint(0, 60)
    
    timestamp = datetime.datetime.now() - datetime.timedelta(
        days=days_ago, 
        hours=hours_ago,
        minutes=minutes_ago
    )
    
    # Add fields
    user['lastLogin'] = timestamp
    user['lastActive'] = timestamp
    user['createdAt'] = timestamp - datetime.timedelta(days=random.randint(1, 30))
    user['user_id'] = user['auth0Id']  # Ensure user_id field exists
    user['subscriptionUpdatedAt'] = timestamp - datetime.timedelta(days=random.randint(0, 5))
    user['preferences'] = {
        'defaultTone': random.choice(['casual', 'formal', 'friendly', 'professional']),
        'saveHistory': random.choice([True, False])
    }

# Insert users
created_users = []
for user in test_users:
    try:
        # Check if user already exists
        existing = users_collection.find_one({'$or': [
            {'email': user['email']},
            {'username': user['username']}
        ]})
        
        if existing:
            print(f"User {user['name']} ({user['email']}) already exists, skipping")
            continue
            
        result = users_collection.insert_one(user)
        user['_id'] = result.inserted_id
        created_users.append(user)
        print(f"Created user: {user['name']} ({user['email']}) with ID: {result.inserted_id}")
    except Exception as e:
        print(f"Error creating user {user['name']}: {e}")

print(f"\nSuccessfully created {len(created_users)} test users")
print("You can now see these users in the admin panel") 