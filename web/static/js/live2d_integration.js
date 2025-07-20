// Live2D Integration for Flask App
// This module integrates the modular Live2D system with the main Flask app

class Live2DIntegration {
    constructor() {
        this.logger = null;
        this.core = null;
        this.modelManager = null;
        this.motionManager = null;
        this.tester = null;
        this.config = null;
        this.initialized = false;
        this.currentModelName = null;
    }

    async initialize(canvasContainerId) {
        // Initialize config and logger first
        this.config = new Live2DConfig();
        this.logger = new Live2DLogger(this.config);
        this.logger.logInfo('Live2D Integration Initializing...');
        
        // Initialize core components
        this.core = new Live2DCore();
        this.core.setLogger(this.logger);
        this.core.setConfig(this.config);
        this.logger.logInfo('Live2D Core initialized');

        // Test library availability
        const librariesReady = this.core.checkLive2DLibrary();
        if (!librariesReady) {
            throw new Error('Live2D libraries are not ready');
        }
        this.logger.log('Live2D libraries are ready', 'success');

        // Initialize PIXI app *before* managers that depend on it
        const canvasElement = document.getElementById(canvasContainerId);
        if (!canvasElement) {
            throw new Error(`Canvas element with id "${canvasContainerId}" not found`);
        }

        const success = await this.core.initApp(canvasElement, {
            backgroundColor: 0x000000,
            backgroundAlpha: 0
        });
        
        if (!success) {
            throw new Error('Failed to initialize PIXI application');
        }
        this.logger.logInfo('PIXI Application and Interaction Manager initialized');

        // Canvas management - size from frame
        this.logger.logInfo('Canvas sizing from frame: ' + this.core.canvasWidth + 'x' + this.core.canvasHeight);

        // Initialize the multi-model manager *after* core app init
        this.modelManager = new Live2DMultiModelManager(this.core, this.logger, this.core.interactionManager);
        this.logger.logInfo('Live2D Multi-Model Manager initialized');

        // Initialize motion manager
        this.motionManager = new Live2DMotionManager(this.core, this.logger);

        // Load available models
        await this.modelManager.loadAvailableModels();

        this.initialized = true;
        this.logger.log('Live2D Integration initialized successfully!', 'success');
        
        return true;
    }

    async loadModel(modelName) {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return null;
        }

        // Prevent duplicate loading
        if (this.currentModelName === modelName) {
            this.logger.log(`Model ${modelName} already loaded`, 'info');
            return this.modelManager.getCurrentModel();
        }

        try {
            const model = await this.modelManager.loadModel(modelName);
            
            // Debug model visibility
            setTimeout(() => {
                this.core.debugModelVisibility();
            }, 1000);
            
            // Load motions for the model
            await this.motionManager.loadModelMotions(modelName);
            
            this.currentModelName = modelName;
            return model;
        } catch (error) {
            this.logger.log(`Failed to load model ${modelName}: ${error.message}`, 'error');
            throw error;
        }
    }

    getAvailableModels() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return [];
        }

        return this.modelManager.getModelList();
    }

    getCurrentModel() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return null;
        }

        return this.modelManager.getCurrentModel();
    }

    // Canvas management methods - delegated to canvas manager
    scaleModel(scale) {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }
        
        if (this.core && this.core.setZoom) {
            this.core.setZoom(scale);
        }
    }

    centerModel() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }
        
        if (this.core && this.core.centerModel) {
            this.core.centerModel();
        }
    }    // Motion management methods
    getAvailableMotions() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return [];
        }

        return this.motionManager.getAvailableMotions();
    }

    async playMotion(motionName) {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }

        return await this.motionManager.playMotion(motionName);
    }

    async playRandomMotion() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }

        return await this.motionManager.playRandomMotion();
    }

    getMotionsByGroup(groupName) {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return [];
        }

        return this.motionManager.getMotionsByGroup(groupName);
    }

    getMotionGroups() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return [];
        }

        return this.motionManager.getMotionGroups();
    }

    // Test functions
    testSimpleTexture() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }

        // Create a simple sprite for testing
        const graphics = new PIXI.Graphics();
        graphics.beginFill(0xff0000);
        graphics.drawRect(0, 0, 100, 100);
        graphics.endFill();
        graphics.x = 50;
        graphics.y = 50;
        
        this.core.app.stage.addChild(graphics);
        this.logger.log('Simple texture test created', 'info');
    }

    testSimpleMesh() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }

        // Create a simple mesh for testing
        const graphics = new PIXI.Graphics();
        graphics.beginFill(0x00ff00);
        graphics.drawCircle(0, 0, 50);
        graphics.endFill();
        graphics.x = 200;
        graphics.y = 200;
        
        this.core.app.stage.addChild(graphics);
        this.logger.log('Simple mesh test created', 'info');
    }

    debugModelBounds() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }

        if (this.core.model) {
            this.logger.log('=== MODEL DEBUG INFO ===', 'info');
            this.logger.log(`Model type: ${this.core.model.constructor.name}`, 'info');
            this.logger.log(`Model dimensions: ${this.core.model.width}x${this.core.model.height}`, 'info');
            this.logger.log(`Model position: (${this.core.model.x}, ${this.core.model.y})`, 'info');
            this.logger.log(`Model scale: ${this.core.model.scale.x}`, 'info');
            
            if (this.core.model.internalModel) {
                this.logger.log(`Internal model type: ${this.core.model.internalModel.constructor.name}`, 'info');
            }
        } else {
            this.logger.log('No model loaded', 'warning');
        }
    }

    runDiagnostics() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }

        this.tester.testCubism4Library();
        this.debugModelBounds();
    }

    // Logger controls
    clearLog() {
        if (this.logger) {
            this.logger.clear();
        }
    }

    copyLogToClipboard() {
        if (this.logger) {
            this.logger.copyToClipboard();
        }
    }

    // UI Controls - delegated to canvas manager
    toggleCanvasFrame() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }
        
        if (this.core && this.core.toggleCanvasFrame) {
            return this.core.toggleCanvasFrame();
        }
        return false;
    }

    toggleModelFrame() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }
        
        if (this.core && this.core.toggleModelFrame) {
            return this.core.toggleModelFrame();
        }
        return false;
    }

    toggleHitAreas() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }
        
        if (this.core && this.core.toggleHitBoxes) {
            return this.core.toggleHitBoxes();
        }
        return false;
    }

    // Configuration access
    getConfig() {
        return this.config;
    }

    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.logger.log('Configuration updated', 'info');
    }

    // Destroy and cleanup
    destroy() {
        if (this.core) {
            this.core.destroy();
        }
        
        this.initialized = false;
        this.logger = null;
        this.core = null;
        this.modelManager = null;
        this.motionManager = null;
        this.tester = null;
        this.config = null;
    }
}

// Export for use in Flask app
window.Live2DIntegration = Live2DIntegration;
