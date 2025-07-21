/**
 * Drawing System - Canvas Drawing and Art Tools
 * Handles drawing functionality, tools, and canvas management
 */

class DrawingSystem {
    constructor() {
        this.drawingState = {
            isDrawing: false,
            currentTool: 'pen',
            currentColor: '#000000',
            brushSize: 5,
            opacity: 1.0,
            drawingCanvas: null,
            drawingContext: null,
            layers: ['Background']
        };
        
        this.initializeDrawingSystem();
    }
    
    initializeDrawingSystem() {
        console.log('Initializing drawing system...');
        this.updateBrushSizeDisplay();
        this.updateOpacityDisplay();
        this.updateLayerList();
    }
    
    // Panel management
    openDrawing() {
        console.log('Opening drawing panel...');
        const panel = document.getElementById('drawingPanel');
        if (panel) {
            panel.classList.add('open');
            this.initializeDrawingCanvas();
        }
    }
    
    closeDrawing() {
        const panel = document.getElementById('drawingPanel');
        if (panel) {
            panel.classList.remove('open');
        }
    }
    
    toggleDrawingSnap() {
        const panel = document.getElementById('drawingPanel');
        if (panel) {
            if (panel.classList.contains('snapped-left')) {
                panel.classList.remove('snapped-left');
                panel.classList.add('snapped-right');
            } else {
                panel.classList.remove('snapped-right');
                panel.classList.add('snapped-left');
            }
        }
    }
    
    // Canvas initialization
    initializeDrawingCanvas() {
        console.log('Initializing drawing canvas...');
        
        // Create canvas element if it doesn't exist
        let canvas = document.getElementById('drawingCanvas');
        if (!canvas) {
            canvas = document.createElement('canvas');
            canvas.id = 'drawingCanvas';
            canvas.width = 800;
            canvas.height = 600;
            canvas.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                border: 1px solid #ccc;
                background: white;
                cursor: crosshair;
            `;
            
            const canvasContainer = document.getElementById('drawingCanvasContainer');
            if (canvasContainer) {
                canvasContainer.appendChild(canvas);
            }
        }
        
        this.drawingState.drawingCanvas = canvas;
        this.drawingState.drawingContext = canvas.getContext('2d');
        
        // Set up canvas event listeners
        this.setupCanvasEvents();
        
        console.log('Drawing canvas initialized');
    }
    
    setupCanvasEvents() {
        const canvas = this.drawingState.drawingCanvas;
        if (!canvas) return;
        
        let isDrawing = false;
        let lastX = 0;
        let lastY = 0;
        
        canvas.addEventListener('mousedown', (e) => {
            isDrawing = true;
            [lastX, lastY] = [e.offsetX, e.offsetY];
            this.drawingState.isDrawing = true;
        });
        
        canvas.addEventListener('mousemove', (e) => {
            if (!isDrawing) return;
            this.draw(lastX, lastY, e.offsetX, e.offsetY);
            [lastX, lastY] = [e.offsetX, e.offsetY];
        });
        
        canvas.addEventListener('mouseup', () => {
            isDrawing = false;
            this.drawingState.isDrawing = false;
        });
        
        canvas.addEventListener('mouseout', () => {
            isDrawing = false;
            this.drawingState.isDrawing = false;
        });
    }
    
    draw(x1, y1, x2, y2) {
        const ctx = this.drawingState.drawingContext;
        if (!ctx) return;
        
        ctx.globalAlpha = this.drawingState.opacity;
        ctx.strokeStyle = this.drawingState.currentColor;
        ctx.lineWidth = this.drawingState.brushSize;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
    }
    
    // Tool selection
    selectTool(tool, event = null) {
        this.drawingState.currentTool = tool;
        
        // Update active tool button
        document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
        if (event && event.target) {
            event.target.classList.add('active');
        }
        
        console.log('Selected tool:', tool);
        
        // Update cursor based on tool
        const canvas = this.drawingState.drawingCanvas;
        if (canvas) {
            switch (tool) {
                case 'pen':
                    canvas.style.cursor = 'crosshair';
                    break;
                case 'eraser':
                    canvas.style.cursor = 'grab';
                    break;
                case 'brush':
                    canvas.style.cursor = 'crosshair';
                    break;
                default:
                    canvas.style.cursor = 'default';
            }
        }
    }
    
    // Color and brush controls
    updateDrawingColor() {
        const colorInput = document.getElementById('drawingColor');
        if (colorInput) {
            this.drawingState.currentColor = colorInput.value;
            console.log('Drawing color updated to:', this.drawingState.currentColor);
        }
    }
    
    updateBrushSize() {
        const sizeInput = document.getElementById('brushSize');
        if (sizeInput) {
            this.drawingState.brushSize = parseInt(sizeInput.value);
            this.updateBrushSizeDisplay();
            console.log('Brush size updated to:', this.drawingState.brushSize);
        }
    }
    
    updateBrushSizeDisplay() {
        const display = document.getElementById('brushSizeValue');
        if (display) {
            display.textContent = `${this.drawingState.brushSize}px`;
        }
    }
    
    updateOpacity() {
        const opacityInput = document.getElementById('opacity');
        if (opacityInput) {
            this.drawingState.opacity = parseInt(opacityInput.value) / 100;
            this.updateOpacityDisplay();
            console.log('Opacity updated to:', this.drawingState.opacity);
        }
    }
    
    updateOpacityDisplay() {
        const display = document.getElementById('opacityValue');
        if (display) {
            display.textContent = `${Math.round(this.drawingState.opacity * 100)}%`;
        }
    }
    
    // Canvas control functions
    clearCanvas() {
        if (confirm('Are you sure you want to clear the canvas? This action cannot be undone.')) {
            const ctx = this.drawingState.drawingContext;
            if (ctx && this.drawingState.drawingCanvas) {
                ctx.clearRect(0, 0, this.drawingState.drawingCanvas.width, this.drawingState.drawingCanvas.height);
                console.log('Canvas cleared');
            }
        }
    }
    
    saveDrawing() {
        const canvas = this.drawingState.drawingCanvas;
        if (!canvas) {
            alert('No drawing to save!');
            return;
        }
        
        try {
            // Create download link
            const link = document.createElement('a');
            link.download = `drawing_${new Date().getTime()}.png`;
            link.href = canvas.toDataURL();
            
            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            console.log('Drawing saved successfully');
        } catch (error) {
            console.error('Failed to save drawing:', error);
            alert('Failed to save drawing. Please try again.');
        }
    }
    
    loadDrawing() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = (event) => {
                const img = new Image();
                img.onload = () => {
                    const ctx = this.drawingState.drawingContext;
                    const canvas = this.drawingState.drawingCanvas;
                    
                    if (ctx && canvas) {
                        // Clear canvas first
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        
                        // Draw loaded image
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        console.log('Image loaded into canvas');
                    }
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
        };
        
        input.click();
    }
    
    // Layer management
    addNewLayer() {
        const layerName = prompt('Enter layer name:', `Layer ${this.drawingState.layers.length + 1}`);
        if (layerName) {
            this.drawingState.layers.push(layerName);
            this.updateLayerList();
            console.log('Added new layer:', layerName);
        }
    }
    
    deleteLayer() {
        if (this.drawingState.layers.length <= 1) {
            alert('Cannot delete the last layer!');
            return;
        }
        
        const activeLayer = document.querySelector('.layer-item.active');
        if (activeLayer && confirm('Are you sure you want to delete this layer?')) {
            const layerIndex = parseInt(activeLayer.dataset.layer);
            this.drawingState.layers.splice(layerIndex, 1);
            this.updateLayerList();
            console.log('Deleted layer at index:', layerIndex);
        }
    }
    
    toggleLayerVisibility(layerIndex) {
        console.log('Toggling visibility for layer:', layerIndex);
        // Implementation for layer visibility toggle
        const layerItem = document.querySelector(`[data-layer="${layerIndex}"]`);
        if (layerItem) {
            layerItem.classList.toggle('hidden');
        }
    }
    
    updateLayerList() {
        const layerList = document.getElementById('layerList');
        if (!layerList) return;
        
        layerList.innerHTML = '';
        this.drawingState.layers.forEach((layerName, index) => {
            const layerItem = document.createElement('div');
            layerItem.className = 'layer-item';
            if (index === 0) layerItem.classList.add('active');
            layerItem.dataset.layer = index;
            
            layerItem.innerHTML = `
                <span>${layerName}</span>
                <button onclick="drawingSystem.toggleLayerVisibility(${index})" title="Toggle Visibility">👁️</button>
            `;
            
            layerItem.addEventListener('click', (e) => {
                if (e.target.tagName !== 'BUTTON') {
                    document.querySelectorAll('.layer-item').forEach(item => item.classList.remove('active'));
                    layerItem.classList.add('active');
                }
            });
            
            layerList.appendChild(layerItem);
        });
    }
    
    // Export functions for integration
    getDrawingData() {
        const canvas = this.drawingState.drawingCanvas;
        if (canvas) {
            return canvas.toDataURL();
        }
        return null;
    }
    
    setDrawingData(dataUrl) {
        if (!dataUrl || !this.drawingState.drawingContext) return;
        
        const img = new Image();
        img.onload = () => {
            const ctx = this.drawingState.drawingContext;
            const canvas = this.drawingState.drawingCanvas;
            
            if (ctx && canvas) {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);
            }
        };
        img.src = dataUrl;
    }
}

// Global instance
let drawingSystem = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    drawingSystem = new DrawingSystem();
    window.drawingSystem = drawingSystem;
});

// Legacy function compatibility
window.openDrawing = () => drawingSystem?.openDrawing();
window.closeDrawing = () => drawingSystem?.closeDrawing();
window.toggleDrawingSnap = () => drawingSystem?.toggleDrawingSnap();
window.selectTool = (tool) => drawingSystem?.selectTool(tool, event);
window.updateDrawingColor = () => drawingSystem?.updateDrawingColor();
window.updateBrushSize = () => drawingSystem?.updateBrushSize();
window.updateOpacity = () => drawingSystem?.updateOpacity();
window.clearCanvas = () => drawingSystem?.clearCanvas();
window.saveDrawing = () => drawingSystem?.saveDrawing();
window.loadDrawing = () => drawingSystem?.loadDrawing();
window.addNewLayer = () => drawingSystem?.addNewLayer();
window.deleteLayer = () => drawingSystem?.deleteLayer();
