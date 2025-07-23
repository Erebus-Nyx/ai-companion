/**
 * User Management System
 * Handles user creation, editing, and management functionality
 */

class UserManagementSystem {
    constructor() {
        this.currentUser = null;
        this.users = [];
        this.init();
    }

    async init() {
        try {
            await this.loadUsers();
            this.populateUserSelect();
            console.log('✅ User Management System initialized');
        } catch (error) {
            console.error('Failed to initialize User Management System:', error);
        }
    }

    async loadUsers() {
        try {
            // TODO: Connect to backend API
            // const response = await fetch('/api/users');
            // if (response.ok) {
            //     this.users = await response.json();
            // }
            
            // Placeholder data for now
            this.users = [
                { id: 1, username: 'admin', displayName: 'Administrator', role: 'admin' },
                { id: 2, username: 'user1', displayName: 'Test User', role: 'user' }
            ];
            console.log('📋 Users loaded:', this.users.length);
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }

    populateUserSelect() {
        const userSelect = document.getElementById('userSelect');
        if (!userSelect) return;

        userSelect.innerHTML = '<option value="">Select a user...</option>';
        
        this.users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = `${user.displayName} (@${user.username})`;
            userSelect.appendChild(option);
        });
    }

    onUserChange() {
        const userSelect = document.getElementById('userSelect');
        const userId = userSelect.value;
        
        if (userId) {
            const user = this.users.find(u => u.id == userId);
            if (user) {
                this.loadUserData(user);
            }
        } else {
            this.clearUserForm();
        }
    }

    loadUserData(user) {
        this.currentUser = user;
        
        // Basic Information
        this.setFieldValue('userName', user.username || '');
        this.setFieldValue('userDisplayName', user.displayName || '');
        this.setFieldValue('userEmail', user.email || '');
        // Note: Don't load password for security
        
        // Role & Permissions
        this.setFieldValue('userRole', user.role || 'user');
        this.setCheckboxValue('permissionChat', user.permissions?.chat || false);
        this.setCheckboxValue('permissionDrawing', user.permissions?.drawing || false);
        this.setCheckboxValue('permissionCharacters', user.permissions?.characters || false);
        this.setCheckboxValue('permissionUserMgmt', user.permissions?.userMgmt || false);
        this.setCheckboxValue('permissionSettings', user.permissions?.settings || false);
        
        // Demographics
        this.setFieldValue('userAge', user.demographics?.age || '');
        this.setFieldValue('userGender', user.demographics?.gender || 'not-specified');
        this.setFieldValue('userLocation', user.demographics?.location || '');
        
        // Personal Characteristics
        this.setFieldValue('userPersonality', user.characteristics?.personality || '');
        this.setFieldValue('userInterests', user.characteristics?.interests || '');
        this.setFieldValue('userLikes', user.characteristics?.likes || '');
        this.setFieldValue('userDislikes', user.characteristics?.dislikes || '');
        
        // Communication Preferences
        this.setFieldValue('userCommunicationStyle', user.preferences?.communicationStyle || 'casual');
        this.setFieldValue('userLanguagePreference', user.preferences?.language || 'en');
        
        // Content Preferences
        this.setCheckboxValue('contentNSFW', user.content?.nsfw || false);
        this.setCheckboxValue('contentMature', user.content?.mature || false);
        this.setCheckboxValue('contentViolence', user.content?.violence || false);
        this.setCheckboxValue('contentProfanity', user.content?.profanity || false);
        this.setFieldValue('userContentPreferences', user.content?.preferences || '');
        
        // Notes
        this.setFieldValue('userNotes', user.notes?.admin || '');
        this.setFieldValue('userBio', user.notes?.bio || '');
        
        console.log('👤 Loaded user data for:', user.displayName);
    }

    clearUserForm() {
        this.currentUser = null;
        
        // Clear all form fields
        const fields = [
            'userName', 'userDisplayName', 'userEmail', 'userPassword',
            'userRole', 'userAge', 'userGender', 'userLocation',
            'userPersonality', 'userInterests', 'userLikes', 'userDislikes',
            'userCommunicationStyle', 'userLanguagePreference',
            'userContentPreferences', 'userNotes', 'userBio'
        ];
        
        fields.forEach(fieldId => this.setFieldValue(fieldId, ''));
        
        // Clear checkboxes
        const checkboxes = [
            'permissionChat', 'permissionDrawing', 'permissionCharacters',
            'permissionUserMgmt', 'permissionSettings',
            'contentNSFW', 'contentMature', 'contentViolence', 'contentProfanity'
        ];
        
        checkboxes.forEach(checkboxId => this.setCheckboxValue(checkboxId, false));
        
        // Reset selects to defaults
        this.setFieldValue('userRole', 'user');
        this.setFieldValue('userGender', 'not-specified');
        this.setFieldValue('userCommunicationStyle', 'casual');
        this.setFieldValue('userLanguagePreference', 'en');
    }

    setFieldValue(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = value;
        }
    }

    setCheckboxValue(checkboxId, checked) {
        const checkbox = document.getElementById(checkboxId);
        if (checkbox) {
            checkbox.checked = checked;
        }
    }

    getFieldValue(fieldId) {
        const field = document.getElementById(fieldId);
        return field ? field.value : '';
    }

    getCheckboxValue(checkboxId) {
        const checkbox = document.getElementById(checkboxId);
        return checkbox ? checkbox.checked : false;
    }

    buildUserData() {
        return {
            username: this.getFieldValue('userName'),
            displayName: this.getFieldValue('userDisplayName'),
            email: this.getFieldValue('userEmail'),
            password: this.getFieldValue('userPassword'),
            role: this.getFieldValue('userRole'),
            permissions: {
                chat: this.getCheckboxValue('permissionChat'),
                drawing: this.getCheckboxValue('permissionDrawing'),
                characters: this.getCheckboxValue('permissionCharacters'),
                userMgmt: this.getCheckboxValue('permissionUserMgmt'),
                settings: this.getCheckboxValue('permissionSettings')
            },
            demographics: {
                age: this.getFieldValue('userAge'),
                gender: this.getFieldValue('userGender'),
                location: this.getFieldValue('userLocation')
            },
            characteristics: {
                personality: this.getFieldValue('userPersonality'),
                interests: this.getFieldValue('userInterests'),
                likes: this.getFieldValue('userLikes'),
                dislikes: this.getFieldValue('userDislikes')
            },
            preferences: {
                communicationStyle: this.getFieldValue('userCommunicationStyle'),
                language: this.getFieldValue('userLanguagePreference')
            },
            content: {
                nsfw: this.getCheckboxValue('contentNSFW'),
                mature: this.getCheckboxValue('contentMature'),
                violence: this.getCheckboxValue('contentViolence'),
                profanity: this.getCheckboxValue('contentProfanity'),
                preferences: this.getFieldValue('userContentPreferences')
            },
            notes: {
                admin: this.getFieldValue('userNotes'),
                bio: this.getFieldValue('userBio')
            }
        };
    }

    showStatusMessage(message, type = 'info') {
        const statusDiv = document.getElementById('userManagementStatus');
        if (statusDiv) {
            statusDiv.textContent = message;
            statusDiv.className = `status-message ${type}`;
            statusDiv.style.display = 'block';
            
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 3000);
        }
    }
}

// Global functions for UI interaction
function createNewUser() {
    if (window.userManagementSystem) {
        window.userManagementSystem.clearUserForm();
        window.userManagementSystem.showStatusMessage('Ready to create new user', 'info');
        console.log('🆕 Creating new user');
    }
}

function duplicateUser() {
    if (window.userManagementSystem && window.userManagementSystem.currentUser) {
        const userData = window.userManagementSystem.buildUserData();
        userData.username = userData.username + '_copy';
        userData.displayName = userData.displayName + ' (Copy)';
        userData.password = ''; // Clear password for security
        
        window.userManagementSystem.loadUserData(userData);
        window.userManagementSystem.showStatusMessage('User duplicated - modify details and save', 'info');
        console.log('📋 User duplicated');
    } else {
        alert('Please select a user to duplicate first');
    }
}

function deleteUser() {
    if (window.userManagementSystem && window.userManagementSystem.currentUser) {
        const username = window.userManagementSystem.currentUser.username;
        if (confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
            // TODO: Implement backend deletion
            window.userManagementSystem.showStatusMessage('TODO: Backend user deletion not implemented yet', 'warning');
            console.log('🗑️ User deletion requested:', username);
        }
    } else {
        alert('Please select a user to delete first');
    }
}

function onUserChange() {
    if (window.userManagementSystem) {
        window.userManagementSystem.onUserChange();
    }
}

function saveUserProfile() {
    if (window.userManagementSystem) {
        const userData = window.userManagementSystem.buildUserData();
        
        // Validate required fields
        if (!userData.username.trim()) {
            window.userManagementSystem.showStatusMessage('Username is required', 'error');
            return;
        }
        
        // TODO: Connect to backend API
        // await fetch('/api/users', { method: 'POST', body: JSON.stringify(userData) });
        
        console.log('💾 Saving user data:', userData);
        window.userManagementSystem.showStatusMessage('TODO: Backend user saving not implemented yet - only username field connected', 'warning');
    }
}

function exportUser() {
    if (window.userManagementSystem && window.userManagementSystem.currentUser) {
        const userData = window.userManagementSystem.buildUserData();
        const dataStr = JSON.stringify(userData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `user_${userData.username}.json`;
        link.click();
        
        window.userManagementSystem.showStatusMessage('User data exported', 'success');
        console.log('📤 User exported:', userData.username);
    } else {
        alert('Please select a user to export first');
    }
}

function importUser() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const userData = JSON.parse(e.target.result);
                    if (window.userManagementSystem) {
                        window.userManagementSystem.loadUserData(userData);
                        window.userManagementSystem.showStatusMessage('User data imported successfully', 'success');
                        console.log('📥 User imported:', userData.username);
                    }
                } catch (error) {
                    alert('Error parsing JSON file: ' + error.message);
                }
            };
            reader.readAsText(file);
        }
    };
    input.click();
}

function sendPasswordReset() {
    if (window.userManagementSystem && window.userManagementSystem.currentUser) {
        const username = window.userManagementSystem.currentUser.username;
        // TODO: Implement backend password reset
        window.userManagementSystem.showStatusMessage('TODO: Backend password reset not implemented yet', 'warning');
        console.log('🔐 Password reset requested for:', username);
    } else {
        alert('Please select a user first');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.userManagementSystem = new UserManagementSystem();
});

// Export for global access
window.UserManagementSystem = UserManagementSystem;
