from pymongo import MongoClient
from pymongo.server_api import ServerApi
import json
import datetime
from bson import ObjectId

# Custom JSON encoder to handle MongoDB types
class MongoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super(MongoEncoder, self).default(obj)

# Connect to MongoDB
client = MongoClient(
    'mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=MrWlah',
    tls=True,
    tlsCertificateKeyFile='certs/X509-cert-5870665680541743449.pem',
    server_api=ServerApi('1')
)

db = client['benchai']

# Search for Auth0 callback logs which would have email information
print("SEARCHING FOR AUTH0 CALLBACK LOGS...")
auth_logs = list(db.logs.find({
    "message": {"$regex": "AUTH CALLBACK", "$options": "i"}
}).sort("timestamp", -1).limit(20))

print(f"Found {len(auth_logs)} Auth0 callback logs")

for log in auth_logs:
    print(json.dumps(log, cls=MongoEncoder, indent=2))

# Check for any logs with "email" in them
print("\nSEARCHING FOR EMAIL LOGS...")
email_logs = list(db.logs.find({
    "message": {"$regex": "email", "$options": "i"}
}).sort("timestamp", -1).limit(20))

print(f"Found {len(email_logs)} logs containing email information")

for log in email_logs:
    print(json.dumps(log, cls=MongoEncoder, indent=2))

# Check for user records in all collections
print("\nSEARCHING FOR USER ACTIVITY IN OTHER COLLECTIONS...")
collections = db.list_collection_names()

for collection_name in collections:
    if collection_name in ['transformations', 'user_sessions', 'interactions', 'apiUsage']:
        collection = db[collection_name]
        
        # Try common user ID field names
        for field in ['userId', 'user_id', 'auth0Id', 'user']:
            if field == 'user':
                # For embedded documents
                count = collection.count_documents({f"{field}.id": {"$exists": True}})
                if count > 0:
                    print(f"Found {count} records in {collection_name} with {field}.id")
                    
                    # Show a sample
                    sample = collection.find_one({f"{field}.id": {"$exists": True}})
                    print(f"Sample: {json.dumps(sample, cls=MongoEncoder, indent=2)}")
            else:
                count = collection.count_documents({field: {"$exists": True}})
                if count > 0:
                    print(f"Found {count} records in {collection_name} with {field}")
                    
                    # Show a sample and list the unique user IDs
                    sample = collection.find_one({field: {"$exists": True}})
                    print(f"Sample: {json.dumps(sample, cls=MongoEncoder, indent=2)}")
                    
                    # Get unique user IDs (limit to 10)
                    user_ids = list(collection.distinct(field))[:10]
                    print(f"Unique {field} values ({len(user_ids)} total): {user_ids}")
                    
                    # For each user ID, check if a user record exists
                    for user_id in user_ids:
                        user_record = db.users.find_one({
                            "$or": [
                                {"_id": user_id if isinstance(user_id, ObjectId) else None},
                                {"user_id": user_id},
                                {"auth0Id": user_id}
                            ]
                        })
                        
                        if user_record:
                            print(f"Found user record for {field}={user_id}: {user_record.get('name', 'Unknown')}, {user_record.get('email', 'No email')}")
                        else:
                            print(f"No user record found for {field}={user_id}")
                    
                    print()

# Check if we need to add any real users
print("\nCHECKING NEED TO ADD REAL USERS...")
transformations = db.transformations.find().limit(5)
real_user_ids = set()

for t in transformations:
    if 'userId' in t:
        real_user_ids.add(t['userId'])
    elif 'user_id' in t:
        real_user_ids.add(t['user_id'])

if real_user_ids:
    print(f"Found {len(real_user_ids)} real user IDs in transformations collection: {real_user_ids}")
    
    # For each user ID, check if a user record exists
    for user_id in real_user_ids:
        user_record = db.users.find_one({
            "$or": [
                {"user_id": user_id},
                {"auth0Id": user_id}
            ]
        })
        
        if not user_record:
            print(f"Missing user record for user_id={user_id}")
            
            # Create a sample record for this user
            new_user = {
                'auth0Id': user_id,
                'user_id': user_id,
                'email': f"user-{user_id[-6:]}@example.com",  # Create a synthetic email
                'name': f"User {user_id[-6:]}",
                'createdAt': datetime.datetime.utcnow(),
                'lastLogin': datetime.datetime.utcnow(),
                'lastActive': datetime.datetime.utcnow(),
                'subscription': 'FREE',
                'usageCount': 0
            }
            
            # Ask to insert this user
            confirm = input(f"Create user record for {user_id}? (y/n): ")
            if confirm.lower() == 'y':
                result = db.users.insert_one(new_user)
                print(f"Created user record with ID: {result.inserted_id}")
        else:
            print(f"User record exists for user_id={user_id}: {user_record.get('name', 'Unknown')}, {user_record.get('email', 'No email')}") 