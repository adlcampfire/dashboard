// Campfire Adelaide Dashboard - Main JavaScript

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash');
    
    flashMessages.forEach(function(flash) {
        setTimeout(function() {
            flash.style.transition = 'opacity 0.5s';
            flash.style.opacity = '0';
            setTimeout(function() {
                flash.remove();
            }, 500);
        }, 5000);
    });
});

// Image preview functionality
function previewImage(input, previewElement) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            previewElement.innerHTML = '<img src="' + e.target.result + '" alt="Preview">';
            previewElement.style.display = 'block';
        }
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Confirm before form submission
function confirmAction(message) {
    return confirm(message);
}

// Auto-refresh timeline (every 30 seconds)
function enableAutoRefresh() {
    const isTimelinePage = window.location.pathname.includes('timeline');
    
    if (isTimelinePage) {
        setInterval(function() {
            // Only refresh if user is not actively typing or interacting
            if (!document.activeElement || document.activeElement.tagName !== 'TEXTAREA') {
                location.reload();
            }
        }, 30000); // 30 seconds
    }
}

// Initialize auto-refresh
// enableAutoRefresh(); // Commented out by default - uncomment to enable

// Mobile menu toggle (if needed in future)
function toggleMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    navMenu.classList.toggle('show');
}

// Handle keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search (if we add search later)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('#search-input');
        if (searchInput) {
            searchInput.focus();
        }
    }
});

// Form validation helper
function validateFileUpload(input, allowedTypes, maxSize) {
    if (!input.files || !input.files[0]) {
        return true;
    }
    
    const file = input.files[0];
    const fileType = file.type;
    const fileSize = file.size;
    
    // Check file type
    if (!allowedTypes.includes(fileType)) {
        alert('Invalid file type. Please upload: ' + allowedTypes.join(', '));
        input.value = '';
        return false;
    }
    
    // Check file size (maxSize in bytes)
    if (fileSize > maxSize) {
        alert('File is too large. Maximum size: ' + (maxSize / 1024 / 1024) + 'MB');
        input.value = '';
        return false;
    }
    
    return true;
}

// Smooth scroll to top
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Add scroll to top button when scrolling down
window.addEventListener('scroll', function() {
    const scrollButton = document.querySelector('.scroll-to-top');
    if (scrollButton) {
        if (window.pageYOffset > 300) {
            scrollButton.style.display = 'block';
        } else {
            scrollButton.style.display = 'none';
        }
    }
});

console.log('🔥 Campfire Adelaide Dashboard loaded successfully!');
