import os
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import google.genai as genai
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import json
from authlib.integrations.flask_client import OAuth
import PyPDF2
import docx
import datetime
import re

# Import database logging functions
try:
    from init_database import add_system_log, log_user_activity
except ImportError:
    # Fallback logging functions if import fails
    def add_system_log(message, level="INFO"):
        print(f"[{level}] {message}")
    
    def log_user_activity(user_id, action, details=None):
        details_str = f" - {json.dumps(details)}" if details else ""
        print(f"[USER {user_id}] {action}{details_str}")

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='.')
CORS(app)

# Configure Google Gemini API
api_key = os.getenv('GEMINI_API_KEY')
genai_client = genai.Client(api_key=api_key)
model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')

# Configure MongoDB - explicitly set the MongoDB URI for BenchAI
# This ensures we don't use any potentially incorrect values from .env
MONGODB_URI = "mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=MrWlah"
mongo_db = os.getenv('MONGODB_DATABASE', 'benchai')

# Initialize collections as None by default
users_collection = None
transformations_collection = None
api_usage_collection = None

# Check if X.509 certificate exists
cert_path = os.path.join('certs', 'X509-cert-5870665680541743449.pem')
has_certificate = os.path.exists(cert_path)

# Connect to MongoDB if certificate exists
if has_certificate:
    try:
        print(f"Connecting to BenchAI MongoDB...")
        print(f"Using X.509 certificate at {cert_path}")
        
        # Set up MongoDB client with X.509 certificate
        mongo_client = MongoClient(
            MONGODB_URI,
            tls=True,
            tlsCertificateKeyFile=cert_path,
            server_api=ServerApi('1')
        )
        
        # Test connection
        mongo_client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Connect to the specified database
        db = mongo_client[mongo_db]
        add_system_log(f"Connected to MongoDB database: {mongo_db}")
        
        # Set up collections
        users_collection = db['users']
        transformations_collection = db['transformations']
        api_usage_collection = db['apiUsage']
        
        # Log connection success with database details
        collections = db.list_collection_names()
        add_system_log(f"Available collections: {', '.join(collections)}", "INFO")
        
    except Exception as e:
        error_msg = f"MongoDB connection error: {str(e)}"
        print(f"❌ {error_msg}")
        add_system_log(error_msg, "ERROR")
else:
    if not has_certificate:
        print(f"⚠️ X.509 certificate not found at {cert_path}")
        add_system_log(f"X.509 certificate not found at {cert_path}", "WARNING")
    
    print("Running in demo mode without database connection")
    add_system_log("Running in demo mode without database connection", "WARNING")

# Configure Auth0
oauth = OAuth(app)
auth0 = oauth.register(
    'auth0',
    client_id=os.getenv('AUTH0_CLIENT_ID'),
    client_secret=os.getenv('AUTH0_CLIENT_SECRET'),
    api_base_url=f"https://{os.getenv('AUTH0_DOMAIN')}",
    access_token_url=f"https://{os.getenv('AUTH0_DOMAIN')}/oauth/token",
    authorize_url=f"https://{os.getenv('AUTH0_DOMAIN')}/authorize",
    client_kwargs={
        'scope': 'openid profile email',
    },
)

# Font style detection and preservation
def detect_font_style(text):
    """Detect font style markers in HTML or common text formatting"""
    font_info = {
        'font_family': None,
        'font_size': None,
        'font_style': None,
        'font_weight': None,
        'text_decoration': None,
        'color': None,
        'html_tags': []
    }
    
    # Check for HTML tags
    html_tags = re.findall(r'<([a-z0-9]+)[^>]*>', text, re.IGNORECASE)
    if html_tags:
        font_info['html_tags'] = list(set(html_tags))
    
    # Check for inline CSS
    font_family_match = re.search(r'font-family:\s*([^;]+);', text, re.IGNORECASE)
    if font_family_match:
        font_info['font_family'] = font_family_match.group(1).strip()
    
    font_size_match = re.search(r'font-size:\s*([^;]+);', text, re.IGNORECASE)
    if font_size_match:
        font_info['font_size'] = font_size_match.group(1).strip()
    
    # Check for direct font tags
    font_tag_match = re.search(r'<font[^>]+face=["\']([^"\']+)["\']', text, re.IGNORECASE)
    if font_tag_match:
        font_info['font_family'] = font_tag_match.group(1).strip()
    
    # Check for other style indicators
    if '<b>' in text.lower() or 'font-weight: bold' in text.lower():
        font_info['font_weight'] = 'bold'
    
    if '<i>' in text.lower() or 'font-style: italic' in text.lower():
        font_info['font_style'] = 'italic'
    
    if '<u>' in text.lower() or 'text-decoration: underline' in text.lower():
        font_info['text_decoration'] = 'underline'
    
    # Check for color
    color_match = re.search(r'color:\s*([^;]+);', text, re.IGNORECASE)
    if color_match:
        font_info['color'] = color_match.group(1).strip()
    
    return font_info

def apply_font_style(text, font_info):
    """Apply detected font style to the output text"""
    
    # If no style detected, return text as is
    if not any(font_info.values()):
        return text
    
    # If HTML tags detected, try to maintain structure
    if font_info['html_tags'] and not ('script' in font_info['html_tags'] or 'style' in font_info['html_tags']):
        # Apply basic styling
        styled_text = text
        
        # Apply font family if detected
        if font_info['font_family']:
            styled_text = f'<span style="font-family: {font_info["font_family"]}">{styled_text}</span>'
        
        # Apply font size if detected
        if font_info['font_size']:
            styled_text = f'<span style="font-size: {font_info["font_size"]}">{styled_text}</span>'
        
        # Apply bold if detected
        if font_info['font_weight'] == 'bold':
            styled_text = f'<b>{styled_text}</b>'
        
        # Apply italic if detected
        if font_info['font_style'] == 'italic':
            styled_text = f'<i>{styled_text}</i>'
        
        # Apply underline if detected
        if font_info['text_decoration'] == 'underline':
            styled_text = f'<u>{styled_text}</u>'
        
        # Apply color if detected
        if font_info['color']:
            styled_text = f'<span style="color: {font_info["color"]}">{styled_text}</span>'
        
        return styled_text
    
    return text

# Helper function to extract text from different file types
def extract_text_from_file(file):
    if file.filename.endswith('.txt'):
        return file.read().decode('utf-8')
    elif file.filename.endswith('.pdf'):
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    elif file.filename.endswith('.docx'):
        doc = docx.Document(file)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    else:
        raise ValueError("Unsupported file format")

# Custom JSON encoder to handle MongoDB ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

app.json_encoder = JSONEncoder

# Routes
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/transform', methods=['POST'])
def transform_text():
    # Get request data
    data = request.get_json() if request.is_json else {}
    text = data.get('text', '')
    tone = data.get('tone', 'casual')
    user_id = data.get('userId')
    preserve_font = data.get('preserveFont', True)
    
    # Log transformation request
    if user_id:
        log_details = {
            "tone": tone,
            "text_length": len(text),
            "preserve_font": preserve_font
        }
        log_user_activity(user_id, "TRANSFORM_TEXT", log_details)
    
    if not text:
        # Check if there's a file upload
        if 'file' in request.files:
            file = request.files['file']
            try:
                text = extract_text_from_file(file)
            except Exception as e:
                return jsonify({'error': f"Error processing file: {str(e)}"}), 400
        else:
            return jsonify({'error': 'No text or file provided'}), 400
    
    try:
        # Detect font style if preservation is requested
        font_info = detect_font_style(text) if preserve_font else {}
        
        # Create prompt for Gemini
        prompt = f"""Rewrite the following text to sound more human. 
                   Add personal experiences, vary sentence structure, 
                   use colloquialisms, and make it engaging.
                   Use a {tone} tone.
                   
                   Text to transform: {text}"""
        
        # Call Gemini API with new client pattern
        response = genai_client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        transformed_text = response.text
        
        # Apply original font style if preservation is requested
        if preserve_font:
            transformed_text = apply_font_style(transformed_text, font_info)
        
        # Log the transformation if MongoDB is configured and user is authenticated
        if transformations_collection is not None and user_id:
            try:
                # Create the transformation record
                transformation = {
                    'userId': user_id,  # Store as string instead of ObjectId
                    'originalText': text,
                    'transformedText': transformed_text,
                    'tone': tone,
                    'fontStylePreserved': preserve_font,
                    'createdAt': datetime.datetime.now(),
                    'metadata': {
                        'characterCount': len(text),
                        'sourceType': 'file' if 'file' in request.files else 'paste',
                        'modelUsed': model_name
                    }
                }
                
                # Insert the transformation record
                result = transformations_collection.insert_one(transformation)
                
                # Log successful storage
                if result.inserted_id:
                    add_system_log(f"Transformation record stored with ID: {result.inserted_id}", "INFO")
            except Exception as db_error:
                # Log the error but don't fail the request
                add_system_log(f"Failed to store transformation: {str(db_error)}", "ERROR")
        
        return jsonify({'transformedText': transformed_text, 'fontInfo': font_info})
    
    except Exception as e:
        error_msg = f"Error transforming text: {str(e)}"
        print(error_msg)
        add_system_log(error_msg, "ERROR")
        return jsonify({'error': 'Failed to transform text'}), 500

@app.route('/api/user/transformations', methods=['GET'])
def get_user_transformations():
    if transformations_collection is None:
        return jsonify({'error': 'MongoDB not configured', 'demo': True}), 200
    
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    try:
        # Find transformations for this user
        transformations = list(transformations_collection.find(
            {'userId': user_id}  # Use string user_id directly
        ).sort('createdAt', -1).limit(10))
        
        add_system_log(f"Retrieved {len(transformations)} transformations for user {user_id}", "INFO")
        return jsonify({'transformations': transformations})
    except Exception as e:
        error_msg = f"Error retrieving transformations: {str(e)}"
        add_system_log(error_msg, "ERROR")
        return jsonify({'error': error_msg}), 500

# Auth0 routes
@app.route('/api/auth/login')
def login():
    add_system_log("Login attempt initiated")
    return auth0.authorize_redirect(
        redirect_uri=os.getenv('AUTH0_CALLBACK_URL')
    )

@app.route('/api/auth/callback')
def callback():
    try:
        token = auth0.authorize_access_token()
        user_info = auth0.get('userinfo').json()
        
        # Log user login
        log_user_activity(
            user_info['sub'], 
            "LOGIN", 
            {"name": user_info.get('name'), "email": user_info.get('email')}
        )
        
        # Store user in MongoDB if configured
        if users_collection is not None:
            try:
                current_time = datetime.datetime.now()
                
                # Check if user exists
                existing_user = users_collection.find_one({"auth0Id": user_info['sub']})
                
                # Update or insert user
                users_collection.update_one(
                    {'auth0Id': user_info['sub']},
                    {'$set': {
                        'email': user_info.get('email'),
                        'name': user_info.get('name'),
                        'lastLogin': current_time
                    }, '$setOnInsert': {
                        'createdAt': current_time,
                        'usageCount': 0,
                        'preferences': {
                            'defaultTone': 'casual',
                            'saveHistory': True
                        }
                    }},
                    upsert=True
                )
                
                # Log whether this was a new user or returning user
                if not existing_user:
                    add_system_log(f"New user created: {user_info.get('email')}", "INFO")
                else:
                    add_system_log(f"Returning user: {user_info.get('email')}", "INFO")
            except Exception as db_error:
                # Log the error but continue with login
                add_system_log(f"Error storing user data: {str(db_error)}", "ERROR")
        else:
            add_system_log("User login successful, but user data not stored (MongoDB not configured)", "WARNING")
        
        # Return user info
        return jsonify(user_info)
    except Exception as e:
        error_msg = f"Login error: {str(e)}"
        add_system_log(error_msg, "ERROR")
        return jsonify({"error": "Authentication failed"}), 401

@app.route('/api/auth/logout')
def logout():
    user_id = request.args.get('userId')
    
    if user_id:
        log_user_activity(user_id, "LOGOUT")
    
    # Clear session
    return jsonify({'message': 'Logged out successfully'})

if __name__ == '__main__':
    try:
        app.jinja_env.auto_reload = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        
        # Get port and environment from .env
        port = int(os.getenv('PORT', 3000))
        debug_mode = os.getenv('NODE_ENV') == 'development'
        
        # Log startup information
        start_msg = f"Starting Mr. Wlah application on port {port}"
        if debug_mode:
            start_msg += " in DEBUG mode"
        add_system_log(start_msg, "INFO")
        
        # Log database status
        if users_collection is not None:
            db_status = f"Connected to {mongo_db} database"
            if transformations_collection is not None:
                try:
                    transform_count = transformations_collection.count_documents({})
                    db_status += f" with {transform_count} transformations"
                except Exception as e:
                    db_status += f" (error counting transformations: {str(e)})"
            add_system_log(db_status, "INFO")
        else:
            add_system_log("Running without database connection", "WARNING")
        
        # Start the Flask app
        app.run(host='0.0.0.0', port=port, debug=debug_mode)
    except Exception as e:
        error_msg = f"Application startup error: {str(e)}"
        print(f"❌ {error_msg}")
        add_system_log(error_msg, "ERROR")
        sys.exit(1) 