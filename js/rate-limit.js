/**
 * Donation popup functionality for Mr. Wlah application
 * Shows a donation request popup on login
 */

// DOM Elements for donation modal
const donationModal = document.getElementById('donation-modal');
const closeDonationButton = document.querySelector('.close-donation');
const maybeLaterButton = document.getElementById('maybe-later-btn');

// Flag to track if donation popup has been shown this session
let donationPopupShown = sessionStorage.getItem('donationPopupShown') === 'true';

/**
 * Initialize the donation popup functionality
 */
function initDonationPopup() {
    // Set up event listeners for modal
    setupDonationModalListeners();
    
    console.log('[Donation] Donation popup system initialized');
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
        const oneWeek = 7 * 24 * 60 * 60 * 1000; // 7 days in milliseconds
        
        // Show if never shown or if more than a week has passed
        if (!lastShown || (now - parseInt(lastShown)) > oneWeek) {
            setTimeout(() => {
                showDonationPopup();
                localStorage.setItem('donationPopupLastShown', now.toString());
            }, 1500); // Show after 1.5 second delay
        } else {
            console.log('[Donation] Donation popup was shown recently, skipping');
        }
    }
}

/**
 * Show the donation modal
 */
function showDonationPopup() {
    if (donationModal) {
        donationModal.style.display = 'block';
        donationPopupShown = true;
        sessionStorage.setItem('donationPopupShown', 'true');
        console.log('[Donation] Showing donation popup');
    }
}

/**
 * Hide the donation modal
 */
function hideDonationPopup() {
    if (donationModal) {
        donationModal.style.display = 'none';
        console.log('[Donation] Donation popup closed');
    }
}

/**
 * Set up event listeners for the donation modal
 */
function setupDonationModalListeners() {
    // Close button
    if (closeDonationButton) {
        closeDonationButton.addEventListener('click', hideDonationPopup);
    }
    
    // Maybe later button
    if (maybeLaterButton) {
        maybeLaterButton.addEventListener('click', hideDonationPopup);
    }
    
    // Click outside modal to close
    if (donationModal) {
        donationModal.addEventListener('click', (event) => {
            if (event.target === donationModal) {
                hideDonationPopup();
            }
        });
    }
}

/**
 * Initialize donation popup on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    initDonationPopup();
    
    // Note: Donation popup will be triggered by auth.js when user logs in
    console.log('[Donation] Donation popup system ready');
});

// Export functions for use in other scripts
window.showDonationPopup = showDonationPopup;
window.hideDonationPopup = hideDonationPopup;
window.showDonationPopupOnLogin = showDonationPopupOnLogin; 