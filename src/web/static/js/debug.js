// debug.js
// Debug UI and logging system for Live2D frontend

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
    window.debugRealtimeLog.scrollTop = window.debugRealtimeLog.scrollHeight;
}

function updateDebugStatus() {
    if (window.live2dv4) setDebugStatus(window.debugSDKStatus, 'Live2D SDK Loaded', 'ok');
    else setDebugStatus(window.debugSDKStatus, 'SDK Missing', 'error');
    const canvas = document.getElementById('live2d4');
    if (canvas && canvas.getContext) {
        try {
            const ctx = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (ctx) setDebugStatus(window.debugCanvasStatus, 'WebGL Ready', 'ok');
            else setDebugStatus(window.debugCanvasStatus, 'WebGL Failed', 'error');
        } catch (e) { setDebugStatus(window.debugCanvasStatus, 'Canvas Error', 'error'); }
    } else setDebugStatus(window.debugCanvasStatus, 'Canvas Missing', 'error');
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
    if (!window.currentModel || !window.live2dv4 || !window.live2dv4._model) {
        debugLog('❌ No model loaded for motion test', 'error');
        return;
    }
    
    debugLog('🎭 Testing random motion...');
    try {
        const model = window.live2dv4._model;
        if (model.internalModel && model.internalModel.motionManager) {
            const motionGroups = Object.keys(model.internalModel.motionManager.definitions || {});
            if (motionGroups.length > 0) {
                const randomGroup = motionGroups[Math.floor(Math.random() * motionGroups.length)];
                model.motion(randomGroup);
                debugLog(`✅ Played motion from group: ${randomGroup}`);
            } else {
                debugLog('❌ No motion groups found', 'warn');
            }
        } else {
            debugLog('❌ Motion manager not available', 'error');
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
    // Patch debug button handlers to check for model presence
    ['debugTestMotion', 'debugLogMotions', 'testBasicLive2D', 'debugLive2D', 'testAllMotions'].forEach(fn => {
        const orig = window[fn];
        if (typeof orig === 'function') {
            window[fn] = function() {
                if (!window.currentModel || !window.live2dv4 || !window.live2dv4._model) {
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
            if (!window.currentModel || !window.live2dv4 || !window.live2dv4._model) {
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
        const canvas = document.getElementById('live2d4');
        debugLog(canvas ? '✅ Canvas: Found' : '❌ Canvas: Missing');
        await testDatabaseConnection();
        debugLog('🎉 === System Test Complete ===');
    };
    window.debugDatabaseInfo = async function() {
        debugLog('💾 Loading database information...');
        try {
            const apiBaseUrl = window.AI_COMPANION_CONFIG?.API_BASE_URL || 'http://localhost:19443';
            const response = await fetch(`${apiBaseUrl}/api/live2d/models`);
            if (response.ok) {
                const models = await response.json();
                debugLog(`📦 Database models: ${models.length}`);
                document.getElementById('debug-db-model-count').textContent = models.length;
                document.getElementById('debug-db-connection').textContent = 'Connected';
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            debugLog(`❌ Database error: ${error.message}`, 'error');
            document.getElementById('debug-db-connection').textContent = 'Error';
        }
    };
    window.debugClearDatabase = async function() {
        if (!confirm('⚠️ WARNING: Delete ALL database content?')) return;
        debugLog('🗑 Clearing database...');
        try {
            const apiBaseUrl = window.AI_COMPANION_CONFIG?.API_BASE_URL || 'http://localhost:19443';
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
            const apiBaseUrl = window.AI_COMPANION_CONFIG?.API_BASE_URL || 'http://localhost:19443';
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
    window.debugLoadDefaultModel = function() {
        debugLog('📦 Loading default model: kanade');
        if (typeof window.loadModel === 'function') {
            window.loadModel('kanade');
        } else {
            debugLog('❌ loadModel function not available', 'error');
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
            const apiBaseUrl = window.AI_COMPANION_CONFIG?.API_BASE_URL || 'http://localhost:19443';
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
