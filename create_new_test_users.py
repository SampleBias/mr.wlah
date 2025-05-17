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

# Generate a timestamp suffix to make emails unique
timestamp_suffix = datetime.datetime.now().strftime("%m%d%H%M")

# Sample user data - with unique emails using timestamp
test_users = [
    {
        'auth0Id': f"auth0|{uuid.uuid4()}",
        'name': 'Test Admin User',
        'email': f'admin.test{timestamp_suffix}@example.com',
        'subscription': 'UNLIMITED',
        'usageCount': 42,
        'username': f'testadmin{timestamp_suffix}'
    },
    {
        'auth0Id': f"auth0|{uuid.uuid4()}",
        'name': 'Test Basic User',
        'email': f'basic.test{timestamp_suffix}@example.com',
        'subscription': 'BASIC',
        'usageCount': 8,
        'username': f'testbasic{timestamp_suffix}'
    },
    {
        'auth0Id': f"auth0|{uuid.uuid4()}",
        'name': 'Test Free User',
        'email': f'free.test{timestamp_suffix}@example.com',
        'subscription': 'FREE',
        'usageCount': 3,
        'username': f'testfree{timestamp_suffix}'
    }
]

# Check the existing users
existing_users = list(users_collection.find())
print(f"Found {len(existing_users)} existing users in the database")

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
print("\nUser details for testing:")
for user in created_users:
    print(f"- Name: {user['name']}")
    print(f"  Email: {user['email']}")
    print(f"  Username: {user['username']}")
    print(f"  Subscription: {user['subscription']}")
    print(f"  Auth0 ID: {user['auth0Id']}")
    print(f"  MongoDB ID: {user['_id']}")
    print("") 