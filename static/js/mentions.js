// Mentions System JavaScript (@username autocomplete)

let mentionCache = [];
let mentionCacheTime = 0;
const CACHE_DURATION = 60000; // 1 minute

// Initialize mentions autocomplete on textareas
function initMentions() {
    const textareas = document.querySelectorAll('.mention-enabled');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', handleMentionInput);
        textarea.addEventListener('keydown', handleMentionKeydown);
    });
}

// Handle input for mention detection
function handleMentionInput(event) {
    const textarea = event.target;
    const text = textarea.value;
    const cursorPos = textarea.selectionStart;
    
    // Find if we're typing after an @
    const textBeforeCursor = text.substring(0, cursorPos);
    const mentionMatch = textBeforeCursor.match(/@(\w*)$/);
    
    if (mentionMatch) {
        const searchTerm = mentionMatch[1];
        showMentionAutocomplete(textarea, searchTerm);
    } else {
        hideMentionAutocomplete();
    }
}

// Handle keyboard navigation in mention autocomplete
function handleMentionKeydown(event) {
    const dropdown = document.querySelector('.mention-dropdown');
    if (!dropdown || dropdown.style.display === 'none') return;
    
    const items = dropdown.querySelectorAll('.mention-item');
    const activeItem = dropdown.querySelector('.mention-item.active');
    let activeIndex = Array.from(items).indexOf(activeItem);
    
    if (event.key === 'ArrowDown') {
        event.preventDefault();
        activeIndex = Math.min(activeIndex + 1, items.length - 1);
        updateActiveMention(items, activeIndex);
    } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        activeIndex = Math.max(activeIndex - 1, 0);
        updateActiveMention(items, activeIndex);
    } else if (event.key === 'Enter' || event.key === 'Tab') {
        if (activeItem) {
            event.preventDefault();
            selectMention(event.target, activeItem.dataset.username);
        }
    } else if (event.key === 'Escape') {
        hideMentionAutocomplete();
    }
}

// Update active mention in dropdown
function updateActiveMention(items, activeIndex) {
    items.forEach((item, index) => {
        if (index === activeIndex) {
            item.classList.add('active');
            item.scrollIntoView({ block: 'nearest' });
        } else {
            item.classList.remove('active');
        }
    });
}

// Show mention autocomplete dropdown
async function showMentionAutocomplete(textarea, searchTerm) {
    const users = await fetchUsers(searchTerm);
    
    if (users.length === 0) {
        hideMentionAutocomplete();
        return;
    }
    
    let dropdown = document.querySelector('.mention-dropdown');
    if (!dropdown) {
        dropdown = createMentionDropdown();
        document.body.appendChild(dropdown);
    }
    
    // Position dropdown
    const rect = textarea.getBoundingClientRect();
    dropdown.style.left = `${rect.left}px`;
    dropdown.style.top = `${rect.bottom + 5}px`;
    dropdown.style.width = `${Math.min(rect.width, 300)}px`;
    
    // Populate dropdown
    dropdown.innerHTML = users.map(user => `
        <div class="mention-item" data-username="${user.username}" onclick="selectMentionFromClick(event)">
            <img src="${user.profile_picture || '/static/uploads/profiles/default.png'}" 
                 alt="${user.username}" class="mention-avatar">
            <span class="mention-username">@${user.username}</span>
        </div>
    `).join('');
    
    // Set first item as active
    const firstItem = dropdown.querySelector('.mention-item');
    if (firstItem) {
        firstItem.classList.add('active');
    }
    
    dropdown.style.display = 'block';
}

// Hide mention autocomplete dropdown
function hideMentionAutocomplete() {
    const dropdown = document.querySelector('.mention-dropdown');
    if (dropdown) {
        dropdown.style.display = 'none';
    }
}

// Create mention dropdown element
function createMentionDropdown() {
    const dropdown = document.createElement('div');
    dropdown.className = 'mention-dropdown';
    dropdown.style.cssText = `
        position: fixed;
        background: white;
        border: 1px solid #ddd;
        border-radius: 5px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        max-height: 200px;
        overflow-y: auto;
        z-index: 1000;
        display: none;
    `;
    return dropdown;
}

// Select mention from click
function selectMentionFromClick(event) {
    const item = event.currentTarget;
    const username = item.dataset.username;
    const textarea = document.querySelector('.mention-enabled:focus');
    if (textarea) {
        selectMention(textarea, username);
    }
}

// Select a mention and insert into textarea
function selectMention(textarea, username) {
    const text = textarea.value;
    const cursorPos = textarea.selectionStart;
    
    // Find the @ symbol before cursor
    const textBeforeCursor = text.substring(0, cursorPos);
    const mentionStart = textBeforeCursor.lastIndexOf('@');
    
    // Replace from @ to cursor with @username
    const newText = text.substring(0, mentionStart) + '@' + username + ' ' + text.substring(cursorPos);
    textarea.value = newText;
    
    // Set cursor after the mention
    const newCursorPos = mentionStart + username.length + 2;
    textarea.setSelectionRange(newCursorPos, newCursorPos);
    
    hideMentionAutocomplete();
    textarea.focus();
}

// Fetch users from server
async function fetchUsers(searchTerm) {
    try {
        // Use cache if recent
        const now = Date.now();
        if (mentionCache.length > 0 && now - mentionCacheTime < CACHE_DURATION) {
            return filterUsers(mentionCache, searchTerm);
        }
        
        const response = await fetch('/api/users/search?q=' + encodeURIComponent(searchTerm));
        const data = await response.json();
        
        if (data.success) {
            mentionCache = data.users;
            mentionCacheTime = now;
            return data.users;
        }
        return [];
    } catch (error) {
        console.error('Error fetching users:', error);
        return [];
    }
}

// Filter users by search term
function filterUsers(users, searchTerm) {
    if (!searchTerm) return users.slice(0, 10);
    
    const term = searchTerm.toLowerCase();
    return users
        .filter(user => user.username.toLowerCase().includes(term))
        .slice(0, 10);
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.querySelector('.mention-dropdown');
    const textareas = document.querySelectorAll('.mention-enabled');
    
    let isInsideTextarea = false;
    textareas.forEach(textarea => {
        if (textarea.contains(event.target)) {
            isInsideTextarea = true;
        }
    });
    
    if (dropdown && !dropdown.contains(event.target) && !isInsideTextarea) {
        hideMentionAutocomplete();
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initMentions();
    console.log('Mentions system initialized');
});
