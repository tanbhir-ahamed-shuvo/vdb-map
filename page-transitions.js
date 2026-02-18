/**
 * Smooth Page Transitions Handler
 * Provides fade-in/fade-out animations and loading states
 */

// Create page transition overlay
function initPageTransitions() {
    // Create overlay element
    const overlay = document.createElement('div');
    overlay.id = 'page-transition-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        opacity: 0;
        pointer-events: none;
        z-index: 99999;
        transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    `;
    document.body.appendChild(overlay);

    // Create loading spinner
    const spinner = document.createElement('div');
    spinner.id = 'page-loading-spinner';
    spinner.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 50px;
        height: 50px;
        border: 4px solid rgba(255, 255, 255, 0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        opacity: 0;
        pointer-events: none;
        z-index: 100000;
        transition: opacity 0.3s ease;
    `;
    document.body.appendChild(spinner);

    // Add spinner animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            to { transform: translate(-50%, -50%) rotate(360deg); }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes slideInDown {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        body.page-entering {
            animation: fadeIn 0.5s ease-out forwards;
        }
        
        .transitions-enabled * {
            animation-fill-mode: both;
        }
    `;
    document.head.appendChild(style);
}

// Show page transition
function showPageTransition(callback) {
    const overlay = document.getElementById('page-transition-overlay');
    const spinner = document.getElementById('page-loading-spinner');
    
    if (overlay) overlay.style.opacity = '0.7';
    if (spinner) spinner.style.opacity = '1';
    
    if (callback) {
        setTimeout(callback, 200);
    }
    
    return () => hidePageTransition();
}

// Hide page transition
function hidePageTransition() {
    const overlay = document.getElementById('page-transition-overlay');
    const spinner = document.getElementById('page-loading-spinner');
    
    if (overlay) overlay.style.opacity = '0';
    if (spinner) spinner.style.opacity = '0';
}

// Navigate to page with transition
function navigateWithTransition(url, target = '_self') {
    const hide = showPageTransition();
    
    // Add slight delay for smooth effect
    setTimeout(() => {
        if (target === '_blank') {
            window.open(url, '_blank');
            hide();
        } else {
            window.location.href = url;
        }
    }, 300);
}

// Add fade-in animation to page on load
function fadeInPage() {
    document.body.classList.add('page-entering');
    hidePageTransition();
    
    // Animate main content elements
    const header = document.querySelector('.header');
    const sidebar = document.querySelector('.sidebar');
    const container = document.querySelector('.container');
    
    if (header) {
        header.style.animation = 'slideInDown 0.5s ease-out 0.1s backwards';
    }
    
    if (sidebar) {
        sidebar.style.animation = 'slideInUp 0.5s ease-out 0.2s backwards';
    }
    
    if (container && !header && !sidebar) {
        container.style.animation = 'fadeIn 0.5s ease-out';
    }
}

// Handle link clicks for smooth transitions
document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href]');
    
    if (link && !link.target && !link.hasAttribute('data-no-transition')) {
        const href = link.getAttribute('href');
        
        // Only apply transition for internal links
        if (href && !href.startsWith('http') && !href.startsWith('//') && href !== '#') {
            e.preventDefault();
            navigateWithTransition(href);
        }
    }
});

// Handle button clicks for smooth transitions
document.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-navigate]');
    
    if (btn) {
        const url = btn.getAttribute('data-navigate');
        const target = btn.getAttribute('data-target') || '_self';
        
        if (url) {
            e.preventDefault();
            navigateWithTransition(url, target);
        }
    }
});

// Override window.location for smooth transitions
const originalLocationAssign = window.location.assign.bind(window.location);
const originalLocationHref = Object.getOwnPropertyDescriptor(Location.prototype, 'href');

Object.defineProperty(window.location, 'href', {
    set(url) {
        if (typeof url === 'string' && !url.includes('blob:') && !url.includes('data:')) {
            navigateWithTransition(url);
        } else {
            originalLocationHref.set.call(this, url);
        }
    },
    get() {
        return originalLocationHref.get.call(this);
    }
});

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initPageTransitions();
        fadeInPage();
    });
} else {
    initPageTransitions();
    fadeInPage();
}

// Fade in when page is fully loaded
window.addEventListener('load', () => {
    hidePageTransition();
});

// Handle back/forward navigation
window.addEventListener('pageshow', (e) => {
    if (e.persisted) {
        fadeInPage();
    }
});

window.addEventListener('pagehide', () => {
    showPageTransition();
});
