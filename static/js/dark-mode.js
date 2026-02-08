// Dark Mode JavaScript

// Toggle dark mode
function toggleDarkMode() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    // Update DOM
    html.setAttribute('data-theme', newTheme);
    
    // Update toggle button icon
    updateThemeIcon(newTheme);
    
    // Save to localStorage
    localStorage.setItem('theme', newTheme);
    
    // Save to server
    saveThemePreference(newTheme);
}

// Update theme icon
function updateThemeIcon(theme) {
    const icon = document.querySelector('#theme-toggle-icon');
    if (icon) {
        icon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
}

// Save theme preference to server
function saveThemePreference(theme) {
    fetch('/api/theme', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ theme: theme })
    })
    .catch(error => console.error('Error saving theme:', error));
}

// Get CSRF token
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

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    const html = document.documentElement;
    
    // Check localStorage first
    const savedTheme = localStorage.getItem('theme');
    
    // Check if theme is set in HTML attribute (from server)
    const serverTheme = html.getAttribute('data-theme');
    
    // Use saved theme or server theme
    const theme = savedTheme || serverTheme || 'light';
    
    html.setAttribute('data-theme', theme);
    updateThemeIcon(theme);
    
    console.log('Dark mode initialized with theme:', theme);
});

// Add smooth transition class after initial load to prevent flash
window.addEventListener('load', function() {
    document.documentElement.classList.add('theme-transition');
});
