// Reactions System JavaScript

// Toggle reaction on a post
function toggleReaction(postId, reactionType) {
    fetch(`/api/reaction/${postId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            reaction_type: reactionType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update reaction count
            updateReactionDisplay(postId, data.reactions);
        } else {
            showToast(data.message || 'Failed to toggle reaction', 'error');
        }
    })
    .catch(error => {
        console.error('Error toggling reaction:', error);
        showToast('Network error occurred', 'error');
    });
}

// Update reaction display on the page
function updateReactionDisplay(postId, reactions) {
    const reactionContainer = document.querySelector(`#reactions-${postId}`);
    if (!reactionContainer) return;
    
    // Clear and rebuild reaction buttons
    const reactionTypes = ['like', 'love', 'celebrate', 'idea', 'fire', 'applause'];
    const emojis = {
        'like': '👍',
        'love': '❤️',
        'celebrate': '🎉',
        'idea': '💡',
        'fire': '🔥',
        'applause': '👏'
    };
    
    let html = '<div class="reaction-buttons">';
    reactionTypes.forEach(type => {
        const reaction = reactions[type] || { count: 0, user_reacted: false };
        const activeClass = reaction.user_reacted ? 'active' : '';
        const countDisplay = reaction.count > 0 ? reaction.count : '';
        
        html += `
            <button class="reaction-btn ${activeClass}" 
                    onclick="toggleReaction(${postId}, '${type}')"
                    title="${type}">
                <span class="emoji">${emojis[type]}</span>
                ${countDisplay ? `<span class="count">${countDisplay}</span>` : ''}
            </button>
        `;
    });
    html += '</div>';
    
    reactionContainer.innerHTML = html;
}

// Get CSRF token from meta tag or cookie
function getCsrfToken() {
    const tokenMeta = document.querySelector('meta[name="csrf-token"]');
    if (tokenMeta) {
        return tokenMeta.getAttribute('content');
    }
    // Fallback to cookie
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

// Initialize reactions on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Reactions system initialized');
});
