// Live2D Interaction Module
// Handles all canvas manipulation: dragging, clicking, frame toggles, zoom

class Live2DInteraction {
    constructor(app, config, logger) {
        this.app = app;
        this.config = config;
        this.logger = logger;
        this.model = null;
        
        // Canvas interaction state
        this.isDragging = false;
        this.dragOffset = { x: 0, y: 0 };
        this.lastMousePosition = { x: 0, y: 0 };
        
        // Zoom state
        this.currentZoom = 1.0;
        this.minZoom = 0.5;
        this.maxZoom = 1.5;
        this.zoomStep = 0.02;
        
        // Frame visualization state
        this.showCanvasFrame = false;
        this.showModelFrame = false;
        this.showHitAreas = false;
        
        // Graphics objects for visualizations
        this.modelFrameGraphics = null;
        this.hitAreaGraphics = null;
        
        // Event handlers
        this.mouseHandlers = {
            onPointerDown: this.onPointerDown.bind(this),
            onPointerMove: this.onPointerMove.bind(this),
            onPointerUp: this.onPointerUp.bind(this),
            onPointerUpOutside: this.onPointerUpOutside.bind(this),
            onWheel: this.onWheel.bind(this)
        };
        
        // Initialize mouse tracking
        this.setupMouseTracking();
    }

    // Initialize the canvas manager - accepts optional model for compatibility
    initialize(model = null) {
        this.logger.logInfo('Interaction manager initialized');
        
        // If a model is provided, update to use it
        if (model) {
            this.updateModel(model);
        }
        
        return true;
    }

    // Update the interaction manager to focus on a new model
    updateModel(newModel) {
        this.logger.logInfo(`Updating interaction model...`);
        
        // Remove interaction from the old model if it exists
        if (this.model) {
            this.removeModelInteraction();
        }
        
        this.model = newModel;
        
        // Set up interaction for the new model if it exists
        if (this.model) {
            this.setupModelInteraction();
        }
    }

    // Set up mouse tracking for the canvas
    setupMouseTracking() {
        // Track mouse position globally
        document.addEventListener('mousemove', (e) => {
            this.lastMousePosition.x = e.clientX;
            this.lastMousePosition.y = e.clientY;
        });
    }

    // Set up interaction for the loaded model
    setupModelInteraction() {
        if (!this.model || !this.app) {
            console.error('Cannot setup interaction - missing model or app:', { model: !!this.model, app: !!this.app });
            return;
        }
        
        console.log('Setting up model interaction for:', this.model.constructor.name);
        console.log('Model details:', {
            position: { x: this.model.x, y: this.model.y },
            scale: { x: this.model.scale.x, y: this.model.scale.y },
            bounds: this.model.getBounds()
        });
        
        // Make model interactive - following live2d-viewer-web pattern
        this.model.interactive = true;
        this.model.eventMode = 'static';
        
        console.log('Model interactive state:', {
            interactive: this.model.interactive,
            eventMode: this.model.eventMode,
            position: { x: this.model.x, y: this.model.y }
        });
        
        // Remove any existing listeners first - be more thorough
        this.model.removeAllListeners('pointerdown');
        this.model.removeAllListeners('pointermove');
        this.model.removeAllListeners('pointerup');
        this.model.removeAllListeners('pointerupoutside');
        
        // Check if already set up to prevent duplicate listeners
        if (this.model._live2dInteractionSetup) {
            console.log('🔄 Model already has interaction setup, skipping duplicate');
            return;
        }
        
        // CRITICAL FIX: Properly bind event handlers to maintain context
        const boundHandlers = {
            onPointerDown: this.mouseHandlers.onPointerDown.bind(this),
            onPointerMove: this.mouseHandlers.onPointerMove.bind(this),
            onPointerUp: this.mouseHandlers.onPointerUp.bind(this),
            onPointerUpOutside: this.mouseHandlers.onPointerUpOutside.bind(this)
        };
        
        console.log('Event handlers being attached:', {
            onPointerDown: typeof boundHandlers.onPointerDown,
            onPointerMove: typeof boundHandlers.onPointerMove,
            onPointerUp: typeof boundHandlers.onPointerUp,
            onPointerUpOutside: typeof boundHandlers.onPointerUpOutside
        });
        
        // Add event listeners directly to model with proper binding
        this.model.on('pointerdown', boundHandlers.onPointerDown);
        this.model.on('pointermove', boundHandlers.onPointerMove);
        this.model.on('pointerup', boundHandlers.onPointerUp);
        this.model.on('pointerupoutside', boundHandlers.onPointerUpOutside);
        
        // Mark as set up to prevent duplicates
        this.model._live2dInteractionSetup = true;
        
        console.log('Event listeners attached, checking:', {
            pointerdown_listeners: this.model.listeners('pointerdown').length,
            pointermove_listeners: this.model.listeners('pointermove').length,
            pointerup_listeners: this.model.listeners('pointerup').length,
            pointerupoutside_listeners: this.model.listeners('pointerupoutside').length
        });
        
        // Add wheel event to canvas for zoom
        const canvas = this.app.canvas || this.app.view;
        if (canvas) {
            console.log('Adding wheel event to canvas element:', canvas.tagName);
            canvas.removeEventListener('wheel', this.mouseHandlers.onWheel);
            canvas.addEventListener('wheel', this.mouseHandlers.onWheel.bind(this), { passive: false });
            
            // Test if wheel events work
            console.log('Canvas wheel event listener added successfully');
        } else {
            console.error('Canvas not found for wheel events - app.canvas:', this.app.canvas, 'app.view:', this.app.view);
        }
        
        console.log('Model interaction setup completed with handlers:', {
            pointerdown: !!this.model.listeners('pointerdown').length,
            pointermove: !!this.model.listeners('pointermove').length,
            canvas_wheel: !!canvas
        });
        
        this.logger.logInfo('Model interaction set up');
    }

    // Remove interaction from the model
    removeModelInteraction() {
        if (!this.model) return;
        
        // Remove all listeners from model (following live2d-viewer-web pattern)
        this.model.off('pointerdown');
        this.model.off('pointermove');
        this.model.off('pointerup');
        this.model.off('pointerupoutside');
        
        // Remove wheel event
        const canvas = this.app.canvas || this.app.view;
        if (canvas) {
            canvas.removeEventListener('wheel', this.mouseHandlers.onWheel);
        }
        
        this.logger.logInfo('Model interaction removed');
    }

    // Clear all visualizations
    clearVisualizations() {
        if (this.modelFrameGraphics) {
            this.modelFrameGraphics.clear();
            this.modelFrameGraphics.visible = false;
        }
        
        if (this.hitAreaGraphics) {
            this.hitAreaGraphics.clear();
            this.hitAreaGraphics.visible = false;
        }
        
        this.logger.logInfo('Visualizations cleared');
    }

    // Update the model reference
    updateModel(model) {
        if (this.model) {
            this.removeModelInteraction();
        }
        
        this.model = model;
        
        if (this.model) {
            this.setupModelInteraction();
        }
        
        this.logger.logInfo('Model updated in interaction manager');
    }

        // Pointer down handler - start drag following live2d-viewer-web pattern
    onPointerDown(event) {
        console.log('🖱️ POINTER DOWN EVENT!', {
            eventType: event.type,
            globalPos: event.data.global,
            target: event.target?.constructor?.name
        });
        
        // Stop event propagation to prevent bubbling to other elements
        event.stopPropagation();
        
        // Find the interaction manager context
        let interactionManager = this;
        if (!this?.model && window.live2dIntegration?.interactionManager) {
            interactionManager = window.live2dIntegration.interactionManager;
            console.log('🔧 Using global interaction manager for pointer down');
        }
        
        if (!interactionManager?.model) {
            console.log('❌ No model available for pointer down');
            return;
        }
        
        const model = interactionManager.model;
        const position = event.data.global;
        
        // Start dragging
        interactionManager.isDragging = true;
        interactionManager.dragStart = { x: position.x, y: position.y };
        interactionManager.modelStart = { x: model.x, y: model.y };
        
        model.alpha = 0.8; // Visual feedback
        
        console.log('🖱️ Drag started:', {
            startPos: interactionManager.dragStart,
            modelStart: interactionManager.modelStart
        });
        
        if (interactionManager.logger) {
            interactionManager.logger.logInfo('Drag started');
        }
        
        // Check for hit areas (if available)
        interactionManager.checkHitAreas(event);
    }

    // Pointer move handler - simplified following live2d-viewer-web pattern
    onPointerMove(event) {
        // Find the interaction manager context
        let interactionManager = this;
        if (!this?.model && window.live2dIntegration?.interactionManager) {
            interactionManager = window.live2dIntegration.interactionManager;
        }
        
        // Only handle move events when actually dragging
        if (!interactionManager?.model || !interactionManager?.isDragging) return;
        
        const position = event.data.global;
        const deltaX = position.x - interactionManager.dragStart.x;
        const deltaY = position.y - interactionManager.dragStart.y;
        
        // Update model position using drag calculation
        interactionManager.model.x = interactionManager.modelStart.x + deltaX;
        interactionManager.model.y = interactionManager.modelStart.y + deltaY;
        
        // Only log occasionally during drag to avoid spam
        if (Math.abs(deltaX) % 10 < 2 || Math.abs(deltaY) % 10 < 2) {
            console.log('🖱️ Dragging model:', {
                newPos: { x: Math.round(interactionManager.model.x), y: Math.round(interactionManager.model.y) },
                delta: { x: Math.round(deltaX), y: Math.round(deltaY) }
            });
        }
        
        // Update frame visualizations if visible
        if (interactionManager.updateFrameVisualizations) {
            interactionManager.updateFrameVisualizations();
        }
    }

        // Pointer up handler - simplified following live2d-viewer-web pattern
    onPointerUp(event) {
        console.log('🎉 POINTER UP EVENT!', {
            eventType: event.type,
            globalPos: event.data.global,
            target: event.target?.constructor?.name
        });
        
        // Stop event propagation
        event.stopPropagation();
        
        // Find the interaction manager context
        let interactionManager = this;
        if (!this?.model && window.live2dIntegration?.interactionManager) {
            interactionManager = window.live2dIntegration.interactionManager;
            console.log('🔧 Using global interaction manager for pointer up');
        }
        
        if (!interactionManager?.model) {
            console.log('❌ No model available for pointer up');
            return;
        }
        
        const model = interactionManager.model;
        
        if (interactionManager.isDragging) {
            console.log('✅ Drag ended at position:', { x: model.x, y: model.y });
            interactionManager.isDragging = false;
            model.alpha = 1.0; // Restore opacity
            
            if (interactionManager.logger) {
                interactionManager.logger.logInfo('Drag ended');
            }
        } else {
            console.log('✅ Click detected (not drag)');
            // Simple click behavior - no hit area testing for now
            console.log('🎯 Click registered on model at:', event.data.global);
        }
    }

    // Pointer up outside handler - only handle when actually dragging
    onPointerUpOutside(event) {
        // Find the interaction manager context
        let interactionManager = this;
        if (!this?.model && window.live2dIntegration?.interactionManager) {
            interactionManager = window.live2dIntegration.interactionManager;
        }
        
        // CRITICAL: Only handle this event if we're actually dragging
        if (!interactionManager?.isDragging) {
            return; // Ignore the event if we're not dragging
        }
        
        console.log('🔼 POINTER UP OUTSIDE EVENT (during drag):', {
            wasActuallyDragging: interactionManager.isDragging,
            modelPosition: { x: interactionManager.model.x, y: interactionManager.model.y }
        });
        
        // End the drag operation
        interactionManager.isDragging = false;
        interactionManager.model.alpha = 1.0;
        
        // Notify multi-model manager to save the new position
        if (window.live2dMultiModelManager && window.live2dMultiModelManager.activeModelId) {
            window.live2dMultiModelManager.saveCurrentModelState();
        }
        
        if (interactionManager.logger) {
            interactionManager.logger.logInfo('Drag ended (outside)');
        }
    }

    // Mouse wheel handler for zoom
    onWheel(event) {
        console.log('🎯 Wheel event triggered:', { deltaY: event.deltaY, currentZoom: this.currentZoom });
        event.preventDefault();
        
        const delta = -Math.sign(event.deltaY);
        const newZoom = this.currentZoom + delta * this.zoomStep;
        console.log('Setting zoom from', this.currentZoom, 'to', newZoom);
        this.setZoom(newZoom);
    }

    // Set zoom level
    setZoom(zoomLevel) {
        if (!this.model) return;
        
        const clampedZoom = Math.max(this.minZoom, Math.min(this.maxZoom, zoomLevel));
        this.currentZoom = clampedZoom;
        
        // Get base scale from model (if it exists)
        const baseScale = this.model.baseScale || 1.0;
        
        // Apply zoom as scale combined with base scale
        this.model.scale.set(baseScale * clampedZoom);
        
        // Update UI
        const zoomSlider = document.getElementById('zoomSlider');
        const zoomValue = document.getElementById('zoomValue');
        if (zoomSlider) zoomSlider.value = this.currentZoom;
        if (zoomValue) zoomValue.textContent = this.currentZoom.toFixed(1);
        
        this.logger.logInfo(`Zoom set to ${this.currentZoom.toFixed(1)} (base: ${baseScale.toFixed(2)})`);
        
        // Update frame visualizations
        this.updateFrameVisualizations();
        
        return clampedZoom;
    }

    // Get current zoom level
    getZoom() {
        return this.currentZoom;
    }

    // Reset zoom to default
    resetZoom() {
        return this.setZoom(1.0);
    }

    // Zoom in
    zoomIn() {
        return this.setZoom(this.currentZoom + this.zoomStep);
    }

    // Zoom out
    zoomOut() {
        return this.setZoom(this.currentZoom - this.zoomStep);
    }

    // Center the model in the canvas
    centerModel() {
        if (!this.model || !this.app) return;
        
        const centerX = this.app.renderer.width / 2;
        const centerY = this.app.renderer.height / 2;
        
        this.model.position.set(centerX, centerY);
        
        // Notify multi-model manager to save the new position
        if (window.live2dMultiModelManager && window.live2dMultiModelManager.activeModelId) {
            window.live2dMultiModelManager.saveCurrentModelState();
        }
        
        // Update frame visualizations
        this.updateFrameVisualizations();
        
        this.logger.logInfo('Model centered');
    }

    // Fit the model to the canvas
    fitModelToCanvas() {
        if (!this.model || !this.app) return;
        
        // Reset zoom first
        this.resetZoom();
        
        // Center the model
        this.centerModel();
        
        this.logger.logInfo('Model fitted to canvas');
    }

    // Canvas frame toggle
    toggleCanvasFrame() {
        if (!this.app) return;
        
        const canvas = this.app.canvas || this.app.view;
        if (!canvas) return;
        
        this.showCanvasFrame = !this.showCanvasFrame;
        
        if (this.showCanvasFrame) {
            canvas.style.border = '2px solid #4a90e2';
            canvas.style.boxShadow = '0 0 10px rgba(74, 144, 226, 0.5)';
            this.logger.logInfo('Canvas frame shown');
        } else {
            canvas.style.border = 'none';
            canvas.style.boxShadow = 'none';
            this.logger.logInfo('Canvas frame hidden');
        }
        
        return this.showCanvasFrame;
    }

    // Model frame toggle
    toggleModelFrame() {
        if (!this.model || !this.app) return;
        
        this.showModelFrame = !this.showModelFrame;
        
        if (this.showModelFrame) {
            this.showModelFrameVisualization();
        } else {
            this.hideModelFrameVisualization();
        }
        
        return this.showModelFrame;
    }

    // Hit areas toggle
    toggleHitAreas() {
        if (!this.model || !this.app) return;
        
        this.showHitAreas = !this.showHitAreas;
        
        if (this.showHitAreas) {
            this.showHitAreasVisualization();
        } else {
            this.hideHitAreasVisualization();
        }
        
        return this.showHitAreas;
    }

    // Show model frame visualization
    showModelFrameVisualization() {
        if (!this.model || !this.app) return;
        
        // Create graphics if not exists
        if (!this.modelFrameGraphics) {
            this.modelFrameGraphics = new PIXI.Graphics();
            this.app.stage.addChild(this.modelFrameGraphics);
        }
        
        this.drawModelFrame();
        this.modelFrameGraphics.visible = true;
        this.updateFrameVisualizations();
        
        this.logger.logInfo('Model frame shown');
    }

    // Hide model frame visualization
    hideModelFrameVisualization() {
        if (this.modelFrameGraphics) {
            this.modelFrameGraphics.visible = false;
        }
        
        this.logger.logInfo('Model frame hidden');
    }

    // Draw model frame
    drawModelFrame() {
        if (!this.modelFrameGraphics || !this.model) return;
        
        this.modelFrameGraphics.clear();
        this.modelFrameGraphics.lineStyle(1, 0xff0000, 0.8);
        
        // Get model bounds
        const bounds = this.model.getBounds();
        
        // Draw a tighter bounding box with proper padding
        const padding = 5;
        this.modelFrameGraphics.drawRect(
            bounds.x - padding, 
            bounds.y - padding, 
            bounds.width + (padding * 2), 
            bounds.height + (padding * 2)
        );
        
        // Draw center cross with smaller lines
        this.modelFrameGraphics.lineStyle(1, 0xff0000, 0.4);
        const centerX = bounds.x + bounds.width / 2;
        const centerY = bounds.y + bounds.height / 2;
        
        // Horizontal line (smaller)
        this.modelFrameGraphics.moveTo(centerX - 10, centerY);
        this.modelFrameGraphics.lineTo(centerX + 10, centerY);
        
        // Vertical line (smaller)
        this.modelFrameGraphics.moveTo(centerX, centerY - 10);
        this.modelFrameGraphics.lineTo(centerX, centerY + 10);
        
        // Add label with dimensions
        const style = new PIXI.TextStyle({
            fontSize: 10,
            fill: 0xff0000,
            backgroundColor: 0x000000,
            backgroundAlpha: 0.7
        });
        
        const label = new PIXI.Text(`${bounds.width.toFixed(0)}×${bounds.height.toFixed(0)}`, style);
        label.position.set(bounds.x, bounds.y - 15);
        this.modelFrameGraphics.addChild(label);
    }

    // Show hit areas visualization
    showHitAreasVisualization() {
        if (!this.model || !this.app) return;
        
        // Check if model has hit areas
        if (!this.model.hitAreas || this.model.hitAreas.length === 0) {
            this.logger.logInfo('No hit areas defined for this model');
            return;
        }
        
        // Create graphics if not exists
        if (!this.hitAreaGraphics) {
            this.hitAreaGraphics = new PIXI.Graphics();
            this.app.stage.addChild(this.hitAreaGraphics);
        }
        
        this.drawHitAreas();
        this.hitAreaGraphics.visible = true;
        this.updateFrameVisualizations();
        
        this.logger.logInfo('Hit areas shown');
    }

    // Hide hit areas visualization
    hideHitAreasVisualization() {
        if (this.hitAreaGraphics) {
            this.hitAreaGraphics.visible = false;
        }
        
        this.logger.logInfo('Hit areas hidden');
    }

    // Draw hit areas
    drawHitAreas() {
        if (!this.hitAreaGraphics || !this.model) return;
        
        this.hitAreaGraphics.clear();
        this.hitAreaGraphics.lineStyle(2, 0x00ff00, 0.8);
        
        // Draw hit areas if they exist
        if (this.model.hitAreas) {
            this.model.hitAreas.forEach((hitArea, index) => {
                const bounds = hitArea.getBounds();
                this.hitAreaGraphics.drawRect(
                    bounds.x, bounds.y, bounds.width, bounds.height
                );
                
                // Add label
                const style = new PIXI.TextStyle({
                    fontSize: 12,
                    fill: 0x00ff00,
                    backgroundColor: 0x000000,
                    backgroundAlpha: 0.8
                });
                
                const label = new PIXI.Text(hitArea.name || `Hit ${index}`, style);
                label.position.set(bounds.x, bounds.y - 20);
                this.hitAreaGraphics.addChild(label);
            });
        }
    }

    // Update all frame visualizations
    updateFrameVisualizations() {
        if (this.showModelFrame && this.modelFrameGraphics) {
            this.drawModelFrame();
        }
        
        if (this.showHitAreas && this.hitAreaGraphics) {
            this.drawHitAreas();
        }
    }

    // Clear all visualizations
    clearVisualizations() {
        if (this.modelFrameGraphics) {
            this.app.stage.removeChild(this.modelFrameGraphics);
            this.modelFrameGraphics.destroy();
            this.modelFrameGraphics = null;
        }
        
        if (this.hitAreaGraphics) {
            this.app.stage.removeChild(this.hitAreaGraphics);
            this.hitAreaGraphics.destroy();
            this.hitAreaGraphics = null;
        }
    }

    // Get mouse position relative to canvas
    getMousePosition() {
        return { ...this.lastMousePosition };
    }

    // Get model position
    getModelPosition() {
        if (!this.model) return { x: 0, y: 0 };
        return {
            x: this.model.position.x,
            y: this.model.position.y
        };
    }

    // Get model bounds
    getModelBounds() {
        if (!this.model) return null;
        return this.model.getBounds();
    }

    // Check if model is within canvas bounds
    isModelOnScreen() {
        if (!this.model || !this.app) return false;
        
        const bounds = this.model.getBounds();
        const canvasWidth = this.app.renderer.width;
        const canvasHeight = this.app.renderer.height;
        
        return bounds.x < canvasWidth && 
               bounds.x + bounds.width > 0 && 
               bounds.y < canvasHeight && 
               bounds.y + bounds.height > 0;
    }

    // Check hit areas (placeholder implementation)
    checkHitAreas(globalPosition) {
        if (!this.model || !this.model.internalModel) {
            return [];
        }

        // Convert global position to model local coordinates
        const localPoint = this.model.toLocal(globalPosition);
        
        try {
            // Try to use Live2D hit testing if available
            if (this.model.internalModel.hitTest) {
                return this.model.internalModel.hitTest(localPoint.x, localPoint.y) || [];
            }
        } catch (error) {
            console.warn('Hit test failed:', error);
        }
        
        return [];
    }

    // Trigger motion (placeholder implementation)
    triggerMotion(motionName, description = '') {
        if (!this.model || !this.model.motion) {
            console.log('Cannot trigger motion - no model or motion system available');
            return;
        }

        try {
            console.log(`Triggering motion: ${motionName} (${description})`);
            this.model.motion(motionName);
        } catch (error) {
            console.warn(`Failed to trigger motion ${motionName}:`, error);
        }
    }

    // Cleanup
    destroy() {
        // Remove event listeners
        this.removeModelInteraction();
        
        // Clear visualizations
        this.clearVisualizations();
        
        // Reset state
        this.app = null;
        this.model = null;
        this.isDragging = false;
        
        this.logger.logInfo('Interaction manager destroyed');
    }
}

// Export for modular use
window.Live2DInteraction = Live2DInteraction;
