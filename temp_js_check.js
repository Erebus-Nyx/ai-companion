console.log('=== Dual Architecture Verification ===');
console.log('PIXI version:', typeof PIXI !== 'undefined' ? PIXI.VERSION : 'Not loaded');
console.log('EventEmitter available:', typeof EventEmitter !== 'undefined');
console.log('Live2D v2 Bundle loaded:', typeof window.Live2D !== 'undefined');
console.log('Cubism 5 Core loaded:', typeof window.Live2DCubismCore !== 'undefined');

// Debug Live2D v2 Bundle
if (typeof window.Live2D !== 'undefined') {
    console.log('✓ Live2D v2 Bundle ready for Cubism 2.x models');
    console.log('- window.Live2D:', typeof window.Live2D);
    console.log('- window.Live2DModelWebGL:', typeof window.Live2DModelWebGL);
    console.log('- window.live2dv2:', typeof window.live2dv2);
}

// Debug Cubism 5 Core
if (typeof window.Live2DCubismCore !== 'undefined') {
    console.log('✓ Cubism 5 Core ready for modern models');
    console.log('- Core version:', window.Live2DCubismCore.Version ? window.Live2DCubismCore.Version.csmGetVersion() : 'unknown');
}

console.log('=== End Verification ===');
// AI Companion API Configuration - Dynamic configuration loading
window.ai2d_chat_CONFIG = {
    // Default fallback configuration
    API_BASE_URL: (() => {
        const protocol = window.location.protocol;
        const hostname = window.location.hostname;
        const port = window.location.port;
        
        // Use current protocol and host
        if (port) {
            return `${protocol}//${hostname}:${port}`;
        }
        return `${protocol}//${hostname}`;
    })(),
    
    // Configuration loading status
    _configLoaded: false,
    _configPromise: null
};

// Function to load server configuration dynamically
async function loadServerConfig() {
    if (window.ai2d_chat_CONFIG._configLoaded) {
        return window.ai2d_chat_CONFIG;
    }
    
    if (window.ai2d_chat_CONFIG._configPromise) {
        return window.ai2d_chat_CONFIG._configPromise;
    }
    
    window.ai2d_chat_CONFIG._configPromise = (async () => {
        try {
            console.log('Loading server configuration from API...');
            
            // Try to fetch configuration from the server
            const configResponse = await fetch('/api/system/config');
            if (configResponse.ok) {
                const serverConfig = await configResponse.json();
                
                // Update the configuration
                window.ai2d_chat_CONFIG.API_BASE_URL = serverConfig.server.base_url;
                window.ai2d_chat_CONFIG.serverConfig = serverConfig;
                window.ai2d_chat_CONFIG._configLoaded = true;
                
                console.log('✅ Server configuration loaded successfully:', serverConfig.server.base_url);
                return window.ai2d_chat_CONFIG;
            } else {
                throw new Error(`Config API returned ${configResponse.status}`);
            }
        } catch (error) {
            console.warn('⚠️ Failed to load server config from API, using fallback:', error.message);
            
            // Fallback: use current location as base
            const protocol = window.location.protocol;
            const hostname = window.location.hostname;
            const port = window.location.port;
            
            window.ai2d_chat_CONFIG.API_BASE_URL = port ? 
                `${protocol}//${hostname}:${port}` : 
                `${protocol}//${hostname}`;
            
            window.ai2d_chat_CONFIG._configLoaded = true;
            
            console.log('Using fallback configuration:', window.ai2d_chat_CONFIG.API_BASE_URL);
            return window.ai2d_chat_CONFIG;
        }
    })();
    
    return window.ai2d_chat_CONFIG._configPromise;
}

// Initialize configuration
console.log('AI Companion API Config (initial):', window.ai2d_chat_CONFIG.API_BASE_URL);
console.log('Protocol detected:', window.location.protocol);

// Helper function for making API calls with proper config loading
window.makeApiCall = async function(endpoint, options = {}) {
    // Ensure config is loaded
    await loadServerConfig();
    
    const url = `${window.ai2d_chat_CONFIG.API_BASE_URL}${endpoint}`;
    console.log(`Making API call to: ${url}`);
    
    return fetch(url, options);
};
// Initialize Live2D plugin following Live2D Viewer Web pattern
console.log('Initializing Live2D plugin (Live2D Viewer Web compatible)...');

// Wait for all scripts to load
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        console.log('Checking library compatibility...');
        
        // Verify libraries are loaded
        if (typeof PIXI === 'undefined') {
            console.error('PIXI.js not loaded');
            return;
        }
        
        if (typeof EventEmitter === 'undefined') {
            console.error('EventEmitter not available');
            return;
        }
        
        console.log('✓ PIXI version:', PIXI.VERSION);
        console.log('✓ EventEmitter type:', typeof EventEmitter);
        
        // Check if PIXI.utils.EventEmitter exists (Live2D Viewer Web pattern)
        if (PIXI.utils && PIXI.utils.EventEmitter) {
            console.log('✓ PIXI.utils.EventEmitter available (Live2D Viewer Web compatible)');
        }
        
        // Check if Live2D plugin is available
        if (typeof PIXI.live2d === 'undefined') {
            console.error('✗ PIXI.live2d not loaded - pixi-live2d-display may not be compatible');
            console.log('Available PIXI properties:', Object.keys(PIXI));
            
            // Try to diagnose the issue
            if (window.pixiLive2DLoadError) {
                console.error('Library loading error detected - check network tab');
            }
        } else {
            console.log('✓ PIXI.live2d loaded successfully');
            console.log('Available PIXI.live2d properties:', Object.keys(PIXI.live2d));
            
            // Check for Live2DModel
            if (PIXI.live2d.Live2DModel) {
                console.log('✓ Live2DModel class available');
                window.Live2DModel = PIXI.live2d.Live2DModel;
                
                // Test if it has the expected methods
                if (typeof PIXI.live2d.Live2DModel.from === 'function') {
                    console.log('✓ Live2DModel.from() method available');
                } else {
                    console.warn('Live2DModel.from() method not found');
                }
            } else {
                console.warn('Live2DModel not found in PIXI.live2d');
            }
            
            // Check for Live2DFactory
            if (PIXI.live2d.Live2DFactory) {
                console.log('✓ Live2DFactory available');
                window.Live2DFactory = PIXI.live2d.Live2DFactory;
            } else {
                console.warn('Live2DFactory not found in PIXI.live2d');
            }
        }
        
        console.log('Live2D plugin initialization check complete');
        console.log('System ready for Live2D model loading');
        
        // NOW INITIALIZE THE LIVE2D SYSTEM
        if (typeof initializeLive2D === 'function') {
            console.log('Starting Live2D modular system initialization...');
            
            // Load server configuration before initializing Live2D
            loadServerConfig().then(() => {
                console.log('Server configuration loaded, initializing Live2D...');
                return initializeLive2D();
            }).then(() => {
                console.log('Live2D system initialization complete!');
            }).catch(error => {
                console.error('Live2D system initialization failed:', error);
            });
        } else {
            console.error('initializeLive2D function not found!');
        }
        
    }, 500); // Increased delay to ensure all libraries are loaded
});
// Global variables for the modular system
let live2dIntegration = null;
let uiController = null;
let live2dMultiModelManager = null; // Make available globally for remove buttons
let currentModel = null; // Add current model reference
let pixiApp = null; // Add PIXI app reference

// Function to update current model reference when active model changes
function updateCurrentModelReference() {
    if (live2dMultiModelManager) {
        const activeModelData = live2dMultiModelManager.getActiveModel();
        console.log('🔍 Active model check:', {
            hasActiveModelData: !!activeModelData,
            activeModelDataKeys: activeModelData ? Object.keys(activeModelData) : null,
            hasModel: activeModelData ? !!activeModelData.model : false,
            modelType: activeModelData && activeModelData.model ? typeof activeModelData.model : null,
            modelName: activeModelData ? activeModelData.name : null
        });
        
        if (activeModelData && activeModelData.model) {
            currentModel = activeModelData.model;
            console.log('🔄 Updated currentModel reference to:', activeModelData.name);
            
            // Update PIXI app reference from integration
            if (live2dIntegration && live2dIntegration.app) {
                pixiApp = live2dIntegration.app;
                console.log('🔄 Updated pixiApp reference from integration');
            }
            
            // Set up mouse interaction for the new current model (only if not already set up)
            if (currentModel && pixiApp && !currentModel._interactionSetup) {
                setupLive2DMouseInteraction(currentModel);
                currentModel._interactionSetup = true; // Mark as set up to prevent duplicates
            }
            
            return true;
        } else {
            // Try alternative method - get all models and find the active one
            const allModels = live2dMultiModelManager.getAllModels();
            console.log('🔍 Trying alternative method - all models:', allModels.length);
            
            for (let modelData of allModels) {
                if (modelData.model && modelData.model.visible) {
                    currentModel = modelData.model;
                    console.log('🔄 Found visible model:', modelData.name);
                    
                    // Update PIXI app reference
                    if (live2dIntegration && live2dIntegration.app) {
                        pixiApp = live2dIntegration.app;
                    }
                    
                    // Set up mouse interaction (only if not already set up)
                    if (currentModel && pixiApp && !currentModel._interactionSetup) {
                        setupLive2DMouseInteraction(currentModel);
                        currentModel._interactionSetup = true;
                    }
                    
                    return true;
                }
            }
            
            currentModel = null;
            console.log('❌ No active model found');
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
        
        // Store PIXI app reference from integration.core.app (correct location)
        pixiApp = live2dIntegration.core.app;
        
        // CRITICAL: Make globals available to debug console and other scripts
        window.live2dIntegration = live2dIntegration;
        window.live2dMultiModelManager = live2dMultiModelManager;
        window.uiController = uiController;
        window.pixiApp = pixiApp;
        
        // Additional debug: verify PIXI app is correctly assigned
        console.log('🔍 PIXI app assignment check:', {
            'live2dIntegration.app': !!live2dIntegration.app,
            'live2dIntegration.core.app': !!live2dIntegration.core.app,
            'assigned pixiApp': !!pixiApp,
            'window.pixiApp': !!window.pixiApp
        });
        
        // CRITICAL: Also expose the interaction manager for debug functions
        if (live2dIntegration && live2dIntegration.core && live2dIntegration.core.interactionManager) {
            window.interactionManager = live2dIntegration.core.interactionManager;
            console.log('✅ Interaction manager exposed globally');
        }
        
        // Also expose the SDK for debug console
        window.LIVE2DCUBISMCORE = window.Live2DCubismCore;
        
        // CRITICAL: Apply interaction fix immediately after initialization
        console.log('🔧 Applying PIXI interaction fix...');
        fixPixiInteractionSystem();
        
        // Set up connection between multi-model manager and UI controller
        live2dMultiModelManager.setUIController(uiController);
        
        // Initialize the People panel with actual loaded models (clear any hardcoded data)
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
            backgroundColor: 0x000000, // Black background instead of blue
            transparent: true,
            antialias: true,
            resolution: window.devicePixelRatio || 1,
            autoDensity: true
        });
        
        // Add canvas to container
        const container = document.getElementById('pixiContainer');
        container.appendChild(pixiApp.view);
        
        // Set up stage interaction (CRITICAL for mouse events)
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
        // This would attempt to load a model from the server
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

// Live2D Viewer Web Mouse Interaction Implementation
function setupLive2DMouseInteraction(model) {
    if (!model || !pixiApp) {
        console.warn('Cannot setup mouse interaction: missing model or PIXI app');
        return;
    }
    
    console.log('🖱️ Setting up Live2D Viewer Web mouse interaction for model:', model.internalModel?.settings?.name || 'Unknown');
    
    // Enable interaction on the model (Live2D Viewer Web pattern)
    model.interactive = true;
    model.buttonMode = true;
    
    // Set up dragging variables
    let isDragging = false;
    let dragStart = { x: 0, y: 0 };
    let modelStart = { x: 0, y: 0 };
    
    // Mouse down - start dragging (Live2D Viewer Web pattern)
    model.removeAllListeners('pointerdown'); // Prevent duplicate listeners
    model.on('pointerdown', (event) => {
        isDragging = true;
        const position = event.data.global;
        dragStart.x = position.x;
        dragStart.y = position.y;
        modelStart.x = model.x;
        modelStart.y = model.y;
        
        // Prevent event bubbling
        event.stopPropagation();
        console.log('🖱️ Model drag started at:', position);
        
        // Update model info
        updateModelInfoDisplay(`Dragging model from (${Math.round(modelStart.x)}, ${Math.round(modelStart.y)})`);
    });
    
    // Mouse move - drag the model (use app stage for global movement)
    pixiApp.stage.removeAllListeners('pointermove'); // Prevent duplicate listeners
    pixiApp.stage.on('pointermove', (event) => {
        if (!isDragging) return;
        
        const position = event.data.global;
        const deltaX = position.x - dragStart.x;
        const deltaY = position.y - dragStart.y;
        
        model.x = modelStart.x + deltaX;
        model.y = modelStart.y + deltaY;
        
        // Update model info during drag
        updateModelInfoDisplay(`Position: (${Math.round(model.x)}, ${Math.round(model.y)}) Scale: ${model.scale.x.toFixed(2)}`);
    });
    
    // Mouse up - stop dragging
    pixiApp.stage.removeAllListeners('pointerup'); // Prevent duplicate listeners
    pixiApp.stage.on('pointerup', () => {
        if (isDragging) {
            isDragging = false;
            console.log('🖱️ Model drag ended at:', { x: model.x, y: model.y });
            updateModelInfoDisplay(`✅ Model positioned at (${Math.round(model.x)}, ${Math.round(model.y)})`);
        }
    });
    
    // Handle mouse leave canvas
    pixiApp.stage.removeAllListeners('pointerupoutside'); // Prevent duplicate listeners
    pixiApp.stage.on('pointerupoutside', () => {
        if (isDragging) {
            isDragging = false;
            console.log('🖱️ Model drag ended (outside canvas)');
            updateModelInfoDisplay(`✅ Model positioned at (${Math.round(model.x)}, ${Math.round(model.y)})`);
        }
    });
    
    // Set up mouse wheel scaling (Live2D Viewer Web pattern)
    setupModelScaling(model);
    
    // Set up hit area testing if available
    setupModelHitAreas(model);
    
    console.log('✅ Mouse interaction setup complete for model');
}

// Live2D Viewer Web scaling pattern implementation
function setupModelScaling(model) {
    if (!pixiApp?.view) {
        console.warn('Cannot setup model scaling: no canvas available');
        return;
    }
    
    const canvas = pixiApp.view;
    
    // Remove any existing wheel listeners to prevent duplicates
    const existingHandler = canvas._live2dWheelHandler;
    if (existingHandler) {
        canvas.removeEventListener('wheel', existingHandler);
    }
    
    // Create wheel handler
    function handleModelWheel(event) {
        event.preventDefault();
        
        if (!model || !model.scale) return;
        
        const scaleFactor = event.deltaY > 0 ? 0.9 : 1.1;
        const newScale = model.scale.x * scaleFactor;
        
        // Limit scale between 0.1 and 5.0 (Live2D Viewer Web limits)
        if (newScale >= 0.1 && newScale <= 5.0) {
            model.scale.set(newScale);
            console.log('🔍 Model scaled to:', newScale.toFixed(2));
            
            // Update UI slider if available
            const slider = document.getElementById('zoomSlider');
            const display = document.getElementById('zoomValue');
            if (slider) slider.value = newScale;
            if (display) display.textContent = newScale.toFixed(2);
            
            // Update model info
            updateModelInfoDisplay(`Position: (${Math.round(model.x)}, ${Math.round(model.y)}) Scale: ${newScale.toFixed(2)}`);
        }
    }
    
    // Store handler reference for cleanup
    canvas._live2dWheelHandler = handleModelWheel;
    
    // Add wheel event listener
    canvas.addEventListener('wheel', handleModelWheel, { passive: false });
    
    console.log('🔍 Mouse wheel scaling set up for model');
}

// Live2D Viewer Web hit area pattern implementation
function setupModelHitAreas(model) {
    if (!model?.internalModel) {
        console.log('Hit areas not available for this model');
        return;
    }
    
    model.removeAllListeners('pointerdown'); // Remove previous listeners
    model.on('pointerdown', (event) => {
        const point = event.data.global;
        
        // Convert global coordinates to model local coordinates
        const localPoint = model.toLocal(point);
        
        console.log('🎯 Hit test at:', localPoint);
        
        // Test hit areas if available (Live2D Viewer Web pattern)
        if (model.internalModel.hitTest) {
            try {
                const hitAreas = model.internalModel.hitTest(localPoint.x, localPoint.y);
                
                if (hitAreas && hitAreas.length > 0) {
                    console.log('🎯 Hit areas detected:', hitAreas);
                    updateModelInfoDisplay(`🎯 Hit: ${hitAreas.join(', ')}`);
                    
                    // Trigger motions based on hit areas
                    hitAreas.forEach(hitArea => {
                        console.log(`🎭 Hit area: ${hitArea}`);
                        // Add motion triggers here if needed
                    });
                } else {
                    console.log('🎯 No hit areas at this location');
                }
            } catch (error) {
                console.warn('Hit test failed:', error);
            }
        } else {
            console.log('🎯 Hit testing not available for this model');
        }
    });
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
        
        // CRITICAL: Enable mouse interactions using Live2D Viewer Web patterns
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
    // Single DOMContentLoaded event listener with backup pattern
    document.addEventListener('DOMContentLoaded', async function() {
        console.log('🚀 Starting AI Companion with BACKUP initialization pattern...');
        
        // Add delay to ensure all scripts are loaded
        setTimeout(async function() {
            try {
                // Set up layout management
                if (typeof setupLayoutManagement === 'function') {
                    setupLayoutManagement();
                }
                
                // Load server configuration if available
                if (typeof loadServerConfig === 'function') {
                    await loadServerConfig();
                    console.log('✓ Server configuration loaded');
                }
                
                // CRITICAL: Initialize Live2D FIRST before other systems
                const live2dSuccess = await initializeLive2D();
                
                if (!live2dSuccess) {
                    console.error('❌ Live2D initialization failed - other systems may not work properly');
                } else {
                    console.log('✅ Live2D system ready for other components');
                }
                
                // Initialize other systems AFTER Live2D is ready
                if (typeof initializeAICompanion === 'function') {
                    const initialized = await initializeAICompanion();
                    
                    if (initialized) {
                        console.log('✅ AI Companion initialization complete!');
                        
                        // Report status
                        setTimeout(() => {
                            if (typeof reportInitializationStatus === 'function') {
                                reportInitializationStatus();
                            }
                        }, 2000);
                    }
                } else {
                    console.log('✅ Backup initialization pattern complete!');
                }
                
            } catch (error) {
                console.error('❌ Critical initialization error:', error);
                if (typeof reportInitializationStatus === 'function') {
                    reportInitializationStatus();
                }
            }
        }, 500); // Delay to ensure script loading
    });
