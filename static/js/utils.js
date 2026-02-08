// Shared utility functions for the dashboard

/**
 * Get CSRF token for AJAX requests
 * @returns {string} CSRF token
 */
function getCsrfToken() {
    const tokenField = document.querySelector('input[name="csrf_token"]');
    if (tokenField) {
        return tokenField.value;
    }
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_token=') || row.startsWith('session='));
    return cookieValue ? cookieValue.split('=')[1] : '';
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type of toast (info, success, error, warning)
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    const colors = {
        'error': '#f44336',
        'success': '#4CAF50',
        'warning': '#ff9800',
        'info': '#2196F3'
    };
    
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${colors[type] || colors.info};
        color: white;
        border-radius: 5px;
        z-index: 10000;
        animation: slideIn 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { getCsrfToken, showToast, escapeHtml };
}
