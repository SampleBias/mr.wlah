/**
 * Configuration file for Mr. Wlah application
 * 
 * In a production environment, these values would be loaded from environment variables
 * using a .env file or environment variables set on the server.
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

/**
 * For client-side applications, you would typically only expose 
 * a subset of these configurations that are safe for client exposure.
 * Sensitive keys like database URIs should remain server-side only.
 */
const clientConfig = {
    gemini: {
        apiUrl: config.gemini.apiUrl
    },
    auth0: {
        domain: config.auth0.domain,
        clientId: config.auth0.clientId,
        audience: config.auth0.audience,
        callbackUrl: config.auth0.callbackUrl
    },
    app: {
        environment: config.app.environment,
        apiBaseUrl: config.app.apiBaseUrl
    }
};

// In a browser environment, expose only the client configuration
if (typeof window !== 'undefined') {
    window.MrWlahConfig = clientConfig;
}

// In a Node.js environment, export the full configuration
if (typeof module !== 'undefined' && module.exports) {
    module.exports = config;
} 