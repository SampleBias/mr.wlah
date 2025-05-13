// Auth0 Configuration
let auth0Config = {
    domain: '',
    clientId: '',
    redirectUri: window.location.origin,
    audience: '',
    cacheLocation: 'localstorage'
};

let auth0Client = null;

// Initialize Auth0 Client
async function initAuth0() {
    // Load configuration from MrWlahConfig if available
    if (window.MrWlahConfig && window.MrWlahConfig.auth0) {
        auth0Config = {
            domain: window.MrWlahConfig.auth0.domain,
            clientId: window.MrWlahConfig.auth0.clientId,
            redirectUri: window.MrWlahConfig.auth0.callbackUrl,
            audience: window.MrWlahConfig.auth0.audience,
            cacheLocation: 'localstorage'
        };
        
        // Store for logout purposes
        localStorage.setItem('auth0Domain', auth0Config.domain);
        localStorage.setItem('auth0ClientId', auth0Config.clientId);
    }
    
    // Initialize actual Auth0 client
    try {
        console.log('Initializing Auth0 client with:', {
            domain: auth0Config.domain,
            clientId: auth0Config.clientId,
            redirectUri: auth0Config.redirectUri
        });
        
        auth0Client = await createAuth0Client({
            domain: auth0Config.domain,
            clientId: auth0Config.clientId,
            authorizationParams: {
                redirect_uri: auth0Config.redirectUri,
                audience: auth0Config.audience
            },
            cacheLocation: auth0Config.cacheLocation
        });
        
        console.log('Auth0 client initialized successfully');
        
        // Check if we're handling a callback
        if (window.location.search.includes("code=") && window.location.search.includes("state=")) {
            console.log('Handling Auth0 callback');
            try {
                await auth0Client.handleRedirectCallback();
                // Handle successful login
                window.history.replaceState({}, document.title, window.location.pathname); // Remove query params
                console.log('Auth0 callback handled successfully');
            } catch (callbackErr) {
                console.error('Error handling callback:', callbackErr);
            }
        }
    } catch (initError) {
        console.error('Error initializing Auth0 client:', initError);
        
        // Fall back to demo client if initialization fails
        auth0Client = {
            isAuthenticated: async () => {
                return localStorage.getItem('demo_is_authenticated') === 'true';
            },
            loginWithRedirect: async () => {
                console.log('Fallback: Would redirect to Auth0 login in production');
                // Direct server-side login as backup
                window.location.href = '/api/auth/login';
            },
            logout: async () => {
                console.log('Fallback: Would logout from Auth0 in production');
                localStorage.removeItem('demo_is_authenticated');
                localStorage.removeItem('demo_user');
                window.location.href = '/api/auth/logout?full_logout=true';
            },
            getUser: async () => {
                return JSON.parse(localStorage.getItem('demo_user')) || null;
            },
            getTokenSilently: async () => {
                return 'demo_token_' + Math.random().toString(36).substring(2);
            }
        };
    }
    
    updateUI();
}

// Update UI based on authentication state
async function updateUI() {
    const isAuthenticated = await auth0Client.isAuthenticated();
    const loginBtn = document.getElementById('login-btn');
    
    // Skip if on login page
    if (!loginBtn) return;
    
    if (isAuthenticated) {
        const user = await auth0Client.getUser();
        loginBtn.textContent = 'Logout';
        loginBtn.onclick = (e) => {
            e.preventDefault();
            logout();
        };
        
        // Create a user profile element if it doesn't exist
        if (!document.getElementById('user-profile')) {
            const headerNav = document.querySelector('nav ul');
            const profileItem = document.createElement('li');
            profileItem.innerHTML = `
                <div id="user-profile" class="user-profile">
                    <img src="${user.picture}" alt="${user.name}" class="profile-pic">
                    <span>${user.name}</span>
                </div>
            `;
            headerNav.prepend(profileItem);
            
            // Add styles for the user profile
            const style = document.createElement('style');
            style.textContent = `
                .user-profile {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 5px;
                    border: 1px solid var(--primary-color);
                    border-radius: 4px;
                }
                .profile-pic {
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    border: 1px solid var(--primary-color);
                }
            `;
            document.head.appendChild(style);
        }
    } else {
        loginBtn.textContent = 'Login';
        loginBtn.onclick = () => login();
        
        // Remove user profile if it exists
        const userProfile = document.getElementById('user-profile');
        if (userProfile) {
            userProfile.parentNode.remove();
        }
    }
}

// Login with Auth0
async function login() {
    try {
        console.log('Logging in...');
        await auth0Client.loginWithRedirect();
    } catch (error) {
        console.error('Login error:', error);
    }
}

// Logout from Auth0
async function logout() {
    try {
        console.log('Logging out...');
        // For API-based logout with full Auth0 logout
        window.location.href = '/api/auth/logout?full_logout=true';
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Get access token for API calls
async function getAccessToken() {
    try {
        return await auth0Client.getTokenSilently();
    } catch (error) {
        console.error('Error getting token:', error);
        return null;
    }
}

// Initialize Auth0 when the page loads
document.addEventListener('DOMContentLoaded', initAuth0);

// For MongoDB API requests with authentication
async function callSecureApi(url, method = 'GET', data = null) {
    try {
        const token = await getAccessToken();
        if (!token) throw new Error('Failed to get access token');
        
        const options = {
            method,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        if (!response.ok) throw new Error('API request failed');
        
        return await response.json();
    } catch (error) {
        console.error('API error:', error);
        throw error;
    }
} 