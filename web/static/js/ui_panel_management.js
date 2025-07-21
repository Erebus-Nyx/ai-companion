/**
 * UI Panel Management System
 * Handles draggable panels, layout management, and window positioning
 */

// Global state variables for UI panels
let chatOpen = false;
let peopleOpen = false;
let settingsOpen = false;
let chatSnapped = false;
let peopleSnapped = false;
let settingsSnapped = false;

// Layout management constants
const LAYOUT_STORAGE_KEY = 'live2d_panel_layout';

// Dragging state variables
let isDragging = false;
let currentDragElement = null;
let dragOffset = { x: 0, y: 0 };

// Helper functions for layout management
function getElementPosition(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return { x: 0, y: 0 };
    
    const computedStyle = window.getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    
    if (element.style.left && element.style.left !== '') {
        const left = parseInt(element.style.left.replace('px', ''));
        const top = parseInt(element.style.top ? element.style.top.replace('px', '') : '0');
        return { x: left, y: top };
    }
    
    return {
        x: Math.max(0, rect.left),
        y: Math.max(0, rect.top)
    };
}

function getElementSize(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return { width: 0, height: 0 };
    
    return {
        width: element.offsetWidth,
        height: element.offsetHeight
    };
}

function applyElementLayout(element, layout) {
    // Reset all positioning properties to prevent cumulative drift
    element.style.left = '';
    element.style.right = '';
    element.style.top = '';
    element.style.bottom = '';
    element.style.transform = '';
    element.style.position = 'fixed';
    
    if (layout.position) {
        if (typeof layout.position.x === 'string') {
            if (layout.position.x === 'center') {
                element.style.left = '50%';
                element.style.transform = 'translateX(-50%)';
            } else if (layout.position.x.includes('left-')) {
                element.style.left = layout.position.x.replace('left-', '') + 'px';
            } else if (layout.position.x.includes('right-')) {
                element.style.right = layout.position.x.replace('right-', '') + 'px';
            }
        } else {
            element.style.left = Math.max(0, layout.position.x) + 'px';
        }
        
        if (typeof layout.position.y === 'string') {
            if (layout.position.y.includes('top-')) {
                element.style.top = layout.position.y.replace('top-', '') + 'px';
            } else if (layout.position.y.includes('bottom-')) {
                element.style.bottom = layout.position.y.replace('bottom-', '') + 'px';
            }
        } else {
            element.style.top = Math.max(0, layout.position.y) + 'px';
        }
    }
    
    if (layout.size) {
        if (layout.size.width !== 'auto') {
            element.style.width = layout.size.width + 'px';
        }
        if (layout.size.height !== 'auto') {
            element.style.height = layout.size.height + 'px';
        }
    }
}

// Save window layout to localStorage
function saveWindowLayout() {
    try {
        const layout = {
            chat: {
                open: chatOpen,
                snapped: chatSnapped,
                position: getElementPosition('chatWindow'),
                size: getElementSize('chatWindow')
            },
            people: {
                open: peopleOpen,
                snapped: peopleSnapped,
                position: getElementPosition('peoplePanel'),
                size: getElementSize('peoplePanel')
            },
            settings: {
                open: settingsOpen,
                snapped: settingsSnapped,
                position: getElementPosition('settingsPanel'),
                size: getElementSize('settingsPanel')
            }
        };
        
        localStorage.setItem(LAYOUT_STORAGE_KEY, JSON.stringify(layout));
        console.log('Window layout saved');
    } catch (error) {
        console.warn('Failed to save layout:', error);
    }
}

// Load window layout from localStorage
function loadWindowLayout() {
    try {
        const layoutData = localStorage.getItem(LAYOUT_STORAGE_KEY);
        if (!layoutData) return;
        
        const layout = JSON.parse(layoutData);
        
        // Restore chat window
        if (layout.chat) {
            chatOpen = layout.chat.open;
            chatSnapped = layout.chat.snapped;
            const chatWindow = document.getElementById('chatWindow');
            if (chatWindow) {
                if (chatOpen) chatWindow.classList.add('open');
                if (layout.chat.position) applyElementLayout(chatWindow, layout.chat);
            }
        }
        
        // Restore people panel
        if (layout.people) {
            peopleOpen = layout.people.open;
            peopleSnapped = layout.people.snapped;
            const peoplePanel = document.getElementById('peoplePanel');
            if (peoplePanel) {
                if (peopleOpen) peoplePanel.classList.add('open');
                if (layout.people.position) applyElementLayout(peoplePanel, layout.people);
            }
        }
        
        // Restore settings panel
        if (layout.settings) {
            settingsOpen = layout.settings.open;
            settingsSnapped = layout.settings.snapped;
            const settingsPanel = document.getElementById('settingsPanel');
            if (settingsPanel) {
                if (settingsOpen) settingsPanel.classList.add('open');
                if (layout.settings.position) applyElementLayout(settingsPanel, layout.settings);
            }
        }
        
        updateNavIconStates();
        console.log('Window layout loaded');
    } catch (error) {
        console.warn('Failed to load layout:', error);
    }
}

// Reset window layout to defaults
function resetWindowLayout() {
    console.log('Resetting window layout to defaults...');
    
    // Reset state variables
    chatOpen = false;
    peopleOpen = false;
    settingsOpen = false;
    chatSnapped = false;
    peopleSnapped = false;
    settingsSnapped = false;
    
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
    
    updateNavIconStates();
    localStorage.removeItem(LAYOUT_STORAGE_KEY);
    console.log('Window layout reset complete');
}

// Emergency function to bring off-screen windows back into view
function rescueOffScreenWindows() {
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
            if (name === 'Chat') chatOpen = true;
            if (name === 'People') peopleOpen = true;
            if (name === 'Settings') settingsOpen = true;
        }
    });
    
    updateNavIconStates();
    saveWindowLayout();
    console.log('Window rescue complete');
}

// Navigation functions
function updateNavIconStates() {
    const navIcons = document.querySelectorAll('.nav-icon');
    navIcons.forEach(icon => {
        icon.classList.remove('active');
    });
    
    if (chatOpen) {
        const chatIcon = document.querySelector('.nav-icon[onclick="openChat()"]');
        if (chatIcon) chatIcon.classList.add('active');
    }
    
    if (peopleOpen) {
        const peopleIcon = document.querySelector('.nav-icon[onclick="openPeople()"]');
        if (peopleIcon) peopleIcon.classList.add('active');
    }
    
    if (settingsOpen) {
        const settingsIcon = document.querySelector('.nav-icon[onclick="openSettings()"]');
        if (settingsIcon) settingsIcon.classList.add('active');
    }
}

// Chat functions
function openChat() {
    chatOpen = !chatOpen;
    const chatWindow = document.getElementById('chatWindow');
    
    if (chatOpen) {
        chatWindow.classList.add('open');
    } else {
        chatWindow.classList.remove('open');
    }
    
    updateNavIconStates();
    saveWindowLayout();
}

function closeChat() {
    chatOpen = false;
    const chatWindow = document.getElementById('chatWindow');
    chatWindow.classList.remove('open');
    updateNavIconStates();
    saveWindowLayout();
}

function toggleChatSnap() {
    const chatWindow = document.getElementById('chatWindow');
    const pinButton = chatWindow.querySelector('.control-btn[onclick="toggleChatSnap()"]');
    chatSnapped = !chatSnapped;
    
    if (chatSnapped) {
        chatWindow.style.position = 'fixed';
        chatWindow.style.transform = 'none';
        chatWindow.classList.add('pinned');
        if (pinButton) pinButton.classList.add('pinned');
    } else {
        chatWindow.style.position = 'fixed';
        chatWindow.classList.remove('pinned');
        if (pinButton) pinButton.classList.remove('pinned');
    }
    
    saveWindowLayout();
}

// People functions
function openPeople() {
    peopleOpen = !peopleOpen;
    const peoplePanel = document.getElementById('peoplePanel');
    
    if (peopleOpen) {
        peoplePanel.classList.add('open');
        populatePeopleModels();
    } else {
        peoplePanel.classList.remove('open');
    }
    
    updateNavIconStates();
    saveWindowLayout();
}

function closePeople() {
    peopleOpen = false;
    const peoplePanel = document.getElementById('peoplePanel');
    peoplePanel.classList.remove('open');
    updateNavIconStates();
    saveWindowLayout();
}

function togglePeopleSnap() {
    const peoplePanel = document.getElementById('peoplePanel');
    const pinButton = peoplePanel.querySelector('.control-btn[onclick="togglePeopleSnap()"]');
    peopleSnapped = !peopleSnapped;
    
    if (peopleSnapped) {
        peoplePanel.style.position = 'fixed';
        peoplePanel.classList.add('pinned');
        if (pinButton) pinButton.classList.add('pinned');
    } else {
        peoplePanel.style.position = 'fixed';
        peoplePanel.classList.remove('pinned');
        if (pinButton) pinButton.classList.remove('pinned');
    }
    
    saveWindowLayout();
}

// Settings functions
function openSettings() {
    settingsOpen = !settingsOpen;
    const settingsPanel = document.getElementById('settingsPanel');
    
    if (settingsOpen) {
        settingsPanel.classList.add('open');
    } else {
        settingsPanel.classList.remove('open');
    }
    
    updateNavIconStates();
    saveWindowLayout();
}

function closeSettings() {
    settingsOpen = false;
    const settingsPanel = document.getElementById('settingsPanel');
    settingsPanel.classList.remove('open');
    updateNavIconStates();
    saveWindowLayout();
}

function toggleSettingsSnap() {
    const settingsPanel = document.getElementById('settingsPanel');
    const pinButton = settingsPanel.querySelector('.control-btn[onclick="toggleSettingsSnap()"]');
    settingsSnapped = !settingsSnapped;
    
    if (settingsSnapped) {
        settingsPanel.style.position = 'fixed';
        settingsPanel.classList.add('pinned');
        if (pinButton) pinButton.classList.add('pinned');
    } else {
        settingsPanel.style.position = 'fixed';
        settingsPanel.classList.remove('pinned');
        if (pinButton) pinButton.classList.remove('pinned');
    }
    
    saveWindowLayout();
}

// Additional navigation functions
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

function toggleHelp() {
    console.log('Help functionality - to be implemented');
}

// Draggable functionality
function initializeDraggable() {
    const draggableElements = [
        { element: document.getElementById('chatWindow'), header: '.chat-header' },
        { element: document.getElementById('peoplePanel'), header: '.people-header' },
        { element: document.getElementById('settingsPanel'), header: '.settings-header' }
    ];
    
    draggableElements.forEach(({ element, header }) => {
        const headerElement = element.querySelector(header);
        if (headerElement) {
            headerElement.addEventListener('mousedown', (e) => startDrag(e, element));
        }
    });
    
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDrag);
}

function startDrag(e, element) {
    const pinButton = element.querySelector('.control-btn[onclick*="Snap"]');
    const isPinned = pinButton && pinButton.classList.contains('pinned');
    
    if (isPinned) {
        return;
    }
    
    isDragging = true;
    currentDragElement = element;
    
    const rect = element.getBoundingClientRect();
    dragOffset.x = e.clientX - rect.left;
    dragOffset.y = e.clientY - rect.top;
    
    element.style.zIndex = '300';
    document.body.style.cursor = 'move';
}

function drag(e) {
    if (!isDragging || !currentDragElement) return;
    
    const x = e.clientX - dragOffset.x;
    const y = e.clientY - dragOffset.y;
    
    const maxX = window.innerWidth - currentDragElement.offsetWidth;
    const maxY = window.innerHeight - currentDragElement.offsetHeight;
    
    const constrainedX = Math.max(0, Math.min(x, maxX));
    const constrainedY = Math.max(0, Math.min(y, maxY));
    
    currentDragElement.style.left = constrainedX + 'px';
    currentDragElement.style.top = constrainedY + 'px';
    currentDragElement.style.right = 'auto';
    currentDragElement.style.bottom = 'auto';
    currentDragElement.style.transform = 'none';
}

function stopDrag() {
    if (isDragging) {
        isDragging = false;
        if (currentDragElement) {
            currentDragElement.style.zIndex = '200';
        }
        currentDragElement = null;
        document.body.style.cursor = 'default';
        
        saveWindowLayout();
    }
}

// Export functions for global access
window.openChat = openChat;
window.closeChat = closeChat;
window.toggleChatSnap = toggleChatSnap;
window.openPeople = openPeople;
window.closePeople = closePeople;
window.togglePeopleSnap = togglePeopleSnap;
window.openSettings = openSettings;
window.closeSettings = closeSettings;
window.toggleSettingsSnap = toggleSettingsSnap;
window.toggleFullscreen = toggleFullscreen;
window.toggleHelp = toggleHelp;
window.resetWindowLayout = resetWindowLayout;
window.rescueOffScreenWindows = rescueOffScreenWindows;
window.loadWindowLayout = loadWindowLayout;
window.saveWindowLayout = saveWindowLayout;
window.initializeDraggable = initializeDraggable;
