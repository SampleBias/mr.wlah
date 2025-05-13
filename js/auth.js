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
    
    // Get the current page
    const currentPage = window.location.pathname;
    
    // Skip auth check on index.html since it has its own check and redirect
    if (currentPage === '/' || currentPage === '/index.html') {
        return;
    }
    
    // Check if this is the login page
    const isLoginPage = currentPage === '/login' || currentPage.includes('login.html');
    
    try {
        // Query authentication status from server
        const response = await fetch('/api/auth/status');
        if (response.ok) {
            const authStatus = await response.json();
            console.log('Auth status from server:', authStatus);
            
            if (authStatus.isAuthenticated) {
                // User is authenticated
                
                // If on login page, redirect to home
                if (isLoginPage) {
                    console.log('User is authenticated on login page, redirecting to home');
                    window.location.href = '/';
                    return;
                }
                
                // Update UI with server-provided user info
                updateUIWithServerAuth(authStatus.user);
            } else {
                // Not authenticated, update UI
                updateUIUnauthenticated();
                
                // If on index.html (main app) and not authenticated, redirect to login
                if (currentPage === '/' || currentPage === '/index.html') {
                    console.log('Not authenticated on main app, redirecting to login');
                    window.location.href = '/login';
                }
            }
        }
    } catch (statusError) {
        console.error('Error checking server auth status:', statusError);
    }
}

// Update UI when authenticated via server
function updateUIWithServerAuth(user) {
    const loginBtn = document.getElementById('login-btn');
    if (!loginBtn) return;
    
    loginBtn.textContent = 'Logout';
    loginBtn.href = '/api/auth/logout';
    loginBtn.onclick = (e) => {
        e.preventDefault();
        logout();
    };
    
    // Create a user profile element if it doesn't exist
    if (!document.getElementById('user-profile') && user) {
        const headerNav = document.querySelector('nav ul');
        if (headerNav) {
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
    }
}

// Update UI when not authenticated
function updateUIUnauthenticated() {
    const loginBtn = document.getElementById('login-btn');
    if (!loginBtn) return;
    
    loginBtn.textContent = 'Login';
    loginBtn.href = '/api/auth/login';
    loginBtn.onclick = (e) => {
        e.preventDefault();
        login();
    };
    
    // Remove user profile if it exists
    const userProfile = document.getElementById('user-profile');
    if (userProfile && userProfile.parentNode) {
        userProfile.parentNode.remove();
    }
}

// Login with Auth0
async function login() {
    try {
        console.log('Logging in...');
        // Use server-side login flow
        window.location.href = '/api/auth/login';
    } catch (error) {
        console.error('Login error:', error);
    }
}

// Logout from Auth0
async function logout() {
    try {
        console.log('Logging out...');
        // Use server-side logout
        window.location.href = '/api/auth/logout?full_logout=true';
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Get access token for API calls
async function getAccessToken() {
    try {
        // Get auth status from server
        const response = await fetch('/api/auth/status');
        if (response.ok) {
            const authStatus = await response.json();
            if (authStatus.isAuthenticated) {
                // Could implement token retrieval from server if needed
                return 'server_auth_token';
            }
        }
        return null;
    } catch (error) {
        console.error('Error getting token:', error);
        return null;
    }
}

// Initialize Auth0 when the page loads
document.addEventListener('DOMContentLoaded', initAuth0);

// For API requests with authentication
async function callSecureApi(url, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include' // Include session cookies
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