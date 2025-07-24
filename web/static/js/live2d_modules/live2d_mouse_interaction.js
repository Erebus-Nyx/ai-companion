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
        if (newScale >= 0 && newScale <= 3.0) {
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

// Enhanced PIXI interaction system fix with comprehensive debugging
function fixPixiInteractionSystem() {
    const pixiApp = window.live2dIntegration?.core?.app || window.pixiApp;
    if (!pixiApp) {
        console.error('❌ No PIXI app found for interaction fix');
        return;
    }
    
    console.log('🔧 Applying PIXI interaction system fix...');
    
    // Step 1: Destroy any corrupted interaction manager
    const interaction = pixiApp.renderer.plugins?.interaction;
    if (interaction) {
        try {
            // Clear corrupted event data
            if (interaction.eventData) {
                Object.keys(interaction.eventData).forEach(key => {
                    delete interaction.eventData[key];
                });
            }
            
            // Remove DOM listeners and destroy
            if (interaction.removeEvents) interaction.removeEvents();
            if (interaction.destroy) interaction.destroy();
            delete pixiApp.renderer.plugins.interaction;
            
            console.log('✅ Old interaction manager cleaned up');
        } catch (error) {
            console.log('⚠️ Error cleaning old interaction:', error.message);
        }
    }
    
    // Step 2: Create new interaction manager or manual fallback
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
            console.log('✅ New PIXI interaction manager created');
        }
    } catch (error) {
        console.log('⚠️ PIXI interaction manager creation failed:', error.message);
    }
    
    // Step 3: Set up manual DOM event bridge with complete drag system
    const canvasElement = pixiApp.view;
    
    // Initialize global drag state if not exists
    if (!window.dragState) {
        window.dragState = {
            isDragging: false,
            dragStart: null,
            modelStart: null,
            activeModel: null,
            moveCount: 0,
            pointerId: undefined
        };
    }
    
    // CRITICAL: Remove existing manual handlers
    if (canvasElement._fixedPointerHandler) {
        canvasElement.removeEventListener('mousedown', canvasElement._fixedPointerHandler);
        canvasElement.removeEventListener('pointerdown', canvasElement._fixedPointerHandler);
        document.removeEventListener('mousemove', canvasElement._fixedMoveHandler);
        document.removeEventListener('mouseup', canvasElement._fixedUpHandler);
        document.removeEventListener('pointerup', canvasElement._fixedUpHandler);
    }
    
    // CRITICAL: Disable all existing Live2D interaction systems that might interfere
    console.log('🔧 DISABLING existing Live2D interaction systems...');
    
    // Disable PIXI stage interaction to prevent conflicts
    pixiApp.stage.interactive = false;
    pixiApp.stage.eventMode = 'passive';
    
    // Find any active models and disable their interaction systems
    const currentActiveModel = window.live2dMultiModelManager?.getActiveModel();
    if (currentActiveModel?.pixiModel) {
        console.log('🔧 Disabling interaction on active model:', currentActiveModel.name);
        currentActiveModel.pixiModel.interactive = false;
        currentActiveModel.pixiModel.eventMode = 'passive';
        currentActiveModel.pixiModel.removeAllListeners();
    }
    
    // Create comprehensive event handlers for full drag system
    canvasElement._fixedPointerHandler = function(event) {
        // Convert to canvas coordinates
        const rect = canvasElement.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        // Test model hit and start drag
        const model = window.live2dMultiModelManager?.getActiveModel();
        if (model?.pixiModel) {
            const pixiModel = model.pixiModel;
            const bounds = pixiModel.getBounds();
            
            console.log('🔍 Hit test debug:', {
                canvasClick: { x: x, y: y },
                modelBounds: { 
                    x: bounds.x, 
                    y: bounds.y, 
                    width: bounds.width, 
                    height: bounds.height 
                },
                modelPosition: { x: pixiModel.x, y: pixiModel.y },
                modelName: model.name,
                withinBounds: x >= bounds.x && x <= bounds.x + bounds.width && 
                             y >= bounds.y && y <= bounds.y + bounds.height
            });
            
            // Check if click is within model bounds
            if (x >= bounds.x && x <= bounds.x + bounds.width && 
                y >= bounds.y && y <= bounds.y + bounds.height) {
                
                // Start drag operation using global state
                window.dragState.isDragging = true;
                window.dragState.dragStart = { x: event.clientX, y: event.clientY };
                window.dragState.modelStart = { x: pixiModel.x, y: pixiModel.y };
                window.dragState.activeModel = pixiModel;
                window.dragState.moveCount = 0; // Reset move counter for new drag
                
                // Visual feedback
                pixiModel.alpha = 0.8;
                
                console.log('🖱️ Drag started:', {
                    startPos: window.dragState.dragStart,
                    modelStart: window.dragState.modelStart,
                    modelName: model.name
                });
                
                // CRITICAL: Store pointerId for potential cleanup, but don't capture
                window.dragState.pointerId = event.pointerId;
            } else {
                console.log('🚫 Click outside model bounds');
            }
        } else {
            console.log('🚫 No active model or pixiModel found');
        }
    };
    
    // Mouse move handler for dragging - with enhanced diagnostics
    canvasElement._fixedMoveHandler = function(event) {
        // ONLY process if we have all required state
        if (!window.dragState.isDragging || !window.dragState.activeModel || 
            !window.dragState.dragStart || !window.dragState.modelStart) {
            return;
        }
        
        // Calculate movement delta from original drag start position
        const deltaX = event.clientX - window.dragState.dragStart.x;
        const deltaY = event.clientY - window.dragState.dragStart.y;
        
        // Update model position in real-time
        const newX = window.dragState.modelStart.x + deltaX;
        const newY = window.dragState.modelStart.y + deltaY;
        
        window.dragState.activeModel.x = newX;
        window.dragState.activeModel.y = newY;
        
        // Increment and log move counter
        if (!window.dragState.moveCount) window.dragState.moveCount = 0;
        window.dragState.moveCount++;
        
        // Log every 10th mousemove to reduce spam but show it's working
        if (window.dragState.moveCount % 10 === 1) {
            console.log('🖱️ REAL-TIME DRAG:', {
                mousePos: { x: event.clientX, y: event.clientY },
                delta: { x: Math.round(deltaX), y: Math.round(deltaY) },
                modelPos: { x: Math.round(newX), y: Math.round(newY) },
                moveCount: window.dragState.moveCount
            });
        }
        
        event.preventDefault();
    };
    
    // Mouse up handler to end drag
    canvasElement._fixedUpHandler = function(event) {
        console.log('🔼 Mouse up event received:', { 
            type: event.type, 
            isDragging: window.dragState.isDragging, 
            hasActiveModel: !!window.dragState.activeModel 
        });
        
        if (window.dragState.isDragging && window.dragState.activeModel) {
            // End drag operation
            window.dragState.isDragging = false;
            window.dragState.activeModel.alpha = 1.0; // Restore opacity
            
            console.log('✅ Drag ended at position:', { 
                x: Math.round(window.dragState.activeModel.x), 
                y: Math.round(window.dragState.activeModel.y),
                totalMoves: window.dragState.moveCount || 0
            });
            
            // Release pointer capture if it was set
            if (canvasElement.releasePointerCapture && window.dragState.pointerId !== undefined) {
                try {
                    canvasElement.releasePointerCapture(window.dragState.pointerId);
                    console.log('✅ Released pointer capture for pointerId:', window.dragState.pointerId);
                } catch (e) {
                    console.log('⚠️ Failed to release pointer capture:', e.message);
                }
            }
            
            // Reset state
            window.dragState.dragStart = null;
            window.dragState.modelStart = null;
            window.dragState.activeModel = null;
            window.dragState.moveCount = 0;
            window.dragState.pointerId = undefined;
            
            event.preventDefault();
            event.stopPropagation();
        } else {
            console.log('🔼 Mouse up but not dragging or no active model');
        }
    };
    
    console.log('🔧 CRITICAL: Adding fresh event listeners...');
    
    // Add all event listeners (both mouse and pointer events)
    canvasElement.addEventListener('mousedown', canvasElement._fixedPointerHandler, { passive: false });
    canvasElement.addEventListener('pointerdown', canvasElement._fixedPointerHandler, { passive: false });
    
    // Use document mousemove to avoid conflicts
    document.addEventListener('mousemove', canvasElement._fixedMoveHandler, { passive: false });
    
    document.addEventListener('mouseup', canvasElement._fixedUpHandler, { passive: false });
    document.addEventListener('pointerup', canvasElement._fixedUpHandler, { passive: false });
    
    console.log('✅ Event listeners added:', {
        canvasDown: 'mousedown + pointerdown',
        documentMove: 'mousemove', 
        documentUp: 'mouseup + pointerup'
    });
    
    // Configure canvas for optimal interaction
    canvasElement.style.touchAction = 'none';
    canvasElement.style.pointerEvents = 'auto';
    canvasElement.style.userSelect = 'none';
    canvasElement.style.webkitUserSelect = 'none';
    canvasElement.style.msUserSelect = 'none';
    canvasElement.style.mozUserSelect = 'none';
    canvasElement.style.webkitUserDrag = 'none';
    canvasElement.style.webkitTouchCallout = 'none';
    canvasElement.style.webkitTapHighlightColor = 'transparent';
    canvasElement.setAttribute('onmousemove', ''); // Force enable mousemove attribute
    
    // CRITICAL: Keep stage interaction DISABLED to prevent conflicts with manual DOM handlers
    pixiApp.stage.interactive = false;
    pixiApp.stage.eventMode = 'passive';
    
    console.log('✅ PIXI interaction system fix applied successfully - manual DOM only');
}

// Export functions for global access
window.setupLive2DMouseInteraction = setupLive2DMouseInteraction;
window.setupModelScaling = setupModelScaling;
window.setupModelHitAreas = setupModelHitAreas;
window.fixPixiInteractionSystem = fixPixiInteractionSystem;
