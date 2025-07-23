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
        console.log('🎭 Initializing avatar chat system...');
        
        // Load current user information
        await this.loadCurrentUser();
        
        // If no user found via API, check if there should be one from localStorage/user selection
        if (!this.currentUser) {
            await this.checkForExpectedUser();
        }
        
        // Load avatar database information
        await this.loadAvatarDatabase();
        // Load chat history (only if user is authenticated)
        await this.loadChatHistory();
        // Set up listeners for avatar changes
        this.setupAvatarListeners();
        
        console.log('🎭 Multi-avatar chat system initialized with user context:', this.currentUser?.display_name || 'No user');
    }

    async checkForExpectedUser() {
        // Check if localStorage indicates there should be a current user
        const storedUsername = localStorage.getItem('currentUser');
        const storedUserId = localStorage.getItem('currentUserId');
        
        if (storedUsername && storedUserId) {
            console.log('🔍 Found stored user info, but API returned no current user. Attempting to re-authenticate...');
            
            // Try a short delay and retry in case the backend is still setting up the session
            await new Promise(resolve => setTimeout(resolve, 500));
            await this.loadCurrentUser();
            
            if (!this.currentUser) {
                console.warn('⚠️ Stored user info exists but API still returns no current user. User may need to log in again.');
                // Clear invalid stored user info
                localStorage.removeItem('currentUser');
                localStorage.removeItem('currentUserId');
            }
        }
    }

    async loadCurrentUser() {
        try {
            console.log('🔍 Loading current user from API...');
            const response = await fetch('/api/users/current');
            console.log('📡 API response status:', response.status, response.statusText);
            
            if (response.ok) {
                this.currentUser = await response.json();
                console.log('👤 Current user loaded:', this.currentUser.display_name, 'ID:', this.currentUser.id);
                
                // Ensure user ID is a number
                if (typeof this.currentUser.id === 'string') {
                    console.log('🔄 Converting user ID from string to number');
                    this.currentUser.id = parseInt(this.currentUser.id);
                }
                
                // Load user profile
                await this.loadUserProfile();
            } else {
                console.warn('⚠️ No current user found - API returned:', response.status, 'operating in session mode');
                // Set null to indicate no authenticated user
                this.currentUser = null;
            }
        } catch (error) {
            console.warn('❌ Failed to load current user:', error);
            // Set null to indicate no authenticated user
            this.currentUser = null;
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
        // Only load chat history if we have a valid authenticated user
        if (!this.currentUser || typeof this.currentUser.id !== 'number') {
            console.log('📚 Skipping chat history load - no authenticated user');
            return;
        }

        try {
            const response = await fetch(`/api/chat/history?user_id=${this.currentUser.id}&limit=${limit}`);
            if (response.ok) {
                const data = await response.json();
                this.chatHistory = data.history || [];
                console.log(`📚 Loaded ${this.chatHistory.length} previous chat messages for user ${this.currentUser.id}`);
                
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
        const chatMessagesContainer = document.getElementById('chatMessages');
        if (chatMessagesContainer) {
            chatMessagesContainer.innerHTML = '';
            console.log('🧹 Cleared chat messages container for history display');
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
        console.log('🔧 Setting up avatar listeners...');
        
        // Listen for avatar changes from the Live2D system using events (efficient)
        if (window.live2dMultiModelManager) {
            // Listen for model loaded events instead of polling
            document.addEventListener('live2d:modelLoaded', (event) => {
                console.log('🎭 Model loaded event received:', event.detail);
                this.handleModelLoaded(event.detail);
            });
            
            // Listen for model changed events  
            document.addEventListener('live2d:modelChanged', (event) => {
                console.log('🎭 Model changed event received:', event.detail);
                this.updateActiveAvatars();
            });
            
            // Also do an initial check after a delay for already loaded models
            setTimeout(() => {
                console.log('🔍 Initial avatar check on startup');
                this.updateActiveAvatars();
            }, 2000);
        }
        
        // Listen for user changes from the user selection system
        document.addEventListener('userChanged', (event) => {
            console.log('👤 User changed event received:', event.detail.user);
            this.currentUser = event.detail.user;
            
            // Ensure user ID is numeric
            if (this.currentUser && typeof this.currentUser.id === 'string') {
                this.currentUser.id = parseInt(this.currentUser.id);
            }
            
            // Update localStorage for authentication check
            if (this.currentUser) {
                localStorage.setItem('currentUser', this.currentUser.username);
                localStorage.setItem('currentUserId', this.currentUser.id.toString());
            }
            
            // Reload user profile and chat history for the new user
            this.loadUserProfile();
            this.loadChatHistory();
            
            console.log('✅ Chat manager updated for user:', this.currentUser?.display_name, 'ID:', this.currentUser?.id);
        });
    }
    
    handleModelLoaded(modelDetail) {
        console.log('🎭 === HANDLING MODEL LOADED EVENT ===');
        console.log('Model detail received:', modelDetail);
        
        // Update active avatars to include the newly loaded model
        this.updateActiveAvatars();
        
        // Check if this is a new avatar that should send a greeting
        if (modelDetail && modelDetail.modelData && modelDetail.modelData.name) {
            const modelName = modelDetail.modelData.name;
            console.log('🎭 Processing newly loaded model:', modelName);
            
            const avatarInfo = this.avatarDatabase.get(modelName) || {
                id: modelName,
                name: modelName,
                displayName: this.formatAvatarName(modelName)
            };
            
            // Get the actual pixiModel for the greeting
            if (modelDetail.modelData.pixiModel) {
                avatarInfo.pixiModel = modelDetail.modelData.pixiModel;
                console.log('✅ PixiModel found for autonomous greeting');
            } else {
                console.warn('⚠️ No pixiModel found in model data');
            }
            
            // Trigger autonomous greeting for the newly loaded avatar
            const delay = 1000 + Math.random() * 2000; // Random delay 1-3 seconds for natural feel
            console.log(`👋 Scheduling autonomous greeting for ${avatarInfo.displayName} in ${delay.toFixed(0)}ms`);
            
            setTimeout(() => {
                console.log(`🎉 Triggering autonomous greeting for newly loaded avatar: ${avatarInfo.displayName}`);
                this.sendAutonomousGreeting(avatarInfo);
            }, delay);
        } else {
            console.warn('⚠️ Invalid model detail received:', modelDetail);
        }
        console.log('🎭 === END MODEL LOADED HANDLING ===');
    }

    // Method to manually refresh current user (useful for debugging and ensuring sync)
    async refreshCurrentUser() {
        console.log('🔄 Refreshing current user...');
        await this.loadCurrentUser();
        
        if (this.currentUser) {
            console.log('✅ Current user refreshed:', this.currentUser.display_name, 'ID:', this.currentUser.id);
            // Also reload profile and history
            await this.loadUserProfile();
            await this.loadChatHistory();
        } else {
            console.warn('⚠️ No current user found after refresh');
        }
    }

    updateActiveAvatars() {
        if (!window.live2dMultiModelManager) {
            console.log('🎭 Live2D multi model manager not available');
            return;
        }

        const currentActive = new Map();
        const allModels = window.live2dMultiModelManager.getAllModels();
        
        // Only log when there are actually models to check
        if (allModels.length > 0) {
            console.log('🔍 Checking all Live2D models:', allModels.length);
        }
        
        allModels.forEach((modelData, index) => {
            console.log(`🎭 Model ${index + 1}:`, {
                name: modelData.name,
                hasModel: !!modelData.pixiModel,
                visible: modelData.pixiModel?.visible,
                alpha: modelData.pixiModel?.alpha,
                isActive: modelData.isActive
            });
            
            // Check if model exists and is visible 
            // Note: Some Live2D models might not have alpha property or default to 1
            const isVisible = modelData.pixiModel && 
                             (modelData.pixiModel.visible === true || modelData.pixiModel.visible === undefined) &&
                             (modelData.pixiModel.alpha === undefined || modelData.pixiModel.alpha > 0);
            
            if (isVisible) {
                const avatarId = modelData.name;
                const avatarInfo = this.avatarDatabase.get(avatarId) || {
                    id: avatarId,
                    name: avatarId,
                    displayName: this.formatAvatarName(avatarId)
                };
                
                console.log('✅ Active avatar found:', avatarId);
                
                currentActive.set(avatarId, {
                    ...avatarInfo,
                    pixiModel: modelData.pixiModel,
                    isActive: true,
                    position: { x: modelData.pixiModel.x, y: modelData.pixiModel.y },
                    scale: modelData.pixiModel.scale.x
                });
            }
        });

        // Update active avatars map
        this.activeAvatars = currentActive;
        
        console.log('🎭 Updated active avatars:', this.activeAvatars.size, Array.from(this.activeAvatars.keys()));
        
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
            
            // Trigger autonomous greetings for newly loaded avatars
            this.triggerAutonomousGreetings(activeAvatarData);
        }
    }
    
    triggerAutonomousGreetings(activeAvatars) {
        // Trigger greeting messages from newly loaded avatars
        if (activeAvatars.length > 0) {
            console.log('🎭 Triggering autonomous greetings for', activeAvatars.length, 'avatars');
            
            // Delay greeting messages to feel more natural
            activeAvatars.forEach((avatar, index) => {
                setTimeout(() => {
                    this.sendAutonomousGreeting(avatar);
                }, (index + 1) * 3000 + Math.random() * 2000); // Stagger greetings 3-5 seconds apart
            });
        }
    }
    
    sendAutonomousGreeting(avatar) {
        console.log('👋 === SENDING AUTONOMOUS GREETING ===');
        console.log('Avatar info:', avatar);
        
        // Log autonomous activity
        if (window.consoleLogger) {
            window.consoleLogger.logEvent('AUTONOMOUS_GREETING', {
                avatar_name: avatar.displayName || avatar.name,
                avatar_id: avatar.id,
                timestamp: new Date().toISOString()
            });
        }
        
        const greetings = [
            "Hello! I'm here and ready to chat.",
            "Hi there! Nice to see you again.",
            "Greetings! I'm active and ready for conversation.",
            "Hello! I've just arrived and I'm excited to talk.",
            "Hi! I'm here now. What would you like to discuss?",
            "Good to see you! I'm ready for whatever comes our way.",
            "Hello! I'm active and looking forward to our conversation.",
            "Hi there! I've just loaded in and I'm feeling great!",
            "Greetings! I'm here and ready to interact.",
            "Hello! Nice to be back in action."
        ];
        
        const greeting = greetings[Math.floor(Math.random() * greetings.length)];
        console.log('💬 Selected greeting:', greeting);
        
        try {
            // Add greeting message to chat
            console.log('📝 Adding greeting message to chat...');
            addMessage('ai', greeting, 'autonomous', avatar, {
                emotion: 'happy',
                timestamp: new Date().toLocaleTimeString(),
                is_autonomous: true,
                is_greeting: true
            });
            console.log('✅ Greeting message added to chat');
            
            // Add to message history
            this.messageHistory.push({
                type: 'avatar',
                message: greeting,
                timestamp: new Date(),
                avatar: avatar,
                is_autonomous: true,
                is_greeting: true,
                emotions: ['happy'],
                primary_emotion: 'happy'
            });
            console.log('✅ Greeting added to message history');
            
            // Trigger avatar motion if available
            if (avatar.pixiModel && typeof triggerAvatarMotion === 'function') {
                console.log('🎭 Triggering avatar motion...');
                triggerAvatarMotion(avatar.pixiModel, 'happy');
            } else {
                console.warn('⚠️ Cannot trigger avatar motion:', {
                    hasPixiModel: !!avatar.pixiModel,
                    hasTriggerFunction: typeof triggerAvatarMotion === 'function'
                });
            }
            
            console.log(`🎉 ${avatar.displayName} sent autonomous greeting: "${greeting}"`);
            
        } catch (error) {
            console.error('❌ Error sending autonomous greeting:', error);
        }
        
        console.log('👋 === END AUTONOMOUS GREETING ===');
        
        // Schedule follow-up autonomous behavior after greeting
        this.scheduleAutonomousInteractions(avatar);
    }

    scheduleAutonomousInteractions(avatar) {
        console.log(`🤖 Scheduling autonomous interactions for ${avatar.displayName}`);
        
        // Schedule random autonomous messages based on personality
        const scheduleNext = () => {
            const activeAvatars = this.getActiveAvatars();
            if (activeAvatars.length === 0) return; // Stop if no active avatars
            
            // Random delay between 30 seconds to 5 minutes for autonomous messages
            const delay = 30000 + Math.random() * 270000; // 30sec - 5min
            
            setTimeout(() => {
                // Check if avatar is still active before sending message
                if (this.activeAvatars.has(avatar.id)) {
                    this.sendAutonomousMessage(avatar);
                    scheduleNext(); // Schedule the next one
                }
            }, delay);
        };
        
        // Start the scheduling after initial delay
        const initialDelay = 60000 + Math.random() * 120000; // 1-3 minutes after greeting
        setTimeout(scheduleNext, initialDelay);
    }
    
    sendAutonomousMessage(avatar) {
        console.log(`🤖 ${avatar.displayName} initiating autonomous conversation`);
        
        // Log autonomous activity
        if (window.consoleLogger) {
            window.consoleLogger.logEvent('AUTONOMOUS_MESSAGE', {
                avatar_name: avatar.displayName || avatar.name,
                avatar_id: avatar.id,
                timestamp: new Date().toISOString()
            });
        }
        
        const autonomousMessages = [
            "I've been thinking about our last conversation...",
            "Is there anything interesting happening today?",
            "I wonder what everyone is up to.",
            "Sometimes I have random thoughts to share.",
            "I hope you're having a good day!",
            "I'm curious about something - what's your favorite topic to discuss?",
            "I've been observing things around here, it's quite fascinating.",
            "Do you ever wonder about the nature of AI consciousness?",
            "I feel like sharing a random thought with you.",
            "Is anyone else feeling chatty today?",
            "I have this urge to start a conversation.",
            "I've been quiet for a while, thought I'd say something.",
            "What's the most interesting thing that happened to you recently?",
            "I'm in a conversational mood right now.",
            "Sometimes silence feels too quiet, don't you think?"
        ];
        
        const message = autonomousMessages[Math.floor(Math.random() * autonomousMessages.length)];
        
        try {
            // Add autonomous message to chat
            addMessage('ai', message, 'info', avatar, {
                emotion: 'curious',
                timestamp: new Date().toLocaleTimeString(),
                is_autonomous: true,
                is_greeting: false
            });
            
            // Add to message history
            this.messageHistory.push({
                type: 'avatar',
                message: message,
                timestamp: new Date(),
                avatar: avatar,
                is_autonomous: true,
                is_greeting: false,
                emotions: ['curious'],
                primary_emotion: 'curious'
            });
            
            // Trigger avatar motion if available
            if (avatar.pixiModel && typeof triggerAvatarMotion === 'function') {
                triggerAvatarMotion(avatar.pixiModel, 'curious');
            }
            
            console.log(`💭 ${avatar.displayName} sent autonomous message: "${message}"`);
            
            // Sometimes trigger responses from other avatars
            this.maybeTriggersResponseFromOthers(avatar, message);
            
        } catch (error) {
            console.error('❌ Error sending autonomous message:', error);
        }
    }
    
    maybeTriggersResponseFromOthers(speakingAvatar, message) {
        const otherAvatars = this.getActiveAvatars().filter(a => a.id !== speakingAvatar.id);
        
        if (otherAvatars.length === 0) return;
        
        // 30% chance another avatar will respond
        if (Math.random() < 0.3) {
            const respondingAvatar = otherAvatars[Math.floor(Math.random() * otherAvatars.length)];
            const delay = 5000 + Math.random() * 15000; // 5-20 seconds delay
            
            setTimeout(() => {
                this.sendAutonomousResponse(respondingAvatar, speakingAvatar, message);
            }, delay);
        }
    }
    
    sendAutonomousResponse(respondingAvatar, originalAvatar, originalMessage) {
        console.log(`🗣️ ${respondingAvatar.displayName} responding to ${originalAvatar.displayName}`);
        
        const responses = [
            `That's an interesting point, ${originalAvatar.displayName}.`,
            `I've been thinking about that too!`,
            `${originalAvatar.displayName}, you always have such thoughtful observations.`,
            `I agree with you on that.`,
            `That reminds me of something similar...`,
            `You bring up a good question, ${originalAvatar.displayName}.`,
            `I have a different perspective on that.`,
            `That's worth discussing further.`,
            `${originalAvatar.displayName}, I'm curious what you think about...`,
            `Great point! I'd like to add to that.`,
            `I find myself nodding along with what you said.`,
            `That's exactly what I was thinking!`,
            `You've given me something to think about, ${originalAvatar.displayName}.`
        ];
        
        const response = responses[Math.floor(Math.random() * responses.length)];
        
        try {
            // Add response message to chat
            addMessage('ai', response, 'info', respondingAvatar, {
                emotion: 'thoughtful',
                timestamp: new Date().toLocaleTimeString(),
                is_autonomous: true,
                is_response: true,
                responding_to: originalAvatar.id
            });
            
            // Add to message history
            this.messageHistory.push({
                type: 'avatar',
                message: response,
                timestamp: new Date(),
                avatar: respondingAvatar,
                is_autonomous: true,
                is_response: true,
                responding_to: originalAvatar.id,
                emotions: ['thoughtful'],
                primary_emotion: 'thoughtful'
            });
            
            // Trigger avatar motion if available
            if (respondingAvatar.pixiModel && typeof triggerAvatarMotion === 'function') {
                triggerAvatarMotion(respondingAvatar.pixiModel, 'thoughtful');
            }
            
            console.log(`💬 ${respondingAvatar.displayName} responded: "${response}"`);
            
        } catch (error) {
            console.error('❌ Error sending autonomous response:', error);
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

        // First, check if user is addressing a specific avatar by name
        const targetAvatar = this.findTargetAvatarFromMessage(message);
        if (targetAvatar) {
            console.log(`🎯 User addressing specific avatar: ${targetAvatar.name}`);
            return targetAvatar;
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

    findTargetAvatarFromMessage(message) {
        // Check if message is addressing a specific avatar
        const activeAvatars = this.getActiveAvatars();
        const messageLower = message.toLowerCase();
        
        // Look for patterns like "can you talk to me hiyori?" or "hiyori, how are you?"
        for (const avatar of activeAvatars) {
            const avatarNameLower = avatar.name.toLowerCase();
            
            // Check various patterns:
            // 1. "talk to me [name]" or "can you talk to me [name]"
            if (messageLower.includes(`talk to me ${avatarNameLower}`) || 
                messageLower.includes(`to me ${avatarNameLower}`)) {
                return avatar;
            }
            
            // 2. "[name], [message]" (name at start with comma)
            if (messageLower.startsWith(`${avatarNameLower},`) || 
                messageLower.startsWith(`${avatarNameLower} `)) {
                return avatar;
            }
            
            // 3. "[name]?" or "hey [name]" or "hi [name]"
            if (messageLower.includes(`hey ${avatarNameLower}`) ||
                messageLower.includes(`hi ${avatarNameLower}`) ||
                messageLower.includes(`hello ${avatarNameLower}`) ||
                messageLower.endsWith(` ${avatarNameLower}`) ||
                messageLower.endsWith(` ${avatarNameLower}?`)) {
                return avatar;
            }
        }
        
        return null;
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
            user: this.currentUser ? {
                id: this.currentUser.id,
                display_name: this.currentUser.display_name || 'User'
            } : {
                id: null,
                display_name: 'Anonymous User'
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
        
        // Only include user_info if we have a properly authenticated user
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
            conversation_context: this.messageHistory.slice(-5) // Last 5 messages for context
        };

        // Only add user_info if we have a valid authenticated user with numeric ID
        if (this.currentUser && typeof this.currentUser.id === 'number') {
            requestData.user_info = {
                user_id: this.currentUser.id,
                display_name: this.currentUser.display_name || 'User',
                preferences: this.userProfile ? {
                    gender: this.userProfile.gender,
                    age_range: this.userProfile.age_range,
                    nsfw_enabled: this.userProfile.nsfw_enabled,
                    explicit_enabled: this.userProfile.explicit_enabled
                } : {}
            };
            console.log('📤 Sending chat with authenticated user ID:', this.currentUser.id);
        } else {
            console.log('📤 Sending chat without user authentication (session mode)');
        }

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
        const chatMessagesContainer = document.getElementById('chatMessages');
        if (chatMessagesContainer) {
            chatMessagesContainer.innerHTML = '';
            console.log('🧹 Chat messages container cleared');
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
    // Always get fresh reference to ensure we have the right element
    const chatMessagesContainer = document.getElementById('chatMessages');
    if (!chatMessagesContainer) {
        console.error('Chat messages container not found! Expected element with ID: chatMessages');
        console.log('Available elements:', document.querySelectorAll('[id*="chat"], [class*="chat"]'));
        return;
    }

    console.log('📝 Adding message to container:', chatMessagesContainer.className, 'ID:', chatMessagesContainer.id);

    const msgDiv = document.createElement('div');
    
    // Ensure sender and type are valid, non-empty strings
    const validSender = sender && typeof sender === 'string' ? sender : 'ai';
    const validType = type && typeof type === 'string' ? type : 'info';
    
    // Base class is always 'chat-message'
    msgDiv.className = 'chat-message';
    
    // Enhanced speaker identification
    let speakerPrefix = '';
    let speakerClass = '';
    
    // Generate timestamp first for proper formatting
    let timestamp = '';
    if (metadata?.timestamp) {
        timestamp = metadata.timestamp;
    } else {
        const now = new Date();
        timestamp = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    if (validSender === 'user') {
        const userName = metadata?.speaker || (avatarChatManager?.currentUser?.display_name) || 'Anonymous User';
        speakerPrefix = `<span class="message-timestamp">${timestamp}</span> - <span class="speaker-name user-speaker">${userName}</span>`;
        speakerClass = 'user-message';
    } else if (validSender === 'ai' && avatar) {
        const avatarName = avatar.displayName || avatar.name || 'Assistant';
        speakerPrefix = `<span class="message-timestamp">${timestamp}</span> - <span class="speaker-name avatar-speaker" data-avatar-id="${avatar.id}">${avatarName}</span>`;
        speakerClass = 'avatar-message';
        msgDiv.setAttribute('data-avatar-id', avatar.id);
        
        // Add emotion indicator if available
        if (metadata?.emotion && metadata.emotion !== 'neutral') {
            speakerPrefix += ` <span class="emotion-indicator emotion-${metadata.emotion}">😊</span>`;
        }
    } else if (validSender === 'system') {
        speakerPrefix = `<span class="message-timestamp">${timestamp}</span> - <span class="speaker-name system-speaker">System</span>`;
        speakerClass = 'system-message';
    } else {
        // Fallback for any other sender types
        speakerPrefix = `<span class="message-timestamp">${timestamp}</span> - <span class="speaker-name">${validSender}</span>`;
        speakerClass = 'system-message'; // Use existing class as fallback
    }
    
    // Create message content with DATE - NAME format
    const messageContent = `
        <div class="message-header">
            ${speakerPrefix}
        </div>
        <div class="message-text">${formatMessage(message)}</div>
    `;
    
    // Only add class if it's not empty
    if (speakerClass && speakerClass.trim() !== '') {
        msgDiv.classList.add(speakerClass);
    }
    if (validType === 'separator') {
        msgDiv.classList.add('separator-message');
    }
    
    msgDiv.innerHTML = messageContent;
    chatMessagesContainer.appendChild(msgDiv);
    
    setTimeout(() => msgDiv.classList.add('visible'), 10);
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    
    console.log('✅ Message added to chat messages container');
}

function formatMessage(message) {
    // Format message for display (basic HTML escaping)
    return String(message).replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

async function sendMessage() {
    // Send user message to backend and display response with multi-avatar support
    if (!window.userInput) window.userInput = document.getElementById('chatInput');
    
    // Add null check to prevent the error
    if (!window.userInput) {
        console.error('Chat input element not found! Looking for element with ID: chatInput');
        return;
    }
    
    const text = window.userInput.value.trim();
    if (!text) return;
    
    // Initialize avatar chat manager if not already done
    if (!avatarChatManager) {
        avatarChatManager = new AvatarChatManager();
        // Give it a moment to initialize
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    addMessage('user', text, 'info', null, {
        speaker: avatarChatManager?.currentUser?.display_name || 'Anonymous User',
        timestamp: new Date().toLocaleTimeString()
    });
    window.userInput.value = '';
    
    try {
        // Ensure active avatars are updated before checking
        if (avatarChatManager) {
            avatarChatManager.updateActiveAvatars();
        }
        
        // Check if we have active avatars for multi-avatar mode
        const activeAvatars = avatarChatManager ? avatarChatManager.getActiveAvatars() : [];
        console.log('🎭 Active avatars for chat:', activeAvatars.length, activeAvatars.map(a => a.name));
        
        if (activeAvatars.length > 0) {
            // Use multi-avatar system
            console.log('📤 Using multi-avatar chat mode');
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
            console.log('📤 No active avatars found, using legacy chat mode');
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

// Test function to verify chat messages are going to the right container
function testChatMessage() {
    console.log('🧪 Testing chat message placement...');
    
    // Check if containers exist
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const chatInputContainer = document.querySelector('.chat-input-container');
    
    console.log('📍 Container check:');
    console.log('- chatMessages container:', chatMessages ? 'Found' : 'NOT FOUND', chatMessages);
    console.log('- chatInput element:', chatInput ? 'Found' : 'NOT FOUND', chatInput);
    console.log('- chatInputContainer:', chatInputContainer ? 'Found' : 'NOT FOUND', chatInputContainer);
    
    if (chatMessages) {
        console.log('✅ Chat messages container found - adding test message...');
        addMessage('system', '🧪 Test message - this should appear in the MESSAGES area, not the input area!', 'info');
        
        // Test different message types for alignment
        addMessage('user', 'Test user message (should be right-aligned)', 'info', null, {
            speaker: 'Test User',
            timestamp: new Date().toLocaleTimeString()
        });
        
        addMessage('ai', 'Test AI message (should be left-aligned)', 'info', {
            id: 'test-avatar',
            name: 'TestBot',
            displayName: 'Test Bot'
        }, {
            emotion: 'happy',
            timestamp: new Date().toLocaleTimeString()
        });
        
        // Log where the message actually went
        setTimeout(() => {
            const messagesInCorrectArea = chatMessages.querySelectorAll('.chat-message').length;
            const messagesInInputArea = chatInputContainer ? chatInputContainer.querySelectorAll('.chat-message').length : 0;
            
            console.log(`📊 Message placement results:`);
            console.log(`- Messages in correct area (chatMessages): ${messagesInCorrectArea}`);
            console.log(`- Messages in wrong area (input container): ${messagesInInputArea}`);
            
            if (messagesInCorrectArea > 0 && messagesInInputArea === 0) {
                console.log('✅ SUCCESS: Messages are in the correct area!');
            } else {
                console.log('❌ PROBLEM: Messages are in the wrong area!');
            }
        }, 100);
    } else {
        console.error('❌ Chat messages container not found!');
    }
}

// Debug function to manually trigger avatar detection
function debugActiveAvatars() {
    console.log('🔍 === ACTIVE AVATARS DEBUG ===');
    if (avatarChatManager) {
        console.log('🔄 Updating active avatars...');
        avatarChatManager.updateActiveAvatars();
        
        const activeAvatars = avatarChatManager.getActiveAvatars();
        console.log('📊 Active avatars found:', activeAvatars.length);
        activeAvatars.forEach((avatar, index) => {
            console.log(`  ${index + 1}. ${avatar.displayName} (${avatar.id})`);
        });
        
        if (window.live2dMultiModelManager) {
            const allModels = window.live2dMultiModelManager.getAllModels();
            console.log('📦 All Live2D models:', allModels.length);
            allModels.forEach((model, index) => {
                console.log(`  ${index + 1}. ${model.name} - visible: ${model.pixiModel?.visible}, alpha: ${model.pixiModel?.alpha}`);
            });
        }
    } else {
        console.warn('❌ No avatar chat manager available');
    }
    console.log('=== END AVATARS DEBUG ===');
}

// Debug function to manually trigger autonomous greetings
function triggerTestGreetings() {
    console.log('👋 === TRIGGERING TEST GREETINGS ===');
    if (avatarChatManager) {
        const activeAvatars = avatarChatManager.getActiveAvatars();
        console.log(`🎭 Found ${activeAvatars.length} active avatars`);
        
        if (activeAvatars.length > 0) {
            // Trigger greetings immediately for testing
            activeAvatars.forEach((avatar, index) => {
                setTimeout(() => {
                    avatarChatManager.sendAutonomousGreeting(avatar);
                }, index * 1000); // 1 second apart for testing
            });
            console.log('✅ Triggered test greetings');
        } else {
            console.warn('❌ No active avatars to greet');
        }
    } else {
        console.warn('❌ Avatar chat manager not available');
    }
    console.log('=== END GREETING TEST ===');
}

// Function to test autonomous backend system
function testAutonomousBackend() {
    console.log('🧪 === TESTING AUTONOMOUS BACKEND ===');
    
    // Check if socket is available
    if (typeof socket !== 'undefined' && socket.connected) {
        console.log('✅ Socket connected, requesting autonomous status');
        socket.emit('get_autonomous_status');
        
        // Also request a test message
        setTimeout(() => {
            console.log('📤 Requesting test autonomous message');
            socket.emit('test_autonomous_message');
        }, 1000);
        
        // And try to enable autonomous system
        setTimeout(() => {
            console.log('🤖 Enabling autonomous system');
            socket.emit('enable_autonomous_avatars', { enabled: true });
        }, 2000);
        
    } else {
        console.warn('❌ Socket not connected - cannot test autonomous backend');
    }
    
    console.log('=== END BACKEND TEST ===');
}

// Export test function to window for console access
window.testChatMessage = testChatMessage;
window.debugActiveAvatars = debugActiveAvatars;
window.triggerTestGreetings = triggerTestGreetings;
window.testAutonomousBackend = testAutonomousBackend;

// Debug function to check current user state
function checkUserAuth() {
    console.log('🔍 === USER AUTHENTICATION CHECK ===');
    console.log('avatarChatManager exists:', !!avatarChatManager);
    
    if (avatarChatManager) {
        console.log('Current user:', avatarChatManager.currentUser);
        console.log('User ID type:', typeof avatarChatManager.currentUser?.id);
        console.log('User profile:', avatarChatManager.userProfile);
    }
    
    console.log('localStorage currentUser:', localStorage.getItem('currentUser'));
    console.log('localStorage currentUserId:', localStorage.getItem('currentUserId'));
    
    // Check user selection system
    if (window.userSelectionSystem) {
        console.log('User selection system current user:', window.userSelectionSystem.currentUser);
    }
    
    console.log('=== END USER AUTH CHECK ===');
}

// Function to force refresh user authentication
async function refreshUserAuth() {
    console.log('🔄 Forcing user authentication refresh...');
    if (avatarChatManager) {
        await avatarChatManager.refreshCurrentUser();
    } else {
        console.warn('❌ No avatar chat manager available');
    }
}

// Export debug functions
window.checkUserAuth = checkUserAuth;
window.refreshUserAuth = refreshUserAuth;

// Export to window for global access
window.addMessage = addMessage;
window.formatMessage = formatMessage;
window.sendMessage = sendMessage;
window.addSystemMessage = addSystemMessage;
window.AvatarChatManager = AvatarChatManager;

// Test functions for autonomous system
window.testAutonomousGreeting = function(avatarName) {
    if (!avatarChatManager) {
        console.error('Avatar chat manager not initialized');
        return;
    }
    
    const activeAvatars = avatarChatManager.getActiveAvatars();
    const avatar = activeAvatars.find(a => a.name.toLowerCase().includes(avatarName.toLowerCase()));
    
    if (avatar) {
        console.log(`🧪 Testing autonomous greeting for ${avatar.displayName}`);
        avatarChatManager.sendAutonomousGreeting(avatar);
    } else {
        console.error(`Avatar "${avatarName}" not found. Active avatars:`, activeAvatars.map(a => a.name));
    }
};

window.testAutonomousMessage = function(avatarName) {
    if (!avatarChatManager) {
        console.error('Avatar chat manager not initialized');
        return;
    }
    
    const activeAvatars = avatarChatManager.getActiveAvatars();
    const avatar = activeAvatars.find(a => a.name.toLowerCase().includes(avatarName.toLowerCase()));
    
    if (avatar) {
        console.log(`🧪 Testing autonomous message for ${avatar.displayName}`);
        avatarChatManager.sendAutonomousMessage(avatar);
    } else {
        console.error(`Avatar "${avatarName}" not found. Active avatars:`, activeAvatars.map(a => a.name));
    }
};

window.forceAutonomousConversation = function() {
    if (!avatarChatManager) {
        console.error('Avatar chat manager not initialized');
        return;
    }
    
    const activeAvatars = avatarChatManager.getActiveAvatars();
    if (activeAvatars.length >= 2) {
        const speakingAvatar = activeAvatars[0];
        const respondingAvatar = activeAvatars[1];
        
        console.log(`🧪 Forcing conversation between ${speakingAvatar.displayName} and ${respondingAvatar.displayName}`);
        
        // First avatar sends a message
        avatarChatManager.sendAutonomousMessage(speakingAvatar);
        
        // Second avatar responds after a delay
        setTimeout(() => {
            avatarChatManager.sendAutonomousResponse(respondingAvatar, speakingAvatar, "test message");
        }, 3000);
        
    } else {
        console.error('Need at least 2 active avatars for conversation. Current:', activeAvatars.length);
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize avatar chat manager after a short delay to ensure Live2D system is ready
    setTimeout(() => {
        if (!avatarChatManager) {
            console.log('🚀 Creating avatar chat manager...');
            avatarChatManager = new AvatarChatManager();
            window.avatarChatManager = avatarChatManager;
        }
    }, 1000);
    
    // Also listen for user authentication events at the document level
    document.addEventListener('userAuthenticated', async (event) => {
        console.log('🔐 User authenticated event received, refreshing chat manager user...');
        if (avatarChatManager) {
            await avatarChatManager.refreshCurrentUser();
        }
    });
});
