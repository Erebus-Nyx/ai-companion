// user-profile.js
// User Profile Management System

class UserProfileManager {
    constructor() {
        this.currentUser = null;
        this.userProfile = null;
        this.isVisible = false;
        this.isDirty = false;
        this.init();
    }

    async init() {
        try {
            // Load current user
            await this.loadCurrentUser();
            console.log('✅ User Profile Manager initialized');
        } catch (error) {
            console.error('Failed to initialize User Profile Manager:', error);
        }
    }

    async loadCurrentUser() {
        try {
            const response = await fetch('/api/users/current');
            if (response.ok) {
                this.currentUser = await response.json();
                console.log('📱 Current user loaded:', this.currentUser.display_name);
                
                // Load user profile
                await this.loadUserProfile();
            } else {
                // No current user, might need to create one
                console.warn('No current user found');
            }
        } catch (error) {
            console.error('Error loading current user:', error);
        }
    }

    async loadUserProfile() {
        if (!this.currentUser) return;

        try {
            const response = await fetch(`/api/users/${this.currentUser.id}/profile`);
            if (response.ok) {
                this.userProfile = await response.json();
                console.log('👤 User profile loaded:', this.userProfile);
            } else {
                console.warn('No user profile found, will create default');
            }
        } catch (error) {
            console.error('Error loading user profile:', error);
        }
    }

    async loadUsers() {
        try {
            const response = await fetch('/api/users');
            if (response.ok) {
                const data = await response.json();
                return data.users || [];
            }
            return [];
        } catch (error) {
            console.error('Error loading users:', error);
            return [];
        }
    }

    async createUser(username, displayName) {
        try {
            const response = await fetch('/api/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: username,
                    display_name: displayName
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ User created:', result);
                return result;
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Failed to create user');
            }
        } catch (error) {
            console.error('Error creating user:', error);
            throw error;
        }
    }

    async activateUser(userId) {
        try {
            const response = await fetch(`/api/users/${userId}/activate`, {
                method: 'POST'
            });

            if (response.ok) {
                await this.loadCurrentUser(); // Reload current user
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Failed to activate user');
            }
        } catch (error) {
            console.error('Error activating user:', error);
            throw error;
        }
    }

    async saveUserProfile(profileData) {
        if (!this.currentUser) {
            throw new Error('No current user to save profile for');
        }

        try {
            const response = await fetch(`/api/users/${this.currentUser.id}/profile`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(profileData)
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ User profile saved:', result);
                
                // Reload profile
                await this.loadUserProfile();
                
                this.isDirty = false;
                return result;
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Failed to save profile');
            }
        } catch (error) {
            console.error('Error saving user profile:', error);
            throw error;
        }
    }

    // UI Methods
    showUserDialog() {
        this.populateUserDialog();
        const dialog = document.getElementById('userSelectionDialog');
        if (dialog) {
            dialog.style.display = 'block';
            this.isVisible = true;
        }
    }

    hideUserDialog() {
        const dialog = document.getElementById('userSelectionDialog');
        if (dialog) {
            dialog.style.display = 'none';
            this.isVisible = false;
        }
    }

    async populateUserDialog() {
        const users = await this.loadUsers();
        const userList = document.getElementById('userSelectionList');
        
        if (!userList) return;

        userList.innerHTML = '';

        // Current user section
        if (this.currentUser) {
            const currentSection = document.createElement('div');
            currentSection.className = 'user-section';
            currentSection.innerHTML = `
                <h4>Current User</h4>
                <div class="user-item current-user">
                    <div class="user-info">
                        <div class="user-name">${this.currentUser.display_name}</div>
                        <div class="user-username">@${this.currentUser.username}</div>
                    </div>
                    <button class="btn btn-primary" onclick="userProfileManager.showUserProfile()">
                        Edit Profile
                    </button>
                </div>
            `;
            userList.appendChild(currentSection);
        }

        // Other users section
        const otherUsers = users.filter(u => !this.currentUser || u.id !== this.currentUser.id);
        if (otherUsers.length > 0) {
            const othersSection = document.createElement('div');
            othersSection.className = 'user-section';
            othersSection.innerHTML = '<h4>Switch User</h4>';
            
            otherUsers.forEach(user => {
                const userItem = document.createElement('div');
                userItem.className = 'user-item';
                userItem.innerHTML = `
                    <div class="user-info">
                        <div class="user-name">${user.display_name}</div>
                        <div class="user-username">@${user.username}</div>
                    </div>
                    <button class="btn btn-secondary" onclick="userProfileManager.switchToUser(${user.id})">
                        Switch
                    </button>
                `;
                othersSection.appendChild(userItem);
            });
            
            userList.appendChild(othersSection);
        }

        // Add new user section
        const addUserSection = document.createElement('div');
        addUserSection.className = 'user-section';
        addUserSection.innerHTML = `
            <h4>Add New User</h4>
            <div class="add-user-form">
                <input type="text" id="newUsername" placeholder="Username" class="form-input">
                <input type="text" id="newDisplayName" placeholder="Display Name" class="form-input">
                <button class="btn btn-success" onclick="userProfileManager.handleCreateUser()">
                    Create User
                </button>
            </div>
        `;
        userList.appendChild(addUserSection);
    }

    async switchToUser(userId) {
        try {
            await this.activateUser(userId);
            alert('User switched successfully!');
            this.hideUserDialog();
        } catch (error) {
            alert('Failed to switch user: ' + error.message);
        }
    }

    async handleCreateUser() {
        const username = document.getElementById('newUsername')?.value.trim();
        const displayName = document.getElementById('newDisplayName')?.value.trim();

        if (!username) {
            alert('Username is required');
            return;
        }

        try {
            await this.createUser(username, displayName || username);
            alert('User created successfully!');
            this.populateUserDialog(); // Refresh the dialog
        } catch (error) {
            alert('Failed to create user: ' + error.message);
        }
    }

    showUserProfile() {
        this.hideUserDialog(); // Close user selection dialog
        this.populateUserProfileForm();
        
        const panel = document.getElementById('userProfilePanel');
        if (panel) {
            panel.classList.add('open');
            this.isVisible = true;
        }
    }

    hideUserProfile() {
        const panel = document.getElementById('userProfilePanel');
        if (panel) {
            panel.classList.remove('open');
            this.isVisible = false;
        }
    }

    populateUserProfileForm() {
        if (!this.userProfile) return;

        // Basic user info
        this.setFieldValue('userDisplayName', this.userProfile.display_name || '');
        this.setFieldValue('userUsername', this.userProfile.username || '');

        // Profile fields
        this.setFieldValue('userGender', this.userProfile.gender || 'not_specified');
        this.setFieldValue('userAgeRange', this.userProfile.age_range || 'adult');
        this.setFieldValue('userBio', this.userProfile.bio || '');
        
        // Checkboxes
        const nsfwCheckbox = document.getElementById('userNsfwEnabled');
        if (nsfwCheckbox) {
            nsfwCheckbox.checked = this.userProfile.nsfw_enabled || false;
        }
        
        const explicitCheckbox = document.getElementById('userExplicitEnabled');
        if (explicitCheckbox) {
            explicitCheckbox.checked = this.userProfile.explicit_enabled || false;
        }

        this.isDirty = false;
    }

    setFieldValue(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = value;
        }
    }

    getFieldValue(fieldId) {
        const field = document.getElementById(fieldId);
        return field ? field.value : '';
    }

    buildUserProfileData() {
        const nsfwCheckbox = document.getElementById('userNsfwEnabled');
        const explicitCheckbox = document.getElementById('userExplicitEnabled');

        return {
            gender: this.getFieldValue('userGender'),
            age_range: this.getFieldValue('userAgeRange'),
            bio: this.getFieldValue('userBio'),
            nsfw_enabled: nsfwCheckbox ? nsfwCheckbox.checked : false,
            explicit_enabled: explicitCheckbox ? explicitCheckbox.checked : false,
            preferences: {} // Could be expanded later
        };
    }

    async handleSaveUserProfile() {
        try {
            const profileData = this.buildUserProfileData();
            await this.saveUserProfile(profileData);
            alert('User profile saved successfully!');
        } catch (error) {
            alert('Failed to save user profile: ' + error.message);
        }
    }

    markDirty() {
        this.isDirty = true;
    }

    getCurrentUser() {
        return this.currentUser;
    }

    getUserProfile() {
        return this.userProfile;
    }
}

// Global user profile manager instance
let userProfileManager = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    userProfileManager = new UserProfileManager();
    
    // Set up form change detection
    const profileFormSelector = '#userProfilePanel input, #userProfilePanel select, #userProfilePanel textarea';
    
    document.addEventListener('change', (event) => {
        if (event.target.matches(profileFormSelector)) {
            if (userProfileManager) {
                userProfileManager.markDirty();
            }
        }
    });

    document.addEventListener('input', (event) => {
        if (event.target.matches(profileFormSelector)) {
            if (userProfileManager) {
                userProfileManager.markDirty();
            }
        }
    });
});

// Global functions for UI interaction
function showUserDialog() {
    if (userProfileManager) {
        userProfileManager.showUserDialog();
    }
}

function closeUserDialog() {
    if (userProfileManager) {
        userProfileManager.hideUserDialog();
    }
}

function closeUserProfile() {
    if (userProfileManager) {
        userProfileManager.hideUserProfile();
    }
}

function saveUserProfile() {
    if (userProfileManager) {
        userProfileManager.handleSaveUserProfile();
    }
}

// Export for global access
window.UserProfileManager = UserProfileManager;
window.userProfileManager = userProfileManager;
