// debug.js
// Debug UI and logging system for Live2D frontend

// Helper function to get API base URL with dynamic config loading
async function getApiBaseUrl() {
    // Ensure server configuration is loaded
    if (typeof loadServerConfig === 'function' && !window.ai2d_chat_CONFIG._configLoaded) {
        try {
            await loadServerConfig();
        } catch (error) {
            console.warn('Failed to load server config in debug functions:', error);
        }
    }
    
    return window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
}

function updateModelInfo() {
    const modelNameElement = document.getElementById('debug-current-model');
    const modelMotionsElement = document.getElementById('debug-motion-count');
    
    // Use new Live2D multi-model manager system
    if (window.live2dMultiModelManager && window.live2dMultiModelManager.activeModelId) {
        const activeModel = window.live2dMultiModelManager.models.get(window.live2dMultiModelManager.activeModelId);
        if (activeModel) {
            if (modelNameElement) modelNameElement.textContent = activeModel.name;
            // Count motions - this would need to be implemented in the motion manager
            if (modelMotionsElement) modelMotionsElement.textContent = '0'; // Placeholder
        }
    } else {
        if (modelNameElement) modelNameElement.textContent = 'None';
        if (modelMotionsElement) modelMotionsElement.textContent = '0';
    }
}

function debugLog(message, type = 'info') {
    if (!window.debugLogBuffer) window.debugLogBuffer = [];
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = { timestamp, message, type, full: `[${timestamp}] ${message}` };
    window.debugLogBuffer.push(logEntry);
    if (window.debugLogBuffer.length > 50) window.debugLogBuffer.shift();
    updateDebugLogDisplay();
    if (window.debugVerboseMode) console.log(`[DEBUG UI] ${message}`);
}

function updateDebugLogDisplay() {
    if (!window.debugRealtimeLog) return;
    if (!window.debugLogBuffer) window.debugLogBuffer = [];
    const logHtml = window.debugLogBuffer.slice(-10).map(entry => {
        const typeClass = entry.type === 'error' ? 'debug-status-error' : entry.type === 'warn' ? 'debug-status-warn' : 'debug-status-ok';
        return `<div class="${typeClass}">${entry.full}</div>`;
    }).join('');
    window.debugRealtimeLog.innerHTML = logHtml;
    
    // Force scroll to bottom
    window.debugRealtimeLog.scrollTop = window.debugRealtimeLog.scrollHeight;
    
    // Ensure the log is visible and scrollable
    if (window.debugRealtimeLog.style.maxHeight !== '200px') {
        window.debugRealtimeLog.style.maxHeight = '200px';
        window.debugRealtimeLog.style.overflowY = 'auto';
    }
}

function updateDebugStatus() {
    // Check Live2D SDK availability
    if (window.LIVE2DCUBISMCORE) {
        setDebugStatus(window.debugSDKStatus, 'Live2D SDK Loaded', 'ok');
    } else {
        setDebugStatus(window.debugSDKStatus, 'SDK Missing', 'error');
    }
    
    // Check for pixiContainer and Live2D integration
    const canvas = document.getElementById('pixiContainer');
    if (canvas) {
        // Check if Live2D integration is initialized
        if (window.live2dIntegration && window.live2dIntegration.initialized) {
            setDebugStatus(window.debugCanvasStatus, 'Live2D System Ready', 'ok');
        } else if (window.live2dIntegration) {
            setDebugStatus(window.debugCanvasStatus, 'Live2D Initializing...', 'warn');
        } else {
            setDebugStatus(window.debugCanvasStatus, 'Live2D Not Started', 'error');
        }
    } else {
        setDebugStatus(window.debugCanvasStatus, 'Canvas Missing', 'error');
    }
    updateModelInfo();
}

function setDebugStatus(element, text, status) {
    if (!element) return;
    element.textContent = text;
    element.className = `debug-status-${status}`;
}

function updateModelInfo() {
    const modelNameElement = document.getElementById('debug-model-name');
    const modelMotionsElement = document.getElementById('debug-model-motions');
    
    if (window.currentModel && window.live2dv4 && window.live2dv4._model) {
        if (modelNameElement) modelNameElement.textContent = window.currentModel;
        if (modelMotionsElement) {
            const motionCount = window.live2dv4._model.internalModel?.motionManager?.expressionManager?._expressions?.length || 0;
            modelMotionsElement.textContent = motionCount;
        }
    } else {
        if (modelNameElement) modelNameElement.textContent = 'None';
        if (modelMotionsElement) modelMotionsElement.textContent = '0';
    }
}

function updateDatabaseInfo() {
    debugDatabaseInfo();
}

function debugRefreshStatus() {
    debugLog('🔄 Refreshing status...');
    updateDebugStatus();
    updateModelInfo();
    updateDatabaseInfo();
}

function debugTestMotion() {
    // Check for new Live2D system
    if (!window.live2dMultiModelManager || !window.live2dMultiModelManager.activeModelId) {
        debugLog('❌ No model loaded for motion test', 'error');
        return;
    }
    
    debugLog('🎭 Testing random motion...');
    try {
        const activeModel = window.live2dMultiModelManager.models.get(window.live2dMultiModelManager.activeModelId);
        if (activeModel && activeModel.pixiModel) {
            // Try to trigger a motion using the PIXI Live2D model
            const model = activeModel.pixiModel;
            if (model.motion) {
                // Try different motion types
                const motionTypes = ['idle', 'tap_body', 'head', 'body', 'expression'];
                const randomMotion = motionTypes[Math.floor(Math.random() * motionTypes.length)];
                model.motion(randomMotion);
                debugLog(`✅ Attempted to play motion: ${randomMotion}`);
            } else {
                debugLog('❌ Motion function not available on model', 'error');
            }
        } else {
            debugLog('❌ No PIXI model found', 'error');
        }
    } catch (error) {
        debugLog(`❌ Motion test failed: ${error.message}`, 'error');
    }
}

function debugLogMotions() {
    if (!window.currentModel || !window.live2dv4 || !window.live2dv4._model) {
        debugLog('❌ No model loaded to log motions', 'error');
        return;
    }
    
    debugLog('📋 Logging available motions...');
    try {
        const model = window.live2dv4._model;
        if (model.internalModel && model.internalModel.motionManager) {
            const motionGroups = Object.keys(model.internalModel.motionManager.definitions || {});
            debugLog(`📋 Motion groups found: ${motionGroups.length}`);
            motionGroups.forEach(group => {
                const motions = model.internalModel.motionManager.definitions[group];
                debugLog(`  📁 ${group}: ${motions ? motions.length : 0} motions`);
            });
        } else {
            debugLog('❌ Motion manager not available', 'error');
        }
    } catch (error) {
        debugLog(`❌ Failed to log motions: ${error.message}`, 'error');
    }
}

function debugClearLog() {
    window.debugLogBuffer = [];
    updateDebugLogDisplay();
    debugLog('🧹 Debug log cleared');
}

function debugToggleVerbose() {
    window.debugVerboseMode = !window.debugVerboseMode;
    debugLog(`🔊 Verbose mode: ${window.debugVerboseMode ? 'ON' : 'OFF'}`);
}

// Move DOMContentLoaded debug UI initialization block from index.html to debug.js

// Initialize debug UI elements
function initDebugUI() {
    console.log('[Debug] Initializing debug UI...');
    
    // Get debug UI elements
    window.debugSDKStatus = document.getElementById('debug-sdk-status');
    window.debugCanvasStatus = document.getElementById('debug-canvas-status');
    window.debugRealtimeLog = document.getElementById('debug-realtime-log');
    
    // Initialize debug log buffer
    if (!window.debugLogBuffer) window.debugLogBuffer = [];
    
    // Initial status update
    updateDebugStatus();
    
    // Load database info immediately
    if (typeof window.debugDatabaseInfo === 'function') {
        debugDatabaseInfo();
    }
    
    debugLog('🎯 Debug UI initialized successfully');
    console.log('[Debug] Debug UI initialization completed');
}

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(initDebugUI, 1000);
    // Add a function to test if debug UI is working
    window.testDebugUI = function() {
        debugLog('🧪 Debug UI test function called!');
        console.log('🧪 Debug UI test function called!');
        alert('Debug UI is working! Check the debug log panel.');
        return true;
    };
    window.loadDefaultModel = function() {
        const defaultModel = 'kanade';
        debugLog('📦 Loading default model: ' + defaultModel);
        if (typeof loadModel === 'function') {
            loadModel(defaultModel);
        } else {
            debugLog('❌ loadModel function not available', 'error');
        }
        setTimeout(() => {
            updateDebugStatus();
            debugLog('✅ Model load attempt completed');
        }, 1500);
    };
    // Patch debug button handlers to check for model presence in new system
    ['debugTestMotion', 'debugLogMotions', 'testBasicLive2D', 'debugLive2D', 'testAllMotions'].forEach(fn => {
        const orig = window[fn];
        if (typeof orig === 'function') {
            window[fn] = function() {
                // Check for new Live2D system
                if (!window.live2dMultiModelManager || !window.live2dMultiModelManager.activeModelId) {
                    debugLog('❌ No model loaded. Please load a model first.', 'error');
                    const loadBtn = document.getElementById('debug-load-default-model');
                    if (loadBtn) loadBtn.style.display = 'inline-block';
                    return false;
                } else {
                    const loadBtn = document.getElementById('debug-load-default-model');
                    if (loadBtn) loadBtn.style.display = 'none';
                    return orig.apply(this, arguments);
                }
            }
        }
    });
    function updateDebugStatusPatched() {
        if (typeof updateDebugStatus === 'function') {
            updateDebugStatus();
        }
        const loadBtn = document.getElementById('debug-load-default-model');
        if (loadBtn) {
            // Check for new Live2D system
            if (!window.live2dMultiModelManager || !window.live2dMultiModelManager.activeModelId) {
                loadBtn.style.display = 'inline-block';
            } else {
                loadBtn.style.display = 'none';
            }
        }
    }
    setInterval(updateDebugStatusPatched, 2000);
    window.addEventListener('error', function(e) {
        debugLog(`❌ JavaScript Error: ${e.message}`, 'error');
        console.error('JavaScript Error caught:', e);
    });
    window.handleDebugButtonClick = function(action) {
        try {
            debugLog(`🔘 Button clicked: ${action}`);
            switch(action) {
                case 'refresh': debugRefreshStatus(); break;
                case 'test-motion': debugTestMotion(); break;
                case 'log-motions': debugLogMotions(); break;
                case 'clear-log': debugClearLog(); break;
                case 'toggle-verbose': debugToggleVerbose(); break;
                default: debugLog(`❓ Unknown action: ${action}`, 'warn');
            }
        } catch (error) {
            debugLog(`❌ Error handling button click: ${error.message}`, 'error');
            console.error('Button click error:', error);
        }
    };
    window.toggleDebugConsole = function() {
        const debugPanel = document.getElementById('debugUIPanel');
        if (!debugPanel) return;
        const isVisible = debugPanel.style.display !== 'none';
        debugPanel.style.display = isVisible ? 'none' : 'block';
        if (!isVisible) {
            debugLog('🔍 Debug console opened');
            debugRefreshAll();
        } else {
            debugLog('🔍 Debug console closed');
        }
    };
    window.debugRefreshAll = function() {
        debugLog('🔄 Refreshing all system status...');
        updateDebugStatus();
        updateDatabaseInfo();
        const modelsListElement = document.getElementById('debug-models-list');
        if (modelsListElement) {
            const availableModels = window.availableModels || [];
            modelsListElement.textContent = availableModels.map(m => m.model_name || m.name).join(', ');
        }
        debugLog('✅ Status refresh completed');
    };
    window.debugTestSystem = async function() {
        debugLog('🧪 === Starting System Test ===');
        debugLog(window.live2dv4 ? '✅ Live2D SDK: Available' : '❌ Live2D SDK: Missing');
        debugLog(window.currentModel ? `✅ Model: ${window.currentModel}` : '❌ Model: None');
        
        // Check for pixiContainer instead of live2d4
        const canvas = document.getElementById('pixiContainer');
        debugLog(canvas ? '✅ Canvas: Found (pixiContainer)' : '❌ Canvas: Missing (pixiContainer)');
        
        // Check Live2D integration status
        if (window.live2dIntegration) {
            debugLog('✅ Live2D Integration: Available');
            if (window.live2dIntegration.initialized) {
                debugLog('✅ Live2D Integration: Initialized');
            } else {
                debugLog('⚠️ Live2D Integration: Not initialized');
            }
        } else {
            debugLog('❌ Live2D Integration: Not available');
        }
        
        // Test multi-model manager positioning
        if (window.live2dMultiModelManager) {
            debugLog('✅ Multi-model manager: Available');
            const models = window.live2dMultiModelManager.getAllModels();
            debugLog(`📦 Loaded models: ${models.length}`);
            if (window.live2dMultiModelManager.activeModelId) {
                const activeModel = window.live2dMultiModelManager.models.get(window.live2dMultiModelManager.activeModelId);
                if (activeModel && activeModel.pixiModel) {
                    const pos = activeModel.pixiModel.position;
                    debugLog(`📍 Active model position: (${pos.x.toFixed(1)}, ${pos.y.toFixed(1)})`);
                    const state = window.live2dMultiModelManager.modelStates.get(window.live2dMultiModelManager.activeModelId);
                    if (state) {
                        debugLog(`💾 Saved state position: (${state.position.x.toFixed(1)}, ${state.position.y.toFixed(1)})`);
                    }
                }
            }
        } else {
            debugLog('❌ Multi-model manager: Not available');
        }
        
        await testDatabaseConnection();
        debugLog('🎉 === System Test Complete ===');
    };
    window.debugDatabaseInfo = async function() {
        debugLog('💾 Loading database information...');
        try {
            const apiBaseUrl = await getApiBaseUrl();
            const response = await fetch(`${apiBaseUrl}/api/live2d/models`);
            if (response.ok) {
                const models = await response.json();
                debugLog(`📦 Database models: ${models.length}`);
                
                // Safely update UI elements if they exist
                const modelCountEl = document.getElementById('debug-db-model-count');
                if (modelCountEl) {
                    modelCountEl.textContent = models.length;
                }
                
                const connectionEl = document.getElementById('debug-db-connection');
                if (connectionEl) {
                    connectionEl.textContent = 'Connected';
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            debugLog(`❌ Database error: ${error.message}`, 'error');
            
            // Safely update UI element if it exists
            const connectionEl = document.getElementById('debug-db-connection');
            if (connectionEl) {
                connectionEl.textContent = 'Error';
            }
        }
    };
    window.debugClearDatabase = async function() {
        if (!confirm('⚠️ WARNING: Delete ALL database content?')) return;
        debugLog('🗑 Clearing database...');
        try {
            const apiBaseUrl = await getApiBaseUrl();
            const response = await fetch(`${apiBaseUrl}/api/live2d/clear_database`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            if (response.ok) {
                debugLog('✅ Database cleared');
                document.getElementById('debug-db-model-count').textContent = '0';
                document.getElementById('debug-db-motion-count').textContent = '0';
            }
        } catch (error) {
            debugLog(`❌ Clear error: ${error.message}`, 'error');
        }
    };
    window.debugReimportData = async function() {
        if (!confirm('📥 Re-import all models and motions?')) return;
        debugLog('📥 Starting re-import...');
        try {
            const apiBaseUrl = await getApiBaseUrl();
            const response = await fetch(`${apiBaseUrl}/api/live2d/reimport_all`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            if (response.ok) {
                const result = await response.json();
                debugLog(`✅ Imported: ${result.models_imported || 0} models, ${result.motions_imported || 0} motions`);
                await debugDatabaseInfo();
            }
        } catch (error) {
            debugLog(`❌ Import error: ${error.message}`, 'error');
        }
    };
    
    // Test model positioning fixes
    window.debugTestPositioning = function() {
        debugLog('📍 === Testing Model Positioning ===');
        
        if (!window.live2dMultiModelManager) {
            debugLog('❌ Multi-model manager not available');
            return;
        }
        
        const models = window.live2dMultiModelManager.getAllModels();
        debugLog(`📦 Testing with ${models.length} loaded models`);
        
        if (models.length === 0) {
            debugLog('⚠️ No models loaded for positioning test');
            return;
        }
        
        models.forEach((modelData, index) => {
            const isActive = window.live2dMultiModelManager.activeModelId === modelData.id;
            const state = window.live2dMultiModelManager.modelStates.get(modelData.id);
            
            debugLog(`🎭 Model ${index + 1}: ${modelData.name} ${isActive ? '(Active)' : ''}`);
            
            if (modelData.pixiModel) {
                const currentPos = modelData.pixiModel.position;
                debugLog(`  📍 Current position: (${currentPos.x.toFixed(1)}, ${currentPos.y.toFixed(1)})`);
                
                if (state) {
                    debugLog(`  💾 Saved state: (${state.position.x.toFixed(1)}, ${state.position.y.toFixed(1)}), scale: ${state.scale}`);
                } else {
                    debugLog(`  ❌ No state saved for this model`);
                }
            } else {
                debugLog(`  ❌ No PIXI model found`);
            }
        });
        
        // Test center function
        if (window.live2dMultiModelManager.activeModelId) {
            debugLog('🎯 Testing center function...');
            const beforePos = window.live2dMultiModelManager.models.get(window.live2dMultiModelManager.activeModelId).pixiModel.position;
            debugLog(`  📍 Before center: (${beforePos.x.toFixed(1)}, ${beforePos.y.toFixed(1)})`);
            
            // Call center function
            if (window.live2dIntegration && window.live2dIntegration.core && window.live2dIntegration.core.interactionManager) {
                window.live2dIntegration.core.interactionManager.centerModel();
                const afterPos = window.live2dMultiModelManager.models.get(window.live2dMultiModelManager.activeModelId).pixiModel.position;
                debugLog(`  📍 After center: (${afterPos.x.toFixed(1)}, ${afterPos.y.toFixed(1)})`);
                
                // Check if state was saved
                const newState = window.live2dMultiModelManager.modelStates.get(window.live2dMultiModelManager.activeModelId);
                if (newState) {
                    debugLog(`  💾 State updated: (${newState.position.x.toFixed(1)}, ${newState.position.y.toFixed(1)})`);
                }
            }
        }
        
        debugLog('✅ === Positioning Test Complete ===');
    };
    
    // Test interaction system (drag and zoom)
    window.debugTestInteraction = function() {
        debugLog('🖱️ === Testing Interaction System ===');
        
        if (!window.live2dIntegration || !window.live2dIntegration.core) {
            debugLog('❌ Live2D integration not available');
            return;
        }
        
        const interactionManager = window.live2dIntegration.core.interactionManager;
        if (!interactionManager) {
            debugLog('❌ Interaction manager not available');
            return;
        }
        
        debugLog('✅ Interaction manager found');
        debugLog(`🎯 Current zoom: ${interactionManager.currentZoom}`);
        debugLog(`🖱️ Is dragging: ${interactionManager.isDragging}`);
        
        // Check if model is interactive
        if (interactionManager.model) {
            debugLog(`🎭 Model interactive: ${interactionManager.model.interactive}`);
            debugLog(`🎭 Model event mode: ${interactionManager.model.eventMode}`);
            debugLog(`🎭 Model position: (${interactionManager.model.x.toFixed(1)}, ${interactionManager.model.y.toFixed(1)})`);
            
            // Check event listeners
            const pointerListeners = interactionManager.model.listeners('pointerdown');
            debugLog(`🎯 Pointer down listeners: ${pointerListeners.length}`);
            
            if (interactionManager.app && interactionManager.app.stage) {
                const moveListeners = interactionManager.app.stage.listeners('pointermove');
                debugLog(`🎯 Pointer move listeners: ${moveListeners.length}`);
            }
            
            // Check canvas wheel event
            const canvas = interactionManager.app?.canvas || interactionManager.app?.view;
            if (canvas) {
                debugLog(`🎯 Canvas element: ${canvas.tagName}`);
                debugLog(`🎯 Canvas size: ${canvas.width}x${canvas.height}`);
            } else {
                debugLog('❌ Canvas element not found');
            }
            
        } else {
            debugLog('❌ No model loaded in interaction manager');
        }
        
        // Test zoom functionality
        debugLog('🧪 Testing zoom functionality...');
        const originalZoom = interactionManager.currentZoom;
        interactionManager.setZoom(originalZoom + 0.1);
        setTimeout(() => {
            debugLog(`🎯 Zoom test: ${originalZoom} → ${interactionManager.currentZoom}`);
            interactionManager.setZoom(originalZoom); // Reset
        }, 100);
        
        debugLog('✅ === Interaction Test Complete ===');
        debugLog('💡 Try clicking and dragging the model, or using mouse wheel to zoom');
    };
    
    window.debugLoadDefaultModel = function() {
        debugLog('📦 Loading default model: kanade');
        
        // Check if multi-model manager is available
        if (window.live2dMultiModelManager) {
            debugLog('🎭 Using multi-model manager to load model...');
            window.live2dMultiModelManager.addModel('kanade').then(() => {
                debugLog('✅ Default model loaded successfully');
                updateDebugStatus();
            }).catch(error => {
                debugLog(`❌ Failed to load default model: ${error.message}`, 'error');
                // Try to refresh available models first
                window.live2dMultiModelManager.loadAvailableModels().then(() => {
                    debugLog('🔄 Retrying model load after refreshing model list...');
                    return window.live2dMultiModelManager.addModel('kanade');
                }).then(() => {
                    debugLog('✅ Default model loaded on retry');
                    updateDebugStatus();
                }).catch(retryError => {
                    debugLog(`❌ Failed to load model even after retry: ${retryError.message}`, 'error');
                });
            });
        } else if (typeof window.loadModel === 'function') {
            debugLog('🎭 Using legacy loadModel function...');
            window.loadModel('kanade');
        } else {
            debugLog('❌ No model loading mechanism available', 'error');
            debugLog('💡 Make sure Live2D system is properly initialized', 'warn');
        }
    };
    window.debugForceModelInit = function() {
        debugLog('🚀 Forcing model initialization...');
        if (typeof window.initModel === 'function') {
            window.initModel();
        } else {
            debugLog('❌ initModel function not available', 'error');
        }
    };
    window.debugExportLog = function() {
        console.log('📤 === EXPORTED DEBUG LOG ===');
        window.debugLogBuffer.forEach(entry => console.log(entry.full));
        console.log('📤 === END DEBUG LOG ===');
        debugLog(`📤 Exported ${window.debugLogBuffer.length} entries`);
    };
    async function testDatabaseConnection() {
        try {
            const apiBaseUrl = await getApiBaseUrl();
            const response = await fetch(`${apiBaseUrl}/api/live2d/models`);
            if (response.ok) {
                debugLog('✅ Database: Connected');
                return true;
            } else {
                debugLog('❌ Database: Failed', 'error');
                return false;
            }
        } catch (error) {
            debugLog(`❌ Database: ${error.message}`, 'error');
            return false;
        }
    }
    setTimeout(() => {
        const debugButton = document.querySelector('.waifu-tool .icon-about');
        if (debugButton) {
            debugButton.addEventListener('click', (e) => {
                e.preventDefault();
                toggleDebugConsole();
            });
            debugLog('🔗 Debug console connected to waifu button');
        }
    }, 2000);
});

// Export to window for global access
window.debugLog = debugLog;
window.updateDebugLogDisplay = updateDebugLogDisplay;
window.updateDebugStatus = updateDebugStatus;
window.setDebugStatus = setDebugStatus;
window.updateModelInfo = updateModelInfo;
window.updateDatabaseInfo = updateDatabaseInfo;
window.debugRefreshStatus = debugRefreshStatus;
window.debugTestMotion = debugTestMotion;
window.debugLogMotions = debugLogMotions;
window.debugClearLog = debugClearLog;
window.debugToggleVerbose = debugToggleVerbose;

// Add missing debug functions that were referenced but not defined
window.debugModelStructure = function() {
    debugLog('🔍 Checking model structure...');
    if (!window.currentModel || !window.live2dv4 || !window.live2dv4._model) {
        debugLog('❌ No model loaded for structure analysis', 'error');
        return;
    }
    
    try {
        const model = window.live2dv4._model;
        debugLog('📋 Model Structure Analysis:');
        debugLog(`  Model instance: ${model ? 'Available' : 'Missing'}`);
        
        if (model.internalModel) {
            debugLog(`  Internal model: Available`);
            debugLog(`  Motion manager: ${model.internalModel.motionManager ? 'Available' : 'Missing'}`);
            
            if (model.internalModel.motionManager) {
                const definitions = model.internalModel.motionManager.definitions || {};
                const groups = Object.keys(definitions);
                debugLog(`  Motion groups: ${groups.length} (${groups.join(', ')})`);
            }
        } else {
            debugLog(`  Internal model: Missing`);
        }
    } catch (error) {
        debugLog(`❌ Structure analysis failed: ${error.message}`, 'error');
    }
};

window.debugLive2D = function() {
    debugLog('🔍 Live2D System Debug...');
    
    // Check SDK availability
    debugLog(`Live2D SDK v4: ${typeof window.live2dv4 !== 'undefined' ? 'Available' : 'Missing'}`);
    debugLog(`Live2D SDK v2: ${typeof window.live2dv2 !== 'undefined' ? 'Available' : 'Missing'}`);
    
    // Check model status
    debugLog(`Current model: ${window.currentModel || 'None'}`);
    debugLog(`Available models: ${window.availableModels ? window.availableModels.length : 0}`);
    
    // Check canvas
    const canvas4 = document.getElementById('live2d4');
    const canvas2 = document.getElementById('live2d2');
    debugLog(`Canvas v4: ${canvas4 ? 'Present' : 'Missing'}`);
    debugLog(`Canvas v2: ${canvas2 ? 'Present' : 'Missing'}`);
    
    // Check WebGL
    if (canvas4) {
        try {
            const gl = canvas4.getContext('webgl') || canvas4.getContext('experimental-webgl');
            debugLog(`WebGL Context: ${gl ? 'Available' : 'Failed'}`);
        } catch (e) {
            debugLog(`WebGL Context: Error - ${e.message}`);
        }
    }
    
    // Test model structure if available
    debugModelStructure();
};

// Ensure all debug functions are available globally
window.debugModelStructure = function() {
    debugLog('🔍 Checking model structure...');
    if (!window.live2dMultiModelManager || !window.live2dMultiModelManager.activeModelId) {
        debugLog('❌ No model loaded for structure analysis', 'error');
        return;
    }
    
    try {
        const activeModel = window.live2dMultiModelManager.models.get(window.live2dMultiModelManager.activeModelId);
        if (activeModel && activeModel.pixiModel) {
            debugLog('📋 Model Structure Analysis:');
            debugLog(`  Model name: ${activeModel.name}`);
            debugLog(`  PIXI model: Available`);
            debugLog(`  Model visible: ${activeModel.pixiModel.visible}`);
            debugLog(`  Model position: (${activeModel.pixiModel.x.toFixed(1)}, ${activeModel.pixiModel.y.toFixed(1)})`);
            debugLog(`  Model scale: ${activeModel.pixiModel.scale.x.toFixed(2)}`);
            debugLog(`  Model interactive: ${activeModel.pixiModel.interactive}`);
            
            // Check for motion capabilities
            if (activeModel.pixiModel.motion) {
                debugLog(`  Motion function: Available`);
            } else {
                debugLog(`  Motion function: Missing`);
            }
        } else {
            debugLog('❌ No PIXI model found', 'error');
        }
    } catch (error) {
        debugLog(`❌ Structure analysis failed: ${error.message}`, 'error');
    }
};

window.debugLive2D = function() {
    debugLog('🔍 Live2D System Debug...');
    debugLog(`Live2D Integration: ${window.live2dIntegration ? 'Available' : 'Missing'}`);
    debugLog(`Multi-Model Manager: ${window.live2dMultiModelManager ? 'Available' : 'Missing'}`);
    debugLog(`PIXI Application: ${window.live2dIntegration?.core?.app ? 'Available' : 'Missing'}`);
    debugLog(`Canvas Element: ${document.getElementById('pixiContainer') ? 'Available' : 'Missing'}`);
    
    if (window.live2dIntegration) {
        debugLog(`Integration Initialized: ${window.live2dIntegration.initialized}`);
        if (window.live2dIntegration.core) {
            debugLog(`Canvas Size: ${window.live2dIntegration.core.canvasWidth}x${window.live2dIntegration.core.canvasHeight}`);
        }
    }
    
    debugLog('✅ Live2D debug complete');
};
