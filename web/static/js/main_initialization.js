/**
 * Main Initialization System
 * Consolidated initialization for all AI Companion systems
 */

// Global initialization state
window.ai2dInitialization = {
    initialized: false,
    initSteps: {
        libraries: false,
        live2d: false,
        ui: false,
        socketio: false,
        audio: false
    },
    errors: []
};

// Main initialization function
async function initializeAICompanion() {
    console.log('🚀 Starting AI Companion initialization...');
    
    try {
        // Step 1: Verify libraries are loaded
        await initializeLibraries();
        
        // Step 2: Initialize Live2D system
        await initializeLive2DSystem();
        
        // Step 3: Initialize UI components
        await initializeUIComponents();
        
        // Step 4: Initialize audio systems
        await initializeAudioSystems();
        
        // Step 5: Initialize SocketIO
        await initializeSocketIOSystem();
        
        // Mark as fully initialized
        window.ai2dInitialization.initialized = true;
        console.log('✅ AI Companion initialization complete!');
        
        return true;
    } catch (error) {
        console.error('❌ AI Companion initialization failed:', error);
        window.ai2dInitialization.errors.push(error);
        return false;
    }
}

// Step 1: Library verification
async function initializeLibraries() {
    console.log('📚 Verifying libraries...');
    
    // Check PIXI.js
    if (typeof PIXI === 'undefined') {
        throw new Error('PIXI.js not loaded');
    }
    console.log('✓ PIXI version:', PIXI.VERSION);
    
    // Check EventEmitter
    if (typeof EventEmitter === 'undefined') {
        throw new Error('EventEmitter not available');
    }
    console.log('✓ EventEmitter available');
    
    // Check Live2D SDK
    if (typeof Live2DCubismCore === 'undefined') {
        throw new Error('Live2D Cubism Core SDK not loaded');
    }
    console.log('✓ Live2D SDK available');
    
    // Make SDK available globally for debug console
    window.LIVE2DCUBISMCORE = Live2DCubismCore;
    
    // Check pixi-live2d-display
    if (typeof PIXI.live2d === 'undefined') {
        console.warn('⚠️ PIXI.live2d not loaded - some features may not work');
    } else {
        console.log('✓ PIXI.live2d loaded successfully');
        
        if (PIXI.live2d.Live2DModel) {
            console.log('✓ Live2DModel class available');
            window.Live2DModel = PIXI.live2d.Live2DModel;
        }
        
        if (PIXI.live2d.Live2DFactory) {
            console.log('✓ Live2DFactory available');
            window.Live2DFactory = PIXI.live2d.Live2DFactory;
        }
    }
    
    window.ai2dInitialization.initSteps.libraries = true;
    console.log('✅ Libraries verified');
}

// Step 2: Live2D system initialization
async function initializeLive2DSystem() {
    console.log('🎭 Initializing Live2D system...');
    
    // Load server configuration first
    if (typeof loadServerConfig === 'function') {
        await loadServerConfig();
        console.log('✓ Server configuration loaded');
    }
    
    // Initialize Live2D with timeout fallback
    if (typeof initializeLive2D === 'function') {
        await Promise.race([
            initializeLive2D(),
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Live2D initialization timeout')), 10000)
            )
        ]);
        console.log('✓ Live2D system initialized');
        
        // Set up initial model reference if available
        setTimeout(() => {
            if (typeof updateCurrentModelReference === 'function') {
                updateCurrentModelReference();
            }
        }, 1000);
    } else {
        console.warn('⚠️ initializeLive2D function not found');
    }
    
    window.ai2dInitialization.initSteps.live2d = true;
    console.log('✅ Live2D system ready');
}

// Step 3: UI components initialization
async function initializeUIComponents() {
    console.log('🎨 Initializing UI components...');
    
    // Load and apply saved window layout
    if (typeof loadWindowLayout === 'function') {
        loadWindowLayout();
        console.log('✓ Window layout loaded');
    }
    
    // Initialize draggable functionality
    if (typeof initializeDraggable === 'function') {
        initializeDraggable();
        console.log('✓ Draggable functionality initialized');
    }
    
    // Initialize navigation states
    if (typeof updateNavIconStates === 'function') {
        updateNavIconStates();
        console.log('✓ Navigation states initialized');
    }
    
    // Set up emergency keyboard shortcuts
    setupEmergencyKeyboardShortcuts();
    
    window.ai2dInitialization.initSteps.ui = true;
    console.log('✅ UI components ready');
}

// Step 4: Audio systems initialization
async function initializeAudioSystems() {
    console.log('🎵 Initializing audio systems...');
    
    // Initialize voice recording system
    if (typeof VoiceRecording !== 'undefined') {
        window.voiceRecording = new VoiceRecording();
        const initialized = await window.voiceRecording.initialize();
        if (initialized) {
            console.log('✓ Voice recording system initialized');
        } else {
            console.warn('⚠️ Voice recording system failed to initialize');
        }
    }
    
    window.ai2dInitialization.initSteps.audio = true;
    console.log('✅ Audio systems ready');
}

// Step 5: SocketIO initialization
async function initializeSocketIOSystem() {
    console.log('🔌 Initializing SocketIO...');
    
    return new Promise((resolve) => {
        setTimeout(() => {
            if (typeof io !== 'undefined') {
                try {
                    const socket = io();
                    
                    socket.on('connect', function() {
                        console.log('🔌 Connected to server via SocketIO');
                        if (typeof addSystemMessage === 'function') {
                            addSystemMessage('Connected to AI live2d chat server', 'success');
                        }
                    });
                    
                    socket.on('disconnect', function() {
                        console.log('🔌 Disconnected from server');
                        if (typeof addSystemMessage === 'function') {
                            addSystemMessage('Disconnected from server', 'warning');
                        }
                    });
                    
                    socket.on('ai_response', function(data) {
                        console.log('📨 Received AI response via SocketIO:', data);
                        if (typeof addChatMessage === 'function') {
                            addChatMessage('ai', data.message);
                        }
                        
                        if (data.tts_data && typeof playEmotionalTTSAudio === 'function') {
                            playEmotionalTTSAudio(data.tts_data);
                        }
                        
                        if (data.emotion && typeof triggerEmotionalResponse === 'function') {
                            triggerEmotionalResponse(data.emotion, data.intensity);
                        }
                    });
                    
                    socket.on('motion_trigger', function(data) {
                        console.log('🎭 Received motion trigger:', data);
                        if (data.motion_type && typeof window.triggerMotion === 'function') {
                            window.triggerMotion(data.motion_type);
                        }
                    });
                    
                    console.log('✓ SocketIO initialized');
                    window.socket = socket;
                } catch (error) {
                    console.warn('⚠️ SocketIO initialization failed:', error);
                }
            } else {
                console.warn('⚠️ SocketIO not available');
            }
            
            window.ai2dInitialization.initSteps.socketio = true;
            console.log('✅ SocketIO system ready');
            resolve();
        }, 2000);
    });
}

// Emergency keyboard shortcuts setup
function setupEmergencyKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+Shift+R to reset window layout
        if (e.ctrlKey && e.shiftKey && e.key === 'R') {
            e.preventDefault();
            console.log('Emergency layout reset triggered');
            if (typeof resetWindowLayout === 'function') {
                resetWindowLayout();
            }
        }
        
        // Ctrl+Shift+B to rescue off-screen windows
        if (e.ctrlKey && e.shiftKey && e.key === 'B') {
            e.preventDefault();
            console.log('Emergency rescue mode triggered');
            if (typeof rescueOffScreenWindows === 'function') {
                rescueOffScreenWindows();
            }
        }
        
        // Escape key to close model selection dialog
        if (e.key === 'Escape') {
            const dialog = document.getElementById('modelSelectionDialog');
            if (dialog && dialog.style.display === 'flex') {
                if (typeof closeAddModelDialog === 'function') {
                    closeAddModelDialog();
                }
            }
        }
    });
    
    console.log('✓ Emergency keyboard shortcuts set up');
}

// Layout management for resize and unload events
function setupLayoutManagement() {
    // Save layout on window resize and before page unload
    window.addEventListener('resize', function() {
        // Debounce resize events to avoid excessive saves
        clearTimeout(window.resizeTimeout);
        window.resizeTimeout = setTimeout(() => {
            if (typeof saveWindowLayout === 'function') {
                saveWindowLayout();
            }
        }, 500);
    });

    window.addEventListener('beforeunload', function() {
        if (typeof saveWindowLayout === 'function') {
            saveWindowLayout();
        }
    });
    
    console.log('✓ Layout management set up');
}

// Enhanced error handling and reporting
function reportInitializationStatus() {
    const steps = window.ai2dInitialization.initSteps;
    const errors = window.ai2dInitialization.errors;
    
    console.log('📊 Initialization Status Report:');
    console.log('- Libraries:', steps.libraries ? '✅' : '❌');
    console.log('- Live2D:', steps.live2d ? '✅' : '❌');
    console.log('- UI Components:', steps.ui ? '✅' : '❌');
    console.log('- Audio Systems:', steps.audio ? '✅' : '❌');
    console.log('- SocketIO:', steps.socketio ? '✅' : '❌');
    console.log('- Overall:', window.ai2dInitialization.initialized ? '✅' : '❌');
    
    if (errors.length > 0) {
        console.log('❌ Errors encountered:');
        errors.forEach((error, index) => {
            console.log(`  ${index + 1}. ${error.message}`);
        });
    }
    
    // Global verification
    console.log('🔍 Global objects available:');
    console.log('- window.live2dIntegration:', typeof window.live2dIntegration);
    console.log('- window.live2dMultiModelManager:', typeof window.live2dMultiModelManager);
    console.log('- window.LIVE2DCUBISMCORE:', typeof window.LIVE2DCUBISMCORE);
}

// Export functions for global access
window.initializeAICompanion = initializeAICompanion;
window.reportInitializationStatus = reportInitializationStatus;
window.setupLayoutManagement = setupLayoutManagement;
