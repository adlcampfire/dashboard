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

// Lightbox functionality for images
let currentLightboxIndex = 0;
let lightboxImages = [];

function openLightbox(src, images = null) {
    if (images) {
        lightboxImages = images;
        currentLightboxIndex = images.indexOf(src);
    } else {
        lightboxImages = [src];
        currentLightboxIndex = 0;
    }
    
    const lightbox = document.createElement('div');
    lightbox.id = 'lightbox';
    lightbox.className = 'lightbox';
    lightbox.innerHTML = `
        <div class="lightbox-content">
            <span class="lightbox-close" onclick="closeLightbox()">&times;</span>
            ${lightboxImages.length > 1 ? '<button class="lightbox-prev" onclick="lightboxPrev()">&#10094;</button>' : ''}
            <img src="${src}" alt="Full size image">
            ${lightboxImages.length > 1 ? '<button class="lightbox-next" onclick="lightboxNext()">&#10095;</button>' : ''}
            ${lightboxImages.length > 1 ? `<div class="lightbox-counter">${currentLightboxIndex + 1} / ${lightboxImages.length}</div>` : ''}
        </div>
    `;
    document.body.appendChild(lightbox);
    document.body.style.overflow = 'hidden';
    
    // Close on click outside
    lightbox.addEventListener('click', function(e) {
        if (e.target === lightbox) {
            closeLightbox();
        }
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', lightboxKeyHandler);
}

function closeLightbox() {
    const lightbox = document.getElementById('lightbox');
    if (lightbox) {
        lightbox.remove();
        document.body.style.overflow = '';
        document.removeEventListener('keydown', lightboxKeyHandler);
    }
}

function lightboxPrev() {
    currentLightboxIndex = (currentLightboxIndex - 1 + lightboxImages.length) % lightboxImages.length;
    updateLightboxImage();
}

function lightboxNext() {
    currentLightboxIndex = (currentLightboxIndex + 1) % lightboxImages.length;
    updateLightboxImage();
}

function updateLightboxImage() {
    const img = document.querySelector('#lightbox img');
    const counter = document.querySelector('.lightbox-counter');
    if (img) {
        img.src = lightboxImages[currentLightboxIndex];
    }
    if (counter) {
        counter.textContent = `${currentLightboxIndex + 1} / ${lightboxImages.length}`;
    }
}

function lightboxKeyHandler(e) {
    if (e.key === 'Escape') {
        closeLightbox();
    } else if (e.key === 'ArrowLeft') {
        lightboxPrev();
    } else if (e.key === 'ArrowRight') {
        lightboxNext();
    }
}

// Report content functionality
function reportPost(postId) {
    showReportModal('post', postId);
}

function reportComment(commentId) {
    showReportModal('comment', commentId);
}

function showReportModal(contentType, contentId) {
    const modal = document.createElement('div');
    modal.id = 'reportModal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="modal-close" onclick="closeReportModal()">&times;</span>
            <h2>Report ${contentType === 'post' ? 'Post' : 'Comment'}</h2>
            <form onsubmit="submitReport(event, '${contentType}', ${contentId})">
                <div class="form-group">
                    <label>Reason:</label>
                    <select id="reportReason" required>
                        <option value="">Select a reason...</option>
                        <option value="spam">Spam</option>
                        <option value="inappropriate">Inappropriate Content</option>
                        <option value="offensive">Offensive Language</option>
                        <option value="harassment">Harassment</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Additional Details (Optional):</label>
                    <textarea id="reportDetails" rows="3" placeholder="Provide more context..."></textarea>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">Submit Report</button>
                    <button type="button" class="btn btn-secondary" onclick="closeReportModal()">Cancel</button>
                </div>
            </form>
        </div>
    `;
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
}

function closeReportModal() {
    const modal = document.getElementById('reportModal');
    if (modal) {
        modal.remove();
        document.body.style.overflow = '';
    }
}

function submitReport(event, contentType, contentId) {
    event.preventDefault();
    
    const reason = document.getElementById('reportReason').value;
    const details = document.getElementById('reportDetails').value;
    
    fetch(`/api/report/${contentType}/${contentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            reason: reason,
            details: details
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Report submitted successfully. Our moderation team will review it.');
            closeReportModal();
        } else {
            alert('Failed to submit report: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while submitting the report.');
    });
}

// Toggle comments section visibility
function toggleComments(postId) {
    const commentsSection = document.getElementById(`comments-section-${postId}`);
    if (commentsSection) {
        commentsSection.style.display = commentsSection.style.display === 'none' ? 'block' : 'none';
    }
}

console.log('🔥 Campfire Adelaide Dashboard loaded successfully!');
