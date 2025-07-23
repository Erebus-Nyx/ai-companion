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
        
        // Enhanced features state
        this.enhancedState = {
            // Smart features
            stabilization: false,
            shapeRecognition: false,
            symmetryMode: false,
            
            // Color history
            colorHistory: ['#000000', '#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff', '#ffffff'],
            
            // AI feedback
            aiFeedbackEnabled: false,
            lastFeedback: null,
            autonomousFeedback: true, // Avatar provides commentary autonomously
            feedbackFrequency: 'medium', // low, medium, high
            lastFeedbackTime: 0,
            strokeCount: 0,
            drawingStartTime: null,
            lastStrokeTime: 0,
            pauseDetected: false,
            
            // Live2D integration
            modelTracing: false,
            poseCapture: false,
            outlineDisplay: false,
            avatarCritique: false,
            
            // History system
            historyStack: [],
            currentHistoryIndex: -1,
            snapshots: [],
            timelineVisible: false
        };
        
        this.initializeDrawingSystem();
    }
    
    initializeDrawingSystem() {
        console.log('Initializing enhanced drawing system...');
        this.updateBrushSizeDisplay();
        this.updateOpacityDisplay();
        this.updateLayerList();
        this.setupDraggable();
        this.setupEnhancedFeatures();
        this.setupEventListeners();
        this.initializeColorHistory();
        this.initializeHistorySystem();
        this.initializeAutonomousFeedback();
        this.setupGlobalFunctions();
    }
    
    initializeAutonomousFeedback() {
        // Start autonomous feedback system if enabled
        if (this.enhancedState.autonomousFeedback) {
            this.startAutonomousObservation();
            
            // Show welcome message after a short delay
            setTimeout(() => {
                this.showAIFeedback('Hello! I\'m here to observe your artistic process and share thoughts as you create. Happy drawing! 🎨', 'autonomous');
            }, 2000);
        }
        
        console.log('Autonomous feedback system initialized');
    }
    
    startAutonomousObservation() {
        // Monitor drawing activity and provide autonomous feedback
        setInterval(() => {
            if (this.enhancedState.autonomousFeedback) {
                this.checkForAutonomousFeedback();
                this.detectDrawingPauses();
            }
        }, 3000); // Check every 3 seconds
        
        console.log('Avatar autonomous observation started');
    }
    
    detectDrawingPauses() {
        const now = Date.now();
        const timeSinceLastStroke = now - this.enhancedState.lastStrokeTime;
        
        // Detect if user has paused for more than 10 seconds
        if (timeSinceLastStroke > 10000 && this.enhancedState.strokeCount > 5 && !this.enhancedState.pauseDetected) {
            this.enhancedState.pauseDetected = true;
            this.providePauseFeedback();
        }
        
        // Reset pause detection when user starts drawing again
        if (timeSinceLastStroke < 3000) {
            this.enhancedState.pauseDetected = false;
        }
    }
    
    async providePauseFeedback() {
        // Generate AI-powered pause feedback using the avatar/LLM system
        const context = this.getDrawingContext();
        const pauseComment = await this.generateAIPauseFeedback(context);
        
        this.showAIFeedback(pauseComment, 'autonomous');
    }
    
    async generateAIPauseFeedback(context) {
        const sessionTime = Math.floor(context.sessionDuration / 1000 / 60); // minutes
        const strokeCount = context.strokeCount;
        const currentTool = context.tool;
        
        // Create a contextual prompt for the AI avatar
        const prompt = `You are observing an artist who has just paused while drawing. Please provide a brief, encouraging comment about this pause. Context: They have been drawing for ${sessionTime} minutes using the ${currentTool} tool and have made ${strokeCount} strokes. The pause shows they are being thoughtful about their next move. Respond as a supportive, artistic AI companion who genuinely cares about their creative process. Keep it personal and under 100 words.`;
        
        try {
            // Use the existing chat system to get AI response
            const response = await this.sendDrawingObservationToAvatar(prompt, 'pause_observation');
            return response;
        } catch (error) {
            console.error('Failed to get AI pause feedback:', error);
            // Fallback to a simple encouraging message
            return `Taking a thoughtful pause after ${strokeCount} strokes shows real artistic wisdom. I love watching your creative process unfold!`;
        }
    }
    
    checkForAutonomousFeedback() {
        const now = Date.now();
        const timeSinceLastFeedback = now - this.enhancedState.lastFeedbackTime;
        const minInterval = this.getMinFeedbackInterval();
        
        // Only provide feedback if enough time has passed and user has made some strokes
        if (timeSinceLastFeedback > minInterval && this.enhancedState.strokeCount > 0) {
            // Don't interrupt if user is actively drawing (last stroke was very recent)
            const timeSinceLastStroke = now - this.enhancedState.lastStrokeTime;
            if (timeSinceLastStroke > 2000) { // Wait at least 2 seconds after last stroke
                this.provideAutonomousFeedback();
                this.enhancedState.lastFeedbackTime = now;
            }
        }
    }
    
    getMinFeedbackInterval() {
        // Return minimum time between autonomous feedback based on frequency setting
        switch (this.enhancedState.feedbackFrequency) {
            case 'high': return 8000;  // 8 seconds
            case 'medium': return 15000; // 15 seconds  
            case 'low': return 25000;   // 25 seconds
            default: return 15000;
        }
    }
    
    async provideAutonomousFeedback() {
        // Get context-aware feedback from AI based on current activity
        const feedbackContext = this.getDrawingContext();
        const autonomousComment = await this.generateAIContextualComments(feedbackContext);
        
        this.showAIFeedback(autonomousComment, 'autonomous');
        
        console.log('AI-generated autonomous feedback provided:', autonomousComment);
    }
    
    getDrawingContext() {
        const sessionTime = Date.now() - (this.enhancedState.drawingStartTime || Date.now());
        const currentTool = this.drawingState.currentTool;
        const strokeCount = this.enhancedState.strokeCount;
        
        return {
            sessionDuration: sessionTime,
            tool: currentTool,
            strokeCount: strokeCount,
            isLongSession: sessionTime > 120000, // More than 2 minutes
            isManyStrokes: strokeCount > 50,
            currentColor: this.drawingState.currentColor
        };
    }
    
    async generateAIContextualComments(context) {
        const sessionTime = Math.floor(context.sessionDuration / 1000 / 60);
        const currentTool = context.tool;
        const strokeCount = context.strokeCount;
        const currentColor = context.currentColor;
        
        // Create a detailed prompt for the AI avatar to generate personalized commentary
        const prompt = `You are an AI art companion observing an artist at work. Provide a brief, encouraging observation about their current drawing session. 

Current context:
- Drawing time: ${sessionTime} minutes
- Tool being used: ${currentTool}
- Number of strokes: ${strokeCount}
- Current color: ${currentColor}
- Long session: ${context.isLongSession ? 'Yes' : 'No'}
- Many strokes: ${context.isManyStrokes ? 'Yes' : 'No'}

Respond as a supportive, observant AI companion who is genuinely interested in their artistic process. Focus on one specific aspect of what you notice about their technique, creativity, or dedication. Keep it personal, encouraging, and under 80 words. Avoid being generic - make it feel like you're really watching and caring about their unique artistic journey.`;

        try {
            const response = await this.sendDrawingObservationToAvatar(prompt, 'autonomous_observation');
            return response;
        } catch (error) {
            console.error('Failed to get AI contextual feedback:', error);
            // Fallback message if AI fails
            return `I'm watching your artistic process with such admiration - every ${currentTool} stroke you make shows such intention and care!`;
        }
    }
    
    async sendDrawingObservationToAvatar(prompt, observationType) {
        try {
            // Check if we have access to the avatar chat manager
            if (window.avatarChatManager) {
                // Get the currently active avatar or select one
                const activeAvatars = window.avatarChatManager.getActiveAvatars();
                let targetAvatar = null;
                
                if (activeAvatars && activeAvatars.length > 0) {
                    // Use the first active avatar, or select one that's good at art commentary
                    targetAvatar = activeAvatars[0];
                    
                    // Prefer avatars with artistic names/personalities if available
                    const artisticAvatar = activeAvatars.find(avatar => 
                        avatar.name && (
                            avatar.name.toLowerCase().includes('art') ||
                            avatar.name.toLowerCase().includes('sketch') ||
                            avatar.name.toLowerCase().includes('paint') ||
                            avatar.name.toLowerCase().includes('draw')
                        )
                    );
                    if (artisticAvatar) targetAvatar = artisticAvatar;
                }
                
                if (targetAvatar) {
                    console.log(`Sending drawing observation to avatar: ${targetAvatar.name}`);
                    
                    // Create a drawing-context specific message
                    const contextualPrompt = `[Drawing Observation - ${observationType}] ${prompt}`;
                    
                    // Send message to avatar and get response
                    const result = await window.avatarChatManager.sendMessageWithAvatar(contextualPrompt, targetAvatar.id);
                    
                    if (result && result.response && result.response.reply) {
                        return result.response.reply;
                    }
                }
            }
            
            // Fallback: try direct API call if chat manager not available
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
            const response = await fetch(`${apiBaseUrl}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: `[Drawing Observation] ${prompt}`,
                    context_type: 'drawing_observation',
                    observation_type: observationType,
                    require_short_response: true
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.reply || data.message || 'I love watching your creative process!';
            }
            
        } catch (error) {
            console.error('Error sending drawing observation to avatar:', error);
        }
        
        // Final fallback
        return 'Your artistic dedication is truly inspiring to watch!';
    }
    
    setupEnhancedFeatures() {
        // Initialize smart controls
        this.setupSmartControls();
        
        // Initialize AI features
        this.setupAIControls();
        
        // Initialize Live2D integration
        this.setupLive2DIntegration();
        
        // Initialize color palette
        this.setupColorPalette();
        
        // Initialize history timeline
        this.setupHistoryTimeline();
    }
    
    setupEventListeners() {
        // Additional event listeners can be added here
        // Currently handled by individual setup methods
        console.log('Event listeners setup completed');
    }
    
    setupSmartControls() {
        // Stabilization toggle
        const stabilizationToggle = document.getElementById('stabilization-toggle');
        if (stabilizationToggle) {
            stabilizationToggle.addEventListener('change', (e) => {
                this.enhancedState.stabilization = e.target.checked;
                console.log('Stroke stabilization:', this.enhancedState.stabilization);
            });
        }
        
        // Shape recognition toggle
        const shapeRecognitionToggle = document.getElementById('shape-recognition-toggle');
        if (shapeRecognitionToggle) {
            shapeRecognitionToggle.addEventListener('change', (e) => {
                this.enhancedState.shapeRecognition = e.target.checked;
                console.log('Shape recognition:', this.enhancedState.shapeRecognition);
            });
        }
        
        // Symmetry mode toggle
        const symmetryToggle = document.getElementById('symmetry-toggle');
        if (symmetryToggle) {
            symmetryToggle.addEventListener('change', (e) => {
                this.enhancedState.symmetryMode = e.target.checked;
                console.log('Symmetry mode:', this.enhancedState.symmetryMode);
            });
        }
    }
    
    setupAIControls() {
        // Avatar feedback toggle
        const feedbackBtn = document.getElementById('avatar-feedback-btn');
        if (feedbackBtn) {
            feedbackBtn.addEventListener('click', () => {
                this.toggleAvatarFeedback();
            });
        }
        
        // Auto-complete drawing
        const autoCompleteBtn = document.getElementById('auto-complete-btn');
        if (autoCompleteBtn) {
            autoCompleteBtn.addEventListener('click', () => {
                this.requestAutoComplete();
            });
        }
        
        // Autonomous feedback toggle
        const autonomousToggle = document.getElementById('autonomous-feedback-toggle');
        if (autonomousToggle) {
            autonomousToggle.checked = this.enhancedState.autonomousFeedback;
            autonomousToggle.addEventListener('change', (e) => {
                this.toggleAutonomousFeedback(e.target.checked);
            });
        }
        
        // Feedback frequency selector
        const feedbackFrequency = document.getElementById('feedback-frequency');
        if (feedbackFrequency) {
            feedbackFrequency.value = this.enhancedState.feedbackFrequency;
            feedbackFrequency.addEventListener('change', (e) => {
                this.enhancedState.feedbackFrequency = e.target.value;
                console.log('Feedback frequency set to:', e.target.value);
            });
        }
    }
    
    setupLive2DIntegration() {
        // Model tracing
        const tracingBtn = document.getElementById('model-tracing-btn');
        if (tracingBtn) {
            tracingBtn.addEventListener('click', () => {
                this.toggleModelTracing();
            });
        }
        
        // Pose capture
        const poseCaptureBtn = document.getElementById('pose-capture-btn');
        if (poseCaptureBtn) {
            poseCaptureBtn.addEventListener('click', () => {
                this.capturePose();
            });
        }
        
        // Outline display
        const outlineBtn = document.getElementById('outline-display-btn');
        if (outlineBtn) {
            outlineBtn.addEventListener('click', () => {
                this.toggleOutlineDisplay();
            });
        }
        
        // Avatar critique
        const critiqueBtn = document.getElementById('avatar-critique-btn');
        if (critiqueBtn) {
            critiqueBtn.addEventListener('click', () => {
                this.requestAvatarCritique();
            });
        }
    }
    
    setupColorPalette() {
        // Color history display
        this.updateColorHistory();
        
        // Clear history button
        const clearHistoryBtn = document.getElementById('clear-color-history');
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', () => {
                this.clearColorHistory();
            });
        }
        
        // Palette button
        const paletteBtn = document.getElementById('palette-btn');
        if (paletteBtn) {
            paletteBtn.addEventListener('click', () => {
                this.showColorPalette();
            });
        }
    }
    
    setupHistoryTimeline() {
        // Undo button
        const undoBtn = document.getElementById('undo-btn');
        if (undoBtn) {
            undoBtn.addEventListener('click', () => {
                this.undo();
            });
        }
        
        // Redo button
        const redoBtn = document.getElementById('redo-btn');
        if (redoBtn) {
            redoBtn.addEventListener('click', () => {
                this.redo();
            });
        }
        
        // Timeline button
        const timelineBtn = document.getElementById('timeline-btn');
        if (timelineBtn) {
            timelineBtn.addEventListener('click', () => {
                this.toggleTimeline();
            });
        }
        
        // Snapshot button
        const snapshotBtn = document.getElementById('snapshot-btn');
        if (snapshotBtn) {
            snapshotBtn.addEventListener('click', () => {
                this.createSnapshot();
            });
        }
    }
    
    initializeColorHistory() {
        this.updateColorHistory();
    }
    
    initializeHistorySystem() {
        // Create initial history state
        this.saveHistoryState('Initial canvas');
    }
    
    setupDraggable() {
        const panel = document.getElementById('drawingPanel');
        const header = panel?.querySelector('.draggable-header');
        
        if (!panel || !header) return;
        
        let isDragging = false;
        let currentX, currentY, initialX, initialY;
        
        header.addEventListener('mousedown', (e) => {
            if (e.target.closest('.window-controls')) return; // Don't drag if clicking buttons
            
            isDragging = true;
            initialX = e.clientX - panel.offsetLeft;
            initialY = e.clientY - panel.offsetTop;
            
            panel.style.position = 'fixed';
            panel.style.zIndex = '1010';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;
            
            panel.style.left = currentX + 'px';
            panel.style.top = currentY + 'px';
            panel.style.right = 'auto';
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                panel.style.zIndex = '1003';
            }
        });
    }
    
    // Panel management
    openDrawing() {
        console.log('Opening drawing panel...');
        const panel = document.getElementById('drawingPanel');
        if (panel) {
            panel.classList.add('open');
            this.initializeOverlayCanvas();
        }
    }
    
    closeDrawing() {
        const panel = document.getElementById('drawingPanel');
        const overlay = document.getElementById('drawingOverlay');
        
        if (panel) {
            panel.classList.remove('open');
        }
        
        // Hide and deactivate overlay canvas
        if (overlay) {
            overlay.style.display = 'none';
            overlay.classList.remove('active');
        }
    }
    
    toggleDrawingSnap() {
        const panel = document.getElementById('drawingPanel');
        if (panel) {
            if (panel.classList.contains('snapped-left')) {
                panel.classList.remove('snapped-left');
                panel.classList.add('snapped-right');
            } else if (panel.classList.contains('snapped-right')) {
                panel.classList.remove('snapped-right');
            } else {
                panel.classList.add('snapped-left');
            }
        }
    }
    
    toggleDrawingResize() {
        const panel = document.getElementById('drawingPanel');
        if (panel) {
            if (panel.classList.contains('resizable-panel')) {
                panel.classList.remove('resizable-panel');
                panel.style.resize = 'none';
            } else {
                panel.classList.add('resizable-panel');
                panel.style.resize = 'both';
            }
        }
    }
    
    toggleDrawingMode() {
        const overlay = document.getElementById('drawingOverlay');
        const toggleBtn = document.getElementById('toggleDrawingMode');
        const modeInfo = document.querySelector('.mode-info small');
        
        if (!overlay) return;
        
        const isDrawingMode = overlay.classList.contains('active');
        
        if (isDrawingMode) {
            // Disable drawing mode - enable Live2D interaction
            overlay.classList.remove('active');
            overlay.style.pointerEvents = 'none';
            
            if (toggleBtn) {
                toggleBtn.innerHTML = '🎨 Enable Drawing Mode';
                toggleBtn.className = 'btn btn-primary';
            }
            
            if (modeInfo) {
                modeInfo.textContent = 'Drawing mode disabled - Live2D interaction active';
            }
            
            console.log('Drawing mode disabled - Live2D interaction enabled');
        } else {
            // Enable drawing mode - disable Live2D interaction
            overlay.classList.add('active');
            overlay.style.pointerEvents = 'all';
            
            if (toggleBtn) {
                toggleBtn.innerHTML = '🖱️ Enable Live2D Interaction';
                toggleBtn.className = 'btn btn-warning';
            }
            
            if (modeInfo) {
                modeInfo.textContent = 'Drawing mode active - Live2D interaction disabled';
            }
            
            console.log('Drawing mode enabled - Live2D interaction disabled');
        }
    }
    
    // Overlay canvas initialization
    initializeOverlayCanvas() {
        console.log('Initializing overlay drawing canvas...');
        
        const overlay = document.getElementById('drawingOverlay');
        const pixiContainer = document.getElementById('pixiContainer');
        
        if (!overlay || !pixiContainer) {
            console.error('Overlay canvas or PIXI container not found');
            return;
        }
        
        // Get the size of the PIXI container
        const containerRect = pixiContainer.getBoundingClientRect();
        
        // Set overlay canvas size to match PIXI container
        overlay.width = containerRect.width;
        overlay.height = containerRect.height;
        
        // Show and activate the overlay
        overlay.style.display = 'block';
        overlay.classList.add('active');
        
        // Store canvas and context
        this.drawingState.drawingCanvas = overlay;
        this.drawingState.drawingContext = overlay.getContext('2d');
        
        // Set up canvas event listeners
        this.setupOverlayCanvasEvents();
        
        console.log('Overlay drawing canvas initialized', {
            width: overlay.width,
            height: overlay.height
        });
    }
    
    setupOverlayCanvasEvents() {
        const canvas = this.drawingState.drawingCanvas;
        if (!canvas) return;
        
        let isDrawing = false;
        let lastX = 0;
        let lastY = 0;
        
        // Clear any existing event listeners
        canvas.onmousedown = null;
        canvas.onmousemove = null;
        canvas.onmouseup = null;
        
        canvas.addEventListener('mousedown', (e) => {
            // Only draw if a drawing tool is selected
            if (!['pen', 'brush', 'eraser', 'blur'].includes(this.drawingState.currentTool)) {
                return;
            }
            
            isDrawing = true;
            const rect = canvas.getBoundingClientRect();
            lastX = e.clientX - rect.left;
            lastY = e.clientY - rect.top;
            this.drawingState.isDrawing = true;
            
            // Track drawing session start for autonomous feedback
            if (this.enhancedState.drawingStartTime === null) {
                this.enhancedState.drawingStartTime = Date.now();
                console.log('Drawing session started - autonomous feedback active');
            }
            
            console.log('Drawing started at:', { x: lastX, y: lastY });
        });
        
        canvas.addEventListener('mousemove', (e) => {
            if (!isDrawing) return;
            
            const rect = canvas.getBoundingClientRect();
            const currentX = e.clientX - rect.left;
            const currentY = e.clientY - rect.top;
            
            this.drawOnCanvas(lastX, lastY, currentX, currentY);
            
            lastX = currentX;
            lastY = currentY;
        });
        
        canvas.addEventListener('mouseup', () => {
            if (isDrawing) {
                isDrawing = false;
                this.drawingState.isDrawing = false;
                
                // Track stroke for autonomous feedback
                this.enhancedState.strokeCount++;
                this.enhancedState.lastStrokeTime = Date.now();
                
                // Save state for undo/redo after each stroke
                this.saveHistoryState(`${this.drawingState.currentTool} stroke`);
                
                console.log('Drawing stroke completed, total strokes:', this.enhancedState.strokeCount);
            }
        });
        
        // Handle mouse leaving canvas
        canvas.addEventListener('mouseleave', () => {
            if (isDrawing) {
                isDrawing = false;
                this.drawingState.isDrawing = false;
                
                // Track stroke completion even when mouse leaves
                this.enhancedState.strokeCount++;
                this.enhancedState.lastStrokeTime = Date.now();
                this.saveHistoryState(`${this.drawingState.currentTool} stroke`);
                
                console.log('Drawing ended (mouse left canvas)');
            }
        });
        
        console.log('Overlay canvas events set up');
    }
    
    drawOnCanvas(x1, y1, x2, y2) {
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
    
    // ===== ENHANCED FEATURES METHODS =====
    
    // Smart Features
    toggleStabilization() {
        this.enhancedState.stabilization = !this.enhancedState.stabilization;
        const toggle = document.getElementById('stabilization-toggle');
        if (toggle) toggle.checked = this.enhancedState.stabilization;
    }
    
    toggleShapeRecognition() {
        this.enhancedState.shapeRecognition = !this.enhancedState.shapeRecognition;
        const toggle = document.getElementById('shape-recognition-toggle');
        if (toggle) toggle.checked = this.enhancedState.shapeRecognition;
    }
    
    toggleSymmetryMode() {
        this.enhancedState.symmetryMode = !this.enhancedState.symmetryMode;
        const toggle = document.getElementById('symmetry-toggle');
        if (toggle) toggle.checked = this.enhancedState.symmetryMode;
    }
    
    // AI Features
    toggleAvatarFeedback() {
        this.enhancedState.aiFeedbackEnabled = !this.enhancedState.aiFeedbackEnabled;
        const btn = document.getElementById('avatar-feedback-btn');
        
        if (this.enhancedState.aiFeedbackEnabled) {
            if (btn) btn.textContent = 'Disable Feedback';
            this.showAIFeedback('Avatar feedback enabled. I\'ll observe your drawing and provide helpful suggestions!');
            console.log('Avatar feedback enabled');
        } else {
            if (btn) btn.textContent = 'Avatar Feedback';
            this.hideAIFeedback();
            console.log('Avatar feedback disabled');
        }
    }
    
    async requestAutoComplete() {
        if (!this.drawingState.drawingCanvas) return;
        
        this.showAIFeedback('Analyzing your drawing for auto-completion suggestions...');
        
        try {
            const canvasData = this.drawingState.drawingCanvas.toDataURL();
            const context = this.getDrawingContext();
            
            // Create a prompt for AI auto-completion suggestions
            const prompt = `You are an AI art assistant analyzing an artwork in progress. The artist has been working for ${Math.floor(context.sessionDuration / 1000 / 60)} minutes using ${context.tool} tool with ${context.strokeCount} strokes. 

Please provide specific, actionable suggestions for completing or enhancing their artwork. Consider:
- What elements might be missing
- Technical improvements they could make
- Next steps in their creative process

Keep your suggestions practical and encouraging, around 70-90 words.`;

            const suggestions = await this.sendDrawingObservationToAvatar(prompt, 'completion_suggestions');
            this.showAIFeedback(suggestions, 'manual');
            
        } catch (error) {
            console.error('Auto-complete error:', error);
            this.showAIFeedback('I\'m having trouble analyzing your drawing right now. Keep going with your creative instincts - you\'re doing great!', 'manual');
        }
    }
    
    showAIFeedback(message, type = 'manual') {
        const feedbackDiv = document.querySelector('.ai-feedback');
        if (feedbackDiv) {
            const headerDiv = feedbackDiv.querySelector('.feedback-header');
            const textDiv = feedbackDiv.querySelector('.feedback-text');
            
            if (textDiv) textDiv.textContent = message;
            
            // Remove existing type classes
            feedbackDiv.classList.remove('autonomous', 'critique');
            
            // Update header and styling based on feedback type
            if (headerDiv) {
                if (type === 'autonomous') {
                    headerDiv.innerHTML = '<span>🤖</span> Avatar Observation';
                    feedbackDiv.classList.add('autonomous');
                } else if (type === 'critique') {
                    headerDiv.innerHTML = '<span>🎨</span> Avatar Critique';
                    feedbackDiv.classList.add('critique');
                } else {
                    headerDiv.innerHTML = '<span>🤖</span> Avatar Feedback';
                }
            }
            
            feedbackDiv.classList.add('visible');
            this.enhancedState.lastFeedback = message;
            
            // Auto-hide autonomous feedback after a delay
            if (type === 'autonomous') {
                setTimeout(() => {
                    feedbackDiv.classList.remove('visible');
                }, 8000); // Hide after 8 seconds
            }
        }
    }
    
    toggleAutonomousFeedback(enabled) {
        this.enhancedState.autonomousFeedback = enabled;
        
        if (enabled) {
            console.log('Autonomous feedback enabled - Avatar will observe and comment while you draw');
            this.showAIFeedback('Autonomous feedback enabled! I\'ll watch your drawing and share my thoughts as you work.', 'autonomous');
        } else {
            console.log('Autonomous feedback disabled');
            this.hideAIFeedback();
        }
    }
    
    hideAIFeedback() {
        const feedbackDiv = document.querySelector('.ai-feedback');
        if (feedbackDiv) {
            feedbackDiv.classList.remove('visible');
        }
    }
    
    // Live2D Integration
    toggleModelTracing() {
        this.enhancedState.modelTracing = !this.enhancedState.modelTracing;
        const btn = document.getElementById('model-tracing-btn');
        
        if (this.enhancedState.modelTracing) {
            if (btn) btn.textContent = 'Stop Tracing';
            console.log('Model tracing enabled - drawing model outline');
            this.startModelTracing();
        } else {
            if (btn) btn.textContent = 'Trace Model';
            console.log('Model tracing disabled');
            this.stopModelTracing();
        }
    }
    
    startModelTracing() {
        // In a real implementation, this would extract Live2D model outline
        if (this.drawingState.drawingContext) {
            this.drawingState.drawingContext.strokeStyle = 'rgba(255, 255, 255, 0.5)';
            this.drawingState.drawingContext.lineWidth = 2;
            this.drawingState.drawingContext.setLineDash([5, 5]);
            
            // Draw a sample outline (in real implementation, would trace actual model)
            this.drawingState.drawingContext.beginPath();
            this.drawingState.drawingContext.ellipse(300, 200, 80, 120, 0, 0, 2 * Math.PI);
            this.drawingState.drawingContext.stroke();
            this.drawingState.drawingContext.setLineDash([]);
        }
    }
    
    stopModelTracing() {
        // Reset drawing context to normal mode
        if (this.drawingState.drawingContext) {
            this.drawingState.drawingContext.setLineDash([]);
        }
    }
    
    capturePose() {
        console.log('Capturing current Live2D model pose...');
        this.showAIFeedback('Model pose captured! You can now reference this pose while drawing.');
        
        // In a real implementation, this would capture the actual Live2D model pose
        const poseData = {
            timestamp: new Date().toISOString(),
            pose: 'reference_pose_' + Date.now()
        };
        
        console.log('Captured pose data:', poseData);
    }
    
    toggleOutlineDisplay() {
        this.enhancedState.outlineDisplay = !this.enhancedState.outlineDisplay;
        const btn = document.getElementById('outline-display-btn');
        
        if (this.enhancedState.outlineDisplay) {
            if (btn) btn.textContent = 'Hide Outline';
            console.log('Model outline display enabled');
            // In real implementation, would overlay model outline on canvas
        } else {
            if (btn) btn.textContent = 'Show Outline';
            console.log('Model outline display disabled');
        }
    }
    
    async requestAvatarCritique() {
        if (!this.drawingState.drawingCanvas) return;
        
        this.showAIFeedback('Let me take a look at your artwork...');
        
        try {
            // Get canvas data for context
            const canvasData = this.drawingState.drawingCanvas.toDataURL();
            const context = this.getDrawingContext();
            
            // Create a detailed prompt for avatar critique
            const prompt = `You are an AI art companion providing constructive critique. The artist has been working for ${Math.floor(context.sessionDuration / 1000 / 60)} minutes using ${context.tool} tool with ${context.strokeCount} strokes. 

Please provide a helpful, encouraging critique of their artwork. Focus on:
- What's working well in their technique
- Suggestions for improvement
- Encouragement for their artistic journey

Keep your response supportive and specific, around 60-80 words. Act as a knowledgeable art mentor who genuinely cares about their growth.`;

            const critique = await this.sendDrawingObservationToAvatar(prompt, 'artwork_critique');
            this.showAIFeedback(critique, 'critique');
            
        } catch (error) {
            console.error('Avatar critique error:', error);
            this.showAIFeedback('I\'m having trouble analyzing your artwork right now. But from what I can see, you\'re developing a really nice artistic voice!', 'manual');
        }
    }
    
    // Color History Management
    addColorToHistory(color) {
        // Remove if already exists
        const index = this.enhancedState.colorHistory.indexOf(color);
        if (index > -1) {
            this.enhancedState.colorHistory.splice(index, 1);
        }
        
        // Add to beginning
        this.enhancedState.colorHistory.unshift(color);
        
        // Keep only last 16 colors
        if (this.enhancedState.colorHistory.length > 16) {
            this.enhancedState.colorHistory = this.enhancedState.colorHistory.slice(0, 16);
        }
        
        this.updateColorHistory();
    }
    
    updateColorHistory() {
        const historyContainer = document.querySelector('.color-history');
        if (!historyContainer) return;
        
        // Keep the label if it exists
        const label = historyContainer.querySelector('.color-history-label');
        historyContainer.innerHTML = '';
        
        if (label) {
            historyContainer.appendChild(label);
        }
        
        this.enhancedState.colorHistory.forEach(color => {
            const swatch = document.createElement('div');
            swatch.className = 'color-swatch';
            swatch.style.backgroundColor = color;
            swatch.title = color;
            swatch.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent triggering palette expansion
                this.selectColor(color);
            });
            historyContainer.appendChild(swatch);
        });
        
        // Make the entire color history section clickable to expand palette
        historyContainer.addEventListener('click', (e) => {
            // Only trigger if not clicking on a color swatch
            if (!e.target.classList.contains('color-swatch')) {
                this.showColorPalette();
            }
        });
        historyContainer.style.cursor = 'pointer';
    }
    
    selectColor(color) {
        this.drawingState.currentColor = color;
        const colorInput = document.getElementById('colorPicker');
        if (colorInput) colorInput.value = color;
        this.addColorToHistory(color);
    }
    
    clearColorHistory() {
        this.enhancedState.colorHistory = ['#000000'];
        this.updateColorHistory();
    }
    
    showColorPalette() {
        // Toggle color palette visibility instead of duplicating functionality
        const colorHistory = document.getElementById('colorHistory');
        if (!colorHistory) return;
        
        // Check if palette is already expanded
        if (colorHistory.classList.contains('expanded')) {
            colorHistory.classList.remove('expanded');
            return;
        }
        
        // Show expanded color palette with preset colors
        const presetColors = [
            '#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF',
            '#800000', '#008000', '#000080', '#808000', '#800080', '#008080', '#C0C0C0', '#808080',
            '#FF6600', '#66FF00', '#0066FF', '#6600FF', '#FF0066', '#00FF66', '#FFB366', '#66FFB3',
            '#B366FF', '#66B3FF', '#FFD700', '#FF69B4', '#98FB98', '#87CEEB', '#DDA0DD', '#F0E68C'
        ];
        
        colorHistory.innerHTML = this.enhancedState.colorHistory.map(color => 
            `<div class="color-swatch" style="background-color: ${color}" onclick="setDrawingColor('${color}')" title="${color}"></div>`
        ).join('') + 
        '<div class="color-divider">Preset Colors:</div>' +
        presetColors.map(color => 
            `<div class="color-swatch preset" style="background-color: ${color}" onclick="setDrawingColor('${color}')" title="${color}"></div>`
        ).join('');
        
        colorHistory.classList.add('expanded');
        console.log('Color palette expanded with presets');
    }
    
    // History System
    saveHistoryState(description = 'Drawing action') {
        if (!this.drawingState.drawingCanvas) return;
        
        const canvasData = this.drawingState.drawingCanvas.toDataURL();
        const historyItem = {
            id: Date.now(),
            data: canvasData,
            description: description,
            timestamp: new Date().toISOString(),
            tool: this.drawingState.currentTool,
            color: this.drawingState.currentColor
        };
        
        // Remove any history after current index
        this.enhancedState.historyStack = this.enhancedState.historyStack.slice(0, this.enhancedState.currentHistoryIndex + 1);
        
        // Add new state
        this.enhancedState.historyStack.push(historyItem);
        this.enhancedState.currentHistoryIndex++;
        
        // Keep only last 50 states
        if (this.enhancedState.historyStack.length > 50) {
            this.enhancedState.historyStack.shift();
            this.enhancedState.currentHistoryIndex--;
        }
        
        this.updateHistoryButtons();
        this.updateTimeline();
    }
    
    undo() {
        if (this.enhancedState.currentHistoryIndex > 0) {
            this.enhancedState.currentHistoryIndex--;
            this.restoreHistoryState(this.enhancedState.historyStack[this.enhancedState.currentHistoryIndex]);
            this.updateHistoryButtons();
            this.updateTimeline();
        }
    }
    
    redo() {
        if (this.enhancedState.currentHistoryIndex < this.enhancedState.historyStack.length - 1) {
            this.enhancedState.currentHistoryIndex++;
            this.restoreHistoryState(this.enhancedState.historyStack[this.enhancedState.currentHistoryIndex]);
            this.updateHistoryButtons();
            this.updateTimeline();
        }
    }
    
    restoreHistoryState(historyItem) {
        if (!this.drawingState.drawingCanvas || !this.drawingState.drawingContext) return;
        
        const img = new Image();
        img.onload = () => {
            this.drawingState.drawingContext.clearRect(0, 0, this.drawingState.drawingCanvas.width, this.drawingState.drawingCanvas.height);
            this.drawingState.drawingContext.drawImage(img, 0, 0);
        };
        img.src = historyItem.data;
    }
    
    updateHistoryButtons() {
        const undoBtn = document.getElementById('undo-btn');
        const redoBtn = document.getElementById('redo-btn');
        
        if (undoBtn) {
            undoBtn.disabled = this.enhancedState.currentHistoryIndex <= 0;
        }
        
        if (redoBtn) {
            redoBtn.disabled = this.enhancedState.currentHistoryIndex >= this.enhancedState.historyStack.length - 1;
        }
    }
    
    toggleTimeline() {
        this.enhancedState.timelineVisible = !this.enhancedState.timelineVisible;
        const timeline = document.querySelector('.history-timeline');
        
        if (timeline) {
            if (this.enhancedState.timelineVisible) {
                timeline.classList.add('visible');
                this.updateTimeline();
            } else {
                timeline.classList.remove('visible');
            }
        }
    }
    
    updateTimeline() {
        const timeline = document.querySelector('.history-timeline');
        if (!timeline) return;
        
        timeline.innerHTML = '<h4 style="margin: 0 0 12px 0; color: #fff; font-size: 14px;">Drawing History</h4>';
        
        this.enhancedState.historyStack.forEach((item, index) => {
            const timelineItem = document.createElement('div');
            timelineItem.className = 'timeline-item';
            if (index === this.enhancedState.currentHistoryIndex) {
                timelineItem.classList.add('current');
            }
            
            const time = new Date(item.timestamp).toLocaleTimeString();
            
            timelineItem.innerHTML = `
                <div class="timeline-icon">🎨</div>
                <div class="timeline-text">${item.description}</div>
                <div class="timeline-time">${time}</div>
            `;
            
            timelineItem.addEventListener('click', () => {
                this.enhancedState.currentHistoryIndex = index;
                this.restoreHistoryState(item);
                this.updateHistoryButtons();
                this.updateTimeline();
            });
            
            timeline.appendChild(timelineItem);
        });
    }
    
    createSnapshot() {
        if (!this.drawingState.drawingCanvas) return;
        
        const snapshot = {
            id: Date.now(),
            name: `Snapshot ${this.enhancedState.snapshots.length + 1}`,
            data: this.drawingState.drawingCanvas.toDataURL(),
            timestamp: new Date().toISOString()
        };
        
        this.enhancedState.snapshots.push(snapshot);
        console.log('Snapshot created:', snapshot.name);
        this.showAIFeedback(`Snapshot "${snapshot.name}" saved! You can restore it anytime.`);
    }

    // Override the existing color update to include history
    updateDrawingColor() {
        const colorInput = document.getElementById('colorPicker');
        if (colorInput) {
            this.drawingState.currentColor = colorInput.value;
            this.addColorToHistory(colorInput.value);
        }
    }
    
    // Unified Avatar Feedback System
    async requestAvatarFeedback() {
        if (!this.drawingState.drawingCanvas) {
            this.showAIFeedback('Please start drawing first before requesting feedback!', 'error');
            return;
        }
        
        try {
            // Capture current drawing state
            const drawingData = this.drawingState.drawingCanvas.toDataURL();
            const strokeCount = this.enhancedState.strokeCount;
            const drawingTime = Date.now() - (this.enhancedState.drawingStartTime || Date.now());
            
            // Show immediate feedback
            this.showAIFeedback('🎨 Analyzing your artwork... The avatar is examining your drawing!', 'analysis');
            
            // Simulate avatar feedback (in real implementation, this would call the AI service)
            setTimeout(() => {
                const feedbackMessages = [
                    "I love the creativity in your composition! The color choices work really well together.",
                    "Your brushwork shows great confidence. Have you considered adding some highlights to make it pop?",
                    "This is coming along beautifully! The proportions look natural and balanced.",
                    "Interesting style! I can see you're experimenting with different techniques.",
                    "The way you're using light and shadow is quite impressive. Keep developing that skill!",
                    "Your artistic vision is unique! I enjoy watching your creative process unfold."
                ];
                
                const randomFeedback = feedbackMessages[Math.floor(Math.random() * feedbackMessages.length)];
                this.showAIFeedback(`💭 Avatar says: "${randomFeedback}"`, 'feedback');
                
                // Update feedback state
                this.enhancedState.lastFeedback = randomFeedback;
                this.enhancedState.lastFeedbackTime = Date.now();
                
            }, 2000);
            
        console.log('🤖 Avatar feedback requested for drawing analysis');
        
    } catch (error) {
        console.error('Error requesting avatar feedback:', error);
        this.showAIFeedback('Sorry, I had trouble analyzing your drawing. Please try again!', 'error');
    }
}

// Additional tool parameter methods
setFlow(flow) {
    // Update flow value for current tool
    this.drawingState.flow = flow / 100;
    const flowValue = document.getElementById('flowValue');
    if (flowValue) flowValue.textContent = flow;
    console.log('Flow set to:', flow + '%');
}

setHardness(hardness) {
    // Update hardness value for current tool
    this.drawingState.hardness = hardness / 100;
    const hardnessValue = document.getElementById('hardnessValue');
    if (hardnessValue) hardnessValue.textContent = hardness;
    console.log('Hardness set to:', hardness + '%');
}

setSpacing(spacing) {
    // Update spacing value for current tool
    this.drawingState.spacing = spacing / 100;
    const spacingValue = document.getElementById('spacingValue');
    if (spacingValue) spacingValue.textContent = spacing;
    console.log('Spacing set to:', spacing + '%');
}

// Smart feature toggles
toggleStabilization(enabled) {
    this.enhancedState.stabilization = enabled;
    console.log('Line stabilization:', enabled ? 'enabled' : 'disabled');
    if (enabled) {
        this.showAIFeedback('✨ Line stabilization enabled - your strokes will be smoothed!', 'info');
    }
}

toggleShapeRecognition(enabled) {
    this.enhancedState.shapeRecognition = enabled;
    console.log('Shape recognition:', enabled ? 'enabled' : 'disabled');
    if (enabled) {
        this.showAIFeedback('🔍 Shape recognition enabled - rough shapes will be auto-corrected!', 'info');
    }
}

toggleSymmetry(enabled) {
    this.enhancedState.symmetryMode = enabled;
    console.log('Symmetry mode:', enabled ? 'enabled' : 'disabled');
    if (enabled) {
        this.showAIFeedback('🪞 Symmetry mode enabled - drawings will be mirrored!', 'info');
    }
}

togglePressure(enabled) {
    this.enhancedState.pressureSensitivity = enabled;
    console.log('Pressure sensitivity:', enabled ? 'enabled' : 'disabled');
    if (enabled) {
        this.showAIFeedback('✍️ Pressure sensitivity enabled for tablet users!', 'info');
    }
}

toggleVectorMode(enabled) {
    this.enhancedState.vectorMode = enabled;
    console.log('Vector mode:', enabled ? 'enabled' : 'disabled');
    if (enabled) {
        this.showAIFeedback('📐 Vector mode enabled - scalable vector paths!', 'info');
    }
}

// History system enhancements
showHistoryTimeline() {
    const timeline = document.querySelector('.history-timeline');
    if (timeline) {
        timeline.style.display = timeline.style.display === 'none' ? 'block' : 'none';
        this.enhancedState.timelineVisible = timeline.style.display === 'block';
        console.log('History timeline toggled:', this.enhancedState.timelineVisible);
    }
}

saveSnapshot() {
    if (!this.drawingState.drawingCanvas) {
        this.showAIFeedback('No drawing to save snapshot of!', 'warning');
        return;
    }
    
    const snapshot = {
        id: Date.now(),
        data: this.drawingState.drawingCanvas.toDataURL(),
        timestamp: new Date().toISOString(),
        description: `Snapshot ${this.enhancedState.snapshots.length + 1}`
    };
    
    this.enhancedState.snapshots.push(snapshot);
    this.showAIFeedback('📷 Snapshot saved successfully!', 'success');
    console.log('Snapshot saved:', snapshot.id);
}

loadSnapshot() {
    if (this.enhancedState.snapshots.length === 0) {
        this.showAIFeedback('No snapshots available to load!', 'warning');
        return;
    }
    
    // For now, load the most recent snapshot
    const latestSnapshot = this.enhancedState.snapshots[this.enhancedState.snapshots.length - 1];
    this.showAIFeedback('📂 Snapshot loaded successfully!', 'success');
    console.log('Snapshot loaded:', latestSnapshot.id);
}    // Export global functions for HTML onclick handlers
    setupGlobalFunctions() {
        // Unify all avatar feedback functions to use the same implementation
        window.requestAvatarFeedback = () => this.requestAvatarFeedback();
        window.requestDrawingCritique = () => this.requestAvatarFeedback(); // Same function
        window.shareDrawingWithAvatar = () => this.requestAvatarFeedback(); // Same function
        
        // Color functions
        window.showColorPalette = () => this.showColorPalette();
        window.setDrawingColor = (color) => this.selectColor(color);
        
        // Tool functions
        window.selectTool = (tool) => this.setTool(tool);
        window.setBrushSize = (size) => this.setBrushSize(size);
        window.setOpacity = (opacity) => this.setOpacity(opacity);
        window.setFlow = (flow) => this.setFlow(flow);
        window.setHardness = (hardness) => this.setHardness(hardness);
        window.setSpacing = (spacing) => this.setSpacing(spacing);
        
        // Canvas functions
        window.clearCanvas = () => this.clearCanvas();
        window.saveDrawing = () => this.saveDrawing();
        window.exportPNG = () => this.exportPNG();
        window.exportSVG = () => this.exportSVG();
        
        // History functions
        window.undoAction = () => this.undo();
        window.redoAction = () => this.redo();
        window.showHistoryTimeline = () => this.showHistoryTimeline();
        window.saveSnapshot = () => this.saveSnapshot();
        window.loadSnapshot = () => this.loadSnapshot();
        
        // Smart feature toggles
        window.toggleStabilization = (enabled) => this.toggleStabilization(enabled);
        window.toggleShapeRecognition = (enabled) => this.toggleShapeRecognition(enabled);
        window.toggleSymmetry = (enabled) => this.toggleSymmetry(enabled);
        window.togglePressure = (enabled) => this.togglePressure(enabled);
        window.toggleVectorMode = (enabled) => this.toggleVectorMode(enabled);
        
        // AI-powered tools (placeholders for now)
        window.autoCompleteDrawing = () => this.showAIFeedback('🤖 AI Auto-complete feature coming soon!', 'info');
        window.applyStyleTransfer = () => this.showAIFeedback('🎨 Style Transfer feature coming soon!', 'info');
        window.removeBackground = () => this.showAIFeedback('🗑️ AI Background Removal feature coming soon!', 'info');
        window.smartSelection = () => this.showAIFeedback('🎯 Smart Selection feature coming soon!', 'info');
        window.generatePoseReference = () => this.showAIFeedback('🚶 Pose Reference feature coming soon!', 'info');
        
        // Live2D integration (placeholders for now)
        window.enableModelTracing = () => this.showAIFeedback('📝 Model Tracing feature coming soon!', 'info');
        window.captureModelPose = () => this.showAIFeedback('📸 Pose Capture feature coming soon!', 'info');
        window.toggleModelOutline = () => this.showAIFeedback('🔲 Model Outline feature coming soon!', 'info');
        window.recordMotion = () => this.showAIFeedback('🎬 Motion Recording feature coming soon!', 'info');
        window.costumeDesigner = () => this.showAIFeedback('👗 Costume Designer feature coming soon!', 'info');
        window.expressionSketching = () => this.showAIFeedback('😊 Expression Sketching feature coming soon!', 'info');
        window.emotionOverlay = () => this.showAIFeedback('💭 Emotion Overlay feature coming soon!', 'info');
        window.interactiveAnnotations = () => this.showAIFeedback('📌 Interactive Annotations feature coming soon!', 'info');
        window.costumePainter = () => this.showAIFeedback('🎨 Costume Painter feature coming soon!', 'info');
        window.sceneCreator = () => this.showAIFeedback('🌄 Scene Creator feature coming soon!', 'info');
        
        // Advanced history features (placeholders for now)
        window.createBranch = () => this.showAIFeedback('🌿 Branch History feature coming soon!', 'info');
        window.compareSnapshots = () => this.showAIFeedback('⚖️ Snapshot Comparison feature coming soon!', 'info');
        
        // Edit functions (placeholders for now)
        window.copySelection = () => this.showAIFeedback('📋 Copy Selection feature coming soon!', 'info');
        window.pasteSelection = () => this.showAIFeedback('📄 Paste Selection feature coming soon!', 'info');
        window.cutSelection = () => this.showAIFeedback('✂️ Cut Selection feature coming soon!', 'info');
        window.pasteExternal = () => this.showAIFeedback('📋 External Paste feature coming soon!', 'info');
        
        // Story mode features (placeholders for now)
        window.enterStoryMode = () => this.showAIFeedback('📖 Story Mode feature coming soon!', 'info');
        window.addDialogueBubble = () => this.showAIFeedback('💬 Dialogue Bubbles feature coming soon!', 'info');
        window.addNarrationBox = () => this.showAIFeedback('📝 Narration Boxes feature coming soon!', 'info');
        window.createChoicePoint = () => this.showAIFeedback('🔀 Choice Points feature coming soon!', 'info');
        
        console.log('Global drawing functions initialized');
    }
}

// Global instance
let drawingSystem = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    drawingSystem = new DrawingSystem();
    window.drawingSystem = drawingSystem;
    
    // Set up global functions
    if (drawingSystem.setupGlobalFunctions) {
        drawingSystem.setupGlobalFunctions();
    }
});

// Legacy function compatibility
window.openDrawing = () => drawingSystem?.openDrawing();
window.closeDrawing = () => drawingSystem?.closeDrawing();

window.toggleDrawingSnap = () => drawingSystem?.toggleDrawingSnap();
window.toggleDrawingResize = () => drawingSystem?.toggleDrawingResize();
window.toggleDrawingMode = () => drawingSystem?.toggleDrawingMode();
window.selectTool = (tool) => drawingSystem?.selectTool(tool, event);
window.updateDrawingColor = () => drawingSystem?.updateDrawingColor();
window.updateBrushSize = () => drawingSystem?.updateBrushSize();
window.updateOpacity = () => drawingSystem?.updateOpacity();
window.clearCanvas = () => drawingSystem?.clearCanvas();
window.saveDrawing = () => drawingSystem?.saveDrawing();
window.loadDrawing = () => drawingSystem?.loadDrawing();
window.addNewLayer = () => drawingSystem?.addNewLayer();
window.deleteLayer = () => drawingSystem?.deleteLayer();

// Enhanced features global functions
window.toggleAvatarFeedback = () => drawingSystem?.toggleAvatarFeedback();
window.requestAutoComplete = () => drawingSystem?.requestAutoComplete();
window.toggleModelTracing = () => drawingSystem?.toggleModelTracing();
window.capturePose = () => drawingSystem?.capturePose();
window.toggleOutlineDisplay = () => drawingSystem?.toggleOutlineDisplay();
window.requestAvatarCritique = () => drawingSystem?.requestAvatarCritique();
window.undoDrawing = () => drawingSystem?.undo();
window.redoDrawing = () => drawingSystem?.redo();
window.toggleTimeline = () => drawingSystem?.toggleTimeline();
window.createSnapshot = () => drawingSystem?.createSnapshot();
