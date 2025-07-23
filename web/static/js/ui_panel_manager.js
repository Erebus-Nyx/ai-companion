/**
 * UI Panel Manager - Window Layout and Navigation System
 * Handles window positioning, state management, and navigation
 */

class UIPanelManager {
    constructor() {
        this.chatOpen = false;
        this.peopleOpen = false;
        this.settingsOpen = false;
        this.characterProfilesOpen = false;
        this.characterProfilesSnapped = false;
        this.drawingOpen = false;
        this.userManagementOpen = false;
        this.userManagementSnapped = false;
        this.windowLayout = this.loadWindowLayout();
        
        // Dragging system state
        this.draggingWindow = null;
        this.dragOffset = { x: 0, y: 0 };
        
        this.init();
    }
    
    init() {
        this.initializeEventListeners();
        console.log('✅ UI Panel Manager initialized');
    }
    
    initializeEventListeners() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // Window resize handler
        window.addEventListener('resize', () => this.handleWindowResize());
        
        // Initialize draggable headers
        this.initializeDraggableHeaders();
        
        // Listen for user authentication events
        document.addEventListener('userChanged', (event) => {
            console.log('🔑 User authenticated, loading Live2D state:', event.detail.user);
            // Load Live2D state now that user is authenticated
            setTimeout(() => {
                if (window.live2dStateManager) {
                    window.live2dStateManager.loadState();
                    console.log('🎭 Live2D state loaded after user authentication');
                }
            }, 1000);
        });
    }
    
    initializeDraggableHeaders() {
        const headers = document.querySelectorAll('.chat-header, .people-header, .settings-header, .dialog-header, .user-profile-header, .character-profiles-header, .user-management-header, .drawing-header, .feedback-header');
        headers.forEach(header => {
            header.addEventListener('mousedown', (e) => this.startDragging(e));
            header.style.cursor = 'move'; // Add visual indicator
        });
        
        document.addEventListener('mousemove', (e) => this.handleDragging(e));
        document.addEventListener('mouseup', () => this.stopDragging());
    }
    
    // Check if user is authenticated and logged in
    isUserAuthenticated() {
        // Check if user selection popup is closed (indicates user is logged in)
        const userSelectionPopup = document.getElementById('userSelectionPopup');
        if (userSelectionPopup && userSelectionPopup.style.display !== 'none') {
            return false; // User selection popup is still shown
        }
        
        // Check if current user exists in avatar chat manager
        if (window.avatarChatManager && window.avatarChatManager.currentUser) {
            return true;
        }
        
        // Check for any other authentication indicators
        const userName = localStorage.getItem('currentUser');
        return userName !== null && userName !== '';
    }
    
    handleKeyboard(e) {
        // Ctrl+Shift+R to reset window layout
        if (e.ctrlKey && e.shiftKey && e.key === 'R') {
            e.preventDefault();
            console.log('Emergency layout reset triggered');
            this.resetWindowLayout();
        }
        
        // Ctrl+Shift+B to bring all windows back into view (rescue mode)
        if (e.ctrlKey && e.shiftKey && e.key === 'B') {
            e.preventDefault();
            console.log('Emergency rescue mode triggered');
            this.rescueOffScreenWindows();
        }
        
        // Escape key to close dialogs
        if (e.key === 'Escape') {
            this.closeDialogs();
        }
    }
    
    closeDialogs() {
        const dialogs = document.querySelectorAll('[id*="Dialog"]');
        dialogs.forEach(dialog => {
            if (dialog.style.display === 'flex') {
                dialog.style.display = 'none';
            }
        });
    }
    
    // Window dragging system
    startDragging(e) {
        const header = e.currentTarget;
        const window = header.closest('.chat-window, .people-panel, .settings-panel, .model-selection-dialog, .user-selection-dialog, .user-profile-panel, .character-profiles-panel, .user-management-panel, .drawing-panel, .resizable-panel');
        
        if (!window) return;
        
        this.draggingWindow = window;
        const rect = window.getBoundingClientRect();
        this.dragOffset.x = e.clientX - rect.left;
        this.dragOffset.y = e.clientY - rect.top;
        
        // Clear any existing transforms that might interfere with dragging
        window.style.transform = 'none';
        window.style.position = 'fixed';
        window.style.zIndex = '9999';
        
        e.preventDefault();
    }
    
    handleDragging(e) {
        if (!this.draggingWindow) return;
        
        const x = e.clientX - this.dragOffset.x;
        const y = e.clientY - this.dragOffset.y;
        
        // Keep window within viewport bounds
        const maxX = window.innerWidth - 300;
        const maxY = window.innerHeight - 100;
        
        const boundedX = Math.max(0, Math.min(x, maxX));
        const boundedY = Math.max(0, Math.min(y, maxY));
        
        this.draggingWindow.style.left = boundedX + 'px';
        this.draggingWindow.style.top = boundedY + 'px';
        this.draggingWindow.style.right = 'auto';
        this.draggingWindow.style.bottom = 'auto';
    }
    
    stopDragging() {
        if (this.draggingWindow) {
            this.draggingWindow.style.zIndex = '';
            this.draggingWindow = null;
            this.saveWindowLayout();
        }
    }
    
    // Window management functions
    openChat() {
        this.chatOpen = !this.chatOpen;
        const chatWindow = document.getElementById('chatWindow');
        
        if (this.chatOpen) {
            chatWindow.classList.add('open');
        } else {
            chatWindow.classList.remove('open');
        }
        
        this.updateNavIconStates();
        this.saveWindowLayout();
    }
    
    showChat() {
        if (!this.chatOpen) {
            this.chatOpen = true;
            const chatWindow = document.getElementById('chatWindow');
            chatWindow.classList.add('open');
            this.updateNavIconStates();
            this.saveWindowLayout();
        }
    }
    
    closeChat() {
        this.chatOpen = false;
        const chatWindow = document.getElementById('chatWindow');
        chatWindow.classList.remove('open');
        this.updateNavIconStates();
        this.saveWindowLayout();
    }
    
    openPeople() {
        this.peopleOpen = !this.peopleOpen;
        const peoplePanel = document.getElementById('peoplePanel');
        
        if (this.peopleOpen) {
            peoplePanel.classList.add('open');
        } else {
            peoplePanel.classList.remove('open');
        }
        
        this.updateNavIconStates();
        this.saveWindowLayout();
    }
    
    closePeople() {
        this.peopleOpen = false;
        const peoplePanel = document.getElementById('peoplePanel');
        peoplePanel.classList.remove('open');
        this.updateNavIconStates();
        this.saveWindowLayout();
    }
    
    openSettings() {
        this.settingsOpen = !this.settingsOpen;
        const settingsPanel = document.getElementById('settingsPanel');
        
        if (this.settingsOpen) {
            settingsPanel.classList.add('open');
        } else {
            settingsPanel.classList.remove('open');
        }
        
        this.updateNavIconStates();
        this.saveWindowLayout();
    }
    
    closeSettings() {
        this.settingsOpen = false;
        const settingsPanel = document.getElementById('settingsPanel');
        settingsPanel.classList.remove('open');
        this.updateNavIconStates();
        this.saveWindowLayout();
    }
    
    openCharacterProfiles() {
        this.characterProfilesOpen = !this.characterProfilesOpen;
        const characterProfilesPanel = document.getElementById('characterProfilesPanel');
        
        if (this.characterProfilesOpen) {
            characterProfilesPanel.classList.add('open');
        } else {
            characterProfilesPanel.classList.remove('open');
        }
        
        this.updateNavIconStates();
        this.saveWindowLayout();
    }
    
    closeCharacterProfiles() {
        this.characterProfilesOpen = false;
        const characterProfilesPanel = document.getElementById('characterProfilesPanel');
        characterProfilesPanel.classList.remove('open');
        this.updateNavIconStates();
        this.saveWindowLayout();
    }
    
    toggleCharacterProfilesSnap() {
        const panel = document.getElementById('characterProfilesPanel');
        if (panel) {
            panel.classList.toggle('snap-to-edge');
        }
    }
    
    openUserManagement() {
        this.userManagementOpen = !this.userManagementOpen;
        const userManagementPanel = document.getElementById('userManagementPanel');
        
        if (this.userManagementOpen) {
            userManagementPanel.classList.add('open');
        } else {
            userManagementPanel.classList.remove('open');
        }
        
        this.updateNavIconStates();
        this.saveWindowLayout();
    }
    
    closeUserManagement() {
        this.userManagementOpen = false;
        const userManagementPanel = document.getElementById('userManagementPanel');
        userManagementPanel.classList.remove('open');
        this.updateNavIconStates();
        this.saveWindowLayout();
    }
    
    toggleUserManagementSnap() {
        const panel = document.getElementById('userManagementPanel');
        if (panel) {
            panel.classList.toggle('snap-to-edge');
        }
    }
    
    // Navigation and fullscreen functions
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }
    
    toggleHelp() {
        const helpPanel = document.getElementById('helpPanel');
        if (helpPanel) {
            helpPanel.classList.toggle('open');
        } else {
            // Create help panel if it doesn't exist
            this.createHelpPanel();
        }
    }
    
    createHelpPanel() {
        const helpPanel = document.createElement('div');
        helpPanel.id = 'helpPanel';
        helpPanel.className = 'help-panel';
        helpPanel.innerHTML = `
            <div class="help-header">
                <span class="help-title">Help & Controls</span>
                <button class="close-btn" onclick="uiPanelManager.toggleHelp()">×</button>
            </div>
            <div class="help-content">
                <h3>Keyboard Shortcuts</h3>
                <ul>
                    <li><kbd>Ctrl+Shift+R</kbd> - Reset window layout</li>
                    <li><kbd>Ctrl+Shift+B</kbd> - Rescue off-screen windows</li>
                    <li><kbd>Escape</kbd> - Close dialogs</li>
                </ul>
                <h3>Mouse Controls</h3>
                <ul>
                    <li>Drag window headers to move panels</li>
                    <li>Click avatar to drag model</li>
                    <li>Scroll on avatar to scale model</li>
                </ul>
            </div>
        `;
        document.body.appendChild(helpPanel);
        helpPanel.classList.add('open');
    }
    
    // Snap functionality
    toggleChatSnap() {
        const chatWindow = document.getElementById('chatWindow');
        this.chatSnapped = !this.chatSnapped;
        
        if (this.chatSnapped) {
            chatWindow.classList.add('pinned');
        } else {
            chatWindow.classList.remove('pinned');
        }
        
        this.saveWindowLayout();
    }
    
    togglePeopleSnap() {
        const peoplePanel = document.getElementById('peoplePanel');
        this.peopleSnapped = !this.peopleSnapped;
        
        if (this.peopleSnapped) {
            peoplePanel.classList.add('pinned');
        } else {
            peoplePanel.classList.remove('pinned');
        }
        
        this.saveWindowLayout();
    }
    
    toggleSettingsSnap() {
        const settingsPanel = document.getElementById('settingsPanel');
        this.settingsSnapped = !this.settingsSnapped;
        
        if (this.settingsSnapped) {
            settingsPanel.classList.add('pinned');
        } else {
            settingsPanel.classList.remove('pinned');
        }
        
        this.saveWindowLayout();
    }
    
    updateNavIconStates() {
        const navIcons = document.querySelectorAll('.nav-icon');
        navIcons.forEach(icon => {
            icon.classList.remove('active');
        });
        
        if (this.chatOpen) {
            const chatIcon = document.querySelector('.nav-icon[onclick*="Chat"]');
            if (chatIcon) chatIcon.classList.add('active');
        }
        
        if (this.peopleOpen) {
            const peopleIcon = document.querySelector('.nav-icon[onclick*="People"]');
            if (peopleIcon) peopleIcon.classList.add('active');
        }
        
        if (this.characterProfilesOpen) {
            const characterIcon = document.querySelector('.nav-icon[onclick*="CharacterProfiles"]');
            if (characterIcon) characterIcon.classList.add('active');
        }
        
        if (this.userManagementOpen) {
            const userIcon = document.querySelector('.nav-icon[onclick*="UserManagement"]');
            if (userIcon) userIcon.classList.add('active');
        }
        
        if (this.settingsOpen) {
            const settingsIcon = document.querySelector('.nav-icon[onclick*="Settings"]');
            if (settingsIcon) settingsIcon.classList.add('active');
        }
    }
    
    // Layout persistence
    saveWindowLayout() {
        const layout = {
            chat: {
                open: this.chatOpen,
                snapped: this.chatSnapped,
                position: this.getElementLayout(document.getElementById('chatWindow'))
            },
            people: {
                open: this.peopleOpen,
                snapped: this.peopleSnapped,
                position: this.getElementLayout(document.getElementById('peoplePanel'))
            },
            characterProfiles: {
                open: this.characterProfilesOpen,
                snapped: this.characterProfilesSnapped,
                position: this.getElementLayout(document.getElementById('characterProfilesPanel'))
            },
            settings: {
                open: this.settingsOpen,
                snapped: this.settingsSnapped,
                position: this.getElementLayout(document.getElementById('settingsPanel'))
            }
        };
        
        try {
            localStorage.setItem('ai2d_chat_window_layout', JSON.stringify(layout));
            
            // Also save Live2D state when saving layout
            if (window.live2dStateManager) {
                window.live2dStateManager.saveState();
            }
            
        } catch (error) {
            console.warn('Failed to save window layout:', error);
        }
    }
    
    loadWindowLayout() {
        try {
            const saved = localStorage.getItem('ai2d_chat_window_layout');
            if (!saved) return;
            
            const layout = JSON.parse(saved);
            
            // Restore chat window
            if (layout.chat) {
                this.chatOpen = layout.chat.open;
                this.chatSnapped = layout.chat.snapped;
                const chatWindow = document.getElementById('chatWindow');
                if (chatWindow) {
                    if (this.chatOpen) chatWindow.classList.add('open');
                    if (this.chatSnapped) chatWindow.classList.add('pinned');
                    if (layout.chat.position) this.applyElementLayout(chatWindow, layout.chat);
                }
            }
            
            // Restore people panel
            if (layout.people) {
                this.peopleOpen = layout.people.open;
                this.peopleSnapped = layout.people.snapped;
                const peoplePanel = document.getElementById('peoplePanel');
                if (peoplePanel) {
                    if (this.peopleOpen) peoplePanel.classList.add('open');
                    if (this.peopleSnapped) peoplePanel.classList.add('pinned');
                    if (layout.people.position) this.applyElementLayout(peoplePanel, layout.people);
                }
            }
            
            // Restore character profiles panel
            if (layout.characterProfiles) {
                this.characterProfilesOpen = layout.characterProfiles.open;
                this.characterProfilesSnapped = layout.characterProfiles.snapped;
                const characterProfilesPanel = document.getElementById('characterProfilesPanel');
                if (characterProfilesPanel) {
                    if (this.characterProfilesOpen) characterProfilesPanel.classList.add('open');
                    if (this.characterProfilesSnapped) characterProfilesPanel.classList.add('pinned');
                    if (layout.characterProfiles.position) this.applyElementLayout(characterProfilesPanel, layout.characterProfiles);
                }
            }
            
            // Restore settings panel
            if (layout.settings) {
                this.settingsOpen = layout.settings.open;
                this.settingsSnapped = layout.settings.snapped;
                const settingsPanel = document.getElementById('settingsPanel');
                if (settingsPanel) {
                    if (this.settingsOpen) settingsPanel.classList.add('open');
                    if (this.settingsSnapped) settingsPanel.classList.add('pinned');
                    if (layout.settings.position) this.applyElementLayout(settingsPanel, layout.settings);
                }
            }
            
            this.updateNavIconStates();
            console.log('Window layout loaded');
            
            // Load Live2D state only after user is authenticated
            setTimeout(() => {
                // Check if user is logged in before loading Live2D state
                if (window.live2dStateManager && this.isUserAuthenticated()) {
                    console.log('User authenticated, loading Live2D state...');
                    window.live2dStateManager.loadState();
                } else {
                    console.log('Skipping Live2D state load - user not authenticated yet');
                }
            }, 2000);
            
        } catch (error) {
            console.warn('Failed to load layout:', error);
        }
    }
    
    getElementLayout(element) {
        if (!element) return null;
        
        const rect = element.getBoundingClientRect();
        return {
            left: element.style.left,
            top: element.style.top,
            right: element.style.right,
            bottom: element.style.bottom,
            width: rect.width,
            height: rect.height
        };
    }
    
    applyElementLayout(element, layout) {
        if (!element || !layout.position) return;
        
        const pos = layout.position;
        if (pos.left) element.style.left = pos.left;
        if (pos.top) element.style.top = pos.top;
        if (pos.right) element.style.right = pos.right;
        if (pos.bottom) element.style.bottom = pos.bottom;
    }
    
    resetWindowLayout() {
        console.log('Resetting window layout to defaults...');
        
        // Reset state variables
        this.chatOpen = false;
        this.peopleOpen = false;
        this.settingsOpen = false;
        this.chatSnapped = false;
        this.peopleSnapped = false;
        this.settingsSnapped = false;
        
        // Reset chat window
        const chatWindow = document.getElementById('chatWindow');
        if (chatWindow) {
            chatWindow.classList.remove('open', 'pinned');
            chatWindow.style.cssText = '';
        }
        
        // Reset people panel
        const peoplePanel = document.getElementById('peoplePanel');
        if (peoplePanel) {
            peoplePanel.classList.remove('open', 'pinned');
            peoplePanel.style.cssText = '';
        }
        
        // Reset settings panel
        const settingsPanel = document.getElementById('settingsPanel');
        if (settingsPanel) {
            settingsPanel.classList.remove('open', 'pinned');
            settingsPanel.style.cssText = '';
        }
        
        this.updateNavIconStates();
        this.clearSavedLayout();
        console.log('Window layout reset complete');
    }
    
    clearSavedLayout() {
        try {
            localStorage.removeItem('ai2d_chat_window_layout');
        } catch (error) {
            console.warn('Failed to clear saved layout:', error);
        }
    }
    
    rescueOffScreenWindows() {
        console.log('Rescuing off-screen windows...');
        
        const windows = [
            { element: document.getElementById('chatWindow'), name: 'Chat' },
            { element: document.getElementById('peoplePanel'), name: 'People' },
            { element: document.getElementById('settingsPanel'), name: 'Settings' }
        ];
        
        windows.forEach(({ element, name }) => {
            if (!element) return;
            
            const rect = element.getBoundingClientRect();
            const isOffScreen = rect.left < 0 || rect.top < 0 || 
                               rect.right > window.innerWidth || 
                               rect.bottom > window.innerHeight;
            
            if (isOffScreen) {
                console.log(`Rescuing ${name} window from off-screen position`);
                
                // Reset positioning and place in safe area
                element.style.left = '';
                element.style.right = '';
                element.style.top = '';
                element.style.bottom = '';
                element.style.transform = '';
                element.style.position = 'fixed';
                
                // Place in center-ish safe area
                const safeX = Math.max(20, Math.min(window.innerWidth - 300, 100));
                const safeY = Math.max(20, Math.min(window.innerHeight - 200, 100));
                
                element.style.left = safeX + 'px';
                element.style.top = safeY + 'px';
                
                // Make sure it's visible
                element.classList.add('open');
                if (name === 'Chat') this.chatOpen = true;
                if (name === 'People') this.peopleOpen = true;
                if (name === 'Settings') this.settingsOpen = true;
            }
        });
        
        this.updateNavIconStates();
        this.saveWindowLayout();
        console.log('Window rescue complete');
    }
    
    handleWindowResize() {
        // Ensure windows stay within bounds on resize
        setTimeout(() => {
            this.rescueOffScreenWindows();
        }, 100);
    }
}

// Global instance
let uiPanelManager = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    uiPanelManager = new UIPanelManager();
    window.uiPanelManager = uiPanelManager;
});

// Legacy function compatibility
window.openChat = () => uiPanelManager?.openChat();
window.showChat = () => uiPanelManager?.showChat();
window.closeChat = () => uiPanelManager?.closeChat();
window.openPeople = () => uiPanelManager?.openPeople();
window.closePeople = () => uiPanelManager?.closePeople();
window.openSettings = () => uiPanelManager?.openSettings();
window.closeSettings = () => uiPanelManager?.closeSettings();
window.toggleChatSnap = () => uiPanelManager?.toggleChatSnap();
window.togglePeopleSnap = () => uiPanelManager?.togglePeopleSnap();
window.toggleSettingsSnap = () => uiPanelManager?.toggleSettingsSnap();
window.toggleFullscreen = () => uiPanelManager?.toggleFullscreen();
window.toggleHelp = () => uiPanelManager?.toggleHelp();
window.openCharacterProfiles = () => uiPanelManager?.openCharacterProfiles();
window.closeCharacterProfiles = () => uiPanelManager?.closeCharacterProfiles();
window.toggleCharacterProfilesSnap = () => uiPanelManager?.toggleCharacterProfilesSnap();
window.openUserManagement = () => uiPanelManager?.openUserManagement();
window.closeUserManagement = () => uiPanelManager?.closeUserManagement();
window.toggleUserManagementSnap = () => uiPanelManager?.toggleUserManagementSnap();
