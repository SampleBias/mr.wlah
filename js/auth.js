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
    }
    
    // This would be the actual Auth0 initialization in production
    /*
    auth0Client = await createAuth0Client({
        domain: auth0Config.domain,
        clientId: auth0Config.clientId,
        authorizationParams: {
            redirect_uri: auth0Config.redirectUri,
            audience: auth0Config.audience
        },
        cacheLocation: auth0Config.cacheLocation
    });
    */
    
    // For demo purposes, simulate Auth0 client
    auth0Client = {
        isAuthenticated: async () => {
            return localStorage.getItem('demo_is_authenticated') === 'true';
        },
        loginWithRedirect: async () => {
            console.log('Would redirect to Auth0 login in production');
            // Simulate successful login for demo
            localStorage.setItem('demo_is_authenticated', 'true');
            localStorage.setItem('demo_user', JSON.stringify({
                name: 'Demo User',
                email: 'demo@example.com',
                picture: 'https://via.placeholder.com/50'
            }));
            // Refresh the page to simulate redirect back
            setTimeout(() => window.location.reload(), 1000);
        },
        logout: async () => {
            console.log('Would logout from Auth0 in production');
            localStorage.removeItem('demo_is_authenticated');
            localStorage.removeItem('demo_user');
            // Refresh the page to simulate redirect back
            setTimeout(() => window.location.reload(), 1000);
        },
        getUser: async () => {
            return JSON.parse(localStorage.getItem('demo_user')) || null;
        },
        getTokenSilently: async () => {
            return 'demo_token_' + Math.random().toString(36).substring(2);
        }
    };
    
    updateUI();
}

// Update UI based on authentication state
async function updateUI() {
    const isAuthenticated = await auth0Client.isAuthenticated();
    const loginBtn = document.getElementById('login-btn');
    
    if (isAuthenticated) {
        const user = await auth0Client.getUser();
        loginBtn.textContent = 'Logout';
        loginBtn.onclick = () => logout();
        
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
        await auth0Client.logout({
            logoutParams: {
                returnTo: window.location.origin
            }
        });
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