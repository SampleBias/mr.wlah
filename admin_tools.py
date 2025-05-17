from pymongo import MongoClient
from pymongo.server_api import ServerApi
import datetime
import uuid
import random
import getpass
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get admin PIN from environment or default
ADMIN_PIN = os.getenv('ADMIN_PIN', '123456')

# Connect to MongoDB
client = MongoClient(
    'mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=MrWlah',
    tls=True,
    tlsCertificateKeyFile='certs/X509-cert-5870665680541743449.pem',
    server_api=ServerApi('1')
)

db = client['benchai']
users_collection = db['users']

# Subscription tiers
SUBSCRIPTION_TIERS = {
    '1': 'FREE',
    '2': 'BASIC',
    '3': 'PRO',
    '4': 'UNLIMITED'
}

def authenticate_admin():
    """Authenticate the admin using the PIN"""
    print("\n=== ADMIN AUTHENTICATION ===")
    attempts = 3
    
    while attempts > 0:
        pin = getpass.getpass("Enter admin PIN: ")
        
        if pin == ADMIN_PIN:
            print("Authentication successful!")
            return True
        else:
            attempts -= 1
            print(f"Incorrect PIN. {attempts} attempts remaining.")
    
    print("Authentication failed. Exiting.")
    return False

def generate_random_auth0_id():
    """Generate a random Auth0 ID for a manually created user"""
    return f"auth0|manual_{uuid.uuid4()}"

def create_new_user():
    """Create a new user in the database"""
    print("\n=== CREATE NEW USER ===")
    
    # Get user details
    name = input("Enter user name: ")
    email = input("Enter user email: ")
    
    # Generate a username (remove spaces and special characters)
    base_username = email.split('@')[0].lower().replace('.', '')
    username = f"{base_username}{random.randint(1000, 9999)}"
    
    # Select subscription tier
    print("\nSelect subscription tier:")
    for key, tier in SUBSCRIPTION_TIERS.items():
        print(f"{key}: {tier}")
    
    subscription_key = input("Enter subscription tier number (default: 1 - FREE): ") or '1'
    subscription = SUBSCRIPTION_TIERS.get(subscription_key, 'FREE')
    
    # Generate Auth0 ID
    auth0_id = generate_random_auth0_id()
    
    # Create user record
    timestamp = datetime.datetime.now()
    user = {
        'auth0Id': auth0_id,
        'user_id': auth0_id,  # Match Auth0 ID for consistency
        'name': name,
        'email': email,
        'username': username,
        'subscription': subscription,
        'usageCount': 0,
        'createdAt': timestamp,
        'lastLogin': timestamp,
        'lastActive': timestamp,
        'subscriptionUpdatedAt': timestamp,
        'is_manual_user': True,  # Flag to indicate manually created user
        'created_by_admin': True,
        'preferences': {
            'defaultTone': 'casual',
            'saveHistory': True
        }
    }
    
    # Check if email already exists
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        print(f"\nERROR: A user with email {email} already exists!")
        print(f"User: {existing_user.get('name')} - {existing_user.get('subscription', 'FREE')}")
        
        update = input("Do you want to update this user's subscription? (y/n): ")
        if update.lower() == 'y':
            users_collection.update_one(
                {'_id': existing_user['_id']},
                {'$set': {
                    'subscription': subscription,
                    'subscriptionUpdatedAt': timestamp
                }}
            )
            print(f"\nUser {name} subscription updated to {subscription}")
            return
        else:
            return
    
    # Try to insert the user
    try:
        result = users_collection.insert_one(user)
        print(f"\nUser {name} created successfully with ID: {result.inserted_id}")
        print(f"Subscription: {subscription}")
        print(f"Email: {email}")
        print(f"Username: {username}")
        print(f"Auth0/user ID: {auth0_id}")
    except Exception as e:
        print(f"Error creating user: {e}")

def update_user_subscription():
    """Update an existing user's subscription"""
    print("\n=== UPDATE USER SUBSCRIPTION ===")
    
    # Get user by email
    email = input("Enter user email: ")
    user = users_collection.find_one({'email': email})
    
    if not user:
        print(f"No user found with email {email}")
        return
    
    # Display user info
    print(f"\nUser: {user.get('name', 'Unknown')}")
    print(f"Current subscription: {user.get('subscription', 'FREE')}")
    print(f"Usage count: {user.get('usageCount', 0)}")
    
    # Select new subscription tier
    print("\nSelect new subscription tier:")
    for key, tier in SUBSCRIPTION_TIERS.items():
        print(f"{key}: {tier}")
    
    subscription_key = input("Enter subscription tier number: ")
    if subscription_key not in SUBSCRIPTION_TIERS:
        print("Invalid selection. Operation cancelled.")
        return
    
    subscription = SUBSCRIPTION_TIERS[subscription_key]
    
    # Reset usage count?
    reset_usage = input("Reset usage count? (y/n): ")
    
    # Update user
    update_data = {
        'subscription': subscription,
        'subscriptionUpdatedAt': datetime.datetime.now()
    }
    
    if reset_usage.lower() == 'y':
        update_data['usageCount'] = 0
    
    users_collection.update_one(
        {'_id': user['_id']},
        {'$set': update_data}
    )
    
    print(f"\nUser {user.get('name', 'Unknown')} subscription updated to {subscription}")
    if reset_usage.lower() == 'y':
        print("Usage count reset to 0")

def list_all_users():
    """List all users in the database"""
    print("\n=== ALL USERS ===")
    
    users = list(users_collection.find().sort('lastActive', -1))
    if not users:
        print("No users found")
        return
    
    print(f"Found {len(users)} users:\n")
    
    print(f"{'NAME':<20} {'EMAIL':<30} {'SUBSCRIPTION':<10} {'USAGE':<5} {'LAST ACTIVE':<25}")
    print("-" * 90)
    
    for user in users:
        # Format last active date
        last_active = "Never"
        if 'lastActive' in user:
            try:
                last_active = user['lastActive'].strftime("%Y-%m-%d %H:%M:%S")
            except:
                last_active = str(user['lastActive'])
        
        name = user.get('name', 'Unknown')
        email = user.get('email', 'No email')
        subscription = user.get('subscription', 'FREE')
        usage_count = user.get('usageCount', 0)
        
        print(f"{name[:19]:<20} {email[:29]:<30} {subscription:<10} {usage_count:<5} {last_active}")

def main():
    """Main function"""
    # Authenticate admin
    if not authenticate_admin():
        return
    
    while True:
        print("\n=== ADMIN TOOLS ===")
        print("1: Create New User")
        print("2: Update User Subscription")
        print("3: List All Users")
        print("0: Exit")
        
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            create_new_user()
        elif choice == '2':
            update_user_subscription()
        elif choice == '3':
            list_all_users()
        elif choice == '0':
            print("Exiting admin tools. Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main() 