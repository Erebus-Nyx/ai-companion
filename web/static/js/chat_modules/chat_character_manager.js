/**
 * Chat Character Manager
 * Manages active character icons in the chat title bar and character switching
 */

class ChatCharacterManager {
    constructor() {
        this.activeCharacters = [];
        this.currentCharacter = null;
        this.charactersContainer = null;
        this.init();
    }
    
    init() {
        this.charactersContainer = document.getElementById('characterIconsContainer');
        this.loadActiveCharacters();
        this.setupModelLoadListeners();
        console.log('✅ Chat Character Manager initialized');
    }
    
    setupModelLoadListeners() {
        // Listen for model loading events from various sources
        document.addEventListener('modelLoaded', (event) => {
            console.log('🎭 Model loaded event detected:', event.detail);
            this.refreshCharacters();
        });
        
        document.addEventListener('modelRemoved', (event) => {
            console.log('🗑️ Model removed event detected:', event.detail);
            this.refreshCharacters();
        });
        
        // Listen for Live2D system events
        if (window.live2dMultiModelManager) {
            // Hook into existing model manager events if available
            const originalAddModel = window.live2dMultiModelManager.addModel;
            if (originalAddModel) {
                window.live2dMultiModelManager.addModel = (...args) => {
                    const result = originalAddModel.apply(window.live2dMultiModelManager, args);
                    setTimeout(() => this.refreshCharacters(), 500); // Delay to ensure model is fully loaded
                    return result;
                };
            }
        }
        
        // Check for changes periodically as fallback
        setInterval(() => {
            this.checkForModelChanges();
        }, 3000);
    }
    
    checkForModelChanges() {
        if (!window.live2dMultiModelManager) return;
        
        const currentModels = window.live2dMultiModelManager.getAllModels();
        const currentCount = currentModels.length;
        const previousCount = this.activeCharacters.length;
        
        if (currentCount !== previousCount) {
            console.log(`🔄 Model count changed: ${previousCount} → ${currentCount}`);
            this.refreshCharacters();
        }
    }
    
    async loadActiveCharacters() {
        try {
            // Get active avatars from Live2D system
            if (window.live2dMultiModelManager) {
                const models = window.live2dMultiModelManager.getAllModels();
                this.activeCharacters = models.map(model => ({
                    id: model.id || model.name,
                    name: model.name || model.id,
                    initials: this.generateInitials(model.name || model.id),
                    isActive: false
                }));
                
                console.log('📊 Loaded characters from Live2D system:', this.activeCharacters);
            } else {
                // Try to get models from other sources
                try {
                    const response = await fetch('/api/live2d/models');
                    if (response.ok) {
                        const modelsData = await response.json();
                        if (modelsData && modelsData.models) {
                            this.activeCharacters = modelsData.models.map(model => ({
                                id: model.id || model.name,
                                name: model.name || model.id,
                                initials: this.generateInitials(model.name || model.id),
                                isActive: false
                            }));
                            console.log('📊 Loaded characters from API:', this.activeCharacters);
                        }
                    }
                } catch (apiError) {
                    console.log('No models available from API');
                }
            }
            
            // If no characters found, show empty state
            if (this.activeCharacters.length === 0) {
                this.activeCharacters = [];
                console.log('📭 No active characters found');
            } else {
                // Set first character as active if none selected
                if (!this.currentCharacter) {
                    this.currentCharacter = this.activeCharacters[0].id;
                    this.activeCharacters[0].isActive = true;
                }
            }
            
            this.renderCharacterIcons();
            
        } catch (error) {
            console.error('Error loading active characters:', error);
            this.renderCharacterIcons(); // Render empty state
        }
    }
    
    generateInitials(name) {
        if (!name) return '?';
        return name.split(' ')
                  .map(word => word.charAt(0).toUpperCase())
                  .join('')
                  .substring(0, 2);
    }
    
    renderCharacterIcons() {
        if (!this.charactersContainer) {
            this.charactersContainer = document.getElementById('characterIconsContainer');
        }
        
        if (!this.charactersContainer) return;
        
        this.charactersContainer.innerHTML = '';
        
        // If no characters are loaded, don't show any message (the + button is visible)
        if (this.activeCharacters.length === 0) {
            return;
        }
        
        this.activeCharacters.forEach(character => {
            const iconElement = document.createElement('div');
            iconElement.className = `character-icon ${character.isActive ? 'active' : ''}`;
            iconElement.setAttribute('data-character-id', character.id);
            
            // Create character name span
            const nameSpan = document.createElement('span');
            nameSpan.className = 'character-name';
            nameSpan.textContent = character.name;
            nameSpan.onclick = (e) => {
                e.stopPropagation();
                this.switchToCharacter(character.id);
            };
            
            // Create remove button
            const removeSpan = document.createElement('span');
            removeSpan.className = 'character-remove';
            removeSpan.textContent = '×';
            removeSpan.onclick = (e) => {
                e.stopPropagation();
                this.removeCharacterWithConfirm(character.id);
            };
            
            iconElement.appendChild(nameSpan);
            iconElement.appendChild(removeSpan);
            
            this.charactersContainer.appendChild(iconElement);
        });
    }
    
    switchToCharacter(characterId) {
        console.log(`🔄 Switching to character: ${characterId}`);
        
        const previousCharacter = this.activeCharacters.find(c => c.isActive);
        
        // Update active states
        this.activeCharacters.forEach(character => {
            character.isActive = (character.id === characterId);
        });
        
        // Update current character
        this.currentCharacter = characterId;
        
        // Re-render icons to update visual state
        this.renderCharacterIcons();
        
        // Notify Live2D system to switch focus
        this.notifyLive2DSwitch(characterId);
        
        // Notify chat system about character change
        this.notifyChatSystem(characterId);
        
        // Dispatch event for state manager
        document.dispatchEvent(new CustomEvent('chat:characterChanged', {
            detail: { 
                characterId, 
                previousCharacterId: previousCharacter?.id,
                character: this.activeCharacters.find(c => c.id === characterId)
            }
        }));
        
        // Show feedback message
        const character = this.activeCharacters.find(c => c.id === characterId);
        if (character) {
            this.showSwitchFeedback(character.name);
        }
    }
    
    notifyLive2DSwitch(characterId) {
        // Integrate with Live2D system to switch active model
        if (window.live2dMultiModelManager) {
            try {
                window.live2dMultiModelManager.setActiveModel(characterId);
                console.log(`🎭 Live2D switched to: ${characterId}`);
            } catch (error) {
                console.error('Error switching Live2D model:', error);
            }
        }
        
        // Also notify the model manager if available
        if (window.setActiveCharacter) {
            window.setActiveCharacter(characterId);
        }
    }
    
    notifyChatSystem(characterId) {
        // Update chat system with new active character
        if (window.avatarChatManager) {
            try {
                window.avatarChatManager.setActiveCharacter(characterId);
                console.log(`💬 Chat system switched to: ${characterId}`);
            } catch (error) {
                console.error('Error switching chat character:', error);
            }
        }
    }
    
    showSwitchFeedback(characterName) {
        // Create a temporary feedback element
        const feedback = document.createElement('div');
        feedback.className = 'character-switch-feedback';
        feedback.textContent = `Switched to ${characterName}`;
        feedback.style.cssText = `
            position: fixed;
            top: 60px;
            right: 20px;
            background: rgba(74, 144, 226, 0.9);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            z-index: 10000;
            animation: slideInRight 0.3s ease, fadeOut 0.3s ease 2.7s;
            pointer-events: none;
        `;
        
        document.body.appendChild(feedback);
        
        // Remove after animation
        setTimeout(() => {
            if (feedback.parentNode) {
                feedback.parentNode.removeChild(feedback);
            }
        }, 3000);
    }
    
    addCharacter(character) {
        const existingIndex = this.activeCharacters.findIndex(c => c.id === character.id);
        
        if (existingIndex === -1) {
            this.activeCharacters.push({
                id: character.id,
                name: character.name,
                initials: this.generateInitials(character.name),
                isActive: false
            });
            
            this.renderCharacterIcons();
            console.log(`➕ Added character: ${character.name}`);
        }
    }
    
    removeCharacter(characterId) {
        const index = this.activeCharacters.findIndex(c => c.id === characterId);
        
        if (index !== -1) {
            const removedCharacter = this.activeCharacters[index];
            this.activeCharacters.splice(index, 1);
            
            // If removing the active character, switch to first available
            if (removedCharacter.isActive && this.activeCharacters.length > 0) {
                this.switchToCharacter(this.activeCharacters[0].id);
            }
            
            this.renderCharacterIcons();
            console.log(`➖ Removed character: ${removedCharacter.name}`);
            
            // Also remove from Live2D system if available
            if (window.live2dMultiModelManager) {
                try {
                    window.live2dMultiModelManager.removeModel(characterId);
                } catch (error) {
                    console.error('Error removing model from Live2D system:', error);
                }
            }
        }
    }
    
    removeCharacterWithConfirm(characterId) {
        const character = this.activeCharacters.find(c => c.id === characterId);
        if (!character) return;
        
        if (confirm(`Remove ${character.name}?`)) {
            this.removeCharacter(characterId);
            this.showSwitchFeedback(`Removed ${character.name}`);
        }
    }
    
    getCurrentCharacter() {
        return this.activeCharacters.find(c => c.isActive);
    }
    
    refreshCharacters() {
        this.loadActiveCharacters();
    }
}

// Global instance
let chatCharacterManager = null;

// Function to refresh character list when models are added/removed
window.refreshChatCharacters = function() {
    if (chatCharacterManager) {
        chatCharacterManager.refreshCharacters();
        console.log('🔄 Chat characters refreshed');
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        chatCharacterManager = new ChatCharacterManager();
        window.chatCharacterManager = chatCharacterManager;
        
        // Refresh characters when Live2D system loads
        const checkLive2DInterval = setInterval(() => {
            if (window.live2dMultiModelManager) {
                chatCharacterManager.refreshCharacters();
                clearInterval(checkLive2DInterval);
            }
        }, 1000);
        
    }, 2000); // Wait for other systems to initialize
});

// Export functions
window.switchToCharacter = function(characterId) {
    if (chatCharacterManager) {
        chatCharacterManager.switchToCharacter(characterId);
    }
};

window.addChatCharacter = function(character) {
    if (chatCharacterManager) {
        chatCharacterManager.addCharacter(character);
    }
};

window.removeChatCharacter = function(characterId) {
    if (chatCharacterManager) {
        chatCharacterManager.removeCharacter(characterId);
    }
};

// Function to be called when a model is successfully loaded via dialog
window.onModelLoadedFromDialog = function(modelData) {
    console.log('🎭 Model loaded from dialog:', modelData);
    if (chatCharacterManager) {
        setTimeout(() => {
            chatCharacterManager.refreshCharacters();
        }, 1000); // Give time for the model to be fully registered
    }
};

// Legacy compatibility - People panel has been replaced with chat title bar icons
window.openPeople = function() {
    console.log('📝 People panel has been replaced with character icons in the chat title bar');
    
    // Show a brief message to user
    const message = document.createElement('div');
    message.style.cssText = `
        position: fixed;
        top: 60px;
        right: 20px;
        background: rgba(255, 193, 7, 0.9);
        color: #856404;
        padding: 8px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        z-index: 10000;
        animation: slideInRight 0.3s ease, fadeOut 0.3s ease 2.7s;
        pointer-events: none;
    `;
    message.textContent = 'Character switching moved to chat title bar';
    
    document.body.appendChild(message);
    
    setTimeout(() => {
        if (message.parentNode) {
            message.parentNode.removeChild(message);
        }
    }, 3000);
};

// People panel related stubs
window.closePeople = function() {
    console.log('📝 People panel has been removed - use chat title bar instead');
};

window.togglePeopleSnap = function() {
    console.log('📝 People panel has been removed');
};
