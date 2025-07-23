/**
 * User Selection System
 * Handles user selection popup and login functionality
 */

class UserSelectionManager {
    constructor() {
        this.currentUser = null;
        this.users = [];
        this.overlay = null;
        this.init();
    }
    
    init() {
        this.overlay = document.getElementById('userSelectionOverlay');
        this.loadUsers();
        console.log('✅ User Selection Manager initialized');
    }
    
    async loadUsers() {
        try {
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
            const response = await fetch(`${apiBaseUrl}/api/users`);
            if (response.ok) {
                this.users = await response.json();
                if (this.users.users) {
                    this.users = this.users.users;
                }
                this.renderUserList();
            } else {
                console.error('Failed to load users');
                this.showError('Failed to load users');
            }
        } catch (error) {
            console.error('Error loading users:', error);
            this.showError('Error loading users');
        }
    }
    
    renderUserList() {
        const userList = document.getElementById('userList');
        if (!userList) return;
        
        userList.innerHTML = '';
        
        if (this.users.length === 0) {
            userList.innerHTML = `
                <div class="no-users">
                    <p>No users found. Create your first user to get started.</p>
                </div>
            `;
            return;
        }
        
        this.users.forEach(user => {
            const userItem = document.createElement('div');
            userItem.className = 'user-item';
            userItem.onclick = () => this.selectUser(user);
            
            const initials = user.display_name ? 
                user.display_name.split(' ').map(n => n[0]).join('').toUpperCase() :
                user.username.substring(0, 2).toUpperCase();
            
            userItem.innerHTML = `
                <div class="user-avatar">${initials}</div>
                <div class="user-info">
                    <div class="user-name">${user.display_name || user.username}</div>
                    <div class="user-details">
                        ${user.email || ''} ${user.is_admin ? '• Admin' : ''}
                    </div>
                </div>
            `;
            
            userList.appendChild(userItem);
        });
    }
    
    selectUser(user) {
        this.currentUser = user;
        
        // Visual feedback
        document.querySelectorAll('.user-item').forEach(item => {
            item.classList.remove('selected');
        });
        event.currentTarget.classList.add('selected');
        
        // Auto-login after short delay
        setTimeout(() => {
            this.loginUser(user);
        }, 500);
    }
    
    async loginUser(user) {
        try {
            // Set current user in session
            const response = await fetch('/api/users/set-current', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id: user.id })
            });
            
            if (response.ok) {
                console.log(`✅ Logged in as: ${user.display_name || user.username}`);
                this.hideUserSelection();
                
                // Trigger user profile refresh
                if (window.userProfileManager) {
                    window.userProfileManager.loadCurrentUser();
                }
                
                // Show success message
                this.showSuccessMessage(`Welcome, ${user.display_name || user.username}!`);
            } else {
                console.error('Failed to set current user');
                this.showError('Failed to login. Please try again.');
            }
        } catch (error) {
            console.error('Error logging in user:', error);
            this.showError('Login error. Please try again.');
        }
    }
    
    showUserSelection() {
        if (this.overlay) {
            this.overlay.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }
    
    hideUserSelection() {
        if (this.overlay) {
            this.overlay.classList.add('hidden');
            document.body.style.overflow = '';
        }
    }
    
    showCreateUser() {
        // Open user management panel to create new user
        if (window.uiPanelManager) {
            window.uiPanelManager.openUserManagement();
            this.hideUserSelection();
        }
    }
    
    logoutUser() {
        // Clear current user and show selection again
        this.currentUser = null;
        this.showUserSelection();
        
        // Clear user profile
        if (window.userProfileManager) {
            window.userProfileManager.currentUser = null;
            window.userProfileManager.updateUserDisplay();
        }
        
        console.log('🔓 User logged out');
    }
    
    getCurrentUser() {
        return this.currentUser;
    }
    
    showError(message) {
        // Simple error display - you can enhance this
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #ff4444;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            z-index: 11000;
        `;
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 3000);
    }
    
    showSuccessMessage(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #44ff44;
            color: black;
            padding: 10px 20px;
            border-radius: 5px;
            z-index: 11000;
        `;
        successDiv.textContent = message;
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }
}

// Navigation functions
function toggleNavigation() {
    const navIcons = document.getElementById('navIcons');
    if (navIcons) {
        navIcons.classList.toggle('collapsed');
        
        const collapseIcon = navIcons.querySelector('.nav-collapse svg');
        if (collapseIcon) {
            if (navIcons.classList.contains('collapsed')) {
                collapseIcon.innerHTML = '<polyline points="6,9 12,15 18,9"/>';
            } else {
                collapseIcon.innerHTML = '<polyline points="18,15 12,9 6,15"/>';
            }
        }
    }
}

function logoutUser() {
    if (window.userSelectionManager) {
        window.userSelectionManager.logoutUser();
    }
}

function showCreateUser() {
    if (window.userSelectionManager) {
        window.userSelectionManager.showCreateUser();
    }
}

// Global instance
let userSelectionManager = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    userSelectionManager = new UserSelectionManager();
    window.userSelectionManager = userSelectionManager;
    
    // Show user selection on page load
    setTimeout(() => {
        userSelectionManager.showUserSelection();
    }, 1000);
});

// Export functions for global access
window.toggleNavigation = toggleNavigation;
window.logoutUser = logoutUser;
window.showCreateUser = showCreateUser;
