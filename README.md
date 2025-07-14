# Mr. Wlah (Write Like A Human)

Mr. Wlah is a Flask application that transforms AI-generated content into human-like text by incorporating personal experience, emotion, and natural language patterns.

## Features

- Transform AI-generated content into human-like text
- Upload .txt, .pdf, or .doc files or paste text directly
- Choose from multiple writing tones (Scientific, Educational, Engaging, etc.)
- Preserve original font styling in transformed content
- Download or copy transformed content
- Minimalist, futuristic design with pixel typography
- Powered by Google Gemini 2.5 Pro AI model
- User authentication via Auth0
- Data storage with MongoDB

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   # Quick install with a single command:
   ./install_dependencies.sh
   
   # Or manually:
   pip install --upgrade pip
   pip install -q -U google-genai
   pip install -U -r requirements.txt
   ```
3. Set up MongoDB X.509 certificate (see [MongoDB Setup](#mongodb-setup) below)
4. Configure environment variables
5. Run the application:
   ```bash
   ./run.sh
   ```

## Environment Configuration

To run the application, you'll need to set up the following environment variables:

### Google Gemini API

- `GEMINI_API_KEY`: Your Google Gemini API key for text transformation
- `GEMINI_MODEL`: The Gemini model to use (default: gemini-2.5-pro)

### Auth0 Configuration

- `AUTH0_DOMAIN`: Your Auth0 tenant domain (e.g., `your-tenant.auth0.com`)
- `AUTH0_CLIENT_ID`: Your Auth0 client ID
- `AUTH0_AUDIENCE`: API identifier for Auth0 (e.g., `https://api.mrwlah.com`)
- `AUTH0_CALLBACK_URL`: Callback URL for Auth0 authentication

### MongoDB Configuration

- `MONGODB_URI`: URI for connecting to your MongoDB instance
- `MONGODB_DATABASE`: Name of the MongoDB database to use

Example URI format for MongoDB Atlas with X.509 authentication:
```
MONGODB_URI=mongodb+srv://benchai.3cq4b8o.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=MrWlah
```

### Application Settings

- `NODE_ENV`: Environment mode (`development`, `test`, or `production`)
- `PORT`: Port to run the application on

Create a `.env` file in the root directory of the project with these variables. For security, this file should never be committed to version control.

## MongoDB Setup

The application uses MongoDB with X.509 certificate authentication. To set up MongoDB:

1. Place your X.509 certificate in the `certs` directory with the filename `X509-cert-5870665680541743449.pem`
2. Update your `.env` file with the correct MongoDB URI (see example format above)
3. Test the connection using one of the provided scripts:

```bash
# Interactive setup and testing:
python setup_mongodb.py

# Simple connection verification:
python verify_mongodb.py

# Test BenchAI database connection specifically:
python test_benchai_connection.py
```

For more details on certificate setup, see the README in the `certs` directory.

## Tech Stack

- Frontend: HTML/CSS/JavaScript
- Backend: Python/Flask
- AI: Google Gemini API
- Authentication: Auth0
- Database: MongoDB
