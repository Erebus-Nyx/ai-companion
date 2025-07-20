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
        this.minZoom = 0.1;
        this.maxZoom = 3.0;
        this.zoomStep = 0.1;
        
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

    // Initialize the canvas manager - no model needed at this stage
    initialize() {
        this.logger.logInfo('Interaction manager initialized');
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
        if (!this.model || !this.app) return;
        
        console.log('Setting up model interaction for:', this.model);
        
        // Make model interactive
        this.model.interactive = true;
        this.model.eventMode = 'static';
        
        // Add event listeners
        this.model.off('pointerdown', this.mouseHandlers.onPointerDown)
                  .on('pointerdown', this.mouseHandlers.onPointerDown);
        this.app.stage.off('pointermove', this.mouseHandlers.onPointerMove)
                      .on('pointermove', this.mouseHandlers.onPointerMove);
        this.app.stage.off('pointerup', this.mouseHandlers.onPointerUp)
                      .on('pointerup', this.mouseHandlers.onPointerUp);
        this.app.stage.off('pointerupoutside', this.mouseHandlers.onPointerUpOutside)
                      .on('pointerupoutside', this.mouseHandlers.onPointerUpOutside);
        
        // Add wheel event to canvas for zoom
        const canvas = this.app.canvas || this.app.view;
        if (canvas) {
            console.log('Adding wheel event to canvas');
            canvas.removeEventListener('wheel', this.mouseHandlers.onWheel);
            canvas.addEventListener('wheel', this.mouseHandlers.onWheel, { passive: false });
        } else {
            console.error('Canvas not found for wheel events');
        }
        
        this.logger.logInfo('Model interaction set up');
    }

    // Remove interaction from the model
    removeModelInteraction() {
        if (!this.model) return;
        
        this.model.off('pointerdown', this.mouseHandlers.onPointerDown);
        
        if (this.app) {
            this.app.stage.off('pointermove', this.mouseHandlers.onPointerMove);
            this.app.stage.off('pointerup', this.mouseHandlers.onPointerUp);
            this.app.stage.off('pointerupoutside', this.mouseHandlers.onPointerUpOutside);
        }
        
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

    // Pointer down handler
    onPointerDown(event) {
        console.log('Pointer down event triggered');
        if (!this.model) return;
        
        // Check for hit areas first
        const hitAreas = this.checkHitAreas(event.data.global);
        if (hitAreas.length > 0) {
            // If hit area is clicked, don't start drag
            return;
        }
        
        this.isDragging = true;
        this.dragOffset.x = event.data.global.x - this.model.x;
        this.dragOffset.y = event.data.global.y - this.model.y;
        
        // Visual feedback
        this.model.alpha = 0.8;
        
        this.logger.logInfo('Drag started');
    }

    // Pointer move handler
    onPointerMove(event) {
        if (!this.model || !this.isDragging) return;
        
        // Update model position
        let newX = event.data.global.x - this.dragOffset.x;
        let newY = event.data.global.y - this.dragOffset.y;
        
        // Boundary constraints
        const bounds = this.model.getBounds();
        const canvasWidth = this.app.renderer.width;
        const canvasHeight = this.app.renderer.height;
        
        // Prevent dragging completely off-screen
        if (bounds.width > canvasWidth) {
            newX = Math.max(newX, canvasWidth - bounds.width);
            newX = Math.min(newX, 0);
        } else {
            newX = Math.max(newX, 0);
            newX = Math.min(newX, canvasWidth - bounds.width);
        }
        
        if (bounds.height > canvasHeight) {
            newY = Math.max(newY, canvasHeight - bounds.height);
            newY = Math.min(newY, 0);
        } else {
            newY = Math.max(newY, 0);
            newY = Math.min(newY, canvasHeight - bounds.height);
        }
        
        this.model.position.set(newX, newY);
        
        // Update frame visualizations if visible
        this.updateFrameVisualizations();
    }

    // Pointer up handler
    onPointerUp(event) {
        if (!this.model || !this.isDragging) return;
        
        this.isDragging = false;
        this.model.alpha = 1.0; // Restore opacity
        
        this.logger.logInfo('Drag ended');
    }

    // Pointer up outside handler
    onPointerUpOutside(event) {
        if (!this.model || !this.isDragging) return;
        
        this.isDragging = false;
        this.model.alpha = 1.0;
        
        this.logger.logInfo('Drag ended (outside)');
    }

    // Mouse wheel handler for zoom
    onWheel(event) {
        console.log('Wheel event triggered:', event.deltaY);
        event.preventDefault();
        
        const delta = -Math.sign(event.deltaY);
        this.setZoom(this.currentZoom + delta * this.zoomStep);
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
