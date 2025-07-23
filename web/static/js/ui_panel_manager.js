/**
 * UI Panel Manager - Handles opening/closing of various UI panels
 * Separates UI management logic from the main HTML file
 */

class UIPanelManager {
    constructor() {
        this.openPanels = new Set();
        this.snapStates = new Map();
        this.init();
    }

    init() {
        console.log('🎛️ UI Panel Manager initialized');
        
        // Set up escape key handler to close panels
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.closeAllPanels();
            }
        });
    }

    // Chat Panel Management
    openChat() {
        const chatWindow = document.getElementById('chatWindow');
        if (chatWindow) {
            chatWindow.style.display = 'block';
            chatWindow.classList.add('open');
            this.openPanels.add('chat');
            console.log('💬 Chat window opened');
        }
    }

    closeChat() {
        const chatWindow = document.getElementById('chatWindow');
        if (chatWindow) {
            chatWindow.classList.remove('open');
            setTimeout(() => {
                chatWindow.style.display = 'none';
            }, 300);
            this.openPanels.delete('chat');
            console.log('💬 Chat window closed');
        }
    }

    toggleChatSnap() {
        const current = this.snapStates.get('chat') || false;
        this.snapStates.set('chat', !current);
        const chatWindow = document.getElementById('chatWindow');
        if (chatWindow) {
            chatWindow.classList.toggle('snapped', !current);
        }
        console.log('📌 Chat snap toggled:', !current);
    }

    // Settings Panel Management
    openSettings() {
        const settingsPanel = document.getElementById('settingsPanel');
        if (settingsPanel) {
            settingsPanel.style.display = 'block';
            settingsPanel.classList.add('open');
            this.openPanels.add('settings');
            console.log('⚙️ Settings panel opened');
        }
    }

    closeSettings() {
        const settingsPanel = document.getElementById('settingsPanel');
        if (settingsPanel) {
            settingsPanel.classList.remove('open');
            setTimeout(() => {
                settingsPanel.style.display = 'none';
            }, 300);
            this.openPanels.delete('settings');
            console.log('⚙️ Settings panel closed');
        }
    }

    toggleSettingsSnap() {
        const current = this.snapStates.get('settings') || false;
        this.snapStates.set('settings', !current);
        const settingsPanel = document.getElementById('settingsPanel');
        if (settingsPanel) {
            settingsPanel.classList.toggle('snapped', !current);
        }
        console.log('📌 Settings snap toggled:', !current);
    }

    // Character Profiles Panel Management
    openCharacterProfiles() {
        const characterPanel = document.getElementById('characterProfilesPanel');
        if (characterPanel) {
            characterPanel.style.display = 'block';
            characterPanel.classList.add('open');
            this.openPanels.add('characterProfiles');
            
            // Load character data when opening
            this.loadCharacterData();
            console.log('👥 Character profiles panel opened');
        }
    }

    closeCharacterProfiles() {
        const characterPanel = document.getElementById('characterProfilesPanel');
        if (characterPanel) {
            characterPanel.classList.remove('open');
            setTimeout(() => {
                characterPanel.style.display = 'none';
            }, 300);
            this.openPanels.delete('characterProfiles');
            console.log('👥 Character profiles panel closed');
        }
    }

    toggleCharacterProfilesSnap() {
        const current = this.snapStates.get('characterProfiles') || false;
        this.snapStates.set('characterProfiles', !current);
        const characterPanel = document.getElementById('characterProfilesPanel');
        if (characterPanel) {
            characterPanel.classList.toggle('snapped', !current);
        }
        console.log('📌 Character profiles snap toggled:', !current);
    }

    // User Management Panel
    openUserManagement() {
        const userPanel = document.getElementById('userManagementPanel');
        if (userPanel) {
            userPanel.style.display = 'block';
            userPanel.classList.add('open');
            this.openPanels.add('userManagement');
            
            // Load user data when opening
            this.loadUserData();
            console.log('👤 User management panel opened');
        }
    }

    closeUserManagement() {
        const userPanel = document.getElementById('userManagementPanel');
        if (userPanel) {
            userPanel.classList.remove('open');
            setTimeout(() => {
                userPanel.style.display = 'none';
            }, 300);
            this.openPanels.delete('userManagement');
            console.log('👤 User management panel closed');
        }
    }

    toggleUserManagementSnap() {
        const current = this.snapStates.get('userManagement') || false;
        this.snapStates.set('userManagement', !current);
        const userPanel = document.getElementById('userManagementPanel');
        if (userPanel) {
            userPanel.classList.toggle('snapped', !current);
        }
        console.log('📌 User management snap toggled:', !current);
    }

    // Drawing Tools Panel
    openDrawing() {
        console.log('🎨 Drawing tools requested - not yet implemented');
        // TODO: Implement drawing tools panel
        alert('Drawing tools feature coming soon!');
    }

    // Utility Functions
    closeAllPanels() {
        const panels = ['chat', 'settings', 'characterProfiles', 'userManagement'];
        panels.forEach(panel => {
            const closeMethod = this[`close${panel.charAt(0).toUpperCase() + panel.slice(1)}`];
            if (closeMethod && this.openPanels.has(panel)) {
                closeMethod.call(this);
            }
        });
        console.log('🚪 All panels closed');
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().then(() => {
                console.log('🖥️ Entered fullscreen mode');
            }).catch(err => {
                console.error('Error entering fullscreen:', err);
            });
        } else {
            document.exitFullscreen().then(() => {
                console.log('🖥️ Exited fullscreen mode');
            }).catch(err => {
                console.error('Error exiting fullscreen:', err);
            });
        }
    }

    // Data Loading Functions
    async loadCharacterData() {
        try {
            const response = await fetch('/api/live2d/characters');
            if (response.ok) {
                const characters = await response.json();
                this.populateCharacterSelect(characters);
            } else {
                console.error('Failed to load character data:', response.statusText);
            }
        } catch (error) {
            console.error('Error loading character data:', error);
        }
    }

    async loadUserData() {
        try {
            const response = await fetch('/api/users');
            if (response.ok) {
                const users = await response.json();
                this.populateUserSelect(users);
            } else {
                console.error('Failed to load user data:', response.statusText);
            }
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    }

    populateCharacterSelect(characters) {
        const select = document.getElementById('characterSelect');
        if (select) {
            select.innerHTML = '<option value="">Select a character...</option>';
            characters.forEach(character => {
                const option = document.createElement('option');
                option.value = character.model_id;
                option.textContent = character.name;
                select.appendChild(option);
            });
        }
    }

    populateUserSelect(users) {
        const select = document.getElementById('userSelect');
        if (select) {
            select.innerHTML = '<option value="">Select a user...</option>';
            users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = user.display_name || user.username;
                select.appendChild(option);
            });
        }
    }

    // Model Dialog Management
    showAddModelDialog() {
        const dialog = document.getElementById('modelSelectionDialog');
        if (dialog) {
            dialog.style.display = 'block';
            dialog.classList.add('open');
            this.openPanels.add('modelDialog');
            
            // Load available models for selection
            this.loadAvailableModelsForDialog();
            console.log('📦 Model selection dialog opened');
        } else {
            console.error('Model selection dialog element not found');
        }
    }

    closeAddModelDialog() {
        const dialog = document.getElementById('modelSelectionDialog');
        if (dialog) {
            dialog.classList.remove('open');
            setTimeout(() => {
                dialog.style.display = 'none';
            }, 300);
            this.openPanels.delete('modelDialog');
            console.log('📦 Model selection dialog closed');
        }
    }

    async loadAvailableModelsForDialog() {
        try {
            const response = await fetch('/api/live2d/models');
            if (response.ok) {
                const models = await response.json();
                this.populateModelDialogSelect(models);
            } else {
                console.error('Failed to load models for dialog:', response.statusText);
            }
        } catch (error) {
            console.error('Error loading models for dialog:', error);
        }
    }

    populateModelDialogSelect(models) {
        const select = document.getElementById('modelDialogSelect');
        if (select) {
            select.innerHTML = '<option value="">Select a model to add...</option>';
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.model_name;
                option.textContent = `${model.model_name} (${model.model_type || 'Unknown'})`;
                select.appendChild(option);
            });
        }
    }

    // Status Methods
    isPanelOpen(panelName) {
        return this.openPanels.has(panelName);
    }

    getPanelSnapState(panelName) {
        return this.snapStates.get(panelName) || false;
    }
}

// Create global instance
window.uiPanelManager = new UIPanelManager();

// Export global functions for onclick handlers
window.openChat = () => window.uiPanelManager.openChat();
window.closeChat = () => window.uiPanelManager.closeChat();
window.toggleChatSnap = () => window.uiPanelManager.toggleChatSnap();

window.openSettings = () => window.uiPanelManager.openSettings();
window.closeSettings = () => window.uiPanelManager.closeSettings();
window.toggleSettingsSnap = () => window.uiPanelManager.toggleSettingsSnap();

window.openCharacterProfiles = () => window.uiPanelManager.openCharacterProfiles();
window.closeCharacterProfiles = () => window.uiPanelManager.closeCharacterProfiles();
window.toggleCharacterProfilesSnap = () => window.uiPanelManager.toggleCharacterProfilesSnap();

window.openUserManagement = () => window.uiPanelManager.openUserManagement();
window.closeUserManagement = () => window.uiPanelManager.closeUserManagement();
window.toggleUserManagementSnap = () => window.uiPanelManager.toggleUserManagementSnap();

window.openDrawing = () => window.uiPanelManager.openDrawing();
window.toggleFullscreen = () => window.uiPanelManager.toggleFullscreen();

// Model dialog functions
window.showAddModelDialog = () => window.uiPanelManager.showAddModelDialog();
window.closeAddModelDialog = () => window.uiPanelManager.closeAddModelDialog();

// Enhanced model dialog functions
window.switchModelDialogTab = (tabName) => {
    // Hide all tab contents
    const tabs = ['existingModelsTab', 'importModelsTab', 'scanDirectoryTab'];
    tabs.forEach(tab => {
        const element = document.getElementById(tab);
        if (element) element.classList.remove('active');
    });
    
    // Hide all tab buttons
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(button => button.classList.remove('active'));
    
    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}ModelsTab`);
    if (selectedTab) selectedTab.classList.add('active');
    
    // Activate selected button
    const selectedButton = document.querySelector(`.tab-button[onclick="switchModelDialogTab('${tabName}')"]`);
    if (selectedButton) selectedButton.classList.add('active');
};

window.addSelectedModel = () => {
    const select = document.getElementById('modelDialogSelect');
    const modelName = select?.value;
    
    if (!modelName) {
        alert('Please select a model to add');
        return;
    }
    
    // Add model to active models (integrate with existing system)
    if (window.live2dModelManager) {
        window.live2dModelManager.loadModel(modelName);
    }
    
    console.log('📦 Adding model:', modelName);
    window.uiPanelManager.closeAddModelDialog();
};

window.scanForModels = () => {
    if (window.live2dModelImportManager) {
        window.live2dModelImportManager.scanForModels();
    }
};

window.refreshModelList = () => {
    if (window.live2dModelImportManager) {
        window.live2dModelImportManager.refreshModelList();
    }
};

console.log('✅ UI Panel Manager module loaded');
