#!/bin/bash

# Mr. Wlah (Write Like A Human) - Application Setup and Run Script

# Ensure script stops on errors
set -e

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not found. Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is required but not found. Please install pip and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install requirements
echo "Installing dependencies..."
pip install -U -r requirements.txt

# Check if .env file exists, create example if not
if [ ! -f ".env" ]; then
    echo "Creating example .env file..."
    cat > .env << EOF
# Mr. Wlah (Write Like A Human) - Environment Variables

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Auth0 Configuration
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your_auth0_client_id_here
AUTH0_CLIENT_SECRET=your_auth0_client_secret_here
AUTH0_AUDIENCE=https://api.mrwlah.com
AUTH0_CALLBACK_URL=http://localhost:3000/api/auth/callback

# MongoDB Connection
MONGODB_URI=mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=MrWlah
MONGODB_DATABASE=benchai

# Application Settings
NODE_ENV=development
PORT=3000
EOF
    echo ""
    echo "⚠️  Please edit the .env file with your actual credentials before running the application."
    echo ""
fi

# Create certs directory if it doesn't exist
if [ ! -d "certs" ]; then
    echo "Creating certs directory..."
    mkdir -p certs
fi

# Check for MongoDB certificate
CERT_PATH="certs/X509-cert-5870665680541743449.pem"
if [ ! -f "$CERT_PATH" ]; then
    echo ""
    echo "⚠️  MongoDB X.509 certificate not found!"
    echo "Please place your X.509 certificate at:"
    echo "   $CERT_PATH"
    echo ""
    echo "For database access, you need to have a valid certificate."
    read -p "Would you like to continue without the certificate? (y/n): " continue_without_cert
    
    if [[ "$continue_without_cert" != "y" && "$continue_without_cert" != "Y" ]]; then
        echo "Exiting. Please add the certificate and run again."
        exit 1
    fi
    
    echo "Continuing without certificate. Database features will not work."
    echo ""
fi

# Update MongoDB connection settings
echo "Updating MongoDB connection settings..."
python update_env_for_benchai.py

# Initialize BenchAI database for Mr. Wlah
if [ -f "$CERT_PATH" ]; then
    echo "Initializing BenchAI database for Mr. Wlah..."
    python initialize_benchai_db.py
    
    # Check if database initialization was successful
    if [ $? -ne 0 ]; then
        echo "⚠️  Warning: BenchAI database initialization failed."
        echo "The application will still start, but database features might not work correctly."
        echo ""
    else
        echo "✅ BenchAI database initialized successfully!"
        
        # Verify logs collection
        echo "Verifying logs collection..."
        python check_logs.py > /dev/null
        
        if [ $? -ne 0 ]; then
            echo "⚠️  Warning: Logs collection verification failed."
        else
            echo "✅ Logs collection verified!"
        fi
    fi
else
    # If no certificate, try to use local MongoDB (fallback)
    echo "Initializing local database (fallback)..."
    python init_database.py
    
    if [ $? -ne 0 ]; then
        echo "⚠️  Warning: Local database initialization may have failed."
        echo "The application will still start, but some features might not work correctly."
        echo ""
    fi
fi

# Start the application
echo ""
echo "Starting Mr. Wlah application..."
python app.py 