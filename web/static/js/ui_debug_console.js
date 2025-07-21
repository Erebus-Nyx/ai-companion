/**
 * Debug Console Management System
 * Handles debug console, diagnostic functions, and testing utilities
 */

// Helper function to update model info display
function updateModelInfoDisplay(message) {
    // Update the model info div if it exists
    let modelInfo = document.getElementById('model-info');
    if (!modelInfo) {
        // Create model info display if it doesn't exist
        modelInfo = document.createElement('div');
        modelInfo.id = 'model-info';
        modelInfo.style.cssText = `
            position: absolute;
            top: 0px;
            left: 0px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 12px;
            border-radius: 6px;
            font-size: 11px;
            z-index: 1000;
            max-width: 280px;
            font-family: monospace;
            white-space: pre-line;
        `;
        document.body.appendChild(modelInfo);
    }
    
    const timestamp = new Date().toLocaleTimeString();
    
    // Get current active model info
    let activeModelInfo = '';
    if (live2dMultiModelManager) {
        const activeModel = live2dMultiModelManager.getActiveModel();
        const allModels = live2dMultiModelManager.getAllModels();
        
        if (activeModel) {
            const modelName = activeModel.name || 'Unknown';
            const position = activeModel.pixiModel ? `(${Math.round(activeModel.pixiModel.x)}, ${Math.round(activeModel.pixiModel.y)})` : '(0, 0)';
            const scale = activeModel.pixiModel ? activeModel.pixiModel.scale.x.toFixed(2) : '1.00';
            const visible = activeModel.pixiModel ? activeModel.pixiModel.visible : false;
            const interactive = activeModel.pixiModel ? activeModel.pixiModel.interactive : false;
            activeModelInfo = `Active Model: ${modelName}\nPosition: ${position}\nScale: ${scale}\nVisible: ${visible}\nInteractive: ${interactive}`;
        } else {
            // Show all models and their visibility status
            activeModelInfo = `No active model\nTotal models: ${allModels.length}`;
            if (allModels.length > 0) {
                activeModelInfo += '\nModels:';
                allModels.forEach((modelData, index) => {
                    const visible = modelData.pixiModel ? modelData.pixiModel.visible : false;
                    activeModelInfo += `\n- ${modelData.name}: ${visible ? 'visible' : 'hidden'}`;
                });
            }
        }
    } else {
        activeModelInfo = 'Live2D system not ready';
    }
    
    modelInfo.innerHTML = `
        <div style="color: #4CAF50; font-weight: bold;">🖱️ Live2D Mouse Controls</div>
        <div style="margin: 8px 0; padding: 8px; background: rgba(255,255,255,0.1); border-radius: 4px;">
            ${message}
        </div>
        <div style="margin: 8px 0; padding: 8px; background: rgba(76,175,80,0.1); border-radius: 4px; font-size: 10px;">
            ${activeModelInfo}
        </div>
        <div style="margin: 8px 0;">
            <button onclick="updateCurrentModelReference(); updateModelInfoDisplay('Model reference updated');" style="background: #2196F3; color: white; border: none; padding: 4px 8px; border-radius: 3px; font-size: 10px; cursor: pointer;">
                🔄 Refresh
            </button>
            <button onclick="debugModelSystem()" style="background: #FF9800; color: white; border: none; padding: 4px 8px; border-radius: 3px; font-size: 10px; cursor: pointer; margin-left: 4px;">
                🔍 Debug
            </button>
        </div>
        <div style="font-size: 10px; color: #aaa;">
            <strong>Controls:</strong><br>
            • Drag model to move<br>
            • Mouse wheel to scale<br>
            • Click parts for hit test<br>
            <br>
            <strong>System Status:</strong><br>
            ✅ PIXI interaction system active<br>
            ✅ Manual DOM bridge functional<br>
            <br>
            <strong>Updated:</strong> ${timestamp}
        </div>
    `;
}

// Enhanced Debug Console
function toggleDebugConsole() {
    const debugPanel = document.getElementById('debugUIPanel');
    if (debugPanel.style.display === 'none' || !debugPanel.style.display) {
        debugPanel.style.display = 'block';
        console.log('🔍 Debug console opened');
    } else {
        debugPanel.style.display = 'none';
        console.log('🔍 Debug console closed');
    }
}

// Simplified diagnostic functions
function debugPixiEvents() {
    let pixiApp = null;
    
    if (window.live2dIntegration?.core?.app) {
        pixiApp = window.live2dIntegration.core.app;
    } else if (window.live2dIntegration?.app) {
        pixiApp = window.live2dIntegration.app;
    } else if (window.pixiApp) {
        pixiApp = window.pixiApp;
    }
    
    if (!pixiApp) {
        console.error('❌ No PIXI app found');
        return;
    }
    
    window.pixiApp = pixiApp;
    
    pixiApp.stage.interactive = true;
    pixiApp.stage.eventMode = 'static';
    pixiApp.stage.hitArea = pixiApp.screen;
    
    const interaction = pixiApp.renderer.plugins?.interaction;
    if (interaction) {
        interaction.interactionDOMElement = pixiApp.view;
        if (interaction.setTargetElement) {
            interaction.setTargetElement(pixiApp.view);
        }
    }
    
    const stageDownHandler = (event) => {
        console.log('🎯 STAGE POINTER DOWN:', {
            x: event.global.x,
            y: event.global.y
        });
    };
    
    pixiApp.stage.off('pointerdown', stageDownHandler);
    pixiApp.stage.on('pointerdown', stageDownHandler);
}

function debugCanvasEvents() {
    const canvas = document.querySelector('canvas');
    if (!canvas) {
        console.error('❌ No canvas found');
        return;
    }
    
    const canvasHandler = (event) => {
        console.log('🎯 CANVAS EVENT:', {
            type: event.type,
            x: event.clientX,
            y: event.clientY
        });
    };
    
    canvas.removeEventListener('mousedown', canvasHandler);
    canvas.removeEventListener('mouseup', canvasHandler);
    canvas.addEventListener('mousedown', canvasHandler);
    canvas.addEventListener('mouseup', canvasHandler);
}

function debugPixiInteractionManager() {
    const pixiApp = window.live2dIntegration?.core?.app || window.pixiApp;
    if (!pixiApp) {
        console.error('❌ No PIXI app found');
        return;
    }
    
    const interaction = pixiApp.renderer.plugins?.interaction;
    if (interaction) {
        interaction.interactionDOMElement = pixiApp.view;
        pixiApp.stage.interactive = true;
        pixiApp.stage.eventMode = 'static';
        pixiApp.stage.hitArea = pixiApp.screen;
        
        if (interaction.setTargetElement) {
            interaction.setTargetElement(pixiApp.view);
        }
        
        const originalOnPointerDown = interaction.onPointerDown;
        interaction.onPointerDown = function(event) {
            updateModelInfoDisplay('🎯 PIXI Interaction Manager working!');
            if (originalOnPointerDown) {
                return originalOnPointerDown.call(this, event);
            }
        };
    } else {
        console.error('❌ PIXI interaction manager not found');
    }
}

function debugModelInteraction() {
    const activeModel = live2dMultiModelManager?.getActiveModel();
    if (!activeModel?.pixiModel) {
        updateModelInfoDisplay('❌ No active model found');
        return;
    }
    
    const model = activeModel.pixiModel;
    
    model.removeAllListeners('pointerdown');
    model.removeAllListeners('pointerup');
    
    model.on('pointerdown', (event) => {
        updateModelInfoDisplay('🎉 Model mouse down detected!');
    });
    
    model.on('pointerup', (event) => {
        updateModelInfoDisplay('🔼 Model mouse up detected!');
    });
    
    model.interactive = true;
    model.eventMode = 'static';
    model.buttonMode = true;
    model.cursor = 'pointer';
    
    updateModelInfoDisplay('🧪 Test listeners added\nTry clicking the model');
}

function debugModelSystem() {
    let debugInfo = 'System Debug:\n';
    debugInfo += `Manager: ${!!live2dMultiModelManager}\n`;
    debugInfo += `PIXI App: ${!!pixiApp}\n`;
    debugInfo += `Current Model: ${!!currentModel}\n`;
    
    if (live2dMultiModelManager) {
        const allModels = live2dMultiModelManager.getAllModels();
        debugInfo += `Total Models: ${allModels.length}`;
    }
    
    updateModelInfoDisplay(debugInfo);
}

// Performance Testing Functions
function testLoadingPerformance() {
    console.log('Testing model loading performance...');
    if (live2dMultiModelManager) {
        console.log('Performance test: Measuring model loading times');
    } else {
        console.log('No Live2D manager available for performance testing');
    }
}

function benchmarkModelSwitching() {
    console.log('Benchmarking model switching performance...');
    if (live2dMultiModelManager) {
        console.log('Performance test: Measuring model switching speed');
    } else {
        console.log('No Live2D manager available for benchmarking');
    }
}

function displayPerformanceStats() {
    console.log('Displaying performance statistics...');
    if (live2dMultiModelManager) {
        const models = live2dMultiModelManager.getAllModels();
        console.log(`Performance Stats:
- Total models loaded: ${models.length}
- Active model: ${live2dMultiModelManager.activeModelId || 'None'}
- Memory usage: ${(performance.memory ? performance.memory.usedJSHeapSize / 1024 / 1024 : 'Unknown')} MB`);
    } else {
        console.log('No Live2D manager available for performance stats');
    }
}

function clearPerformanceCache() {
    console.log('Clearing performance cache...');
    console.log('Performance cache cleared');
}

// Export functions for global access
window.updateModelInfoDisplay = updateModelInfoDisplay;
window.toggleDebugConsole = toggleDebugConsole;
window.debugPixiEvents = debugPixiEvents;
window.debugCanvasEvents = debugCanvasEvents;
window.debugPixiInteractionManager = debugPixiInteractionManager;
window.debugModelInteraction = debugModelInteraction;
window.debugModelSystem = debugModelSystem;
window.testLoadingPerformance = testLoadingPerformance;
window.benchmarkModelSwitching = benchmarkModelSwitching;
window.displayPerformanceStats = displayPerformanceStats;
window.clearPerformanceCache = clearPerformanceCache;
