from pymongo import MongoClient
from pymongo.server_api import ServerApi
import datetime
import json
from bson import ObjectId

# Custom JSON encoder to handle ObjectId and datetime
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
users_collection = db['users']

# Find all users
print("SEARCHING FOR ALL USERS IN DATABASE...")
all_users = list(users_collection.find())

if all_users:
    print(f"Found {len(all_users)} users in database:")
    
    for i, user in enumerate(all_users):
        print(f"\n--- USER {i+1} ---")
        print(f"_id: {user['_id']}")
        
        # Check for Auth0 identifiers
        print(f"auth0Id: {user.get('auth0Id', 'N/A')}")
        print(f"user_id: {user.get('user_id', 'N/A')}")
        
        # Basic user info
        print(f"name: {user.get('name', 'N/A')}")
        print(f"email: {user.get('email', 'N/A')}")
        
        # Check subscription info
        print(f"subscription: {user.get('subscription', 'FREE')}")
        print(f"usageCount: {user.get('usageCount', 0)}")
        
        # Check dates
        if 'lastLogin' in user:
            print(f"lastLogin: {user.get('lastLogin')}")
        if 'lastActive' in user:
            print(f"lastActive: {user.get('lastActive')}")
        if 'createdAt' in user:
            print(f"createdAt: {user.get('createdAt')}")
else:
    print("No users found in database")

print("\n--- SCANNING FOR OTHER COLLECTIONS ---")
collections = db.list_collection_names()
print(f"Collections in database: {collections}")

# Check auth_session collection if it exists
if 'auth_sessions' in collections:
    print("\nChecking auth_sessions collection...")
    auth_sessions = list(db.auth_sessions.find())
    print(f"Found {len(auth_sessions)} auth sessions")
    
    if auth_sessions:
        for session in auth_sessions[:2]:  # Show first 2 only
            print(json.dumps(session, cls=MongoEncoder, indent=2))

# Check for user activity logs
if 'user_activity' in collections:
    print("\nChecking user_activity collection...")
    activities = list(db.user_activity.find())
    print(f"Found {len(activities)} user activities")
    
    if activities:
        for activity in activities[:2]:  # Show first 2 only
            print(json.dumps(activity, cls=MongoEncoder, indent=2))

# Check for logs that might contain user information
if 'logs' in collections:
    print("\nChecking logs collection for user logins...")
    login_logs = list(db.logs.find({
        "$or": [
            {"message": {"$regex": "Auth0", "$options": "i"}},
            {"message": {"$regex": "authenticated", "$options": "i"}},
            {"message": {"$regex": "User.*logged in", "$options": "i"}}
        ]
    }).sort("timestamp", -1).limit(5))
    
    print(f"Found {len(login_logs)} login-related logs")
    
    if login_logs:
        for log in login_logs:
            print(json.dumps(log, cls=MongoEncoder, indent=2)) 