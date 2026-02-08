// Comments System JavaScript

// Submit comment on a post
function submitComment(postId) {
    const textarea = document.querySelector(`#comment-input-${postId}`);
    const content = textarea.value.trim();
    
    if (!content) {
        showToast('Please enter a comment', 'error');
        return;
    }
    
    fetch(`/api/comment/${postId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            content: content
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear textarea
            textarea.value = '';
            
            // Add comment to display
            addCommentToDisplay(postId, data.comment);
            
            showToast('Comment posted successfully', 'success');
        } else {
            showToast(data.message || 'Failed to post comment', 'error');
        }
    })
    .catch(error => {
        console.error('Error posting comment:', error);
        showToast('Network error occurred', 'error');
    });
}

// Add comment to display
function addCommentToDisplay(postId, comment) {
    const commentsContainer = document.querySelector(`#comments-${postId}`);
    if (!commentsContainer) return;
    
    const commentHtml = `
        <div class="comment" id="comment-${comment.id}">
            <img src="${comment.user.profile_picture || '/static/uploads/profiles/default.png'}" 
                 alt="${comment.user.username}" class="comment-avatar">
            <div class="comment-content">
                <div class="comment-header">
                    <a href="/user/${comment.user.id}" class="comment-author">${comment.user.username}</a>
                    <span class="comment-time">${comment.time_ago}</span>
                </div>
                <div class="comment-text">${comment.content_html}</div>
            </div>
            ${comment.can_delete ? `
                <button class="comment-delete-btn" onclick="deleteComment(${comment.id})" title="Delete comment">
                    🗑️
                </button>
            ` : ''}
        </div>
    `;
    
    commentsContainer.insertAdjacentHTML('beforeend', commentHtml);
}

// Delete comment
function deleteComment(commentId) {
    if (!confirm('Are you sure you want to delete this comment?')) {
        return;
    }
    
    fetch(`/api/comment/${commentId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove comment from display
            const commentElement = document.querySelector(`#comment-${commentId}`);
            if (commentElement) {
                commentElement.remove();
            }
            showToast('Comment deleted', 'success');
        } else {
            showToast(data.message || 'Failed to delete comment', 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting comment:', error);
        showToast('Network error occurred', 'error');
    });
}

// Toggle comments visibility
function toggleComments(postId) {
    const commentsSection = document.querySelector(`#comments-section-${postId}`);
    if (commentsSection) {
        const isHidden = commentsSection.style.display === 'none';
        commentsSection.style.display = isHidden ? 'block' : 'none';
        
        // Load comments if not loaded yet
        if (isHidden && commentsSection.dataset.loaded !== 'true') {
            loadComments(postId);
            commentsSection.dataset.loaded = 'true';
        }
    }
}

// Load comments for a post
function loadComments(postId) {
    fetch(`/api/comments/${postId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const commentsContainer = document.querySelector(`#comments-${postId}`);
                if (commentsContainer) {
                    commentsContainer.innerHTML = data.comments.map(comment => `
                        <div class="comment" id="comment-${comment.id}">
                            <img src="${comment.user.profile_picture || '/static/uploads/profiles/default.png'}" 
                                 alt="${comment.user.username}" class="comment-avatar">
                            <div class="comment-content">
                                <div class="comment-header">
                                    <a href="/user/${comment.user.id}" class="comment-author">${comment.user.username}</a>
                                    <span class="comment-time">${comment.time_ago}</span>
                                </div>
                                <div class="comment-text">${comment.content_html}</div>
                            </div>
                            ${comment.can_delete ? `
                                <button class="comment-delete-btn" onclick="deleteComment(${comment.id})" title="Delete comment">
                                    🗑️
                                </button>
                            ` : ''}
                        </div>
                    `).join('');
                }
            }
        })
        .catch(error => console.error('Error loading comments:', error));
}

// Get CSRF token
function getCsrfToken() {
    const tokenMeta = document.querySelector('meta[name="csrf-token"]');
    if (tokenMeta) {
        return tokenMeta.getAttribute('content');
    }
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_token='));
    return cookieValue ? cookieValue.split('=')[1] : '';
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'error' ? '#f44336' : type === 'success' ? '#4CAF50' : '#2196F3'};
        color: white;
        border-radius: 5px;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initialize comments on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Comments system initialized');
});
