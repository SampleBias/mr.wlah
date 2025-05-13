/**
 * Rate limiting functionality for Mr. Wlah application
 * Controls usage limits and subscription prompts
 */

// Configuration for rate limits based on subscription tiers
const RATE_LIMITS = {
    FREE: 2,               // Free tier: 2 transformations total
    BASIC: 10,             // Basic plan: 10 transformations per month
    PRO: 25,               // Pro plan: 25 transformations per month
    UNLIMITED: Infinity    // Unlimited plan: No limit
};

// DOM Elements for subscription modal
const subscriptionModal = document.getElementById('subscription-modal');
const closeSubscriptionButton = document.querySelector('.close-subscription');
const usageCountDisplay = document.querySelector('.usage-count');

// Initialize rate limiting system
let currentUser = {
    subscription: 'FREE',
    usageCount: 0,
    usageLimit: RATE_LIMITS.FREE,
    lastResetDate: null
};

/**
 * Initialize the rate limiting functionality
 */
function initRateLimiting() {
    // Check for existing usage data in localStorage
    loadUserUsageData();
    
    // Add event listeners for modal
    setupSubscriptionModalListeners();
    
    // Hook into transform button
    hookTransformButton();
    
    console.log('[Rate Limit] System initialized with plan:', currentUser.subscription);
    console.log('[Rate Limit] Current usage:', currentUser.usageCount, '/', currentUser.usageLimit);
}

/**
 * Load user's usage data from localStorage or server
 */
function loadUserUsageData() {
    // Try to load from localStorage first (for demo/testing)
    const savedData = localStorage.getItem('mrwlah_user_usage');
    
    if (savedData) {
        try {
            const parsedData = JSON.parse(savedData);
            currentUser = {
                ...currentUser,
                ...parsedData
            };
            console.log('[Rate Limit] Loaded user data from storage:', currentUser);
        } catch (e) {
            console.error('[Rate Limit] Error parsing saved usage data:', e);
        }
    }
    
    // Otherwise, make server request to get current user info
    fetchUserSubscriptionInfo();
}

/**
 * Fetch subscription info from the server
 */
async function fetchUserSubscriptionInfo() {
    try {
        const response = await fetch('/api/user/subscription');
        if (response.ok) {
            const data = await response.json();
            
            // Update current user with server data
            if (data.subscription) {
                currentUser.subscription = data.subscription;
                currentUser.usageCount = data.usageCount || 0;
                currentUser.lastResetDate = data.lastResetDate;
                
                // Set usage limit based on subscription
                setUsageLimitFromSubscription(currentUser.subscription);
                
                // Save to localStorage for quick access
                saveUserUsageData();
                
                console.log('[Rate Limit] Updated user data from server:', currentUser);
            }
        }
    } catch (error) {
        console.error('[Rate Limit] Error fetching subscription info:', error);
    }
}

/**
 * Set usage limit based on subscription level
 */
function setUsageLimitFromSubscription(subscription) {
    switch (subscription.toUpperCase()) {
        case 'BASIC':
            currentUser.usageLimit = RATE_LIMITS.BASIC;
            break;
        case 'PRO':
            currentUser.usageLimit = RATE_LIMITS.PRO;
            break;
        case 'UNLIMITED':
            currentUser.usageLimit = RATE_LIMITS.UNLIMITED;
            break;
        default:
            currentUser.usageLimit = RATE_LIMITS.FREE;
    }
}

/**
 * Save user usage data to localStorage
 */
function saveUserUsageData() {
    localStorage.setItem('mrwlah_user_usage', JSON.stringify(currentUser));
}

/**
 * Hook into the transform button to check usage limits
 */
function hookTransformButton() {
    const transformBtn = document.getElementById('transform-btn');
    
    if (transformBtn) {
        // Store the original click listener
        const originalClickListener = transformBtn.onclick;
        
        // Replace with our rate-limited version
        transformBtn.onclick = function(event) {
            // Check if user has reached their limit
            if (hasReachedUsageLimit()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Show subscription modal
                showSubscriptionModal();
                return false;
            }
            
            // If not at limit, increment count and proceed
            incrementUsageCount();
            
            // Call original handler if it exists
            if (typeof originalClickListener === 'function') {
                return originalClickListener.call(this, event);
            }
        };
    }
}

/**
 * Check if user has reached their usage limit
 */
function hasReachedUsageLimit() {
    return currentUser.usageCount >= currentUser.usageLimit;
}

/**
 * Increment usage count
 */
function incrementUsageCount() {
    currentUser.usageCount++;
    
    // Record transformation in server
    recordTransformation();
    
    // Update local storage
    saveUserUsageData();
    
    console.log('[Rate Limit] Usage count incremented:', currentUser.usageCount, '/', currentUser.usageLimit);
}

/**
 * Record a transformation on the server
 */
async function recordTransformation() {
    try {
        await fetch('/api/user/record-transformation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                timestamp: new Date().toISOString()
            })
        });
    } catch (error) {
        console.error('[Rate Limit] Error recording transformation:', error);
    }
}

/**
 * Show the subscription modal
 */
function showSubscriptionModal() {
    // Update usage display
    updateUsageDisplay();
    
    // Show modal
    subscriptionModal.style.display = 'block';
}

/**
 * Update the usage display in the subscription modal
 */
function updateUsageDisplay() {
    if (usageCountDisplay) {
        usageCountDisplay.textContent = `${currentUser.usageCount}/${currentUser.usageLimit}`;
    }
}

/**
 * Set up event listeners for the subscription modal
 */
function setupSubscriptionModalListeners() {
    // Close button listener
    if (closeSubscriptionButton) {
        closeSubscriptionButton.addEventListener('click', () => {
            subscriptionModal.style.display = 'none';
        });
    }
    
    // Click outside modal to close
    window.addEventListener('click', (event) => {
        if (event.target === subscriptionModal) {
            subscriptionModal.style.display = 'none';
        }
    });
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', initRateLimiting); 