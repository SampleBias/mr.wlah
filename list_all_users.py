from pymongo import MongoClient
from pymongo.server_api import ServerApi
import json
from bson.objectid import ObjectId
import datetime

# Custom JSON encoder to handle MongoDB objects
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        return super().default(o)

# Connect to MongoDB
client = MongoClient(
    'mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=MrWlah',
    tls=True,
    tlsCertificateKeyFile='certs/X509-cert-5870665680541743449.pem',
    server_api=ServerApi('1')
)

db = client['benchai']
users = list(db.users.find())
print(f'Found {len(users)} users in database')

print("\nUSER SUMMARY:")
for i, user in enumerate(users):
    print(f'{i+1}. {user.get("name", "Unknown")} - {user.get("email", "No Email")} - {user.get("subscription", "FREE")}')

# For each user, print full details
for i, user in enumerate(users):
    print(f'\n--- USER {i+1} DETAILS ---')
    print(f'ID: {user.get("_id")}')
    print(f'Name: {user.get("name", "N/A")}')
    print(f'Email: {user.get("email", "N/A")}')
    print(f'Auth0Id: {user.get("auth0Id", "N/A")}')
    print(f'user_id: {user.get("user_id", "N/A")}')
    print(f'Username: {user.get("username", "N/A")}')
    print(f'Subscription: {user.get("subscription", "FREE")}')
    print(f'Usage Count: {user.get("usageCount", 0)}')
    
    # Format dates nicely
    if "lastLogin" in user:
        try:
            print(f'Last Login: {user["lastLogin"].strftime("%Y-%m-%d %H:%M:%S")}')
        except:
            print(f'Last Login: {user["lastLogin"]}')
    
    if "lastActive" in user:
        try:
            print(f'Last Active: {user["lastActive"].strftime("%Y-%m-%d %H:%M:%S")}')
        except:
            print(f'Last Active: {user["lastActive"]}')
            
    if "createdAt" in user:
        try:
            print(f'Created At: {user["createdAt"].strftime("%Y-%m-%d %H:%M:%S")}')
        except:
            print(f'Created At: {user["createdAt"]}') 