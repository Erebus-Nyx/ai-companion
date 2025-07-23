/**
 * Compatibility Functions
 * Bridge functions for backward compatibility with existing code
 */

// Enhanced error handling and TTS integration
function triggerEmotionalResponse(emotion, intensity = 0.5) {
    if (!window.live2dIntegration || !window.live2dIntegration.motionManager) {
        console.warn('Live2D integration not available for emotional response');
        return;
    }
    
    // Map emotions to Live2D motions
    const emotionMotionMap = {
        'happy': 'idle',
        'excited': 'head',
        'sad': 'body',
        'surprised': 'expression',
        'curious': 'special',
        'thoughtful': 'talk'
    };
    
    const motionType = emotionMotionMap[emotion] || 'idle';
    
    console.log(`🎭 Triggering emotional response: ${emotion} (${motionType})`);
    
    // Trigger motion via Live2D integration
    if (typeof window.triggerMotion === 'function') {
        window.triggerMotion(motionType);
    }
}

// Enhanced TTS audio playback
function playEmotionalTTSAudio(ttsData) {
    if (!ttsData || !ttsData.audio_data) {
        console.warn('No TTS audio data provided');
        return;
    }
    
    try {
        // Create audio element
        const audio = new Audio();
        
        // Handle different audio data formats
        if (ttsData.audio_data.startsWith('data:')) {
            // Base64 data URL
            audio.src = ttsData.audio_data;
        } else if (ttsData.audio_data.startsWith('http')) {
            // URL
            audio.src = ttsData.audio_data;
        } else {
            // Base64 string - convert to data URL
            audio.src = `data:audio/wav;base64,${ttsData.audio_data}`;
        }
        
        // Set up event handlers
        audio.oncanplaythrough = () => {
            console.log('🔊 Playing TTS audio');
            audio.play().catch(error => {
                console.error('TTS audio playback failed:', error);
            });
        };
        
        audio.onerror = (error) => {
            console.error('TTS audio loading failed:', error);
        };
        
        audio.onended = () => {
            console.log('🔊 TTS audio playback completed');
            
            // Trigger emotion if provided
            if (ttsData.emotion) {
                triggerEmotionalResponse(ttsData.emotion, ttsData.intensity || 0.5);
            }
        };
        
        // Load the audio
        audio.load();
        
    } catch (error) {
        console.error('Error setting up TTS audio:', error);
    }
}

// Chat input handling
function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        if (typeof sendMessage === 'function') {
            sendMessage();
        } else {
            console.warn('sendMessage function not available');
        }
    }
}

// Model reference update for interaction system
function updateCurrentModelReference() {
    if (!window.live2dMultiModelManager) {
        console.warn('Multi-model manager not available for model reference update');
        return;
    }
    
    const activeModel = window.live2dMultiModelManager.getActiveModel();
    if (activeModel && activeModel.pixiModel) {
        console.log('🎯 Updated current model reference:', activeModel.name);
        
        // Apply mouse interaction fix if needed
        setTimeout(() => {
            if (typeof fixPixiInteractionSystem === 'function') {
                fixPixiInteractionSystem();
            }
        }, 500);
    } else {
        console.log('🎯 No active model for reference update');
    }
}

// Chat history management functions
function refreshChatHistory() {
    console.log('🔄 Refreshing chat history...');
    // Implementation can be added as needed
    if (typeof window.refreshChatHistory === 'function') {
        window.refreshChatHistory();
    }
}

function clearChatHistory() {
    console.log('🗑️ Clearing chat history...');
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.innerHTML = '';
        console.log('✅ Chat history cleared');
    }
    
    // Call modular function if available
    if (typeof window.clearChatHistory === 'function') {
        window.clearChatHistory();
    }
}

function exportChatHistory() {
    console.log('📥 Exporting chat history...');
    // Implementation can be added as needed
    if (typeof window.exportChatHistory === 'function') {
        window.exportChatHistory();
    }
}

// Model management helper functions
function reloadCurrentModel() {
    if (!window.live2dMultiModelManager) {
        console.warn('Multi-model manager not available');
        return;
    }
    
    const activeModel = window.live2dMultiModelManager.getActiveModel();
    if (activeModel) {
        console.log('🔄 Reloading current model:', activeModel.name);
        // Implementation for model reload
        window.live2dMultiModelManager.reloadModel(activeModel.id);
    } else {
        console.log('No active model to reload');
    }
}

function removeCurrentModel() {
    if (!window.live2dMultiModelManager) {
        console.warn('Multi-model manager not available');
        return;
    }
    
    const activeModel = window.live2dMultiModelManager.getActiveModel();
    if (activeModel) {
        console.log('🗑️ Removing current model:', activeModel.name);
        window.live2dMultiModelManager.removeModel(activeModel.id);
    } else {
        console.log('No active model to remove');
    }
}

function centerModel() {
    const activeModel = window.live2dMultiModelManager?.getActiveModel();
    if (activeModel && activeModel.pixiModel) {
        const canvas = document.querySelector('#pixiContainer canvas');
        if (canvas) {
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            
            activeModel.pixiModel.x = centerX;
            activeModel.pixiModel.y = centerY;
            
            console.log('🎯 Model centered at:', { x: centerX, y: centerY });
        }
    }
}

function resetScale() {
    const activeModel = window.live2dMultiModelManager?.getActiveModel();
    if (activeModel && activeModel.pixiModel) {
        activeModel.pixiModel.scale.set(1.0);
        
        // Update UI slider if available
        const scaleSlider = document.getElementById('scaleSlider');
        const scaleValue = document.getElementById('scaleValue');
        if (scaleSlider) scaleSlider.value = 1.0;
        if (scaleValue) scaleValue.textContent = '1.0';
        
        console.log('↩️ Model scale reset to 1.0');
    }
}

// Motion and expression controls
function playSelectedMotion() {
    const motionSelect = document.getElementById('motionSelect');
    if (motionSelect && motionSelect.value) {
        console.log('🎭 Playing selected motion:', motionSelect.value);
        
        if (typeof window.triggerMotion === 'function') {
            window.triggerMotion(motionSelect.value);
        }
    }
}

function stopMotion() {
    console.log('⏹️ Stopping motion');
    // Implementation for stopping motion
    const activeModel = window.live2dMultiModelManager?.getActiveModel();
    if (activeModel && activeModel.pixiModel && typeof activeModel.pixiModel.stopAllMotions === 'function') {
        activeModel.pixiModel.stopAllMotions();
    }
}

function setExpression() {
    const expressionSelect = document.getElementById('expressionSelect');
    if (expressionSelect && expressionSelect.value) {
        console.log('😊 Setting expression:', expressionSelect.value);
        
        const activeModel = window.live2dMultiModelManager?.getActiveModel();
        if (activeModel && activeModel.pixiModel && typeof activeModel.pixiModel.expression === 'function') {
            activeModel.pixiModel.expression(expressionSelect.value);
        }
    }
}

function resetExpression() {
    console.log('😐 Resetting expression');
    const activeModel = window.live2dMultiModelManager?.getActiveModel();
    if (activeModel && activeModel.pixiModel && typeof activeModel.pixiModel.expression === 'function') {
        activeModel.pixiModel.expression();
    }
}

// Character and user management
function onCharacterChange() {
    const characterSelect = document.getElementById('characterSelect');
    console.log('👤 Character selection changed:', characterSelect?.value);
    // Implementation can be added as needed
}

// Fullscreen and help toggles
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.error('Error attempting to enable fullscreen:', err);
        });
    } else {
        document.exitFullscreen();
    }
}

function toggleHelp() {
    console.log('❓ Toggle help');
    // Implementation can be added for help panel
}

// Drawing system functions (placeholder)
function selectTool(tool) {
    console.log('🎨 Selected tool:', tool);
    // Implementation handled by ui_drawing_system.js
}

function updateDrawingColor() {
    const colorInput = document.getElementById('drawingColor');
    console.log('🎨 Drawing color updated:', colorInput?.value);
}

function updateBrushSize() {
    const brushSize = document.getElementById('brushSize');
    const brushSizeValue = document.getElementById('brushSizeValue');
    if (brushSize && brushSizeValue) {
        brushSizeValue.textContent = brushSize.value + 'px';
    }
}

function updateOpacity() {
    const opacity = document.getElementById('opacity');
    const opacityValue = document.getElementById('opacityValue');
    if (opacity && opacityValue) {
        opacityValue.textContent = opacity.value + '%';
    }
}

function clearCanvas() {
    console.log('🗑️ Clear drawing canvas');
    // Implementation handled by ui_drawing_system.js
}

function saveDrawing() {
    console.log('💾 Save drawing');
    // Implementation handled by ui_drawing_system.js
}

function loadDrawing() {
    console.log('📁 Load drawing');
    // Implementation handled by ui_drawing_system.js
}

// Model info display function
function updateModelInfoDisplay() {
    console.log('📋 Updating model info display');
    const activeModel = window.live2dMultiModelManager?.getActiveModel();
    if (activeModel) {
        console.log('📋 Active model info:', {
            name: activeModel.name,
            id: activeModel.id,
            hasPixiModel: !!activeModel.pixiModel
        });
        
        // Update UI elements if they exist
        const modelSelect = document.getElementById('modelSelect');
        if (modelSelect && activeModel.id) {
            modelSelect.value = activeModel.id;
        }
        
        // Update people panel if available
        if (typeof window.updatePeoplePanel === 'function') {
            window.updatePeoplePanel();
        }
    } else {
        console.log('📋 No active model to display');
    }
}

// Export all functions for global access
window.triggerEmotionalResponse = triggerEmotionalResponse;
window.playEmotionalTTSAudio = playEmotionalTTSAudio;
window.handleChatKeyPress = handleChatKeyPress;
window.updateCurrentModelReference = updateCurrentModelReference;
window.refreshChatHistory = refreshChatHistory;
window.clearChatHistory = clearChatHistory;
window.exportChatHistory = exportChatHistory;
window.reloadCurrentModel = reloadCurrentModel;
window.removeCurrentModel = removeCurrentModel;
window.centerModel = centerModel;
window.resetScale = resetScale;
window.playSelectedMotion = playSelectedMotion;
window.stopMotion = stopMotion;
window.setExpression = setExpression;
window.resetExpression = resetExpression;
window.onCharacterChange = onCharacterChange;
window.toggleFullscreen = toggleFullscreen;
window.toggleHelp = toggleHelp;
window.selectTool = selectTool;
window.updateDrawingColor = updateDrawingColor;
window.updateBrushSize = updateBrushSize;
window.updateOpacity = updateOpacity;
window.clearCanvas = clearCanvas;
window.saveDrawing = saveDrawing;
window.loadDrawing = loadDrawing;
window.updateModelInfoDisplay = updateModelInfoDisplay;
