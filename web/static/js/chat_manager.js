// chat.js
// Multi-avatar chat and message handling logic for frontend

// Avatar management for chat with user context
class AvatarChatManager {
    constructor() {
        this.activeAvatars = new Map(); // Map of avatar_id -> avatar_data
        this.speakingAvatar = null; // Currently speaking avatar
        this.avatarDatabase = new Map(); // Avatar-specific information
        this.messageHistory = []; // Chat history with avatar attribution
        this.currentUser = null; // Current user information
        this.userProfile = null; // User profile data
        this.chatHistory = []; // Full chat history from database
        this.initializeAvatarSystem();
    }

    async initializeAvatarSystem() {
        // Load current user information
        await this.loadCurrentUser();
        // Load avatar database information
        await this.loadAvatarDatabase();
        // Load chat history
        await this.loadChatHistory();
        // Set up listeners for avatar changes
        this.setupAvatarListeners();
        console.log('🎭 Multi-avatar chat system initialized with user context');
    }

    async loadCurrentUser() {
        try {
            const response = await fetch('/api/users/current');
            if (response.ok) {
                this.currentUser = await response.json();
                console.log('👤 Current user loaded:', this.currentUser.display_name);
                
                // Load user profile
                await this.loadUserProfile();
            } else {
                console.warn('No current user found');
                // Create a default user for this session
                this.currentUser = { id: 'session_user', username: 'session_user', display_name: 'User' };
            }
        } catch (error) {
            console.warn('Failed to load current user:', error);
            this.currentUser = { id: 'session_user', username: 'session_user', display_name: 'User' };
        }
    }

    async loadUserProfile() {
        if (!this.currentUser) return;

        try {
            const response = await fetch(`/api/users/${this.currentUser.id}/profile`);
            if (response.ok) {
                this.userProfile = await response.json();
                console.log('📋 User profile loaded');
            }
        } catch (error) {
            console.warn('Failed to load user profile:', error);
        }
    }

    async loadChatHistory(limit = 50) {
        if (!this.currentUser) return;

        try {
            const response = await fetch(`/api/chat/history?user_id=${this.currentUser.id}&limit=${limit}`);
            if (response.ok) {
                const data = await response.json();
                this.chatHistory = data.history || [];
                console.log(`📚 Loaded ${this.chatHistory.length} previous chat messages`);
                
                // Display recent history in chat window
                this.displayChatHistory();
            }
        } catch (error) {
            console.warn('Failed to load chat history:', error);
        }
    }

    async loadAvatarDatabase() {
        try {
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
            const response = await fetch(`${apiBaseUrl}/api/live2d/models`);
            if (response.ok) {
                const models = await response.json();
                models.forEach(model => {
                    this.avatarDatabase.set(model.model_name, {
                        id: model.model_name,
                        name: model.model_name,
                        displayName: this.formatAvatarName(model.model_name),
                        description: model.description || '',
                        motions: model.motions || {},
                        expressions: model.expressions || {},
                        lastActive: null,
                        messageCount: 0,
                        personality: null // To be loaded separately when personality system is rebuilt
                    });
                });
                console.log(`📦 Loaded ${this.avatarDatabase.size} avatar profiles`);
            }
        } catch (error) {
            console.warn('Failed to load avatar database:', error);
        }
    }

    displayChatHistory() {
        // Display recent chat history in the chat window
        if (!this.chatHistory || this.chatHistory.length === 0) return;
        
        // Clear existing messages first
        if (window.chatWindow) {
            window.chatWindow.innerHTML = '';
        }
        
        // Show last 10 messages to avoid overwhelming the interface
        const recentHistory = this.chatHistory.slice(-10);
        
        // Add a separator for history
        if (recentHistory.length > 0) {
            addSystemMessage(`📚 Previous conversation (${recentHistory.length} messages)`);
        }
        
        // Display each historical message with proper speaker identification
        recentHistory.forEach(msg => {
            // Add user message
            addMessage('user', msg.user_message, 'info', null, {
                timestamp: new Date(msg.timestamp).toLocaleString(),
                speaker: msg.user_display_name
            });
            
            // Add AI response with avatar info
            const avatarInfo = this.avatarDatabase.get(msg.avatar_id) || {
                displayName: msg.avatar_name,
                id: msg.avatar_id
            };
            
            addMessage('ai', msg.ai_response, 'info', avatarInfo, {
                timestamp: new Date(msg.timestamp).toLocaleString(),
                emotion: msg.primary_emotion
            });
        });
        
        // Add separator for new conversation
        if (recentHistory.length > 0) {
            addSystemMessage('--- New conversation ---', 'separator');
        }
    }

    formatAvatarName(modelName) {
        // Convert model names like 'haruka' to 'Haruka'
        return modelName.charAt(0).toUpperCase() + modelName.slice(1);
    }

    setupAvatarListeners() {
        // Listen for avatar changes from the Live2D system
        if (window.live2dMultiModelManager) {
            // Set up periodic check for active avatars
            setInterval(() => {
                this.updateActiveAvatars();
            }, 1000);
        }
    }

    updateActiveAvatars() {
        if (!window.live2dMultiModelManager) return;

        const currentActive = new Map();
        const allModels = window.live2dMultiModelManager.getAllModels();
        
        allModels.forEach(modelData => {
            if (modelData.model && modelData.model.visible) {
                const avatarId = modelData.name;
                const avatarInfo = this.avatarDatabase.get(avatarId) || {
                    id: avatarId,
                    name: avatarId,
                    displayName: this.formatAvatarName(avatarId)
                };
                
                currentActive.set(avatarId, {
                    ...avatarInfo,
                    pixiModel: modelData.model,
                    isActive: true,
                    position: { x: modelData.model.x, y: modelData.model.y },
                    scale: modelData.model.scale.x
                });
            }
        });

        // Update active avatars map
        this.activeAvatars = currentActive;
        
        // Update UI if needed
        this.updateChatUI();
        
        // Notify autonomous system about avatar changes
        this.notifyAutonomousSystem();
    }
    
    notifyAutonomousSystem() {
        // Notify autonomous avatar system about active avatar changes
        if (typeof socket !== 'undefined' && socket.connected) {
            const activeAvatarData = Array.from(this.activeAvatars.values()).map(a => ({
                id: a.id,
                name: a.name,
                displayName: a.displayName
            }));
            
            socket.emit('active_avatars_updated', {
                avatars: activeAvatarData,
                count: activeAvatarData.length
            });
        }
    }

    updateChatUI() {
        // Update chat interface to show active avatars
        const activeCount = this.activeAvatars.size;
        if (activeCount > 0) {
            const avatarNames = Array.from(this.activeAvatars.values()).map(a => a.displayName).join(', ');
            this.updateChatTitle(`Chat (${activeCount} avatars: ${avatarNames})`);
        } else {
            this.updateChatTitle('Chat');
        }
    }

    updateChatTitle(title) {
        const chatTitle = document.querySelector('.chat-title');
        if (chatTitle) {
            chatTitle.textContent = title;
        }
    }

    getActiveAvatars() {
        return Array.from(this.activeAvatars.values());
    }

    selectSpeakingAvatar(message) {
        // Logic to determine which avatar should respond
        const activeAvatars = this.getActiveAvatars();
        
        if (activeAvatars.length === 0) {
            return null;
        }
        
        if (activeAvatars.length === 1) {
            return activeAvatars[0];
        }

        // For multiple avatars, use simple round-robin for now
        // TODO: This will be enhanced when personality system is rebuilt
        const lastSpeaker = this.speakingAvatar;
        if (!lastSpeaker) {
            return activeAvatars[0];
        }

        const currentIndex = activeAvatars.findIndex(a => a.id === lastSpeaker.id);
        const nextIndex = (currentIndex + 1) % activeAvatars.length;
        return activeAvatars[nextIndex];
    }

    setSpeakingAvatar(avatar) {
        this.speakingAvatar = avatar;
        if (avatar) {
            // Update avatar stats
            if (this.avatarDatabase.has(avatar.id)) {
                const avatarData = this.avatarDatabase.get(avatar.id);
                avatarData.messageCount++;
                avatarData.lastActive = new Date();
                this.avatarDatabase.set(avatar.id, avatarData);
            }
        }
    }

    async sendMessageWithAvatar(message, targetAvatarId = null) {
        // Determine which avatar should respond
        let selectedAvatar;
        
        if (targetAvatarId && this.activeAvatars.has(targetAvatarId)) {
            selectedAvatar = this.activeAvatars.get(targetAvatarId);
        } else {
            selectedAvatar = this.selectSpeakingAvatar(message);
        }

        if (!selectedAvatar) {
            throw new Error('No active avatars available');
        }

        this.setSpeakingAvatar(selectedAvatar);
        
        // Add user message to history with user info
        this.messageHistory.push({
            type: 'user',
            message: message,
            timestamp: new Date(),
            avatar: null,
            user: {
                id: this.currentUser?.id,
                display_name: this.currentUser?.display_name || 'User'
            }
        });

        // Send to backend with avatar context
        const response = await this.sendToBackend(message, selectedAvatar);
        
        // Add avatar response to history
        this.messageHistory.push({
            type: 'avatar',
            message: response.reply,
            timestamp: new Date(),
            avatar: selectedAvatar,
            emotions: response.emotions || [],
            primary_emotion: response.primary_emotion || 'neutral'
        });

        return {
            avatar: selectedAvatar,
            response: response
        };
    }

    async sendToBackend(message, avatar) {
        const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
        
        const requestData = {
            message: message,
            avatar_id: avatar.id,
            avatar_name: avatar.name,
            active_avatars: this.getActiveAvatars().map(a => ({
                id: a.id,
                name: a.name,
                position: a.position,
                scale: a.scale
            })),
            conversation_context: this.messageHistory.slice(-5), // Last 5 messages for context
            user_info: {
                user_id: this.currentUser?.id,
                display_name: this.currentUser?.display_name || 'User',
                preferences: this.userProfile ? {
                    gender: this.userProfile.gender,
                    age_range: this.userProfile.age_range,
                    nsfw_enabled: this.userProfile.nsfw_enabled,
                    explicit_enabled: this.userProfile.explicit_enabled
                } : {}
            }
        };

        const response = await fetch(`${apiBaseUrl}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`Chat API failed: ${response.status}`);
        }

        return await response.json();
    }

    getAvatarStats() {
        const stats = {};
        this.avatarDatabase.forEach((data, id) => {
            stats[id] = {
                name: data.displayName,
                messageCount: data.messageCount,
                lastActive: data.lastActive,
                isCurrentlyActive: this.activeAvatars.has(id)
            };
        });
        return stats;
    }

    getChatHistory(avatarId = null) {
        if (avatarId) {
            return this.messageHistory.filter(msg => 
                msg.type === 'user' || (msg.avatar && msg.avatar.id === avatarId)
            );
        }
        return this.messageHistory;
    }

    async clearChatHistory() {
        // Clear current session history
        this.messageHistory = [];
        if (window.chatWindow) {
            window.chatWindow.innerHTML = '';
        }
        addSystemMessage('Chat history cleared');
    }

    async exportChatHistory() {
        // Export chat history as JSON
        const exportData = {
            user: this.currentUser,
            session_start: new Date().toISOString(),
            messages: this.messageHistory,
            avatars_used: Array.from(this.activeAvatars.values()).map(a => ({
                id: a.id,
                name: a.name,
                displayName: a.displayName
            }))
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_history_${this.currentUser?.username || 'user'}_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    async refreshChatHistory() {
        // Reload chat history from server
        await this.loadChatHistory();
        addSystemMessage('Chat history refreshed from server');
    }
}

// Initialize global avatar chat manager
let avatarChatManager = null;

function addMessage(sender, message, type = 'info', avatar = null, metadata = null) {
    // Add a message to the chat window with enhanced speaker identification
    if (!window.chatWindow) window.chatWindow = document.getElementById('chatMessages');
    if (!window.chatWindow) {
        console.warn('Chat window not found');
        return;
    }

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender} ${type}`;
    
    // Enhanced speaker identification
    let speakerPrefix = '';
    let speakerClass = '';
    
    if (sender === 'user') {
        const userName = metadata?.speaker || (avatarChatManager?.currentUser?.display_name) || 'User';
        speakerPrefix = `<span class="speaker-name user-speaker">${userName}:</span> `;
        speakerClass = 'user-message';
    } else if (sender === 'ai' && avatar) {
        const avatarName = avatar.displayName || avatar.name || 'Assistant';
        speakerPrefix = `<span class="speaker-name avatar-speaker" data-avatar-id="${avatar.id}">${avatarName}:</span> `;
        speakerClass = 'avatar-message';
        msgDiv.setAttribute('data-avatar-id', avatar.id);
        
        // Add emotion indicator if available
        if (metadata?.emotion && metadata.emotion !== 'neutral') {
            speakerPrefix += `<span class="emotion-indicator emotion-${metadata.emotion}">😊</span> `;
        }
    } else if (sender === 'system') {
        speakerPrefix = `<span class="speaker-name system-speaker">System:</span> `;
        speakerClass = 'system-message';
    }
    
    // Add timestamp if available
    let timestampSuffix = '';
    if (metadata?.timestamp) {
        timestampSuffix = `<span class="message-timestamp">${metadata.timestamp}</span>`;
    }
    
    // Create message content with speaker identification
    const messageContent = `
        <div class="message-header">
            ${speakerPrefix}
            ${timestampSuffix}
        </div>
        <div class="message-text">${formatMessage(message)}</div>
    `;
    
    msgDiv.classList.add(speakerClass);
    if (type === 'separator') {
        msgDiv.classList.add('separator-message');
    }
    
    msgDiv.innerHTML = messageContent;
    window.chatWindow.appendChild(msgDiv);
    
    setTimeout(() => msgDiv.classList.add('visible'), 10);
    window.chatWindow.scrollTop = window.chatWindow.scrollHeight;
}

function formatMessage(message) {
    // Format message for display (basic HTML escaping)
    return String(message).replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

async function sendMessage() {
    // Send user message to backend and display response with multi-avatar support
    if (!window.userInput) window.userInput = document.getElementById('user-input');
    const text = window.userInput.value.trim();
    if (!text) return;
    
    // Initialize avatar chat manager if not already done
    if (!avatarChatManager) {
        avatarChatManager = new AvatarChatManager();
        // Give it a moment to initialize
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    addMessage('user', text, 'info', null, {
        speaker: avatarChatManager?.currentUser?.display_name || 'User',
        timestamp: new Date().toLocaleTimeString()
    });
    window.userInput.value = '';
    
    try {
        // Check if we have active avatars for multi-avatar mode
        if (avatarChatManager.getActiveAvatars().length > 0) {
            // Use multi-avatar system
            const result = await avatarChatManager.sendMessageWithAvatar(text);
            addMessage('ai', result.response.reply || '[No reply]', 'info', result.avatar, {
                emotion: result.response.primary_emotion,
                timestamp: new Date().toLocaleTimeString()
            });
            
            // Trigger avatar motion if available
            if (result.avatar && result.avatar.pixiModel && result.response.primary_emotion) {
                triggerAvatarMotion(result.avatar.pixiModel, result.response.primary_emotion);
            }
            
        } else {
            // Fallback to legacy single chat mode
            await sendMessageLegacy(text);
        }
        
    } catch (error) {
        console.error('Multi-avatar chat error:', error);
        // Fallback to legacy mode on error
        try {
            await sendMessageLegacy(text);
        } catch (legacyError) {
            addSystemMessage('Failed to send message: ' + error.message, 'error');
        }
    }
}

async function sendMessageLegacy(text) {
    // Legacy single chat mode for fallback
    try {
        // Use the same fetchWithFallback system as Live2D models
        let apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL;
        let response;
        
        // Try primary API URL first
        if (apiBaseUrl) {
            try {
                response = await fetch(`${apiBaseUrl}/api/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                if (response.ok) {
                    const data = await response.json();
                    addMessage('ai', data.reply || '[No reply]');
                    return;
                }
            } catch (error) {
                console.warn(`Chat API failed with primary URL ${apiBaseUrl}:`, error.message);
            }
        }
        
        // Try fallback URLs if primary failed
        const fallbackUrls = window.ai2d_chat_CONFIG?.FALLBACK_URLS || [];
        for (const fallbackUrl of fallbackUrls) {
            try {
                console.log(`Trying chat API fallback URL: ${fallbackUrl}`);
                response = await fetch(`${fallbackUrl}/api/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                if (response.ok) {
                    console.log(`Chat API successful with fallback URL: ${fallbackUrl}`);
                    // Update the working URL for future requests
                    window.ai2d_chat_CONFIG.API_BASE_URL = fallbackUrl;
                    const data = await response.json();
                    addMessage('ai', data.reply || '[No reply]');
                    return;
                }
            } catch (error) {
                console.warn(`Chat API fallback failed with ${fallbackUrl}:`, error.message);
            }
        }
        
        // If all URLs failed, throw error
        throw new Error('All chat API endpoints failed');
        
    } catch (error) {
        throw error; // Re-throw to be handled by caller
    }
}

function triggerAvatarMotion(pixiModel, emotion) {
    // Trigger motion based on emotion
    try {
        const motionMap = {
            'happy': 'happy',
            'joy': 'happy', 
            'excited': 'happy',
            'sad': 'sad',
            'angry': 'angry',
            'surprised': 'surprised',
            'neutral': 'idle',
            'default': 'idle'
        };
        
        const motionName = motionMap[emotion] || motionMap['default'];
        
        if (pixiModel && typeof pixiModel.motion === 'function') {
            pixiModel.motion(motionName);
        }
    } catch (error) {
        console.warn('Failed to trigger avatar motion:', error);
    }
}

function addSystemMessage(message, type = 'info') {
    // Add a system message to the chat window
    addMessage('system', message, type);
}

// Export to window for global access
window.addMessage = addMessage;
window.formatMessage = formatMessage;
window.sendMessage = sendMessage;
window.addSystemMessage = addSystemMessage;
window.AvatarChatManager = AvatarChatManager;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize avatar chat manager after a short delay to ensure Live2D system is ready
    setTimeout(() => {
        if (!avatarChatManager) {
            avatarChatManager = new AvatarChatManager();
            window.avatarChatManager = avatarChatManager;
        }
    }, 1000);
});
