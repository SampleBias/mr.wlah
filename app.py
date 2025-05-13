import os
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file, url_for, redirect, session
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
from docx.shared import Pt
import datetime
import re
import io
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from urllib.parse import urlencode
import uuid

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
CORS(app, supports_credentials=True)

# Set a more reliable secret key - Generate a fixed key for production
if os.getenv('SESSION_SECRET'):
    app.secret_key = os.getenv('SESSION_SECRET')
else:
    # Only for development - in production always use an environment variable
    app.secret_key = 'mr_wlah_dev_secret_key_12345'

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_USE_SIGNER'] = True

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
    server_metadata_url=f"https://{os.getenv('AUTH0_DOMAIN')}/.well-known/openid-configuration"
)

# Helper function to clean LLM output
def clean_llm_response(text):
    """
    Removes common LLM prefacing and concluding meta-text from responses
    to provide only the usable transformed content.
    """
    # List of common prefacing patterns to remove
    prefacing_patterns = [
        r"^(Here'?s|Here is|I'?ve|I have|Below is|The following is).*?:\s*\n+",
        r"^(Sure|Okay|Alright|Of course|I'd be happy to|I can|I will).*?:\s*\n+",
        r"^(I'?ve transformed|I'?ve rewritten|I'?ve humanized|I'?ve modified).*?:\s*\n+",
        r"^(Your text|The text|This content) (has been|is now).*?:\s*\n+",
        r"^(In|With|Using|Employing|Applying) a.*?tone.*?:\s*\n+",
        r"^(As requested|As per your request|Based on your request).*?:\s*\n+",
        r"^(This is|Now the text is|Now it sounds) (more|much more|significantly).*?:\s*\n+",
        r"^(I've kept|While maintaining|Maintaining|I've maintained).*?:\s*\n+",
        r"^(Using|Incorporating|Adding|With) (personal|my own|human).*?:\s*\n+",
        r"^(Transformed version|Human version|Human-like version|Rewritten version).*?:\s*\n+",
    ]
    
    # List of common concluding patterns to remove
    concluding_patterns = [
        r"\n+\s*(I hope|Hope|Hopefully) (this|that|these|it).*?\.$",
        r"\n+\s*(Let me know|Feel free to|Please) (if|to|contact).*?\.$",
        r"\n+\s*(This|The text|This version|This rewrite) (should|now|has).*?\.$",
        r"\n+\s*(Is there|Do you|Would you|If you) (anything|like|need).*?\.$",
        r"\n+\s*(Thank you|Thanks) (for|and).*?\.$",
        r"\n+\s*(How'?s that|How does that sound|Does this work|What do you think).*?\.$",
        r"\n+\s*(I'?ve tried|I tried|I'?ve attempted) (to|my best).*?\.$",
        r"\n+\s*(I'?ve maintained|I maintained|I'?ve preserved) (the|your|original).*?\.$",
        r"\n+\s*(The word count|This keeps|I'?ve kept) (is|the|within).*?\.$",
        r"\n+\s*(This|The above|The text above) (maintains|keeps|preserves).*?\.$",
    ]
    
    # Apply all prefacing patterns
    for pattern in prefacing_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Apply all concluding patterns
    for pattern in concluding_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Remove any leading or trailing whitespace
    text = text.strip()
    
    return text

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
        try:
            # Enhanced PDF text extraction
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)
            text = []
            
            # Extract text from each page with structure preservation
            for i in range(total_pages):
                page = reader.pages[i]
                page_text = page.extract_text()
                
                # Basic structure preservation
                if page_text:
                    # Add page number for longer documents
                    if total_pages > 1:
                        text.append(f"--- Page {i+1} ---\n")
                    
                    # Clean up common PDF extraction issues
                    lines = page_text.split('\n')
                    cleaned_lines = []
                    
                    for line in lines:
                        # Remove excessive spaces
                        cleaned_line = re.sub(r'\s+', ' ', line).strip()
                        if cleaned_line:
                            cleaned_lines.append(cleaned_line)
                    
                    # Join with proper paragraph breaks
                    text.append('\n'.join(cleaned_lines))
                    
                    # Add extra newline between pages
                    if i < total_pages - 1:
                        text.append("\n")
            
            return "\n".join(text)
        except Exception as e:
            add_system_log(f"PDF extraction error: {str(e)}", "ERROR")
            # Fallback to basic extraction
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
            
    elif file.filename.endswith('.docx'):
        try:
            # Enhanced DOCX text extraction
            doc = docx.Document(file)
            full_text = []
            
            # Process paragraphs with structure preservation
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
            
            # Get text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        full_text.append(" | ".join(row_text))
            
            return "\n\n".join(full_text)
        except Exception as e:
            add_system_log(f"DOCX extraction error: {str(e)}", "ERROR")
            # Fallback to basic extraction
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
    # Check if user is logged in
    is_logged_in = 'logged_in' in session and session['logged_in'] == True
    
    # Add detailed logging to troubleshoot the issue
    if is_logged_in:
        # User is authenticated
        user_info = session.get('profile', {})
        add_system_log(f"[INDEX ROUTE] User accessing homepage: {user_info.get('name', 'Unknown')} with session ID: {id(session)}", "INFO")
        add_system_log(f"[INDEX ROUTE] Session data: logged_in={session.get('logged_in')}, has_profile={('profile' in session)}", "INFO")
        
        # Make sure session is persisted
        session.modified = True
        
        # Serve the main application
        return send_file('index.html')
    else:
        # Look for session but not properly logged in
        if 'profile' in session:
            add_system_log(f"[INDEX ROUTE] Session exists but not properly logged in, clearing session. Session ID: {id(session)}", "WARNING")
            add_system_log(f"[INDEX ROUTE] Session data before clearing: {dict(session)}", "WARNING")
            session.clear()
        
        add_system_log("[INDEX ROUTE] Unauthenticated user attempting to access homepage, redirecting to login", "INFO")
        
        # If not authenticated, redirect to login
        return redirect('/login')

@app.route('/login')
def login_page():
    # If user is already logged in, redirect to homepage
    if 'logged_in' in session and session['logged_in'] == True:
        add_system_log(f"[LOGIN ROUTE] Authenticated user accessing login page, redirecting to homepage. Session ID: {id(session)}", "INFO")
        add_system_log(f"[LOGIN ROUTE] Session data: {dict(session)}", "INFO")
        
        # Ensure session data persists
        session.modified = True
        
        return redirect('/')
    
    # Check if there's an error parameter
    error = request.args.get('error')
    if error:
        add_system_log(f"[LOGIN ROUTE] Login page accessed with error: {error}", "WARNING")
    
    # Log for debugging the double login issue
    add_system_log(f"[LOGIN ROUTE] Serving login page to unauthenticated user. Session ID: {id(session)}", "INFO")
    add_system_log(f"[LOGIN ROUTE] Current session data: {dict(session)}", "INFO")
    
    # Otherwise serve the login page
    return send_file('login.html')

@app.route('/logout')
def logout_page():
    return send_file('logout.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/document/status', methods=['GET'])
def document_processing_status():
    """Endpoint to check document processing status for large files"""
    job_id = request.args.get('job_id')
    
    if not job_id:
        return jsonify({
            'status': 'error',
            'message': 'No job ID provided'
        }), 400
    
    # For simplicity, we'll just return a success status
    # In a production app, you'd check a queue or database for the actual status
    return jsonify({
        'status': 'completed',
        'job_id': job_id,
        'progress': 100
    })

@app.route('/api/transform', methods=['POST'])
def transform_text():
    try:
        # Check if this is a file upload from FormData
        if request.files and 'file' in request.files:
            file = request.files['file']
            try:
                # Extract text from the file
                text = extract_text_from_file(file)
                
                # If we're just extracting text for display, return it
                if request.form.get('extract_only') == 'true':
                    return jsonify({'originalText': text})
                
                # Otherwise, set it for transformation below
                tone = request.form.get('tone', 'casual')
                preserve_font = request.form.get('preserveFont', 'true') == 'true'
                target_word_count = request.form.get('targetWordCount')
                if target_word_count:
                    target_word_count = int(target_word_count)
                user_id = request.form.get('userId')
            except Exception as e:
                return jsonify({'error': f"Error processing file: {str(e)}"}), 400
        else:
            # Get request data from JSON
            data = request.get_json() if request.is_json else {}
            text = data.get('text', '')
            tone = data.get('tone', 'casual')
            user_id = data.get('userId')
            preserve_font = data.get('preserveFont', True)
            target_word_count = data.get('targetWordCount')
            
            if not text:
                return jsonify({'error': 'No text or file provided'}), 400
        
        # Log transformation request
        if user_id:
            log_details = {
                "tone": tone,
                "text_length": len(text),
                "preserve_font": preserve_font,
                "target_word_count": target_word_count
            }
            log_user_activity(user_id, "TRANSFORM_TEXT", log_details)
        
        # If this is just a file upload without immediate transformation
        if request.files and not request.form.get('transform', False):
            # Return the extracted text without transformation
            return jsonify({
                'originalText': text,
                'message': 'File processed successfully'
            })
        
        # Detect font style if preservation is requested
        font_info = detect_font_style(text) if preserve_font else {}
        
        # Calculate original word count if target requested
        original_word_count = len(text.split()) if target_word_count else None
        
        # Create prompt for Gemini, including word count constraint if specified
        if target_word_count:
            prompt = f"""Rewrite the following text to sound more human. 
                     Add personal experiences, vary sentence structure, 
                     use colloquialisms, and make it engaging.
                     Use a {tone} tone.
                     
                     IMPORTANT: The output must be approximately {target_word_count} words (±100 words).
                     Current word count is approximately {original_word_count} words.
                     
                     IMPORTANT: Do not include any introductory phrases like "Here's your transformed text:" 
                     or concluding phrases like "I hope this helps!". Just provide the transformed content directly.
                     
                     Text to transform: {text}"""
        else:
            prompt = f"""Rewrite the following text to sound more human. 
                     Add personal experiences, vary sentence structure, 
                     use colloquialisms, and make it engaging.
                     Use a {tone} tone.
                     
                     IMPORTANT: Do not include any introductory phrases like "Here's your transformed text:" 
                     or concluding phrases like "I hope this helps!". Just provide the transformed content directly.
                     
                     Text to transform: {text}"""
        
        # Call Gemini API with new client pattern
        response = genai_client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        transformed_text = response.text
        
        # Clean the LLM response to remove any prefacing or concluding meta-text
        transformed_text = clean_llm_response(transformed_text)
        
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
                        'wordCount': original_word_count,
                        'targetWordCount': target_word_count,
                        'sourceType': 'file' if request.files else 'paste',
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
        
        return jsonify({
            'transformedText': transformed_text, 
            'fontInfo': font_info,
            'originalText': text
        })
    
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
    # Check if already logged in
    if 'logged_in' in session and session['logged_in'] == True:
        add_system_log("Already authenticated user attempting to log in, redirecting to home", "INFO")
        return redirect('/')
    
    # Log the login attempt
    add_system_log("Login attempt initiated, redirecting to Auth0", "INFO")
    
    # Make sure to clear any leftover session data
    session.clear()
    
    # Redirect to Auth0 for authentication
    return auth0.authorize_redirect(
        redirect_uri=url_for('callback', _external=True)
    )

@app.route('/api/auth/callback')
def callback():
    try:
        # Get the auth0 token
        auth0.authorize_access_token()
        resp = auth0.get('userinfo')
        userinfo = resp.json()
        
        add_system_log(f"[AUTH CALLBACK] Auth0 callback received for user: {userinfo.get('email', 'Unknown')}")
        
        # Clear and regenerate session for security
        session.clear()
        
        # Set session to permanent
        session.permanent = True
        
        # Store user info in session
        session['jwt_payload'] = userinfo
        session['profile'] = {
            'user_id': userinfo['sub'],
            'name': userinfo.get('name', ''),
            'picture': userinfo.get('picture', ''),
            'email': userinfo.get('email', '')
        }
        session['logged_in'] = True
        session['auth_time'] = datetime.datetime.now().timestamp()
        
        # Add a session ID for tracking
        session['session_id'] = str(uuid.uuid4())
        
        # Ensure session is saved immediately
        session.modified = True
        
        # Log the successful authentication
        add_system_log(f"[AUTH CALLBACK] User authenticated: {userinfo.get('name', 'Unknown')} ({userinfo.get('email', 'No email')})")
        add_system_log(f"[AUTH CALLBACK] Session data after authentication: {dict(session)}")
        add_system_log(f"[AUTH CALLBACK] Session ID: {id(session)}")
        
        # Handle user record in database if configured
        if users_collection:
            try:
                # Check if user exists
                user = users_collection.find_one({'auth0_id': userinfo['sub']})
                
                # If not, create user record
                if not user:
                    new_user = {
                        'auth0_id': userinfo['sub'],
                        'email': userinfo.get('email', ''),
                        'name': userinfo.get('name', ''),
                        'created_at': datetime.datetime.now(),
                        'last_login': datetime.datetime.now()
                    }
                    users_collection.insert_one(new_user)
                    add_system_log(f"New user created: {userinfo.get('email', 'No email')}")
                else:
                    # Update last login
                    users_collection.update_one(
                        {'auth0_id': userinfo['sub']},
                        {'$set': {'last_login': datetime.datetime.now()}}
                    )
            except Exception as e:
                add_system_log(f"Error updating user record: {str(e)}", "ERROR")
        
        # Debug log to trace the issue
        add_system_log(f"[AUTH CALLBACK] Authentication complete, redirecting to home page", "INFO")
        
        # Instead of complex JavaScript, just directly redirect to avoid issues
        return redirect("/")
    except Exception as e:
        add_system_log(f"[AUTH CALLBACK] Auth0 callback error: {str(e)}", "ERROR")
        return redirect('/login?error=callback_failed')

@app.route('/api/auth/logout')
def logout():
    # Clear session
    session.clear()
    
    # Log the logout
    add_system_log("User logged out")
    
    # Check if full Auth0 logout is required
    full_logout = request.args.get('full_logout', 'false').lower() == 'true'
    
    if full_logout:
        # Build the logout URL for Auth0
        params = {
            'returnTo': url_for('logout_page', _external=True),
            'client_id': os.getenv('AUTH0_CLIENT_ID')
        }
        logout_url = f"https://{os.getenv('AUTH0_DOMAIN')}/v2/logout?" + urlencode(params)
        return redirect(logout_url)
    else:
        # Just redirect to logout page
        return redirect('/logout')

@app.route('/api/document/generate', methods=['POST'])
def generate_document():
    try:
        # Get request data from JSON
        data = request.get_json() if request.is_json else {}
        text = data.get('text', '')
        format_type = data.get('fileType', 'pdf')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Generate document based on file type
        if format_type == 'pdf':
            return generate_pdf(text)
        elif format_type == 'doc':
            return generate_docx(text)
        elif format_type == 'odt':
            return generate_odt(text)
        else:
            return jsonify({'error': f'Unsupported file type: {format_type}'}), 400
    
    except Exception as e:
        error_msg = f"Error generating document: {str(e)}"
        print(error_msg)
        add_system_log(error_msg, "ERROR")
        return jsonify({'error': 'Failed to generate document'}), 500

def generate_pdf(text):
    """Generate a PDF document from text"""
    try:
        # Create a bytes buffer for the PDF
        buffer = io.BytesIO()
        
        # Create the PDF with ReportLab
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Set up font and margins
        pdf.setFont("Helvetica", 12)
        margin = 72  # 1 inch margins
        text_width = width - 2 * margin
        y_position = height - margin
        
        # Process the text and add to PDF
        lines = text.split('\n')
        for line in lines:
            # Use ReportLab's wrap functionality to handle line breaks
            text_object = pdf.beginText(margin, y_position)
            text_object.setFont("Helvetica", 12)
            
            # If it's a blank line, move down
            if not line.strip():
                y_position -= 20
                continue
                
            # Wrap text to fit within margins
            wrapped_text = [line[i:i+80] for i in range(0, len(line), 80)]
            
            for wrap in wrapped_text:
                text_object.textLine(wrap)
                y_position -= 15
                
                # Check if we need a new page
                if y_position < margin:
                    pdf.drawText(text_object)
                    pdf.showPage()
                    pdf.setFont("Helvetica", 12)
                    y_position = height - margin
                    text_object = pdf.beginText(margin, y_position)
                    text_object.setFont("Helvetica", 12)
            
            pdf.drawText(text_object)
        
        # Save the PDF
        pdf.save()
        
        # Move the buffer position to the beginning
        buffer.seek(0)
        
        # Return the PDF as a response
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='mr-wlah-transformed.pdf'
        )
    
    except Exception as e:
        error_msg = f"PDF generation error: {str(e)}"
        add_system_log(error_msg, "ERROR")
        return jsonify({'error': error_msg}), 500

def generate_docx(text):
    """Generate a DOCX document from text"""
    try:
        # Create a new Document
        doc = docx.Document()
        
        # Add title
        title = doc.add_heading('Mr. Wlah Transformed Text', 0)
        title.alignment = 1  # Center alignment
        
        # Add paragraphs
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                p = doc.add_paragraph()
                p.add_run(para).font.size = Pt(12)
        
        # Save to a BytesIO object
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        # Return the document as a response
        return send_file(
            buffer,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name='mr-wlah-transformed.docx'
        )
    
    except Exception as e:
        error_msg = f"DOCX generation error: {str(e)}"
        add_system_log(error_msg, "ERROR")
        return jsonify({'error': error_msg}), 500

def generate_odt(text):
    """Generate an ODT document from text"""
    try:
        # For ODT format, we'll convert from DOCX
        # First create a DOCX document
        doc = docx.Document()
        
        # Add title
        title = doc.add_heading('Mr. Wlah Transformed Text', 0)
        title.alignment = 1  # Center alignment
        
        # Add paragraphs
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                p = doc.add_paragraph()
                p.add_run(para).font.size = Pt(12)
        
        # Save to a temporary file
        temp_docx = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        doc.save(temp_docx.name)
        temp_docx.close()
        
        # Use a third-party conversion like LibreOffice (in a production environment)
        # For this implementation, we'll return a DOCX file with a message
        with open(temp_docx.name, 'rb') as file:
            docx_data = file.read()
        
        # Clean up the temporary file
        os.unlink(temp_docx.name)
        
        # Prepare the response
        buffer = io.BytesIO(docx_data)
        
        # Return the document
        return send_file(
            buffer,
            mimetype='application/vnd.oasis.opendocument.text',
            as_attachment=True,
            download_name='mr-wlah-transformed.odt'
        )
    
    except Exception as e:
        error_msg = f"ODT generation error: {str(e)}"
        add_system_log(error_msg, "ERROR")
        return jsonify({'error': error_msg}), 500

@app.route('/api/auth/status')
def auth_status():
    """Endpoint to check if user is authenticated"""
    is_authenticated = 'logged_in' in session and session['logged_in']
    
    # Add diagnostic logging
    add_system_log(f"[AUTH STATUS] Auth status check - is_authenticated: {is_authenticated}, session ID: {id(session)}")
    if 'profile' in session:
        profile = session.get('profile', {})
        add_system_log(f"[AUTH STATUS] User in session: {profile.get('name', 'Unknown')}")
    
    if is_authenticated:
        profile = session.get('profile', {})
        add_system_log(f"[AUTH STATUS] Returning authenticated status for user: {profile.get('name', 'Unknown')}")
        
        # Ensure session data persists
        session.modified = True
        
        return jsonify({
            'isAuthenticated': True,
            'user': {
                'name': profile.get('name', ''),
                'email': profile.get('email', ''),
                'picture': profile.get('picture', ''),
                'userId': profile.get('user_id', '')  # Include user ID for API calls
            }
        })
    else:
        add_system_log("[AUTH STATUS] Returning unauthenticated status")
        return jsonify({
            'isAuthenticated': False
        })

@app.route('/api/config')
def client_config():
    """Endpoint to provide client-side configuration"""
    return jsonify({
        'auth0': {
            'domain': os.getenv('AUTH0_DOMAIN'),
            'clientId': os.getenv('AUTH0_CLIENT_ID'),
            'audience': os.getenv('AUTH0_AUDIENCE', 'https://api.mrwlah.com'),
            'callbackUrl': f"{request.host_url.rstrip('/')}/api/auth/callback"
        },
        'app': {
            'environment': os.getenv('FLASK_ENV', 'production'),
            'apiBaseUrl': '/api'
        }
    })

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