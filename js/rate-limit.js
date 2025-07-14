/**
 * Donation popup functionality for Mr. Wlah application
 * Shows a donation request popup on login
 */

// DOM Elements for donation modal - will be initialized when DOM is ready
let donationModal = null;
let closeDonationButton = null;
let maybeLaterButton = null;

// Flag to track if donation popup has been shown this session
let donationPopupShown = false;

/**
 * Initialize the donation popup functionality
 */
function initDonationPopup() {
    // Get DOM elements
    donationModal = document.getElementById('donation-modal');
    closeDonationButton = document.querySelector('.close-donation');
    maybeLaterButton = document.getElementById('maybe-later-btn');
    
    // Verify main modal exists
    if (!donationModal) {
        return false;
    }
    
    // Check session storage
    const sessionShown = sessionStorage.getItem('donationPopupShown');
    donationPopupShown = sessionShown === 'true';
    
    // Set up event listeners for modal
    setupDonationModalListeners();
    
    return true;
}

/**
 * Show the donation popup on login
 */
function showDonationPopupOnLogin() {
    // Only show if not already shown this session
    if (!donationPopupShown) {
        // Check if this is a fresh login (not just a page reload)
        const lastShown = localStorage.getItem('donationPopupLastShown');
        const now = Date.now();
        const oneDay = 24 * 60 * 60 * 1000; // 1 day in milliseconds
        
        // Show if never shown or if more than a day has passed
        if (!lastShown || (now - parseInt(lastShown)) > oneDay) {
            setTimeout(() => {
                showDonationPopup();
                localStorage.setItem('donationPopupLastShown', now.toString());
            }, 2000); // Show after 2 second delay
        }
    }
}

/**
 * Show the donation modal
 */
function showDonationPopup() {
    if (!donationModal) {
        return false;
    }
    
    donationModal.style.display = 'block';
    donationPopupShown = true;
    sessionStorage.setItem('donationPopupShown', 'true');
    
    // Add smooth transition
    setTimeout(() => {
        if (donationModal) {
            donationModal.style.opacity = '1';
        }
    }, 100);
    
    return true;
}

/**
 * Hide the donation modal
 */
function hideDonationPopup() {
    if (donationModal) {
        donationModal.style.display = 'none';
        donationModal.style.opacity = '0';
    }
}

/**
 * Set up event listeners for the donation modal
 */
function setupDonationModalListeners() {
    // Close button
    if (closeDonationButton) {
        closeDonationButton.addEventListener('click', (e) => {
            e.preventDefault();
            hideDonationPopup();
        });
    }
    
    // Maybe later button
    if (maybeLaterButton) {
        maybeLaterButton.addEventListener('click', (e) => {
            e.preventDefault();
            hideDonationPopup();
        });
    }
    
    // Click outside modal to close
    if (donationModal) {
        donationModal.addEventListener('click', (event) => {
            if (event.target === donationModal) {
                hideDonationPopup();
            }
        });
    }
    
    // ESC key to close
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && donationModal && donationModal.style.display === 'block') {
            hideDonationPopup();
        }
    });
}

/**
 * Force show donation popup (for testing)
 */
function forceShowDonationPopup() {
    // Reset session storage
    sessionStorage.removeItem('donationPopupShown');
    localStorage.removeItem('donationPopupLastShown');
    donationPopupShown = false;
    
    // Show immediately
    showDonationPopup();
}

/**
 * Initialize donation popup on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit to ensure all scripts are loaded
    setTimeout(() => {
        initDonationPopup();
    }, 500);
});

// Export functions for use in other scripts
window.showDonationPopup = showDonationPopup;
window.hideDonationPopup = hideDonationPopup;
window.showDonationPopupOnLogin = showDonationPopupOnLogin;
window.forceShowDonationPopup = forceShowDonationPopup; // For testing 