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
        if (window.sendMessage) {
            const originalSendMessage = window.sendMessage;
            window.sendMessage = async (...args) => {
                this.updateUserActivity();
                return await originalSendMessage.apply(this, args);
            };
        }
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
        
        // Add autonomous message to chat with special styling
        if (window.addMessage) {
            window.addMessage('ai', message, 'autonomous', avatar, {
                ...metadata,
                is_autonomous: true,
                timestamp: new Date().toLocaleTimeString()
            });
        }

        // Add to chat history
        if (this.avatarChatManager) {
            this.avatarChatManager.messageHistory.push({
                type: 'avatar',
                message: message,
                timestamp: new Date(),
                avatar: avatar,
                is_autonomous: true,
                emotions: ['neutral'],
                primary_emotion: metadata.emotion || 'neutral'
            });
        }

        // Trigger avatar motion/expression if available
        this.triggerAutonomousAvatarMotion(avatar, metadata.emotion || 'neutral');

        console.log(`🤖 Autonomous message from ${avatar.name}: ${message.substring(0, 50)}...`);
    }

    handleSelfReflection(data) {
        const { avatar, message, metadata } = data;
        
        // Add self-reflection with special styling
        if (window.addMessage) {
            window.addMessage('ai', message, 'reflection', avatar, {
                ...metadata,
                is_self_reflection: true,
                timestamp: new Date().toLocaleTimeString()
            });
        }

        console.log(`🧠 Self-reflection from ${avatar.name}: ${message.substring(0, 50)}...`);
    }

    triggerAutonomousAvatarMotion(avatar, emotion) {
        // Find the avatar's PIXI model and trigger motion
        if (window.live2dMultiModelManager) {
            const models = window.live2dMultiModelManager.getAllModels();
            const avatarModel = models.find(m => m.name === avatar.id);
            
            if (avatarModel && avatarModel.model) {
                // Trigger subtle motion for autonomous conversations
                if (typeof window.triggerAvatarMotion === 'function') {
                    window.triggerAvatarMotion(avatarModel.model, emotion);
                }
                
                // Also trigger a subtle idle motion
                setTimeout(() => {
                    if (typeof window.triggerSubtleIdleMotion === 'function') {
                        window.triggerSubtleIdleMotion(avatarModel.model);
                    }
                }, 1000);
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
})();

// Global instance
let autonomousAvatarUI = null;

// Initialize when chat manager is ready
function initializeAutonomousAvatarUI() {
    if (window.avatarChatManager && !autonomousAvatarUI) {
        autonomousAvatarUI = new AutonomousAvatarUI(window.avatarChatManager);
        window.autonomousAvatarUI = autonomousAvatarUI;
        
        console.log('🤖 Autonomous Avatar UI initialized successfully');
        
        // Enable by default when any avatars are loaded
        setTimeout(() => {
            const activeAvatars = window.avatarChatManager.getActiveAvatars();
            console.log('🎭 Checking for active avatars:', activeAvatars.length);
            
            if (activeAvatars.length >= 1) {
                console.log('🤖 Enabling autonomous conversations for', activeAvatars.length, 'avatar(s)');
                autonomousAvatarUI.enableAutonomousConversations();
                
                // Also request a test autonomous message to verify the system
                setTimeout(() => {
                    if (typeof socket !== 'undefined' && socket.connected) {
                        socket.emit('test_autonomous_message');
                        console.log('🧪 Requested test autonomous message');
                    }
                }, 5000);
            } else {
                console.log('🤖 No active avatars yet, will check again...');
            }
        }, 2000);
        
        // Also check periodically for newly loaded avatars
        setInterval(() => {
            if (autonomousAvatarUI && !autonomousAvatarUI.autonomousEnabled) {
                const activeAvatars = window.avatarChatManager.getActiveAvatars();
                if (activeAvatars.length >= 1) {
                    console.log('🎭 Found active avatars, enabling autonomous system');
                    autonomousAvatarUI.enableAutonomousConversations();
                }
            }
        }, 10000); // Check every 10 seconds
    }
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(initializeAutonomousAvatarUI, 2000);
});

// Also check periodically in case chat manager loads later
setInterval(() => {
    if (!autonomousAvatarUI) {
        initializeAutonomousAvatarUI();
    }
}, 5000);

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
