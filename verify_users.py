from pymongo import MongoClient
from pymongo.server_api import ServerApi
import datetime
from bson import ObjectId

# Connect to MongoDB
client = MongoClient(
    'mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=MrWlah',
    tls=True,
    tlsCertificateKeyFile='certs/X509-cert-5870665680541743449.pem',
    server_api=ServerApi('1')
)

db = client['benchai']
users_collection = db['users']

def display_user(user):
    """Format and display user information"""
    # Format dates for better readability
    created_at = user.get('createdAt', 'Unknown')
    if isinstance(created_at, datetime.datetime):
        created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
    
    last_login = user.get('lastLogin', 'Never')
    if isinstance(last_login, datetime.datetime):
        last_login = last_login.strftime('%Y-%m-%d %H:%M:%S')
    
    last_active = user.get('lastActive', 'Never')
    if isinstance(last_active, datetime.datetime):
        last_active = last_active.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"- ID: {user['_id']}")
    print(f"  Name: {user.get('name', 'No name')}")
    print(f"  Email: {user.get('email', 'No email')}")
    print(f"  Username: {user.get('username', 'No username')}")
    print(f"  Subscription: {user.get('subscription', 'None')}")
    print(f"  Usage Count: {user.get('usageCount', 0)}")
    print(f"  Created: {created_at}")
    print(f"  Last Login: {last_login}")
    print(f"  Last Active: {last_active}")
    print("")

def main():
    # Check if users collection exists
    if 'users' not in db.list_collection_names():
        print("Error: 'users' collection does not exist in the database")
        return
    
    # Count users
    user_count = users_collection.count_documents({})
    print(f"Database contains {user_count} users\n")
    
    # Get and display all users
    users = list(users_collection.find().sort("lastActive", -1))
    
    print("=== All Users (sorted by last active date) ===")
    for user in users:
        display_user(user)
        
    # Check for test users
    test_users = list(users_collection.find({"name": {"$regex": "Test", "$options": "i"}}))
    if test_users:
        print(f"\n=== {len(test_users)} Test Users ===")
        for user in test_users:
            display_user(user)
    
    print("\nTo delete a user, use the following MongoDB command:")
    print("db.users.deleteOne({_id: ObjectId('paste-user-id-here')})")

if __name__ == "__main__":
    main() 