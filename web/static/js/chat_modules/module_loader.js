/**
 * Module Loader and Initializer  
 * Loads and initializes all chat system modules
 * Updated for chat_modules directory structure
 */
class ChatSystemModules {
    constructor() {
        this.modules = {};
        this.initialized = false;
        this.chatManager = null;
    }

    async initializeAllModules() {
        console.log('🚀 Initializing Chat System Modules...');

        try {
            // Check if module classes are available
            if (typeof AvatarPersonalityManager === 'undefined') {
                throw new Error('AvatarPersonalityManager not loaded');
            }
            if (typeof ConversationContextManager === 'undefined') {
                throw new Error('ConversationContextManager not loaded');
            }
            if (typeof ResponseGenerationManager === 'undefined') {
                throw new Error('ResponseGenerationManager not loaded');
            }
            if (typeof AvatarInteractionManager === 'undefined') {
                throw new Error('AvatarInteractionManager not loaded');
            }

            // Initialize personality manager
            this.modules.personalityManager = new AvatarPersonalityManager();
            window.avatarPersonalityManager = this.modules.personalityManager;

            // Initialize conversation context manager  
            this.modules.conversationManager = new ConversationContextManager();
            window.conversationContextManager = this.modules.conversationManager;

            // Initialize response generation manager
            this.modules.responseManager = new ResponseGenerationManager();
            window.responseGenerationManager = this.modules.responseManager;

            // Initialize avatar interaction manager
            this.modules.interactionManager = new AvatarInteractionManager();
            window.avatarInteractionManager = this.modules.interactionManager;

            this.initialized = true;
            console.log('✅ All chat system modules initialized successfully');

            // Initialize the main chat manager
            await this.initializeChatManager();

            // Emit event for other systems to know modules are ready
            document.dispatchEvent(new CustomEvent('chatModulesReady', {
                detail: { modules: this.modules, chatManager: this.chatManager }
            }));

            return this.modules;

        } catch (error) {
            console.error('❌ Error initializing chat modules:', error);
            throw error;
        }
    }

    async initializeChatManager() {
        console.log('🎭 Initializing main chat manager...');
        
        try {
            if (typeof AvatarChatManager === 'undefined') {
                throw new Error('AvatarChatManager not loaded');
            }

            this.chatManager = new AvatarChatManager();
            window.avatarChatManager = this.chatManager;
            
            console.log('✅ Main chat manager initialized');
        } catch (error) {
            console.error('❌ Error initializing chat manager:', error);
            throw error;
        }
    }

    getModule(moduleName) {
        if (!this.initialized) {
            console.warn('⚠️ Modules not yet initialized');
            return null;
        }
        return this.modules[moduleName];
    }

    getAllModules() {
        return this.modules;
    }

    // Helper method to ensure modules are loaded
    async ensureModulesLoaded() {
        if (!this.initialized) {
            await this.initializeAllModules();
        }
        return this.modules;
    }

    // Update conversation history in relevant modules
    updateConversationHistory(messageHistory) {
        if (this.modules.conversationManager) {
            this.modules.conversationManager.updateMessageHistory(messageHistory);
        }
    }

    // Update active avatars in relevant modules
    updateActiveAvatars(activeAvatars) {
        if (this.modules.interactionManager) {
            this.modules.interactionManager.updateActiveAvatars(activeAvatars);
        }
    }

    // Clear all module caches
    clearAllCaches() {
        Object.values(this.modules).forEach(module => {
            if (module.clearCache) {
                module.clearCache();
            }
        });
        console.log('🧹 All module caches cleared');
    }
}

// Create global instance
window.chatSystemModules = new ChatSystemModules();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await window.chatSystemModules.initializeAllModules();
    } catch (error) {
        console.error('Failed to auto-initialize chat modules:', error);
    }
});

// Export for manual initialization if needed
window.ChatSystemModules = ChatSystemModules;
