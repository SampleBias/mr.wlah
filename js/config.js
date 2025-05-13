/**
 * Configuration file for Mr. Wlah application
 * 
 * In a production environment, these values are loaded from environment variables
 * on the server and then securely passed to the client.
 */

// Configuration object for the application
const config = {
    // Google Gemini API configuration
    gemini: {
        apiKey: process.env.GEMINI_API_KEY || 'YOUR_GEMINI_API_KEY', 
        apiUrl: 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'
    },
    
    // Auth0 configuration
    auth0: {
        domain: process.env.AUTH0_DOMAIN || 'YOUR_AUTH0_DOMAIN',
        clientId: process.env.AUTH0_CLIENT_ID || 'YOUR_AUTH0_CLIENT_ID',
        audience: process.env.AUTH0_AUDIENCE || 'https://api.mrwlah.com',
        callbackUrl: process.env.AUTH0_CALLBACK_URL || window.location.origin
    },
    
    // MongoDB configuration
    mongodb: {
        uri: process.env.MONGODB_URI || 'mongodb://localhost:27017/mrwlah',
        database: process.env.MONGODB_DATABASE || 'mrwlah'
    },
    
    // Application settings
    app: {
        environment: process.env.NODE_ENV || 'development',
        port: process.env.PORT || 3000,
        apiBaseUrl: process.env.API_BASE_URL || '/api'
    }
};

// Default configuration (will be overridden with server values)
let clientConfig = {
    auth0: {
        domain: '',
        clientId: '',
        audience: 'https://api.mrwlah.com',
        callbackUrl: window.location.origin + '/api/auth/callback'
    },
    app: {
        environment: 'development',
        apiBaseUrl: '/api'
    }
};

// Function to fetch configuration from the server
async function loadServerConfig() {
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            const config = await response.json();
            // Update client config with server values
            clientConfig = config;
            console.log('Server configuration loaded successfully');
            
            // Make it available globally
            window.MrWlahConfig = clientConfig;
            
            // Dispatch event to notify that config is loaded
            window.dispatchEvent(new CustomEvent('mrwlah-config-loaded'));
        } else {
            console.error('Failed to load server configuration');
        }
    } catch (error) {
        console.error('Error loading server configuration:', error);
    }
}

// In a browser environment, expose the client configuration
if (typeof window !== 'undefined') {
    window.MrWlahConfig = clientConfig;
    
    // Load configuration from server when the page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadServerConfig);
    } else {
        loadServerConfig();
    }
}

// In a Node.js environment, export the configuration
if (typeof module !== 'undefined' && module.exports) {
    module.exports = clientConfig;
} 