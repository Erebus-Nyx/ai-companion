/*
Autonomous Avatar Interaction - Frontend Component
=================================================

Handles display and management of autonomous avatar conversations on the frontend.
Integrates with the existing chat system to show avatar-to-avatar interactions.
*/

class AutonomousAvatarUI {
    constructor(avatarChatManager) {
        this.avatarChatManager = avatarChatManager;
        this.autonomousEnabled = false;
        this.lastUserActivity = Date.now();
        this.setupEventListeners();
        this.setupSocketListeners();
        console.log('🤖 Autonomous Avatar UI initialized');
    }

    setupEventListeners() {
        // Track user activity to pause autonomous conversations
        document.addEventListener('click', () => this.updateUserActivity());
        document.addEventListener('keypress', () => this.updateUserActivity());
        
        // Listen for user messages to pause autonomous system
        if (window.sendMessage && typeof window.sendMessage === 'function') {
            const originalSendMessage = window.sendMessage;
            window.sendMessage = async (...args) => {
                this.updateUserActivity();
                return await originalSendMessage.apply(this, args);
            };
        }
        
        // Listen for model loaded events directly
        document.addEventListener('live2d:modelLoaded', (event) => {
            console.log('🤖 Autonomous system detected model load:', event.detail);
            this.handleModelLoaded(event.detail);
        });
    }

    setupSocketListeners() {
        // Listen for autonomous avatar messages via SocketIO
        if (typeof socket !== 'undefined') {
            socket.on('autonomous_avatar_message', (data) => {
                this.handleAutonomousMessage(data);
            });

            socket.on('avatar_self_reflection', (data) => {
                this.handleSelfReflection(data);
            });

            console.log('🔌 Autonomous avatar socket listeners setup');
        }
    }

    updateUserActivity() {
        this.lastUserActivity = Date.now();
        
        // Notify backend that user is active (pause autonomous conversations)
        if (typeof socket !== 'undefined' && socket.connected) {
            socket.emit('user_activity', { timestamp: this.lastUserActivity });
        }
    }

    handleAutonomousMessage(data) {
        const { avatar, message, metadata } = data;
        
        console.log('🤖 Handling autonomous message:', { avatar, message, metadata });
        
        // Add autonomous message to chat with special styling
        if (window.addMessage && typeof window.addMessage === 'function') {
            window.addMessage('ai', message, 'autonomous', avatar, {
                ...metadata,
                is_autonomous: true,
                timestamp: new Date().toLocaleTimeString()
            });
        } else {
            console.warn('🤖 Cannot display autonomous message - addMessage not available');
        }

        // Trigger TTS with enhanced lipsync for autonomous message
        if (window.triggerEnhancedTTSWithLipsync && avatar && avatar.id) {
            const emotion = metadata?.emotion || 'neutral';
            const intensity = metadata?.intensity || 0.6;
            
            console.log(`🎤 Triggering TTS for autonomous message from ${avatar.id}`);
            
            window.triggerEnhancedTTSWithLipsync(
                message,
                emotion,
                avatar.id,
                {},
                intensity
            ).catch(error => {
                console.error('Failed to play autonomous TTS:', error);
                
                // Fallback to basic TTS if enhanced fails
                if (window.triggerEmotionalTTS) {
                    window.triggerEmotionalTTS(message, emotion, avatar.id, {}, intensity)
                        .catch(fallbackError => {
                            console.error('Fallback TTS also failed:', fallbackError);
                        });
                }
            });
        } else {
            console.warn('🤖 Enhanced TTS not available for autonomous message');
        }

        // Add to chat history
        if (this.avatarChatManager && this.avatarChatManager.messageHistory) {
            this.avatarChatManager.messageHistory.push({
                type: 'avatar',
                message: message,
                timestamp: new Date(),
                avatar: avatar,
                is_autonomous: true,
                emotions: ['neutral'],
                primary_emotion: metadata?.emotion || 'neutral'
            });
        }

        // Trigger avatar motion/expression if available
        this.triggerAutonomousAvatarMotion(avatar, metadata?.emotion || 'neutral');

        console.log(`🤖 Autonomous message from ${avatar.name}: ${message.substring(0, 50)}...`);
    }

    handleSelfReflection(data) {
        const { avatar, message, metadata } = data;
        
        console.log('🧠 Handling self-reflection:', { avatar, message, metadata });
        
        // Add self-reflection with special styling
        if (window.addMessage && typeof window.addMessage === 'function') {
            window.addMessage('ai', message, 'reflection', avatar, {
                ...metadata,
                is_self_reflection: true,
                timestamp: new Date().toLocaleTimeString()
            });
        }

        // Trigger TTS for self-reflection (usually more thoughtful/quiet)
        if (window.triggerEnhancedTTSWithLipsync && avatar && avatar.id) {
            const emotion = metadata?.emotion || 'thoughtful';
            const intensity = metadata?.intensity || 0.4; // Quieter for self-reflection
            
            console.log(`🎤 Triggering TTS for self-reflection from ${avatar.id}`);
            
            window.triggerEnhancedTTSWithLipsync(
                message,
                emotion,
                avatar.id,
                {},
                intensity
            ).catch(error => {
                console.error('Failed to play self-reflection TTS:', error);
            });
        }

        console.log(`🧠 Self-reflection from ${avatar.name}: ${message.substring(0, 50)}...`);
    }

    handleModelLoaded(modelDetail) {
        console.log('🤖 === AUTONOMOUS SYSTEM HANDLING MODEL LOADED ===');
        console.log('Model detail:', modelDetail);
        
        // Trigger autonomous greeting for newly loaded model
        if (modelDetail && modelDetail.modelData && modelDetail.modelData.name) {
            const modelName = modelDetail.modelData.name;
            console.log('🤖 Processing newly loaded model for autonomous greeting:', modelName);
            
            const avatarInfo = {
                id: modelName,
                name: modelName,
                displayName: this.formatAvatarName(modelName)
            };
            
            // Add pixiModel reference if available
            if (modelDetail.modelData.pixiModel) {
                avatarInfo.pixiModel = modelDetail.modelData.pixiModel;
            }
            
            // Schedule autonomous greeting with delay
            const delay = 2000 + Math.random() * 3000; // 2-5 seconds
            console.log(`🤖 Scheduling autonomous greeting for ${avatarInfo.displayName} in ${delay.toFixed(0)}ms`);
            
            setTimeout(() => {
                this.sendAutonomousGreeting(avatarInfo);
                // Auto-enable autonomous conversations if not already enabled
                if (!this.autonomousEnabled) {
                    console.log('🤖 Auto-enabling autonomous conversations due to model load');
                    this.enableAutonomousConversations();
                }
            }, delay);
        }
        console.log('🤖 === END AUTONOMOUS MODEL LOADED HANDLING ===');
    }

    formatAvatarName(modelName) {
        // Convert model names like 'haruka' to 'Haruka'
        return modelName.charAt(0).toUpperCase() + modelName.slice(1);
    }

    async sendAutonomousGreeting(avatar) {
        console.log('🤖 === SENDING AUTONOMOUS GREETING ===');
        console.log('Avatar info:', avatar);
        
        try {
            // Generate AI-based greeting using backend
            const greeting = await this.generateAutonomousMessage(avatar, 'greeting', {
                context: 'Avatar just loaded and is greeting the user',
                intent: 'welcome_user',
                emotion: 'happy'
            });
            
            console.log('💬 Generated greeting:', greeting);
            
            if (greeting) {
                // Add greeting message to chat
                if (window.addMessage && typeof window.addMessage === 'function') {
                    console.log('📝 Adding autonomous greeting to chat...');
                    window.addMessage('ai', greeting, 'autonomous', avatar, {
                        emotion: 'happy',
                        timestamp: new Date().toLocaleTimeString(),
                        is_autonomous: true,
                        is_greeting: true
                    });
                    console.log('✅ Autonomous greeting added to chat');
                } else {
                    console.warn('⚠️ Cannot add autonomous greeting - addMessage not available');
                }
                
                // Add to message history if chat manager is available
                if (this.avatarChatManager && this.avatarChatManager.messageHistory) {
                    this.avatarChatManager.messageHistory.push({
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
                }
                
                // Trigger avatar motion if available
                this.triggerAutonomousAvatarMotion(avatar, 'happy');
                
                // Trigger enhanced TTS with lipsync if available
                if (window.triggerEnhancedTTSWithLipsync) {
                    console.log('🔊 Triggering enhanced TTS with lipsync for autonomous greeting...');
                    try {
                        await window.triggerEnhancedTTSWithLipsync(
                            greeting,
                            'happy',
                            avatar.id,
                            {}, // personality traits
                            0.7  // intensity
                        );
                        console.log('✅ Enhanced TTS with lipsync triggered successfully');
                    } catch (error) {
                        console.warn('⚠️ Enhanced TTS failed, trying fallback:', error);
                        
                        // Fallback to basic TTS
                        if (typeof triggerEmotionalTTS === 'function') {
                            triggerEmotionalTTS(greeting, 'happy', avatar.id, {}, 0.7);
                        }
                    }
                } else if (typeof triggerEmotionalTTS === 'function') {
                    console.log('🔊 Triggering basic TTS for autonomous greeting...');
                    try {
                        triggerEmotionalTTS(
                            greeting,
                            'happy',
                            avatar.id,
                            {}, // personality traits
                            0.7  // intensity
                        );
                        console.log('✅ Basic TTS triggered successfully');
                    } catch (error) {
                        console.warn('⚠️ Error triggering TTS:', error);
                    }
                } else {
                    console.warn('⚠️ No TTS functions available');
                }
                
                console.log(`🎉 ${avatar.displayName} sent autonomous greeting: "${greeting}"`);
            } else {
                console.warn('⚠️ Failed to generate greeting, avatar will remain silent');
            }
            
        } catch (error) {
            console.error('❌ Error sending autonomous greeting:', error);
        }
        
        console.log('🤖 === END AUTONOMOUS GREETING ===');
    }

    async generateAutonomousMessage(avatar, messageType, context) {
        /**
         * Generate AI-based autonomous messages using the backend LLM
         * @param {Object} avatar - Avatar object with id, name, displayName
         * @param {String} messageType - 'greeting', 'spontaneous', 'response'
         * @param {Object} context - Context for message generation
         */
        try {
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
            
            // Sanitize avatar data to prevent circular references
            const sanitizedAvatar = {
                id: avatar.id,
                name: avatar.name,
                displayName: avatar.displayName,
                // Only include safe properties, exclude Live2D model references
            };
            
            // Sanitize active avatars to prevent circular references
            const sanitizedActiveAvatars = this.avatarChatManager ? 
                this.avatarChatManager.getActiveAvatars().map(a => ({
                    id: a.id,
                    name: a.name,
                    displayName: a.displayName
                })) : [sanitizedAvatar];
            
            // Sanitize conversation history to remove any complex objects
            const sanitizedHistory = this.avatarChatManager ? 
                this.avatarChatManager.messageHistory.slice(-3).map(msg => ({
                    id: msg.id,
                    message: msg.message,
                    sender: msg.sender,
                    timestamp: msg.timestamp,
                    // Remove any circular references or complex objects
                })) : [];
            
            const requestData = {
                message_type: 'autonomous',
                autonomous_type: messageType,
                avatar_id: sanitizedAvatar.id,
                avatar_name: sanitizedAvatar.name,
                avatar_display_name: sanitizedAvatar.displayName,
                context: context, // Context should be simple object passed by caller
                active_avatars: sanitizedActiveAvatars,
                conversation_history: sanitizedHistory,
                user_info: this.avatarChatManager?.currentUser ? {
                    user_id: this.avatarChatManager.currentUser.id,
                    display_name: this.avatarChatManager.currentUser.display_name || 'User'
                } : null
            };

            console.log(`🤖 Generating ${messageType} message for ${avatar.displayName}...`);
            
            // Safe JSON stringify with circular reference protection
            let requestBody;
            try {
                requestBody = JSON.stringify(requestData);
            } catch (jsonError) {
                console.error('❌ JSON serialization error:', jsonError);
                console.log('🔧 Attempting to clean requestData...');
                
                // Fallback: create minimal safe request
                const safeRequestData = {
                    message_type: 'autonomous',
                    autonomous_type: messageType,
                    avatar_id: String(sanitizedAvatar.id),
                    avatar_name: String(sanitizedAvatar.name),
                    avatar_display_name: String(sanitizedAvatar.displayName),
                    context: typeof context === 'string' ? context : JSON.stringify(context),
                    active_avatars: [{ 
                        id: sanitizedAvatar.id, 
                        name: sanitizedAvatar.name, 
                        displayName: sanitizedAvatar.displayName 
                    }],
                    conversation_history: [],
                    user_info: null
                };
                
                requestBody = JSON.stringify(safeRequestData);
                console.log('✅ Using safe fallback request data');
            }
            
            const response = await fetch(`${apiBaseUrl}/api/chat/autonomous`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: requestBody
            });

            if (!response.ok) {
                console.warn(`Autonomous message API failed: ${response.status}`);
                return null;
            }

            const data = await response.json();
            console.log(`✅ Generated autonomous message for ${avatar.displayName}:`, data.message);
            
            return data.message || data.reply;
            
        } catch (error) {
            console.error('❌ Error generating autonomous message:', error);
            return null;
        }
    }

    triggerAutonomousAvatarMotion(avatar, emotion) {
        // Find the avatar's PIXI model and trigger motion
        if (window.live2dMultiModelManager) {
            const models = window.live2dMultiModelManager.getAllModels();
            const avatarModel = models.find(m => m.name === avatar.id);
            
            // Support both .model and .pixiModel properties
            const pixiModel = avatarModel?.model || avatarModel?.pixiModel || avatar.pixiModel;
            
            if (pixiModel) {
                console.log('🎭 Triggering autonomous avatar motion:', emotion);
                
                // Trigger subtle motion for autonomous conversations
                if (typeof window.triggerAvatarMotion === 'function') {
                    window.triggerAvatarMotion(pixiModel, emotion);
                } else if (typeof pixiModel.motion === 'function') {
                    // Direct motion trigger as fallback
                    try {
                        pixiModel.motion(emotion === 'happy' ? 'happy' : 'idle');
                    } catch (e) {
                        console.warn('Direct motion trigger failed:', e);
                    }
                }
                
                // Also trigger a subtle idle motion
                setTimeout(() => {
                    if (typeof window.triggerSubtleIdleMotion === 'function') {
                        window.triggerSubtleIdleMotion(pixiModel);
                    }
                }, 1000);
            } else {
                console.warn('🤖 No PIXI model found for autonomous motion:', avatar.id);
            }
        }
    }

    enableAutonomousConversations() {
        this.autonomousEnabled = true;
        
        // Notify backend to start autonomous system
        if (typeof socket !== 'undefined' && socket.connected) {
            socket.emit('enable_autonomous_avatars', { enabled: true });
        }

        // Add system message
        if (window.addSystemMessage) {
            window.addSystemMessage('🤖 Autonomous avatar conversations enabled', 'info');
        }

        console.log('🤖 Autonomous conversations enabled');
    }

    disableAutonomousConversations() {
        this.autonomousEnabled = false;
        
        // Notify backend to stop autonomous system
        if (typeof socket !== 'undefined' && socket.connected) {
            socket.emit('enable_autonomous_avatars', { enabled: false });
        }

        // Add system message
        if (window.addSystemMessage) {
            window.addSystemMessage('🤖 Autonomous avatar conversations disabled', 'info');
        }

        console.log('🤖 Autonomous conversations disabled');
    }

    toggleAutonomousConversations() {
        if (this.autonomousEnabled) {
            this.disableAutonomousConversations();
        } else {
            this.enableAutonomousConversations();
        }
    }

    getAutonomousStatus() {
        return {
            enabled: this.autonomousEnabled,
            lastUserActivity: this.lastUserActivity,
            timeSinceLastActivity: Date.now() - this.lastUserActivity
        };
    }
}

// Extend the existing addMessage function to handle autonomous messages
(function() {
    if (window.addMessage && typeof window.addMessage === 'function') {
        const originalAddMessage = window.addMessage;
        
        window.addMessage = function(sender, message, type = 'info', avatar = null, metadata = null) {
            // Add special styling for autonomous messages
            if (metadata && metadata.is_autonomous) {
                type = type + ' autonomous';
            }
            
            if (metadata && metadata.is_self_reflection) {
                type = type + ' reflection';
            }
            
            // Call original function
            return originalAddMessage.call(this, sender, message, type, avatar, metadata);
        };
    } else {
        console.warn('🤖 window.addMessage not available - autonomous message styling disabled');
    }
})();

// Global instance
let autonomousAvatarUI = null;

// Initialize immediately when possible, don't wait for chat manager
function initializeAutonomousAvatarUI() {
    if (!autonomousAvatarUI) {
        // Initialize with or without chat manager
        const chatManager = window.avatarChatManager || null;
        autonomousAvatarUI = new AutonomousAvatarUI(chatManager);
        window.autonomousAvatarUI = autonomousAvatarUI;
        
        console.log('🤖 Autonomous Avatar UI initialized successfully');
        
        // Check for active avatars after a delay
        setTimeout(() => {
            if (window.avatarChatManager) {
                const activeAvatars = window.avatarChatManager.getActiveAvatars();
                console.log('🎭 Checking for active avatars:', activeAvatars.length);
                
                if (activeAvatars.length >= 1 && !autonomousAvatarUI.autonomousEnabled) {
                    console.log('🤖 Enabling autonomous conversations for', activeAvatars.length, 'avatar(s)');
                    autonomousAvatarUI.enableAutonomousConversations();
                }
            }
        }, 2000);
        
        return true;
    }
    return false;
}

// Auto-initialize immediately
document.addEventListener('DOMContentLoaded', () => {
    console.log('🤖 DOM loaded - initializing autonomous avatar system');
    initializeAutonomousAvatarUI();
});

// Also initialize on script load in case DOM is already ready
if (document.readyState === 'loading') {
    console.log('🤖 Document still loading - will initialize on DOMContentLoaded');
} else {
    console.log('🤖 Document already loaded - initializing autonomous avatar system immediately');
    initializeAutonomousAvatarUI();
}

// Check periodically in case chat manager loads later
setInterval(() => {
    if (!autonomousAvatarUI) {
        initializeAutonomousAvatarUI();
    } else if (autonomousAvatarUI && !autonomousAvatarUI.avatarChatManager && window.avatarChatManager) {
        // Update chat manager reference if it becomes available
        console.log('🔄 Updating autonomous system with chat manager');
        autonomousAvatarUI.avatarChatManager = window.avatarChatManager;
    }
}, 3000);

// Export to window
window.AutonomousAvatarUI = AutonomousAvatarUI;
window.initializeAutonomousAvatarUI = initializeAutonomousAvatarUI;

// Add global test functions for debugging
window.testAutonomousSystem = function() {
    if (autonomousAvatarUI) {
        console.log('🤖 Testing autonomous system...');
        autonomousAvatarUI.enableAutonomousConversations();
        
        // Force trigger a test message after 5 seconds
        setTimeout(() => {
            if (typeof socket !== 'undefined' && socket.connected) {
                socket.emit('test_autonomous_message');
                console.log('🤖 Test autonomous message requested');
            }
        }, 5000);
        
        return true;
    } else {
        console.error('❌ Autonomous avatar UI not initialized');
        return false;
    }
};

window.getAutonomousStatus = function() {
    if (autonomousAvatarUI) {
        console.log('🤖 Autonomous system status:', {
            enabled: autonomousAvatarUI.autonomousEnabled,
            manager: !!autonomousAvatarUI.avatarChatManager,
            lastActivity: autonomousAvatarUI.lastUserActivity,
            socketConnected: typeof socket !== 'undefined' && socket.connected
        });
    } else {
        console.log('❌ Autonomous system not initialized');
    }
};

// Test function to manually trigger greeting for any loaded model
window.testAutonomousGreeting = function() {
    console.log('🧪 Testing autonomous greeting...');
    
    if (!autonomousAvatarUI) {
        console.error('❌ Autonomous system not initialized');
        return false;
    }
    
    // Try to find any loaded model
    if (window.live2dMultiModelManager) {
        const models = window.live2dMultiModelManager.getAllModels();
        console.log('🔍 Found models:', models.length);
        
        if (models.length > 0) {
            const model = models[0];
            const avatarInfo = {
                id: model.name,
                name: model.name,
                displayName: autonomousAvatarUI.formatAvatarName(model.name),
                pixiModel: model.model || model.pixiModel
            };
            
            console.log('🎭 Testing greeting for:', avatarInfo.displayName);
            autonomousAvatarUI.sendAutonomousGreeting(avatarInfo);
            return true;
        } else {
            console.error('❌ No models loaded to test with');
            return false;
        }
    } else {
        console.error('❌ Live2D manager not available');
        return false;
    }
};
