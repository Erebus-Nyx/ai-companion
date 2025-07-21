/**
 * Live2D Model Loading and Management System
 * Handles model initialization, loading, and management
 */

// Global variables for the modular system
let live2dIntegration = null;
let uiController = null;
let live2dMultiModelManager = null;
let currentModel = null;
let pixiApp = null;

// Function to update current model reference when active model changes
function updateCurrentModelReference() {
    if (live2dMultiModelManager) {
        const activeModelData = live2dMultiModelManager.getActiveModel();
        
        if (activeModelData && activeModelData.model) {
            currentModel = activeModelData.model;
            
            // Update PIXI app reference from integration
            if (live2dIntegration && live2dIntegration.app) {
                pixiApp = live2dIntegration.app;
            }
            
            // Set up mouse interaction for the new current model
            if (currentModel && pixiApp && !currentModel._interactionSetup) {
                setupLive2DMouseInteraction(currentModel);
                currentModel._interactionSetup = true;
            }
            
            return true;
        } else {
            // Try alternative method - get all models and find the active one
            const allModels = live2dMultiModelManager.getAllModels();
            
            for (let modelData of allModels) {
                if (modelData.model && modelData.model.visible) {
                    currentModel = modelData.model;
                    
                    // Update PIXI app reference
                    if (live2dIntegration && live2dIntegration.app) {
                        pixiApp = live2dIntegration.app;
                    }
                    
                    // Set up mouse interaction
                    if (currentModel && pixiApp && !currentModel._interactionSetup) {
                        setupLive2DMouseInteraction(currentModel);
                        currentModel._interactionSetup = true;
                    }
                    
                    return true;
                }
            }
            
            currentModel = null;
            return false;
        }
    }
    currentModel = null;
    return false;
}

// Initialize the modular Live2D system
async function initializeLive2D() {
    try {
        console.log('Initializing Live2D modular system...');
        
        // Check if modular classes are available, if not use fallback
        if (typeof Live2DIntegration === 'undefined') {
            console.warn('Live2DIntegration class not found, using fallback initialization');
            await initializeFallbackLive2D();
            return;
        }
        
        // Create integration instance
        live2dIntegration = new Live2DIntegration();
        
        // Initialize integration (canvas container)
        const success = await live2dIntegration.initialize('pixiContainer');
        
        if (!success) {
            throw new Error('Failed to initialize Live2D integration');
        }
        
        // Create UI controller
        uiController = new Live2DUIController(live2dIntegration);
        
        // Initialize UI controller
        await uiController.initialize();
        
        // Store reference to multi-model manager for global access
        live2dMultiModelManager = live2dIntegration.modelManager;
        
        // Store PIXI app reference from integration.core.app
        pixiApp = live2dIntegration.core.app;
        
        // Make globals available to debug console and other scripts
        window.live2dIntegration = live2dIntegration;
        window.live2dMultiModelManager = live2dMultiModelManager;
        window.uiController = uiController;
        window.pixiApp = pixiApp;
        
        // Expose the interaction manager for debug functions
        if (live2dIntegration && live2dIntegration.core && live2dIntegration.core.interactionManager) {
            window.interactionManager = live2dIntegration.core.interactionManager;
        }
        
        // Also expose the SDK for debug console
        window.LIVE2DCUBISMCORE = window.Live2DCubismCore;
        
        // Apply interaction fix immediately after initialization
        fixPixiInteractionSystem();
        
        // Set up connection between multi-model manager and UI controller
        live2dMultiModelManager.setUIController(uiController);
        
        // Initialize the People panel with actual loaded models
        populatePeopleModels();
        
        console.log('Live2D system initialized successfully!');
        
    } catch (error) {
        console.error('Failed to initialize Live2D system:', error);
        console.log('Attempting fallback initialization...');
        await initializeFallbackLive2D();
    }
}

// Fallback initialization with Direct Mouse Interaction Implementation
async function initializeFallbackLive2D() {
    try {
        console.log('Initializing fallback Live2D system with mouse interaction...');
        
        // Create basic PIXI application
        pixiApp = new PIXI.Application({
            width: window.innerWidth,
            height: window.innerHeight,
            backgroundColor: 0x000000,
            transparent: true,
            antialias: true,
            resolution: window.devicePixelRatio || 1,
            autoDensity: true
        });
        
        // Add canvas to container
        const container = document.getElementById('pixiContainer');
        container.appendChild(pixiApp.view);
        
        // Set up stage interaction
        pixiApp.stage.interactive = true;
        pixiApp.stage.hitArea = pixiApp.screen;
        
        // Make globals available
        window.pixiApp = pixiApp;
        window.currentModel = null;
        
        console.log('✅ Fallback Live2D system with mouse interaction initialized');
        
        // Set up model info display
        updateModelInfoDisplay('System ready - load a model to test mouse interaction');
        
        // Try to load a test model if available
        await tryLoadTestModel();
        
    } catch (error) {
        console.error('Failed to initialize fallback Live2D system:', error);
        updateModelInfoDisplay('❌ Failed to initialize Live2D system');
    }
}

// Try to load a test model for interaction testing
async function tryLoadTestModel() {
    try {
        const response = await fetch('/api/live2d/models');
        if (response.ok) {
            const models = await response.json();
            if (models && models.length > 0) {
                console.log(`Found ${models.length} models available for testing`);
                updateModelInfoDisplay(`Found ${models.length} models - use People panel to load one`);
            }
        }
    } catch (error) {
        console.log('Could not fetch models for testing:', error.message);
        updateModelInfoDisplay('System ready - add models via People panel');
    }
}

// Enhanced model loading function with mouse interaction
async function loadLive2DModel(modelPath) {
    try {
        console.log('🎭 Loading Live2D model from:', modelPath);
        
        if (!pixiApp) {
            throw new Error('PIXI application not available');
        }
        
        updateModelInfoDisplay('Loading model...');
        
        // Clear existing model
        if (currentModel) {
            pixiApp.stage.removeChild(currentModel);
            currentModel.destroy();
            currentModel = null;
        }
        
        // Load new model using Live2D Viewer Web pattern
        currentModel = await Live2DModel.from(modelPath);
        
        if (!currentModel) {
            throw new Error('Failed to create Live2D model');
        }
        
        // Add to stage
        pixiApp.stage.addChild(currentModel);
        
        // Center the model
        currentModel.x = pixiApp.screen.width / 2;
        currentModel.y = pixiApp.screen.height / 2;
        
        // Set initial scale
        currentModel.scale.set(0.3);
        
        // Enable mouse interactions using Live2D Viewer Web patterns
        setupLive2DMouseInteraction(currentModel);
        
        // Store globally
        window.currentModel = currentModel;
        
        console.log('✅ Model loaded successfully with mouse interaction:', currentModel);
        
        // Update model info display
        const modelName = currentModel.internalModel?.settings?.name || 'Unknown Model';
        updateModelInfoDisplay(`✅ ${modelName} loaded - drag to move, scroll to scale`);
        
        return currentModel;
        
    } catch (error) {
        console.error('❌ Error loading model:', error);
        updateModelInfoDisplay(`❌ Failed to load model: ${error.message}`);
        throw error;
    }
}

// Override onModelChange to use new loading function
function onModelChange() {
    console.log('onModelChange called');
    const modelSelect = document.getElementById('modelSelect');
    const modelName = modelSelect?.value;
    
    if (!modelName) {
        console.log('No model selected');
        return;
    }
    
    // Try to load the model with mouse interaction
    const modelPath = `/static/live2d_models/${modelName}/${modelName}.model3.json`;
    loadLive2DModel(modelPath).catch(error => {
        console.error('Failed to load model:', error);
        updateModelInfoDisplay(`❌ Failed to load ${modelName}\nError: ${error.message}`);
    });
}

// Export functions for global access
window.initializeLive2D = initializeLive2D;
window.updateCurrentModelReference = updateCurrentModelReference;
window.loadLive2DModel = loadLive2DModel;
window.onModelChange = onModelChange;
window.live2dIntegration = live2dIntegration;
window.live2dMultiModelManager = live2dMultiModelManager;
window.uiController = uiController;
window.currentModel = currentModel;
window.pixiApp = pixiApp;
