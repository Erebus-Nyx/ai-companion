/**
 * Combined UI Panel Manager - Window Layout and Navigation System
 * Handles window positioning, state management, and navigation
 * Snap-to-edge functionality is removed.
 */

class UIPanelManager2 {
    constructor() {
        // Panel state
        this.panels = {
            chat: { open: false },
            people: { open: false },
            settings: { open: false },
            characterProfiles: { open: false },
            userManagement: { open: false }
        };
        this.LAYOUT_STORAGE_KEY = 'ai2d_chat_window_layout_v2';
        this.currentUser = null;

        // Drag state
        this.draggingWindow = null;
        this.dragOffset = { x: 0, y: 0 };

        this.init();
    }

    init() {
        this.initializeEventListeners();
        // Wait for user authentication before loading layout
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeDraggableHeaders();
            // Check for user authentication events
            document.addEventListener('userChanged', (event) => {
                this.currentUser = event.detail.user;
                this.loadWindowLayout();
            });
            // Also check if user is already set
            setTimeout(() => {
                if (window.avatarChatManager && window.avatarChatManager.currentUser) {
                    this.currentUser = window.avatarChatManager.currentUser;
                    this.loadWindowLayout();
                }
            }, 500);
        });
        console.log('✅ UI Panel Manager 2 initialized');
    }

    initializeEventListeners() {
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        window.addEventListener('resize', () => this.handleWindowResize());
        // Removed duplicate DOMContentLoaded for draggable headers
    }

    initializeDraggableHeaders() {
        const headers = document.querySelectorAll(
            '.chat-header, .people-header, .settings-header, .dialog-header, .user-profile-header, .character-profiles-header, .user-management-header, .drawing-header, .feedback-header'
        );
        headers.forEach(header => {
            header.addEventListener('mousedown', (e) => this.startDragging(e));
            header.style.cursor = 'move';
        });
        document.addEventListener('mousemove', (e) => this.handleDragging(e));
        document.addEventListener('mouseup', () => this.stopDragging());
    }

    handleKeyboard(e) {
        if (e.ctrlKey && e.shiftKey && e.key === 'R') {
            e.preventDefault();
            this.resetWindowLayout();
        }
        if (e.ctrlKey && e.shiftKey && e.key === 'B') {
            e.preventDefault();
            this.rescueOffScreenWindows();
        }
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

    // --- Dragging ---
    startDragging(e) {
        const header = e.currentTarget;
        const windowEl = header.closest(
            '.chat-window, .people-panel, .settings-panel, .model-selection-dialog, .user-selection-dialog, .user-profile-panel, .character-profiles-panel, .user-management-panel, .drawing-panel, .resizable-panel'
        );
        if (!windowEl) return;
        this.draggingWindow = windowEl;
        const rect = windowEl.getBoundingClientRect();
        this.dragOffset.x = e.clientX - rect.left;
        this.dragOffset.y = e.clientY - rect.top;
        windowEl.style.transform = 'none';
        windowEl.style.position = 'fixed';
        windowEl.style.zIndex = '9999';
        e.preventDefault();
    }

    handleDragging(e) {
        if (!this.draggingWindow) return;
        const x = e.clientX - this.dragOffset.x;
        const y = e.clientY - this.dragOffset.y;
        const maxX = window.innerWidth - this.draggingWindow.offsetWidth;
        const maxY = window.innerHeight - this.draggingWindow.offsetHeight;
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

    // --- Panel Open/Close ---
    openPanel(panel) {
        this.panels[panel].open = !this.panels[panel].open;
        const el = this.getPanelElement(panel);
        if (el) {
            if (this.panels[panel].open) el.classList.add('open');
            else el.classList.remove('open');
        }
        this.updateNavIconStates();
        this.saveWindowLayout();
    }

    closePanel(panel) {
        this.panels[panel].open = false;
        const el = this.getPanelElement(panel);
        if (el) el.classList.remove('open');
        this.updateNavIconStates();
        this.saveWindowLayout();
    }

    getPanelElement(panel) {
        switch (panel) {
            case 'chat': return document.getElementById('chatWindow');
            case 'people': return document.getElementById('peoplePanel');
            case 'settings': return document.getElementById('settingsPanel');
            case 'characterProfiles': return document.getElementById('characterProfilesPanel');
            case 'userManagement': return document.getElementById('userManagementPanel');
            default: return null;
        }
    }

    // --- Layout Persistence ---
    getElementLayout(element) {
        if (!element) return null;
        // Use actual style values for accurate position tracking
        const computedStyle = window.getComputedStyle(element);
        let left = parseFloat(element.style.left) || 0;
        let top = parseFloat(element.style.top) || 0;
        
        // If element has explicit style positioning, use that
        if (element.style.left && element.style.left !== '') {
            left = parseFloat(element.style.left);
        } else if (computedStyle.left && computedStyle.left !== 'auto') {
            left = parseFloat(computedStyle.left);
        } else {
            // Fallback to current position
            left = element.getBoundingClientRect().left;
        }

        if (element.style.top && element.style.top !== '') {
            top = parseFloat(element.style.top);
        } else if (computedStyle.top && computedStyle.top !== 'auto') {
            top = parseFloat(computedStyle.top);
        } else {
            // Fallback to current position
            top = element.getBoundingClientRect().top;
        }

        const rect = element.getBoundingClientRect();
        return {
            left,
            top,
            width: rect.width,
            height: rect.height
        };
    }

    applyElementLayout(element, layout) {
        if (!element || !layout) return;
        const width = layout.width || 300;
        const height = layout.height || 100;
        const maxX = window.innerWidth - width;
        const maxY = window.innerHeight - height;
        let left = typeof layout.left === 'number' ? layout.left : Math.max(0, (window.innerWidth - width) / 2);
        let top = typeof layout.top === 'number' ? layout.top : Math.max(0, (window.innerHeight - height) / 2);
        left = Math.max(0, Math.min(left, maxX));
        top = Math.max(0, Math.min(top, maxY));
        element.style.position = 'fixed';
        element.style.left = left + 'px';
        element.style.top = top + 'px';
        element.style.right = 'auto';
        element.style.bottom = 'auto';
    }

    saveWindowLayout() {
        if (!this.currentUser) {
            console.log('[UIPanelManager2] No user authenticated, skipping layout save');
            return;
        }

        const layout = {};
        for (const panel in this.panels) {
            const el = this.getPanelElement(panel);
            layout[panel] = {
                open: this.panels[panel].open,
                position: this.getElementLayout(el)
            };
        }
        try {
            const userSpecificKey = `${this.LAYOUT_STORAGE_KEY}_${this.currentUser}`;
            localStorage.setItem(userSpecificKey, JSON.stringify(layout));
            console.log(`[UIPanelManager2] Layout saved for user: ${this.currentUser}`);
        } catch (error) {
            console.warn('Failed to save window layout:', error);
        }
    }

    loadWindowLayout() {
        if (!this.currentUser) {
            console.log('[UIPanelManager2] No user authenticated, skipping layout load');
            return;
        }

        try {
            const userSpecificKey = `${this.LAYOUT_STORAGE_KEY}_${this.currentUser}`;
            const saved = localStorage.getItem(userSpecificKey);
            if (!saved) {
                console.log(`[UIPanelManager2] No saved layout found for user: ${this.currentUser}`);
                return;
            }
            
            const layout = JSON.parse(saved);
            console.log(`[UIPanelManager2] Loading layout for user: ${this.currentUser}`);
            
            // Use setTimeout to ensure DOM is fully rendered and CSS applied
            setTimeout(() => {
                for (const panel in this.panels) {
                    const el = this.getPanelElement(panel);
                    if (el && layout[panel]) {
                        // Force position immediately, even if closed
                        if (layout[panel].position) {
                            // Override any CSS positioning first
                            el.style.position = 'fixed';
                            el.style.transform = 'none';
                            el.style.left = 'auto';
                            el.style.right = 'auto';
                            el.style.top = 'auto';
                            el.style.bottom = 'auto';
                            
                            // Apply saved position
                            this.applyElementLayout(el, layout[panel].position);
                        }
                        
                        // Set open state after positioning
                        if (layout[panel].open) {
                            el.classList.add('open');
                            this.panels[panel].open = true;
                        } else {
                            el.classList.remove('open');
                            this.panels[panel].open = false;
                        }
                    }
                }
                this.updateNavIconStates();
            }, 100);
            
        } catch (error) {
            console.warn('Failed to load layout:', error);
        }
    }

    resetWindowLayout() {
        for (const panel in this.panels) {
            this.panels[panel].open = false;
            const el = this.getPanelElement(panel);
            if (el) {
                el.classList.remove('open');
                el.style.cssText = '';
            }
        }
        this.updateNavIconStates();
        if (this.currentUser) {
            const userSpecificKey = `${this.LAYOUT_STORAGE_KEY}_${this.currentUser}`;
            localStorage.removeItem(userSpecificKey);
        }
    }

    rescueOffScreenWindows() {
        const panels = ['chat', 'people', 'settings', 'characterProfiles', 'userManagement'];
        panels.forEach(panel => {
            const el = this.getPanelElement(panel);
            if (!el) return;
            const rect = el.getBoundingClientRect();
            const isOffScreen = rect.left < 0 || rect.top < 0 ||
                rect.right > window.innerWidth ||
                rect.bottom > window.innerHeight;
            if (isOffScreen) {
                el.style.left = '';
                el.style.right = '';
                el.style.top = '';
                el.style.bottom = '';
                el.style.transform = '';
                el.style.position = 'fixed';
                const safeX = Math.max(20, Math.min(window.innerWidth - 300, 100));
                const safeY = Math.max(20, Math.min(window.innerHeight - 200, 100));
                el.style.left = safeX + 'px';
                el.style.top = safeY + 'px';
                el.classList.add('open');
                this.panels[panel].open = true;
            }
        });
        this.updateNavIconStates();
        this.saveWindowLayout();
    }

    handleWindowResize() {
        setTimeout(() => {
            this.rescueOffScreenWindows();
        }, 100);
    }

    // --- Navigation ---
    updateNavIconStates() {
        const navIcons = document.querySelectorAll('.nav-icon');
        navIcons.forEach(icon => icon.classList.remove('active'));
        if (this.panels.chat.open) {
            const chatIcon = document.querySelector('.nav-icon[onclick*="Chat"]');
            if (chatIcon) chatIcon.classList.add('active');
        }
        if (this.panels.people.open) {
            const peopleIcon = document.querySelector('.nav-icon[onclick*="People"]');
            if (peopleIcon) peopleIcon.classList.add('active');
        }
        if (this.panels.characterProfiles && this.panels.characterProfiles.open) {
            const characterIcon = document.querySelector('.nav-icon[onclick*="CharacterProfiles"]');
            if (characterIcon) characterIcon.classList.add('active');
        }
        if (this.panels.userManagement && this.panels.userManagement.open) {
            const userIcon = document.querySelector('.nav-icon[onclick*="UserManagement"]');
            if (userIcon) userIcon.classList.add('active');
        }
        if (this.panels.settings.open) {
            const settingsIcon = document.querySelector('.nav-icon[onclick*="Settings"]');
            if (settingsIcon) settingsIcon.classList.add('active');
        }
    }

    // --- Fullscreen/Help ---
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
                <button class="close-btn" onclick="uiPanelManager2.toggleHelp()">×</button>
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
                </ul>
            </div>
        `;
        document.body.appendChild(helpPanel);
        helpPanel.classList.add('open');
    }
}

// --- Global instance and function exports ---
let uiPanelManager2 = new UIPanelManager2();
window.uiPanelManager2 = uiPanelManager2;

// Exported functions for legacy/global use
window.openChat = () => uiPanelManager2.openPanel('chat');
window.closeChat = () => uiPanelManager2.closePanel('chat');
window.openPeople = () => uiPanelManager2.openPanel('people');
window.closePeople = () => uiPanelManager2.closePanel('people');
window.openSettings = () => uiPanelManager2.openPanel('settings');
window.closeSettings = () => uiPanelManager2.closePanel('settings');
window.openCharacterProfiles = () => uiPanelManager2.openPanel('characterProfiles');
window.closeCharacterProfiles = () => uiPanelManager2.closePanel('characterProfiles');
window.openUserManagement = () => uiPanelManager2.openPanel('userManagement');
window.closeUserManagement = () => uiPanelManager2.closePanel('userManagement');
window.toggleFullscreen = () => uiPanelManager2.toggleFullscreen();
window.toggleHelp = () => uiPanelManager2.toggleHelp();
window.resetWindowLayout = () => uiPanelManager2.resetWindowLayout();
window.rescueOffScreenWindows = () => uiPanelManager2.rescueOffScreenWindows();
window.saveWindowLayout = () => uiPanelManager2.saveWindowLayout();
window.loadWindowLayout = () => uiPanelManager2.loadWindowLayout();

// NOTE: Model selection dialog functions are handled by ui_people_panel.js
// Removed duplicate implementation to prevent conflicts

// Handle Escape key for dialog - ensure this doesn't conflict
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const dialog = document.getElementById('modelSelectionDialog');
        if (dialog && (dialog.style.display === 'block' || dialog.style.display === 'flex')) {
            if (typeof window.closeAddModelDialog === 'function') {
                window.closeAddModelDialog();
            }
        }
    }
});

// Debug logging on load
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        console.log('🔍 Model dialog debug check:');
        console.log('- showAddModelDialog function:', typeof window.showAddModelDialog);
        console.log('- Add button element:', !!document.querySelector('.add-character-btn'));
        console.log('- Dialog element:', !!document.getElementById('modelSelectionDialog'));
        
        // Test the function is accessible
        if (typeof window.showAddModelDialog === 'function') {
            console.log('✅ showAddModelDialog is properly defined');
        } else {
            console.error('❌ showAddModelDialog is not properly defined');
        }
    }, 2000);
});
