// Live2D Canvas Management Module
// Handles all canvas manipulation: dragging, clicking, frame toggles, zoom

class Live2DCanvas {
    constructor(core, logger) {
        this.core = core;
        this.logger = logger;
        this.app = null;
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

    // Initialize the canvas manager with PIXI app and model
    initialize(app, model) {
        this.app = app;
        this.model = model;
        
        if (this.model) {
            this.setupModelInteraction();
        }
        
        this.log('Canvas manager initialized', 'info');
        return true;
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
        
        // Make model interactive
        this.model.interactive = true;
        this.model.eventMode = 'static';
        
        // Add event listeners
        this.model.on('pointerdown', this.mouseHandlers.onPointerDown);
        this.model.on('pointermove', this.mouseHandlers.onPointerMove);
        this.model.on('pointerup', this.mouseHandlers.onPointerUp);
        this.model.on('pointerupoutside', this.mouseHandlers.onPointerUpOutside);
        
        // Add wheel event to canvas for zoom
        const canvas = this.app.canvas || this.app.view;
        if (canvas) {
            canvas.addEventListener('wheel', this.mouseHandlers.onWheel, { passive: false });
        }
        
        this.log('Model interaction set up', 'info');
    }

    // Remove interaction from the model
    removeModelInteraction() {
        if (!this.model) return;
        
        this.model.off('pointerdown', this.mouseHandlers.onPointerDown);
        this.model.off('pointermove', this.mouseHandlers.onPointerMove);
        this.model.off('pointerup', this.mouseHandlers.onPointerUp);
        this.model.off('pointerupoutside', this.mouseHandlers.onPointerUpOutside);
        
        // Remove wheel event - check multiple possible canvas references
        let canvas = null;
        if (this.app && this.app.canvas) {
            canvas = this.app.canvas;
        } else if (this.app && this.app.view) {
            canvas = this.app.view;
        } else if (this.app && this.app.renderer && this.app.renderer.view) {
            canvas = this.app.renderer.view;
        }
        
        if (canvas) {
            canvas.removeEventListener('wheel', this.mouseHandlers.onWheel);
        }
        
        this.log('Model interaction removed', 'info');
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
        
        this.log('Visualizations cleared', 'info');
    }

    // Update the model reference
    updateModel(model) {
        // Remove old interaction
        this.removeModelInteraction();
        
        // Clear visualizations
        this.clearVisualizations();
        
        // Set new model
        this.model = model;
        
        // Set up new interaction
        if (this.model) {
            this.setupModelInteraction();
        }
        
        this.log('Model updated in canvas manager', 'info');
    }

    // Pointer down handler
    onPointerDown(event) {
        if (!this.model) return;
        
        this.isDragging = true;
        this.dragOffset.x = event.data.global.x - this.model.x;
        this.dragOffset.y = event.data.global.y - this.model.y;
        
        // Visual feedback
        this.model.alpha = 0.8;
        
        // Get local click position for hit testing
        const localPoint = this.model.toLocal(event.data.global);
        
        // Check for hit areas
        this.checkHitAreas(localPoint);
        
        this.log('Drag started', 'info');
    }

    // Pointer move handler
    onPointerMove(event) {
        if (!this.model) return;
        
        if (this.isDragging) {
            // Update model position
            this.model.position.x = event.data.global.x - this.dragOffset.x;
            this.model.position.y = event.data.global.y - this.dragOffset.y;
            
            // Update frame visualizations if visible
            this.updateFrameVisualizations();
        }
    }

    // Pointer up handler
    onPointerUp(event) {
        if (!this.model || !this.isDragging) return;
        
        this.isDragging = false;
        this.model.alpha = 1.0; // Restore opacity
        
        this.log(`Model positioned at: ${this.model.position.x.toFixed(0)}, ${this.model.position.y.toFixed(0)}`, 'info');
    }

    // Pointer up outside handler
    onPointerUpOutside(event) {
        this.onPointerUp(event);
    }

    // Wheel handler for zoom
    onWheel(event) {
        event.preventDefault();
        
        const delta = event.deltaY > 0 ? -this.zoomStep : this.zoomStep;
        const newZoom = Math.max(this.minZoom, Math.min(this.maxZoom, this.currentZoom + delta));
        
        this.setZoom(newZoom);
    }

    // Check for hit areas at the given local point
    checkHitAreas(localPoint) {
        if (!this.model) return;
        
        // Check if model has hit test capability
        if (this.model.hitTest && typeof this.model.hitTest === 'function') {
            const hitAreas = this.model.hitTest(localPoint.x, localPoint.y);
            if (hitAreas && hitAreas.length > 0) {
                this.log(`Hit areas clicked: ${hitAreas.join(', ')}`, 'info');
                return hitAreas;
            }
        }
        
        this.log(`Model clicked at: ${localPoint.x.toFixed(0)}, ${localPoint.y.toFixed(0)}`, 'info');
        return [];
    }

    // Zoom functionality
    setZoom(zoomLevel) {
        if (!this.model) return;
        
        const clampedZoom = Math.max(this.minZoom, Math.min(this.maxZoom, zoomLevel));
        this.currentZoom = clampedZoom;
        
        // Apply zoom as scale
        this.model.scale.set(clampedZoom);
        
        // Update frame visualizations
        this.updateFrameVisualizations();
        
        this.log(`Zoom set to: ${clampedZoom.toFixed(1)}`, 'info');
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
        
        this.log(`Model centered at: ${centerX.toFixed(0)}, ${centerY.toFixed(0)}`, 'info');
    }

    // Fit model to canvas
    fitModelToCanvas() {
        if (!this.model || !this.app) return;
        
        // Reset zoom first
        this.resetZoom();
        
        // Center the model
        this.centerModel();
        
        this.log('Model fitted to canvas', 'info');
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
            this.log('Canvas frame shown', 'info');
        } else {
            canvas.style.border = 'none';
            canvas.style.boxShadow = 'none';
            this.log('Canvas frame hidden', 'info');
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
        
        this.log('Model frame shown', 'info');
    }

    // Hide model frame visualization
    hideModelFrameVisualization() {
        if (this.modelFrameGraphics) {
            this.modelFrameGraphics.visible = false;
        }
        
        this.log('Model frame hidden', 'info');
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
            this.log('No hit areas defined for this model', 'warning');
            return;
        }
        
        // Create graphics if not exists
        if (!this.hitAreaGraphics) {
            this.hitAreaGraphics = new PIXI.Graphics();
            this.app.stage.addChild(this.hitAreaGraphics);
        }
        
        this.drawHitAreas();
        this.hitAreaGraphics.visible = true;
        
        this.log('Hit areas shown', 'info');
    }

    // Hide hit areas visualization
    hideHitAreasVisualization() {
        if (this.hitAreaGraphics) {
            this.hitAreaGraphics.visible = false;
        }
        
        this.log('Hit areas hidden', 'info');
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

    // Update frame visualizations
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

    // Logging helper
    log(message, type = 'info') {
        if (this.logger) {
            this.logger.log(`[Canvas] ${message}`, type);
        } else {
            console.log(`[Canvas ${type.toUpperCase()}] ${message}`);
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
        
        this.log('Canvas manager destroyed', 'info');
    }
}

// Export for use in other modules
window.Live2DCanvas = Live2DCanvas;
