// Live2D UI Controller - Modular UI management for Live2D Integration
class Live2DUIController {
    constructor(integration) {
        this.integration = integration;
        this.elements = {};
        this.state = {
            panelCollapsed: true, // Start with panel closed
            logVisible: false,
            currentModel: null,
            currentMotionGroup: null,
            currentMotion: null,
            currentExpression: null
        };
        
        this.initializeElements();
        this.setupEventListeners();
        
        // Initialize panel state
        this.initializePanelState();
    }

    initializePanelState() {
        // Set initial panel state (closed) - no need to add class since closed is default
        // Panel starts closed, so don't add 'open' class
        
        // Set initial app container state
        const appContainer = document.querySelector('.app-container');
        if (appContainer) {
            appContainer.classList.add('panel-collapsed');
        }
        
        // Show toggle button
        if (this.elements.panelToggle) {
            this.elements.panelToggle.style.display = 'block';
        }
    }

    initializeElements() {
        // Cache DOM elements
        this.elements = {
            // Panel controls
            leftPanel: document.getElementById('leftPanel'),
            panelToggle: document.getElementById('panelToggle'),
            settingsPanel: document.getElementById('settingsPanel'),
            
            // Model selection
            modelSelect: document.getElementById('modelSelect'),
            modelName: document.getElementById('modelName'),
            modelId: document.getElementById('modelId'),
            
            // Motion controls
            motionGroupSelect: document.getElementById('motionGroupSelect'),
            motionSelect: document.getElementById('motionSelect'),
            
            // Expression controls
            expressionSelect: document.getElementById('expressionSelect'),
            
            // Info display
            modelStatus: document.getElementById('modelStatus'),
            modelPosition: document.getElementById('modelPosition'),
            modelScale: document.getElementById('modelScale'),
            mousePosition: document.getElementById('mousePosition'),
            
            // Settings controls
            showCanvasFrame: document.getElementById('showCanvasFrame'),
            showModelFrame: document.getElementById('showModelFrame'),
            showHitAreas: document.getElementById('showHitAreas'),
            debugMode: document.getElementById('debugMode'),
            showFPS: document.getElementById('showFPS'),
            logMouseEvents: document.getElementById('logMouseEvents'),
            renderQuality: document.getElementById('renderQuality'),
            enableAntialiasing: document.getElementById('enableAntialiasing'),
            
            // Canvas container
            canvasContainer: document.querySelector('.canvas-container'),
            pixiContainer: document.getElementById('pixiContainer')
        };
        
        // Initialize settings state
        this.state.settingsVisible = false;
        this.state.canvasFrameVisible = true;
        this.state.modelFrameVisible = false;
        this.state.hitAreasVisible = false;
        this.state.debugMode = false;
        this.state.fpsVisible = false;
        this.state.mouseLogging = false;
        this.fpsCounter = null;
    }

    setupEventListeners() {
        // Model selection change
        if (this.elements.modelSelect) {
            this.elements.modelSelect.addEventListener('change', (e) => {
                this.onModelChange(e.target.value);
            });
        }

        // Motion group selection
        if (this.elements.motionGroupSelect) {
            this.elements.motionGroupSelect.addEventListener('change', (e) => {
                this.onMotionGroupChange(e.target.value);
            });
        }

        // Motion selection
        if (this.elements.motionSelect) {
            this.elements.motionSelect.addEventListener('change', (e) => {
                this.onMotionTypeChange(e.target.value);
            });
        }

        // Expression selection
        if (this.elements.expressionSelect) {
            this.elements.expressionSelect.addEventListener('change', (e) => {
                this.onExpressionChange(e.target.value);
            });
        }

        // Mouse tracking on canvas
        if (this.elements.pixiContainer) {
            this.elements.pixiContainer.addEventListener('mousemove', (e) => {
                this.updateMousePosition(e.clientX, e.clientY);
            });
        }
    }

    // Panel Management
    togglePanel(force = null) {
        if (force !== null) {
            this.state.panelCollapsed = !force;
        } else {
            this.state.panelCollapsed = !this.state.panelCollapsed;
        }
        
        if (this.elements.leftPanel) {
            this.elements.leftPanel.classList.toggle('open', !this.state.panelCollapsed);
        }
        
        if (this.elements.panelToggle) {
            this.elements.panelToggle.textContent = '☰';
            // Panel starts closed, so toggle button should be visible
            this.elements.panelToggle.style.display = 'block';
            this.elements.panelToggle.classList.toggle('panel-open', !this.state.panelCollapsed);
        }
        
        // Update canvas positioning using new CSS classes
        const appContainer = document.querySelector('.app-container');
        if (appContainer) {
            if (this.state.panelCollapsed) {
                appContainer.classList.remove('panel-open');
                appContainer.classList.add('panel-collapsed');
            } else {
                appContainer.classList.remove('panel-collapsed');
                appContainer.classList.add('panel-open');
            }
        }
    }

    toggleLog() {
        this.state.logVisible = !this.state.logVisible;
        
        if (this.elements.logPanel) {
            this.elements.logPanel.classList.toggle('visible', this.state.logVisible);
        }
    }

    // Settings Management
    toggleSettings() {
        this.state.settingsVisible = !this.state.settingsVisible;
        
        if (this.elements.settingsPanel) {
            this.elements.settingsPanel.classList.toggle('visible', this.state.settingsVisible);
        }
    }

    toggleCanvasFrame() {
        const checkbox = document.getElementById('showCanvasFrame');
        if (checkbox) {
            checkbox.checked = !checkbox.checked;
        }
        
        if (this.integration && this.integration.core && this.integration.core.canvasManager) {
            this.integration.core.canvasManager.toggleCanvasFrame();
        }
        
        this.integration.logger.log('Canvas frame toggled', 'info');
    }

    toggleModelFrame() {
        const checkbox = document.getElementById('showModelFrame');
        if (checkbox) {
            checkbox.checked = !checkbox.checked;
        }
        
        if (this.integration && this.integration.core && this.integration.core.canvasManager) {
            this.integration.core.canvasManager.toggleModelFrame();
        }
        
        this.integration.logger.log('Model frame toggled', 'info');
    }

    toggleHitAreas() {
        const checkbox = document.getElementById('showHitAreas');
        if (checkbox) {
            checkbox.checked = !checkbox.checked;
        }
        
        if (this.integration && this.integration.core && this.integration.core.canvasManager) {
            this.integration.core.canvasManager.toggleHitAreas();
        }
        
        this.integration.logger.log('Hit areas toggled', 'info');
    }

    toggleDebugMode() {
        this.state.debugMode = !this.state.debugMode;
        this.integration.logger.log(`Debug mode: ${this.state.debugMode ? 'ON' : 'OFF'}`);
    }

    toggleFPS() {
        this.state.fpsVisible = !this.state.fpsVisible;
        
        if (this.state.fpsVisible) {
            this.createFPSCounter();
        } else {
            this.removeFPSCounter();
        }
    }

    createFPSCounter() {
        if (!this.fpsCounter) {
            this.fpsCounter = document.createElement('div');
            this.fpsCounter.className = 'fps-counter';
            this.fpsCounter.textContent = 'FPS: 0';
            this.elements.canvasContainer.appendChild(this.fpsCounter);
            
            // Start FPS monitoring
            this.startFPSMonitoring();
        }
    }

    removeFPSCounter() {
        if (this.fpsCounter) {
            this.fpsCounter.remove();
            this.fpsCounter = null;
            this.stopFPSMonitoring();
        }
    }

    startFPSMonitoring() {
        let lastTime = performance.now();
        let frameCount = 0;
        
        const updateFPS = () => {
            frameCount++;
            const currentTime = performance.now();
            
            if (currentTime - lastTime >= 1000) {
                const fps = Math.round(frameCount / ((currentTime - lastTime) / 1000));
                if (this.fpsCounter) {
                    this.fpsCounter.textContent = `FPS: ${fps}`;
                }
                frameCount = 0;
                lastTime = currentTime;
            }
            
            if (this.state.fpsVisible) {
                requestAnimationFrame(updateFPS);
            }
        };
        
        requestAnimationFrame(updateFPS);
    }

    stopFPSMonitoring() {
        // FPS monitoring will stop automatically when fpsVisible is false
    }

    toggleMouseLogging() {
        this.state.mouseLogging = !this.state.mouseLogging;
        this.integration.logger.log(`Mouse logging: ${this.state.mouseLogging ? 'ON' : 'OFF'}`);
    }

    changeRenderQuality() {
        const quality = this.elements.renderQuality?.value || 'medium';
        this.integration.logger.log(`Render quality changed to: ${quality}`);
        // Implementation will be added to core
    }

    toggleAntialiasing() {
        const enabled = this.elements.enableAntialiasing?.checked || false;
        this.integration.logger.log(`Antialiasing: ${enabled ? 'ON' : 'OFF'}`);
        // Implementation will be added to core
    }

    debugModel() {
        if (this.integration) {
            this.integration.debugModelBounds();
        }
    }

    // Model Management
    async onModelChange(modelName) {
        if (!modelName) return;

        this.showLoading(true);
        
        try {
            // Use the multi-model manager to add model
            await this.integration.modelManager.addModel(modelName);
            this.state.currentModel = modelName;
            
            // Update UI
            this.updateModelInfo();
            await this.loadModelMotions(modelName);
            await this.loadModelExpressions(modelName);
            
            this.updateModelStatus('success', 'Model loaded successfully');
            
        } catch (error) {
            this.updateModelStatus('error', `Failed to load model: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    // Called when model focus changes (from character icon clicks)
    async onModelFocusChanged(modelName) {
        if (!modelName) return;

        console.log(`Model focus changed to: ${modelName}`);
        
        try {
            this.state.currentModel = modelName;
            
            // Update UI
            this.updateModelInfo();
            await this.loadModelMotions(modelName);
            await this.loadModelExpressions(modelName);
            
            this.updateModelStatus('success', 'Model focused');
            
        } catch (error) {
            this.updateModelStatus('error', `Failed to load model data: ${error.message}`);
            console.error('Error in onModelFocusChanged:', error);
        }
    }

    async loadModelMotions(modelName) {
        try {
            // Use the integration's motion manager
            const motions = await this.integration.motionManager.loadModelMotions(modelName);
            
            // Get motion groups from the motion manager
            const groups = this.integration.getMotionGroups();
            this.populateMotionGroupsFromManager(groups);
            
        } catch (error) {
            console.error('Failed to load motions:', error);
            this.populateMotionGroupsFromManager([]);
        }
    }

    async loadModelExpressions(modelName) {
        try {
            const baseUrl = await getApiBaseUrl();
            const response = await fetch(`${baseUrl}/api/live2d/model/${modelName}/expressions`);
            const data = await response.json();
            
            this.populateExpressions(data.expressions || []);
            
        } catch (error) {
            console.error('Failed to load expressions:', error);
            this.populateExpressions([]);
        }
    }

    populateMotionGroupsFromManager(groups) {
        if (!this.elements.motionGroupSelect) return;

        // Clear and populate dropdown
        this.elements.motionGroupSelect.innerHTML = '<option value="">Select motion group...</option>';
        
        groups.forEach(group => {
            const motions = this.integration.getMotionsByGroup(group);
            const option = document.createElement('option');
            option.value = group;
            option.textContent = `${group} (${motions.length})`;
            this.elements.motionGroupSelect.appendChild(option);
        });

        // Store groups for later use
        this.motionGroups = {};
        groups.forEach(group => {
            this.motionGroups[group] = this.integration.getMotionsByGroup(group).map(m => m.name);
        });
    }

    populateMotionGroups(motions) {
        if (!this.elements.motionGroupSelect) return;

        // Group motions by category
        const groups = {};
        motions.forEach(motion => {
            const parts = motion.split('_');
            const group = parts[0] || 'default';
            if (!groups[group]) groups[group] = [];
            groups[group].push(motion);
        });

        // Clear and populate dropdown
        this.elements.motionGroupSelect.innerHTML = '<option value="">Select motion group...</option>';
        
        Object.keys(groups).forEach(group => {
            const option = document.createElement('option');
            option.value = group;
            option.textContent = `${group} (${groups[group].length})`;
            this.elements.motionGroupSelect.appendChild(option);
        });

        this.motionGroups = groups;
    }

    onMotionGroupChange(group) {
        if (!this.elements.motionSelect) return;

        this.state.currentMotionGroup = group;
        this.elements.motionSelect.innerHTML = '<option value="">Select motion...</option>';

        if (group && this.motionGroups && this.motionGroups[group]) {
            this.motionGroups[group].forEach(motion => {
                const option = document.createElement('option');
                option.value = motion;
                option.textContent = motion;
                this.elements.motionSelect.appendChild(option);
            });
        }
    }

    onMotionTypeChange(motion) {
        this.state.currentMotion = motion;
    }

    populateExpressions(expressions) {
        if (!this.elements.expressionSelect) return;

        this.elements.expressionSelect.innerHTML = '<option value="">Select expression...</option>';
        
        expressions.forEach(expression => {
            const option = document.createElement('option');
            option.value = expression;
            option.textContent = expression;
            this.elements.expressionSelect.appendChild(option);
        });
    }

    onExpressionChange(expression) {
        this.state.currentExpression = expression;
    }

    // Display Controls
    fitModel() {
        // Center and fit the model
        if (this.integration && this.integration.core && this.integration.core.canvasManager) {
            this.integration.core.canvasManager.fitModelToCanvas();
        }
    }

    centerModel() {
        // Center the model at current level
        if (this.integration && this.integration.core && this.integration.core.canvasManager) {
            this.integration.core.canvasManager.centerModel();
        }
    }

    // Action Handlers
    async playMotion(motionName) {
        if (!this.integration || !this.integration.initialized) {
            throw new Error('Integration not initialized');
        }

        return await this.integration.playMotion(motionName);
    }

    async playSelectedMotion() {
        if (!this.state.currentMotion) {
            this.showNotification('Please select a motion first', 'warning');
            return;
        }

        if (!this.integration || !this.integration.modelManager) {
            this.showNotification('Integration not initialized', 'error');
            return;
        }

        try {
            // Get the active model from multi-model manager
            const activeModelData = this.integration.modelManager.getActiveModel();
            if (!activeModelData || !activeModelData.pixiModel) {
                throw new Error('No active model found');
            }

            const model = activeModelData.pixiModel;
            
            // Parse motion string (group/index format)
            const [group, motionIndex] = this.state.currentMotion.split('/');
            
            // Play motion using the model's motion method
            if (model.motion && typeof model.motion === 'function') {
                await model.motion(group, parseInt(motionIndex) || 0);
                this.showNotification(`Playing motion: ${this.state.currentMotion}`, 'success');
            } else {
                throw new Error('Model does not support motion playback');
            }
        } catch (error) {
            this.showNotification(`Failed to play motion: ${error.message}`, 'error');
        }
    }

    async playRandomMotion() {
        if (!this.integration || !this.integration.modelManager) {
            this.showNotification('Integration not initialized', 'error');
            return;
        }

        try {
            // Get the active model from multi-model manager
            const activeModelData = this.integration.modelManager.getActiveModel();
            if (!activeModelData || !activeModelData.pixiModel) {
                throw new Error('No active model found');
            }

            const model = activeModelData.pixiModel;
            
            // Get available motions from the current UI state
            if (!this.motionGroups || Object.keys(this.motionGroups).length === 0) {
                throw new Error('No motions available');
            }

            // Pick a random group
            const groups = Object.keys(this.motionGroups);
            const randomGroup = groups[Math.floor(Math.random() * groups.length)];
            
            // Pick a random motion from the group
            const motions = this.motionGroups[randomGroup];
            const randomMotion = motions[Math.floor(Math.random() * motions.length)];
            
            // Parse motion string (group/index format)
            const [group, motionIndex] = randomMotion.split('/');
            
            // Play motion using the model's motion method
            if (model.motion && typeof model.motion === 'function') {
                await model.motion(group, parseInt(motionIndex) || 0);
                this.showNotification(`Playing random motion: ${randomMotion}`, 'success');
            } else {
                throw new Error('Model does not support motion playback');
            }
        } catch (error) {
            this.showNotification(`Failed to play random motion: ${error.message}`, 'error');
        }
    }

    async playExpression() {
        if (!this.state.currentExpression) {
            this.showNotification('Please select an expression first', 'warning');
            return;
        }

        try {
            await this.applyExpression(this.state.currentExpression);
            this.showNotification(`Applied expression: ${this.state.currentExpression}`, 'success');
        } catch (error) {
            this.showNotification(`Failed to apply expression: ${error.message}`, 'error');
        }
    }

    async applyExpression(expressionName) {
        if (!this.integration || !this.integration.modelManager) {
            throw new Error('Integration not initialized');
        }

        // Get the active model from multi-model manager
        const activeModelData = this.integration.modelManager.getActiveModel();
        if (!activeModelData || !activeModelData.pixiModel) {
            throw new Error('No active model found');
        }

        const model = activeModelData.pixiModel;
        if (model.expression && typeof model.expression === 'function') {
            await model.expression(expressionName);
        } else {
            throw new Error('Model does not support expressions');
        }
    }

    resetExpression() {
        try {
            this.applyExpression('default');
            this.showNotification('Expression reset to default', 'success');
        } catch (error) {
            this.showNotification(`Failed to reset expression: ${error.message}`, 'error');
        }
    }

    testModel() {
        if (!this.integration) {
            this.showNotification('Integration not initialized', 'error');
            return;
        }

        this.integration.testSimpleTexture();
        this.integration.testSimpleMesh();
        this.integration.runDiagnostics();
        this.showNotification('Model diagnostics completed - check log', 'info');
    }

    resetModel() {
        // this.resetZoom(); // Removed zoom functionality
        this.centerModel();
        this.resetExpression();
        
        // Stop any playing motions
        if (this.integration && this.integration.motionManager) {
            try {
                this.integration.motionManager.stopCurrentMotion();
            } catch (error) {
                console.warn('Failed to stop motions:', error);
            }
        }
        
        this.showNotification('Model reset to default state', 'success');
    }

    // UI Updates
    updateModelInfo() {
        if (this.elements.modelName) {
            this.elements.modelName.textContent = this.state.currentModel || 'No model loaded';
            this.elements.modelName.className = this.state.currentModel ? 'model-name' : 'model-name placeholder';
        }
    }

    updateModelStatus(type, message) {
        if (this.elements.modelStatus) {
            const indicator = this.elements.modelStatus.querySelector('.status-indicator');
            const statusTypes = ['status-success', 'status-warning', 'status-error'];
            
            if (indicator) {
                indicator.className = `status-indicator status-${type}`;
            }
            
            this.elements.modelStatus.querySelector('.status-indicator').nextSibling.textContent = ` ${message}`;
        }
    }

    updateModelPosition(x, y) {
        if (this.elements.modelPosition) {
            this.elements.modelPosition.textContent = `${Math.round(x)}, ${Math.round(y)}`;
        }
    }

    updateModelScale(scale) {
        if (this.elements.modelScale) {
            this.elements.modelScale.textContent = scale.toFixed(1);
        }
    }

    updateMousePosition(x, y) {
        if (this.elements.mousePosition) {
            this.elements.mousePosition.textContent = `${x}, ${y}`;
        }
    }

    showLoading(show) {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element if it doesn't exist
        let notification = document.getElementById('notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'notification';
            notification.className = 'notification';
            document.body.appendChild(notification);
        }

        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.style.display = 'block';
        
        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    }

    // Populate Model List
    async populateModelList() {
        if (!this.elements.modelSelect) return;

        try {
            const models = this.integration.getAvailableModels();
            
            this.elements.modelSelect.innerHTML = '<option value="">Select a model...</option>';
            
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = model.name;
                this.elements.modelSelect.appendChild(option);
            });
            
        } catch (error) {
            console.error('Failed to populate model list:', error);
            this.elements.modelSelect.innerHTML = '<option value="">Error loading models</option>';
        }
    }

    // Log Management
    copyLogToClipboard() {
        if (this.integration && this.integration.copyLogToClipboard) {
            this.integration.copyLogToClipboard();
        }
    }

    clearLog() {
        if (this.integration && this.integration.clearLog) {
            this.integration.clearLog();
        }
    }

    showModelInfo() {
        if (!this.integration) {
            this.showNotification('Integration not initialized', 'error');
            return;
        }

        this.integration.debugModelBounds();
        
        // Show motion statistics
        if (this.integration.motionManager) {
            const stats = this.integration.motionManager.getMotionStats();
            
            this.integration.logger.log('=== MOTION STATISTICS ===', 'info');
            this.integration.logger.log(`Total motions: ${stats.totalMotions}`, 'info');
            this.integration.logger.log(`Motion groups: ${stats.groups}`, 'info');
            this.integration.logger.log(`Current motion: ${stats.currentMotion}`, 'info');
            this.integration.logger.log(`Queue length: ${stats.queueLength}`, 'info');
            
            Object.keys(stats.types).forEach(type => {
                this.integration.logger.log(`${type}: ${stats.types[type]}`, 'info');
            });
        }
        
        this.showNotification('Model info displayed in log', 'info');
    }

    // Initialize the UI controller
    async initialize() {
        try {
            // Wait for integration to be ready
            if (!this.integration.initialized) {
                throw new Error('Integration not initialized');
            }

            // Populate model list
            await this.populateModelList();

            // Set initial state
            this.updateModelStatus('warning', 'No model loaded');
            this.updateModelPosition(0, 0);
            this.updateModelScale(1.0);

            // Set up panel state
            this.setupPanelState();
            
            // Initialize settings
            this.initializeSettings();

            console.log('UI Controller initialized successfully');
            return true;

        } catch (error) {
            console.error('Failed to initialize UI Controller:', error);
            return false;
        }
    }

    setupPanelState() {
        // Update toggle button position
        if (this.elements.panelToggle) {
            this.elements.panelToggle.classList.toggle('panel-open', !this.state.panelCollapsed);
        }
    }

    initializeSettings() {
        // Initialize canvas frame
        if (this.state.canvasFrameVisible) {
            this.toggleCanvasFrame();
        }
        
        // Sync checkbox states
        if (this.elements.showCanvasFrame) {
            this.elements.showCanvasFrame.checked = this.state.canvasFrameVisible;
        }
        if (this.elements.showModelFrame) {
            this.elements.showModelFrame.checked = this.state.modelFrameVisible;
        }
        if (this.elements.showHitAreas) {
            this.elements.showHitAreas.checked = this.state.hitAreasVisible;
        }
        if (this.elements.debugMode) {
            this.elements.debugMode.checked = this.state.debugMode;
        }
        if (this.elements.showFPS) {
            this.elements.showFPS.checked = this.state.fpsVisible;
        }
        if (this.elements.logMouseEvents) {
            this.elements.logMouseEvents.checked = this.state.mouseLogging;
        }
    }
}

// Export for use in other modules
window.Live2DUIController = Live2DUIController;
