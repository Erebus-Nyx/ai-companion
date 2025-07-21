/**
 * Live2D Mouse Interaction System
 * Handles dragging, scaling, and hit area detection for Live2D models
 */

// Global drag state variables
window.dragState = {
    isDragging: false,
    dragStart: null,
    modelStart: null,
    activeModel: null,
    moveCount: 0,
    pointerId: undefined
};

// Live2D Viewer Web Mouse Interaction Implementation
function setupLive2DMouseInteraction(model) {
    if (!model || !window.pixiApp) {
        console.warn('Cannot setup mouse interaction: missing model or PIXI app');
        return;
    }
    
    // Enable interaction on the model
    model.interactive = true;
    model.buttonMode = true;
    
    // Set up dragging variables
    let isDragging = false;
    let dragStart = { x: 0, y: 0 };
    let modelStart = { x: 0, y: 0 };
    
    // Mouse down - start dragging
    model.removeAllListeners('pointerdown');
    model.on('pointerdown', (event) => {
        isDragging = true;
        const position = event.data.global;
        dragStart.x = position.x;
        dragStart.y = position.y;
        modelStart.x = model.x;
        modelStart.y = model.y;
        
        event.stopPropagation();
        updateModelInfoDisplay(`Dragging model from (${Math.round(modelStart.x)}, ${Math.round(modelStart.y)})`);
    });
    
    // Mouse move - drag the model
    window.pixiApp.stage.removeAllListeners('pointermove');
    window.pixiApp.stage.on('pointermove', (event) => {
        if (!isDragging) return;
        
        const position = event.data.global;
        const deltaX = position.x - dragStart.x;
        const deltaY = position.y - dragStart.y;
        
        model.x = modelStart.x + deltaX;
        model.y = modelStart.y + deltaY;
        
        updateModelInfoDisplay(`Position: (${Math.round(model.x)}, ${Math.round(model.y)}) Scale: ${model.scale.x.toFixed(2)}`);
    });
    
    // Mouse up - stop dragging
    window.pixiApp.stage.removeAllListeners('pointerup');
    window.pixiApp.stage.on('pointerup', () => {
        if (isDragging) {
            isDragging = false;
            updateModelInfoDisplay(`✅ Model positioned at (${Math.round(model.x)}, ${Math.round(model.y)})`);
        }
    });
    
    // Handle mouse leave canvas
    window.pixiApp.stage.removeAllListeners('pointerupoutside');
    window.pixiApp.stage.on('pointerupoutside', () => {
        if (isDragging) {
            isDragging = false;
            updateModelInfoDisplay(`✅ Model positioned at (${Math.round(model.x)}, ${Math.round(model.y)})`);
        }
    });
    
    // Set up mouse wheel scaling
    setupModelScaling(model);
    
    // Set up hit area testing if available
    setupModelHitAreas(model);
}

// Live2D Viewer Web scaling pattern implementation
function setupModelScaling(model) {
    if (!window.pixiApp?.view) {
        console.warn('Cannot setup model scaling: no canvas available');
        return;
    }
    
    const canvas = window.pixiApp.view;
    
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
        
        // Limit scale between 0.1 and 5.0
        if (newScale >= 0.1 && newScale <= 5.0) {
            model.scale.set(newScale);
            
            // Update UI slider if available
            const slider = document.getElementById('zoomSlider');
            const display = document.getElementById('zoomValue');
            if (slider) slider.value = newScale;
            if (display) display.textContent = newScale.toFixed(2);
            
            updateModelInfoDisplay(`Position: (${Math.round(model.x)}, ${Math.round(model.y)}) Scale: ${newScale.toFixed(2)}`);
        }
    }
    
    // Store handler reference for cleanup
    canvas._live2dWheelHandler = handleModelWheel;
    
    // Add wheel event listener
    canvas.addEventListener('wheel', handleModelWheel, { passive: false });
}

// Live2D Viewer Web hit area pattern implementation
function setupModelHitAreas(model) {
    if (!model?.internalModel) {
        return;
    }
    
    model.removeAllListeners('pointerdown');
    model.on('pointerdown', (event) => {
        const point = event.data.global;
        const localPoint = model.toLocal(point);
        
        // Test hit areas if available
        if (model.internalModel.hitTest) {
            try {
                const hitAreas = model.internalModel.hitTest(localPoint.x, localPoint.y);
                
                if (hitAreas && hitAreas.length > 0) {
                    updateModelInfoDisplay(`🎯 Hit: ${hitAreas.join(', ')}`);
                    
                    // Trigger motions based on hit areas
                    hitAreas.forEach(hitArea => {
                        // Add motion triggers here if needed
                    });
                }
            } catch (error) {
                console.warn('Hit test failed:', error);
            }
        }
    });
}

// Integrated PIXI interaction system fix
function fixPixiInteractionSystem() {
    const pixiApp = window.live2dIntegration?.core?.app || window.pixiApp;
    if (!pixiApp) {
        return;
    }
    
    // Step 1: Destroy any corrupted interaction manager
    const interaction = pixiApp.renderer.plugins?.interaction;
    if (interaction) {
        try {
            if (interaction.eventData) {
                Object.keys(interaction.eventData).forEach(key => {
                    delete interaction.eventData[key];
                });
            }
            if (interaction.removeEvents) interaction.removeEvents();
            if (interaction.destroy) interaction.destroy();
            delete pixiApp.renderer.plugins.interaction;
        } catch (error) {
            // Ignore cleanup errors
        }
    }
    
    // Step 2: Create new interaction manager
    try {
        let newInteraction = null;
        
        if (PIXI.InteractionManager) {
            newInteraction = new PIXI.InteractionManager(pixiApp.renderer);
        } else if (PIXI.interaction?.InteractionManager) {
            newInteraction = new PIXI.interaction.InteractionManager(pixiApp.renderer);
        }
        
        if (newInteraction) {
            pixiApp.renderer.plugins.interaction = newInteraction;
            newInteraction.interactionDOMElement = pixiApp.view;
        }
    } catch (error) {
        // Use manual fallback if PIXI interaction fails
    }
    
    // Step 3: Set up manual DOM event bridge
    const canvas = pixiApp.view;
    
    // Remove existing manual handlers
    if (canvas._fixedPointerHandler) {
        canvas.removeEventListener('mousedown', canvas._fixedPointerHandler);
        canvas.removeEventListener('pointerdown', canvas._fixedPointerHandler);
        document.removeEventListener('mousemove', canvas._fixedMoveHandler);
        document.removeEventListener('mouseup', canvas._fixedUpHandler);
        document.removeEventListener('pointerup', canvas._fixedUpHandler);
    }
    
    // Disable PIXI stage interaction to prevent conflicts
    pixiApp.stage.interactive = false;
    pixiApp.stage.eventMode = 'passive';
    
    // Find any active models and disable their interaction systems
    const activeModel = window.live2dMultiModelManager?.getActiveModel();
    if (activeModel?.pixiModel) {
        activeModel.pixiModel.interactive = false;
        activeModel.pixiModel.eventMode = 'passive';
        activeModel.pixiModel.removeAllListeners();
    }
    
    // Create event handlers for drag system
    canvas._fixedPointerHandler = function(event) {
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        const model = window.live2dMultiModelManager?.getActiveModel();
        if (model?.pixiModel) {
            const pixiModel = model.pixiModel;
            const bounds = pixiModel.getBounds();
            
            if (x >= bounds.x && x <= bounds.x + bounds.width && 
                y >= bounds.y && y <= bounds.y + bounds.height) {
                
                window.dragState.isDragging = true;
                window.dragState.dragStart = { x: event.clientX, y: event.clientY };
                window.dragState.modelStart = { x: pixiModel.x, y: pixiModel.y };
                window.dragState.activeModel = pixiModel;
                window.dragState.moveCount = 0;
                
                pixiModel.alpha = 0.8;
                window.dragState.pointerId = event.pointerId;
            }
        }
    };
    
    // Mouse move handler for dragging
    canvas._fixedMoveHandler = function(event) {
        if (!window.dragState.isDragging || !window.dragState.activeModel || 
            !window.dragState.dragStart || !window.dragState.modelStart) {
            return;
        }
        
        const deltaX = event.clientX - window.dragState.dragStart.x;
        const deltaY = event.clientY - window.dragState.dragStart.y;
        
        const newX = window.dragState.modelStart.x + deltaX;
        const newY = window.dragState.modelStart.y + deltaY;
        
        window.dragState.activeModel.x = newX;
        window.dragState.activeModel.y = newY;
        
        window.dragState.moveCount++;
        event.preventDefault();
    };
    
    // Mouse up handler to end drag
    canvas._fixedUpHandler = function(event) {
        if (window.dragState.isDragging && window.dragState.activeModel) {
            window.dragState.isDragging = false;
            window.dragState.activeModel.alpha = 1.0;
            
            if (canvas.releasePointerCapture && window.dragState.pointerId !== undefined) {
                try {
                    canvas.releasePointerCapture(window.dragState.pointerId);
                } catch (e) {
                    // Ignore pointer capture errors
                }
            }
            
            window.dragState.dragStart = null;
            window.dragState.modelStart = null;
            window.dragState.activeModel = null;
            window.dragState.moveCount = 0;
            window.dragState.pointerId = undefined;
            
            event.preventDefault();
            event.stopPropagation();
        }
    };
    
    // Add event listeners
    canvas.addEventListener('mousedown', canvas._fixedPointerHandler, { passive: false });
    canvas.addEventListener('pointerdown', canvas._fixedPointerHandler, { passive: false });
    document.addEventListener('mousemove', canvas._fixedMoveHandler, { passive: false });
    document.addEventListener('mouseup', canvas._fixedUpHandler, { passive: false });
    document.addEventListener('pointerup', canvas._fixedUpHandler, { passive: false });
    
    // Configure canvas for optimal interaction
    canvas.style.touchAction = 'none';
    canvas.style.pointerEvents = 'auto';
    canvas.style.userSelect = 'none';
    canvas.style.webkitUserSelect = 'none';
    canvas.style.msUserSelect = 'none';
    canvas.style.mozUserSelect = 'none';
    canvas.style.webkitUserDrag = 'none';
    canvas.style.webkitTouchCallout = 'none';
    canvas.style.webkitTapHighlightColor = 'transparent';
    
    // Keep stage interaction DISABLED to prevent conflicts
    pixiApp.stage.interactive = false;
    pixiApp.stage.eventMode = 'passive';
}

// Export functions for global access
window.setupLive2DMouseInteraction = setupLive2DMouseInteraction;
window.setupModelScaling = setupModelScaling;
window.setupModelHitAreas = setupModelHitAreas;
window.fixPixiInteractionSystem = fixPixiInteractionSystem;
