/**
 * User Selection System - Login/User Selection on App Start
 * Handles user selection popup, user loading, and authentication
 */

class UserSelectionSystem {
    constructor() {
        this.currentUser = null;
        this.users = [];
        this.popupElement = null;
        
        this.init();
    }
    
    async init() {
        console.log('🔑 Initializing User Selection System');
        
        // Find the popup element
        this.popupElement = document.getElementById('userSelectionPopup');
        if (!this.popupElement) {
            console.error('User selection popup element not found');
            return;
        }
        
        // Load existing users and show popup
        await this.loadUsers();
        this.showUserSelectionPopup();
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    async loadUsers() {
        try {
            console.log('Loading existing users...');
            const response = await fetch('/api/users');
            
            if (response.ok) {
                const data = await response.json();
                this.users = data.users || [];
                console.log(`Found ${this.users.length} existing users:`, this.users);
            } else {
                console.warn('Failed to load users, starting with empty list');
                this.users = [];
            }
        } catch (error) {
            console.error('Error loading users:', error);
            this.users = [];
        }
    }
    
    showUserSelectionPopup() {
        // Clear existing content
        const userList = document.getElementById('userSelectionList');
        const newUserForm = document.getElementById('newUserForm');
        
        if (!userList || !newUserForm) {
            console.error('User selection elements not found');
            return;
        }
        
        // Clear previous content
        userList.innerHTML = '';
        
        // Show existing users if any
        if (this.users.length > 0) {
            console.log('Displaying existing users for selection');
            
            // Add header for existing users
            const existingHeader = document.createElement('h3');
            existingHeader.textContent = 'Select Existing User:';
            existingHeader.className = 'user-section-header';
            userList.appendChild(existingHeader);
            
            // Add user cards
            this.users.forEach(user => {
                const userCard = this.createUserCard(user);
                userList.appendChild(userCard);
            });
            
            // Add separator
            const separator = document.createElement('div');
            separator.className = 'user-section-separator';
            separator.innerHTML = '<hr><span>OR</span><hr>';
            userList.appendChild(separator);
        }
        
        // Add "Create New User" section
        const newUserHeader = document.createElement('h3');
        newUserHeader.textContent = this.users.length > 0 ? 'Create New User:' : 'Create Your First User:';
        newUserHeader.className = 'user-section-header';
        userList.appendChild(newUserHeader);
        
        // Show the new user form
        newUserForm.style.display = 'block';
        
        // Show the popup with blur effect using class-based approach like other modals
        this.popupElement.style.display = 'flex';
        this.popupElement.classList.add('open');
        document.body.classList.add('user-selection-active');
        
        console.log('User selection popup displayed');
    }
    
    createUserCard(user) {
        const card = document.createElement('div');
        card.className = 'user-card';
        card.innerHTML = `
            <div class="user-avatar">
                <i class="fas fa-user-circle"></i>
            </div>
            <div class="user-info">
                <div class="user-name">${user.display_name || user.username}</div>
                <div class="user-username">@${user.username}</div>
                ${user.is_admin ? '<div class="user-badge admin">Admin</div>' : ''}
                <div class="user-last-active">Last active: ${this.formatDate(user.created_at)}</div>
            </div>
            <button class="user-select-btn" onclick="userSelectionSystem.selectUser(${user.id})">
                <i class="fas fa-sign-in-alt"></i>
                Select
            </button>
        `;
        return card;
    }
    
    formatDate(dateString) {
        if (!dateString) return 'Never';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        } catch (error) {
            return 'Unknown';
        }
    }
    
    async selectUser(userId) {
        try {
            console.log(`Selecting user ID: ${userId}`);
            
            // Find the user
            const user = this.users.find(u => u.id === userId);
            if (!user) {
                console.error('User not found');
                return;
            }
            
            // Set as current user via API
            const response = await fetch('/api/users/set-current', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id: userId })
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('User selected successfully:', result);
                
                this.currentUser = user;
                
                console.log('🔑 About to hide user selection popup...');
                this.hideUserSelectionPopup();
                
                // Trigger user change event for other systems
                this.notifyUserChange(user);
                
                // Show success message
                this.showMessage(`Welcome back, ${user.display_name || user.username}!`, 'success');
                
            } else {
                const error = await response.json();
                console.error('Failed to select user:', error);
                this.showMessage('Failed to select user. Please try again.', 'error');
            }
            
        } catch (error) {
            console.error('Error selecting user:', error);
            this.showMessage('An error occurred. Please try again.', 'error');
        }
    }
    
    async createNewUser() {
        const form = document.getElementById('newUserForm');
        const formData = new FormData(form);
        
        const userData = {
            username: formData.get('username'),
            display_name: formData.get('display_name') || formData.get('username'),
            email: formData.get('email') || '',
            is_admin: false
        };
        
        // Basic validation
        if (!userData.username.trim()) {
            this.showMessage('Username is required', 'error');
            return;
        }
        
        if (userData.username.length < 3) {
            this.showMessage('Username must be at least 3 characters', 'error');
            return;
        }
        
        try {
            console.log('Creating new user:', userData);
            
            const response = await fetch('/api/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('User created successfully:', result);
                
                // Automatically select the new user
                await this.selectUser(result.user.id);
                
            } else {
                const error = await response.json();
                console.error('Failed to create user:', error);
                this.showMessage(error.error || 'Failed to create user', 'error');
            }
            
        } catch (error) {
            console.error('Error creating user:', error);
            this.showMessage('An error occurred while creating user', 'error');
        }
    }
    
    hideUserSelectionPopup() {
        // Use class-based approach like other modals
        console.log('🔑 Hiding user selection popup - removing open class');
        console.log('🔑 Current classes before:', this.popupElement.className);
        
        this.popupElement.classList.remove('open');
        document.body.classList.remove('user-selection-active');
        
        console.log('🔑 Current classes after removing open:', this.popupElement.className);
        
        // Set display none after transition delay
        setTimeout(() => {
            console.log('🔑 Setting display: none after transition delay');
            this.popupElement.style.display = 'none';
        }, 300);
        
        console.log('User selection popup hidden');
    }
    
    notifyUserChange(user) {
        // Update localStorage for authentication checks
        localStorage.setItem('currentUser', user.username);
        localStorage.setItem('currentUserId', user.id.toString());
        
        // Notify other systems about user change
        const event = new CustomEvent('userChanged', {
            detail: { user: user }
        });
        document.dispatchEvent(event);
        
        // Update UI elements that show current user
        this.updateUserDisplay(user);
    }
    
    updateUserDisplay(user) {
        // Update any UI elements that show the current user
        const userDisplayElements = document.querySelectorAll('.current-user-display');
        userDisplayElements.forEach(element => {
            element.textContent = user.display_name || user.username;
        });
        
        // Update title or other indicators
        document.title = `AI 2D Chat - ${user.display_name || user.username}`;
    }
    
    setupEventListeners() {
        // Handle form submission
        const newUserForm = document.getElementById('newUserForm');
        if (newUserForm) {
            newUserForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createNewUser();
            });
        }
        
        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.popupElement.style.display === 'flex') {
                // Don't allow closing with escape - user must select
                console.log('User selection is required - cannot close with escape');
            }
        });
        
        // Prevent clicking outside to close
        this.popupElement.addEventListener('click', (e) => {
            if (e.target === this.popupElement) {
                // Don't close when clicking outside
                console.log('User selection is required');
            }
        });
    }
    
    showMessage(message, type = 'info') {
        const messageElement = document.getElementById('userSelectionMessage');
        if (messageElement) {
            messageElement.textContent = message;
            messageElement.className = `user-message ${type}`;
            messageElement.style.display = 'block';
            
            // Auto-hide after 3 seconds
            setTimeout(() => {
                messageElement.style.display = 'none';
            }, 3000);
        }
    }
    
    logout() {
        console.log('Logging out current user');
        this.currentUser = null;
        
        // Clear current user from session
        fetch('/api/users/logout', { method: 'POST' })
            .then(() => {
                // Show user selection again
                this.loadUsers().then(() => {
                    this.showUserSelectionPopup();
                });
            })
            .catch(error => {
                console.error('Logout error:', error);
                // Still show user selection
                this.loadUsers().then(() => {
                    this.showUserSelectionPopup();
                });
            });
    }
}

// Global instance
let userSelectionSystem = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    userSelectionSystem = new UserSelectionSystem();
    window.userSelectionSystem = userSelectionSystem;
    
    // Test that navigation function is working
    console.log('🔧 User selection system loaded. Testing navigation...');
    if (typeof toggleNavigation === 'function') {
        console.log('✅ toggleNavigation function is available');
        window.toggleNavigation = toggleNavigation;
    } else {
        console.error('❌ toggleNavigation function not found');
    }
});

// Legacy function compatibility
window.selectUser = (userId) => userSelectionSystem?.selectUser(userId);
window.createNewUser = () => userSelectionSystem?.createNewUser();
window.logoutUser = () => userSelectionSystem?.logout();

// Navigation functions
function toggleNavigation() {
    console.log('🔧 toggleNavigation called');
    
    const navIcons = document.getElementById('navIcons');
    if (!navIcons) {
        console.error('❌ Navigation container #navIcons not found');
        return;
    }
    
    console.log('🔧 Current classes:', navIcons.className);
    
    // Toggle the collapsed class
    navIcons.classList.toggle('collapsed');
    
    console.log('🔧 New classes:', navIcons.className);
    console.log('🔧 Is collapsed:', navIcons.classList.contains('collapsed'));
    
    // Find and update the collapse icon
    const collapseButton = navIcons.querySelector('.nav-collapse');
    if (!collapseButton) {
        console.error('❌ Collapse button not found');
        return;
    }
    
    const collapseIcon = collapseButton.querySelector('svg');
    if (!collapseIcon) {
        console.error('❌ Collapse icon SVG not found');
        return;
    }
    
    // Update the icon based on state
    if (navIcons.classList.contains('collapsed')) {
        console.log('🔧 Setting expand icon (down arrow)');
        collapseIcon.innerHTML = `<polyline points="6,9 12,15 18,9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`;
        collapseButton.title = "Expand Navigation";
    } else {
        console.log('🔧 Setting collapse icon (up arrow)');
        collapseIcon.innerHTML = `<polyline points="18,15 12,9 6,15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`;
        collapseButton.title = "Collapse Navigation";
    }
    
    console.log('✅ Navigation toggle complete');
}

function logoutUser() {
    console.log('🔓 Logout requested');
    if (window.userSelectionSystem) {
        window.userSelectionSystem.logout();
    } else {
        console.error('❌ User selection system not available');
    }
}

// Export navigation functions for global access
window.toggleNavigation = toggleNavigation;
