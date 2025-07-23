/**
 * Live2D Avatar State Manager
 * Handles saving and loading of avatar states including models, positions, scales, and active character
 */

class Live2DAvatarStateManager {
    constructor() {
        this.storageKey = 'ai2d_chat_live2d_state';
        this.autoSaveInterval = null;
        this.autoSaveDelay = 2000; // 2 seconds
        this.isInitialized = false;
        this.lastStateHash = null; // Track last saved state for change detection
        
        // Bind methods to ensure correct context
        this.saveState = this.saveState.bind(this);
        this.loadState = this.loadState.bind(this);
        this.autoSave = this.autoSave.bind(this);
    }
    
    initialize() {
        if (this.isInitialized) return;
        
        console.log('🎭 Initializing Live2D Avatar State Manager...');
        
        // Set up auto-save on model changes
        this.setupAutoSave();
        
        // Set up event listeners for state changes
        this.setupEventListeners();
        
        this.isInitialized = true;
        console.log('✅ Live2D Avatar State Manager initialized');
    }
    
    setupAutoSave() {
        // Clear any existing interval
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }
        
        // Set up periodic auto-save
        this.autoSaveInterval = setInterval(() => {
            this.autoSave();
        }, this.autoSaveDelay);
    }
    
    setupEventListeners() {
        // Listen for window unload to save state
        window.addEventListener('beforeunload', () => {
            this.saveState();
        });
        
        // Listen for Live2D model changes
        document.addEventListener('live2d:modelLoaded', () => {
            setTimeout(() => this.autoSave(), 500);
        });
        
        document.addEventListener('live2d:modelChanged', () => {
            setTimeout(() => this.autoSave(), 500);
        });
        
        // Listen for chat character changes
        document.addEventListener('chat:characterChanged', () => {
            setTimeout(() => this.autoSave(), 100);
        });
    }
    
    autoSave() {
        try {
            const currentState = this.gatherCurrentState();
            const currentHash = this.generateStateHash(currentState);
            
            // Only save if state has changed
            if (this.lastStateHash !== currentHash) {
                if (currentState.models.length > 0 || currentState.activeCharacter) {
                    localStorage.setItem(this.storageKey, JSON.stringify(currentState));
                    this.lastStateHash = currentHash;
                    console.log(`💾 Auto-saved Live2D state: ${currentState.models.length} models, active: ${currentState.activeCharacter}`);
                }
            }
        } catch (error) {
            console.warn('Auto-save failed:', error);
        }
    }
    
    saveState() {
        try {
            const state = this.gatherCurrentState();
            
            if (state.models.length > 0 || state.activeCharacter) {
                localStorage.setItem(this.storageKey, JSON.stringify(state));
                this.lastStateHash = this.generateStateHash(state);
                console.log(`💾 Manually saved Live2D state: ${state.models.length} models, active: ${state.activeCharacter}`);
            }
            
        } catch (error) {
            console.error('Failed to save Live2D state:', error);
        }
    }
    
    // Generate a simple hash of the state for change detection
    generateStateHash(state) {
        // Create a simplified version for comparison (excluding timestamp)
        const hashData = {
            models: state.models.map(model => ({
                id: model.id,
                position: model.position,
                scale: model.scale,
                visible: model.visible
            })),
            activeCharacter: state.activeCharacter,
            chatCharacters: state.chatCharacters
        };
        
        // Simple string-based hash
        return JSON.stringify(hashData);
    }
    
    gatherCurrentState() {
        const state = {
            version: '1.0',
            timestamp: Date.now(),
            models: [],
            activeCharacter: null,
            chatCharacters: []
        };
        
        // Gather model states from Live2D system
        if (window.live2dMultiModelManager) {
            const manager = window.live2dMultiModelManager;
            
            // Get active character
            state.activeCharacter = manager.activeModelId;
            
            // Get all loaded models and their states
            manager.models.forEach((modelData, modelId) => {
                const modelState = manager.modelStates.get(modelId);
                
                if (modelData && modelState) {
                    const savedModel = {
                        id: modelId,
                        name: modelData.name,
                        path: modelData.path,
                        position: {
                            x: modelData.pixiModel?.x || modelState.position?.x || 0,
                            y: modelData.pixiModel?.y || modelState.position?.y || 0
                        },
                        scale: modelState.scale || 1.0,
                        visible: modelData.pixiModel?.visible ?? modelState.visible ?? true,
                        baseScale: modelData.baseScale || 1.0,
                        loadedAt: modelData.loadedAt || Date.now()
                    };
                    
                    state.models.push(savedModel);
                }
            });
        }
        
        // Gather chat character states
        if (window.chatCharacterManager) {
            const chatManager = window.chatCharacterManager;
            
            state.chatCharacters = chatManager.activeCharacters.map(char => ({
                id: char.id,
                name: char.name,
                isActive: char.isActive
            }));
        }
        
        return state;
    }
    
    async loadState() {
        try {
            const savedData = localStorage.getItem(this.storageKey);
            if (!savedData) {
                console.log('📂 No saved Live2D state found');
                return false;
            }
            
            const state = JSON.parse(savedData);
            console.log(`📂 Loading Live2D state: ${state.models?.length || 0} models from ${new Date(state.timestamp).toLocaleString()}`);
            
            return await this.restoreState(state);
            
        } catch (error) {
            console.error('Failed to load Live2D state:', error);
            return false;
        }
    }
    
    async restoreState(state) {
        if (!state || !state.models) {
            console.log('📂 No models to restore');
            return false;
        }
        
        let restoredCount = 0;
        
        // Wait for Live2D system to be ready
        if (!window.live2dMultiModelManager) {
            console.log('⏳ Waiting for Live2D system...');
            await this.waitForLive2DSystem();
        }
        
        const manager = window.live2dMultiModelManager;
        if (!manager) {
            console.error('❌ Live2D system not available');
            return false;
        }
        
        // Load models in order of last loaded (most recent first)
        const sortedModels = state.models.sort((a, b) => (b.loadedAt || 0) - (a.loadedAt || 0));
        
        for (const modelState of sortedModels) {
            try {
                console.log(`🎭 Restoring model: ${modelState.name}`);
                
                // Check if model is already loaded
                if (manager.models.has(modelState.id)) {
                    console.log(`✅ Model ${modelState.name} already loaded, updating state`);
                    this.updateExistingModelState(modelState);
                    restoredCount++;
                    continue;
                }
                
                // Load the model
                const success = await this.loadModelFromState(modelState);
                if (success) {
                    restoredCount++;
                    
                    // Small delay between model loads to prevent overwhelming the system
                    await new Promise(resolve => setTimeout(resolve, 300));
                }
                
            } catch (error) {
                console.error(`Failed to restore model ${modelState.name}:`, error);
            }
        }
        
        // Set active character after all models are loaded
        if (state.activeCharacter && manager.models.has(state.activeCharacter)) {
            setTimeout(() => {
                manager.setActiveModel(state.activeCharacter);
                console.log(`🎯 Set active character: ${state.activeCharacter}`);
            }, 1000);
        }
        
        // Update chat character manager
        if (window.chatCharacterManager && state.chatCharacters) {
            setTimeout(() => {
                window.chatCharacterManager.refreshCharacters();
                console.log(`💬 Updated chat characters: ${state.chatCharacters.length}`);
            }, 1500);
        }
        
        console.log(`✅ Restored ${restoredCount}/${state.models.length} Live2D models`);
        
        // Update hash to current state to prevent immediate auto-save after load
        if (restoredCount > 0) {
            const currentState = this.gatherCurrentState();
            this.lastStateHash = this.generateStateHash(currentState);
        }
        
        return restoredCount > 0;
    }
    
    async loadModelFromState(modelState) {
        try {
            const manager = window.live2dMultiModelManager;
            
            // Add model using the manager
            await manager.addModel(modelState.id, modelState.path);
            
            // Wait a moment for the model to be fully loaded
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Apply the saved state
            this.updateExistingModelState(modelState);
            
            console.log(`✅ Loaded and configured model: ${modelState.name}`);
            return true;
            
        } catch (error) {
            console.error(`Failed to load model ${modelState.name}:`, error);
            return false;
        }
    }
    
    updateExistingModelState(modelState) {
        const manager = window.live2dMultiModelManager;
        const modelData = manager.models.get(modelState.id);
        
        if (!modelData || !modelData.pixiModel) {
            console.warn(`Cannot update state for ${modelState.name}: model not ready`);
            return;
        }
        
        // Update position
        if (modelState.position) {
            modelData.pixiModel.position.set(
                modelState.position.x || 0,
                modelState.position.y || 0
            );
        }
        
        // Update scale
        if (modelState.scale && modelState.baseScale) {
            const finalScale = modelState.baseScale * modelState.scale;
            modelData.pixiModel.scale.set(finalScale);
            
            // Update UI slider if available
            const scaleSlider = document.getElementById('zoomSlider');
            if (scaleSlider) {
                scaleSlider.value = modelState.scale;
            }
        }
        
        // Update visibility
        if (typeof modelState.visible === 'boolean') {
            modelData.pixiModel.visible = modelState.visible;
        }
        
        // Update model state in manager
        const currentState = manager.modelStates.get(modelState.id);
        if (currentState) {
            Object.assign(currentState, {
                position: modelState.position,
                scale: modelState.scale,
                visible: modelState.visible
            });
        }
        
        console.log(`🔄 Updated state for ${modelState.name}`);
    }
    
    async waitForLive2DSystem(maxWait = 10000) {
        const startTime = Date.now();
        
        while (!window.live2dMultiModelManager && (Date.now() - startTime < maxWait)) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        return !!window.live2dMultiModelManager;
    }
    
    clearState() {
        try {
            localStorage.removeItem(this.storageKey);
            console.log('🗑️ Cleared Live2D state');
        } catch (error) {
            console.error('Failed to clear Live2D state:', error);
        }
    }
    
    exportState() {
        try {
            const state = this.gatherCurrentState();
            const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `live2d_state_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            URL.revokeObjectURL(url);
            console.log('💾 Live2D state exported');
            
        } catch (error) {
            console.error('Failed to export Live2D state:', error);
        }
    }
    
    async importState(file) {
        try {
            const text = await file.text();
            const state = JSON.parse(text);
            
            const success = await this.restoreState(state);
            if (success) {
                console.log('📁 Live2D state imported successfully');
            }
            
            return success;
            
        } catch (error) {
            console.error('Failed to import Live2D state:', error);
            return false;
        }
    }
    
    destroy() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
        }
        
        // Save final state
        this.saveState();
        
        this.isInitialized = false;
        console.log('🔄 Live2D Avatar State Manager destroyed');
    }
}

// Global instance
window.live2dStateManager = new Live2DAvatarStateManager();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        if (window.live2dStateManager) {
            window.live2dStateManager.initialize();
        }
    }, 1000);
});

// Integration functions
window.saveLive2DState = () => window.live2dStateManager?.saveState();
window.loadLive2DState = () => window.live2dStateManager?.loadState();
window.clearLive2DState = () => window.live2dStateManager?.clearState();
window.exportLive2DState = () => window.live2dStateManager?.exportState();

console.log('🎭 Live2D Avatar State Manager loaded');
