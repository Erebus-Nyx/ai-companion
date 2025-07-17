class Live2DConfig {
    constructor() {
        this.settings = {
            // Basic settings
            'modelUrl': '/static/assets',                    // URL of directory containing model folders
            'tipsMessage': '',                              // Message tips file (can be empty)
            
            // Model settings
            'modelName': 'kanade',                          // Default fallback model name
            'modelStorage': true,                           // Save model name in browser (last used model)
            'modelRandMode': true,                         // Random model switching
            'preLoadMotion': true,                          // Preload motion files (SDK4 only)
            'tryWebp': false,                               // Try WebP textures first
            
            // Display settings - Modern Live2D Viewer Web approach
            'live2dHeight': 0,                              // Canvas height (0 = auto-detect container)
            'live2dWidth': 0,                               // Canvas width (0 = auto-detect container)
            'canvasMargin': 40,                            // Margin from canvas boundaries (px)
            'modelScale': 0.75,                            // Default model scale (75% of canvas height)
            'waifuMinWidth': '100px',                       // Hide on small screens
            'waifuEdgeSide': 'left:0',                      // Position (left:0, right:0, etc.)
            'waifuResize': true,                            // Allow resizing
            'waifuwidth': '500px',                          // Width of the Live2D container
            'waifuheight': '500px',                         // Height of the Live2D container
            
            // Tool menu settings
            'showToolMenu': true,                           // Show tool buttons
            'canCloseLive2d': true,                         // Show close button
            'canSwitchModel': true,                         // Show model switch button
            'canSwitchHitokoto': false,                     // Show message switch button
            'canTakeScreenshot': true,                      // Show screenshot button
            'canTurnToHomePage': true,                      // Show home button
            'canTurnToAboutPage': true,                     // Show about button
            'showVolumeBtn': false,                         // Show volume buttons
            
            // Message settings
            'showHitokoto': false,                          // Show random messages
            'hitokotoAPI': '',                              // Hitokoto API endpoint
            'showWelcomeMessage': true,                     // Show welcome message
            'showF12OpenMsg': false,                        // Show F12 console message
            'showCopyMessage': false,                       // Show copy message
            
            // Debug settings
            'debug': true,                                  // Global debug mode
            'debugMousemove': false,                        // Debug mouse movement
            'logMessageToConsole': true,                    // Log messages to console
            
            // URLs
            'l2dVersion': '2.0.0',                          // Version string
            'homePageUrl': '/',                             // Home page URL
            'aboutPageUrl': 'https://github.com/Konata09/Live2dOnWeb/',
            'screenshotCaptureName': 'live2d_screenshot.png' // Screenshot filename
        };
    }

    get(key) {
        return this.settings[key];
    }

    set(key, value) {
        this.settings[key] = value;
    }
}

// DYNAMIC MODEL LOADING - No static models
// Models are loaded from database via API calls
// This ensures models are discovered and registered dynamically

// Available models list - populated by API
window.availableModels = [];
window.currentModel = null;
window.lastUsedModel = null;

// PERFORMANCE OPTIMIZATIONS
let modelCachePromise = null;
let isModelCacheReady = false;

// Function to load available models from database with caching
async function loadAvailableModels() {
    // Return existing promise if already loading
    if (modelCachePromise) {
        return modelCachePromise;
    }
    
    // Return cached data if available
    if (isModelCacheReady && window.availableModels.length > 0) {
        return window.availableModels;
    }
    
    modelCachePromise = (async () => {
        try {
            const startTime = performance.now();
            const response = await fetch('http://localhost:13443/api/live2d/models');
            if (response.ok) {
                const models = await response.json();
                window.availableModels = models;
                isModelCacheReady = true;
                const loadTime = (performance.now() - startTime).toFixed(2);
                console.log(`[Live2D Config] Loaded ${models.length} models in ${loadTime}ms`);
                return models;
            } else {
                console.error('[Live2D Config] Failed to load models from API');
                return [];
            }
        } catch (error) {
            console.error('[Live2D Config] Error loading models:', error);
            return [];
        } finally {
            modelCachePromise = null; // Reset promise for future calls
        }
    })();
    
    return modelCachePromise;
}

// Function to get last used model from localStorage
function getLastUsedModel() {
    if (live2d_settings.modelStorage) {
        const saved = localStorage.getItem('modelName');
        if (saved) {
            console.log(`[Live2D Config] Found last used model: ${saved}`);
            return saved;
        }
    }
    console.log(`[Live2D Config] No last used model, using default: ${live2d_settings.modelName}`);
    return live2d_settings.modelName;
}

// Function to save current model as last used
function saveLastUsedModel(modelName) {
    if (live2d_settings.modelStorage) {
        localStorage.setItem('modelName', modelName);
        console.log(`[Live2D Config] Saved last used model: ${modelName}`);
    }
}

// Function to get model info by name from database
function getModelInfo(modelName) {
    return window.availableModels.find(model => model.model_name === modelName);
}

// LIVE2D VIEWER WEB ZOOM SYSTEM
// Based on Live2D Viewer Web ModelEntity approach
// Uses PIXI.js scale and position properties directly

// Scale configuration
const SCALE_CONFIG = {
    default: 1.0,
    min: 0.1,
    max: 3.0,
    step: 0.1
};

// Current model state
let currentModelScale = SCALE_CONFIG.default;
let currentModelPosition = { x: 0, y: 0 };
let currentPixiModel = null;

// Live2D Viewer Web style model scaling
function scaleModel(scaleValue) {
    if (!currentPixiModel) {
        console.warn('[Live2D Scale] No model loaded');
        return;
    }
    
    // Clamp scale value
    scaleValue = Math.max(SCALE_CONFIG.min, Math.min(SCALE_CONFIG.max, scaleValue));
    
    // Apply scale to PIXI model
    currentPixiModel.scale.set(scaleValue);
    currentModelScale = scaleValue;
    
    console.log(`[Live2D Scale] Set model scale to ${scaleValue.toFixed(2)}`);
    
    // Save scale to localStorage
    localStorage.setItem('live2d_model_scale', scaleValue.toString());
    
    // Dispatch custom event
    document.dispatchEvent(new CustomEvent('modelScaleChanged', { 
        detail: { scale: scaleValue } 
    }));
}

// Live2D Viewer Web style model positioning
function positionModel(x, y) {
    if (!currentPixiModel) {
        console.warn('[Live2D Position] No model loaded');
        return;
    }
    
    // Apply position to PIXI model
    currentPixiModel.position.set(x, y);
    currentModelPosition = { x, y };
    
    console.log(`[Live2D Position] Set model position to (${x}, ${y})`);
    
    // Save position to localStorage
    localStorage.setItem('live2d_model_position', JSON.stringify({ x, y }));
    
    // Dispatch custom event
    document.dispatchEvent(new CustomEvent('modelPositionChanged', { 
        detail: { position: { x, y } } 
    }));
}

// Live2D Viewer Web style fit model to canvas
function fitModelToCanvas() {
    if (!currentPixiModel) {
        console.warn('[Live2D Fit] No model loaded');
        return;
    }
    
    // Get canvas dimensions
    const canvas = document.getElementById('pixiContainer');
    if (!canvas) {
        console.warn('[Live2D Fit] Canvas not found');
        return;
    }
    
    const canvasWidth = canvas.offsetWidth;
    const canvasHeight = canvas.offsetHeight;
    
    // Get model bounds
    const modelBounds = currentPixiModel.getBounds();
    
    // Calculate scale to fit model in canvas
    const scaleX = canvasWidth / modelBounds.width;
    const scaleY = canvasHeight / modelBounds.height;
    const fitScale = Math.min(scaleX, scaleY) * 0.8; // 80% of available space
    
    // Apply fit scale
    scaleModel(fitScale);
    
    // Center model in canvas
    centerModel();
    
    console.log(`[Live2D Fit] Fit model to canvas with scale ${fitScale.toFixed(2)}`);
}

// Live2D Viewer Web style center model in canvas
function centerModel() {
    if (!currentPixiModel) {
        console.warn('[Live2D Center] No model loaded');
        return;
    }
    
    // Get canvas dimensions
    const canvas = document.getElementById('pixiContainer');
    if (!canvas) {
        console.warn('[Live2D Center] Canvas not found');
        return;
    }
    
    const canvasWidth = canvas.offsetWidth;
    const canvasHeight = canvas.offsetHeight;
    
    // Center position
    const centerX = canvasWidth / 2;
    const centerY = canvasHeight / 2;
    
    // Apply center position
    positionModel(centerX, centerY);
    
    console.log(`[Live2D Center] Centered model at (${centerX}, ${centerY})`);
}

// Reset model scale and position
function resetModel() {
    scaleModel(SCALE_CONFIG.default);
    centerModel();
    
    // Clear saved values
    localStorage.removeItem('live2d_model_scale');
    localStorage.removeItem('live2d_model_position');
    
    console.log('[Live2D Reset] Reset model scale and position');
}

// Load saved model state
function loadSavedModelState() {
    // Load saved scale
    const savedScale = localStorage.getItem('live2d_model_scale');
    if (savedScale) {
        currentModelScale = parseFloat(savedScale);
        currentModelScale = Math.max(SCALE_CONFIG.min, Math.min(SCALE_CONFIG.max, currentModelScale));
        console.log(`[Live2D State] Loaded saved scale: ${currentModelScale.toFixed(2)}`);
    }
    
    // Load saved position
    const savedPosition = localStorage.getItem('live2d_model_position');
    if (savedPosition) {
        try {
            currentModelPosition = JSON.parse(savedPosition);
            console.log(`[Live2D State] Loaded saved position: (${currentModelPosition.x}, ${currentModelPosition.y})`);
        } catch (e) {
            console.warn('[Live2D State] Failed to parse saved position:', e);
            currentModelPosition = { x: 0, y: 0 };
        }
    }
}

// Apply saved state to model (called when model is loaded)
function applySavedStateToModel(pixiModel) {
    if (!pixiModel) return;
    
    currentPixiModel = pixiModel;
    
    // Apply saved scale
    if (currentModelScale !== SCALE_CONFIG.default) {
        pixiModel.scale.set(currentModelScale);
        console.log(`[Live2D State] Applied saved scale ${currentModelScale.toFixed(2)} to model`);
    }
    
    // Apply saved position or center if no saved position
    if (currentModelPosition.x !== 0 || currentModelPosition.y !== 0) {
        pixiModel.position.set(currentModelPosition.x, currentModelPosition.y);
        console.log(`[Live2D State] Applied saved position (${currentModelPosition.x}, ${currentModelPosition.y}) to model`);
    } else {
        centerModel();
    }
}

// Initialize model state system
document.addEventListener('DOMContentLoaded', loadSavedModelState);

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        live2d_settings, 
        loadAvailableModels, 
        getLastUsedModel, 
        saveLastUsedModel, 
        getModelInfo 
    };
}

// Make available globally
window.live2d_settings = live2d_settings;
window.loadAvailableModels = loadAvailableModels;
window.getLastUsedModel = getLastUsedModel;
window.saveLastUsedModel = saveLastUsedModel;
window.getModelInfo = getModelInfo;

// Make Live2D Viewer Web zoom functions available globally
window.scaleModel = scaleModel;
window.positionModel = positionModel;
window.fitModelToCanvas = fitModelToCanvas;
window.centerModel = centerModel;
window.resetModel = resetModel;
window.loadSavedModelState = loadSavedModelState;
window.applySavedStateToModel = applySavedStateToModel;
window.currentModelScale = currentModelScale;
window.currentModelPosition = currentModelPosition;
window.SCALE_CONFIG = SCALE_CONFIG;
