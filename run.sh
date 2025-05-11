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
MONGODB_URI=mongodb://localhost:27017/mrwlah
MONGODB_DATABASE=mrwlah

# Application Settings
NODE_ENV=development
PORT=3000
EOF
    echo ""
    echo "⚠️  Please edit the .env file with your actual credentials before running the application."
    echo ""
fi

# Check for MongoDB certificate
CERT_PATH="certs/X509-cert-5870665680541743449.pem"
if [ ! -f "$CERT_PATH" ] && [ -f "$CERT_PATH.sample" ]; then
    echo ""
    echo "⚠️  MongoDB X.509 certificate not found!"
    echo "If you're using X.509 authentication, please place your certificate at:"
    echo "   $CERT_PATH"
    echo "A sample file is available at $CERT_PATH.sample"
    echo ""
fi

# Initialize database
echo "Initializing Mr. Wlah database..."
python init_database.py

# Check if database initialization was successful
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Database initialization may have failed."
    echo "The application will still start, but some features might not work correctly."
    echo ""
fi

# Start the application
echo "Starting Mr. Wlah application..."
python app.py 