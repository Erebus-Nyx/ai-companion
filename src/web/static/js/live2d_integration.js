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

    async initialize(canvasElementId) {
        try {
            // Initialize logger (no log element needed - console only)
            this.logger = new Live2DLogger();
            this.logger.log('Initializing Live2D Integration...');

            // Initialize configuration
            this.config = live2d_settings || {};
            this.logger.log('Configuration loaded');

            // Initialize core
            this.core = new Live2DCore();
            this.core.setLogger(this.logger);

            // Initialize tester
            this.tester = new Live2DTester(this.core, this.logger);

            // Check Live2D library availability
            const libraryAvailable = this.core.checkLive2DLibrary();
            if (!libraryAvailable) {
                throw new Error('Live2D library not properly loaded');
            }

            // Initialize model manager
            this.modelManager = new Live2DModelManager(this.core, this.logger);

            // Initialize motion manager
            this.motionManager = new Live2DMotionManager(this.core, this.logger);

            // Initialize PIXI app
            const canvasElement = document.getElementById(canvasElementId);
            if (!canvasElement) {
                throw new Error(`Canvas element with id "${canvasElementId}" not found`);
            }

            const success = await this.core.initApp(canvasElement, {
                width: this.config.live2dWidth || 0,
                height: this.config.live2dHeight || 0,
                canvasMargin: this.config.canvasMargin || 40,
                backgroundColor: 0x000000,
                backgroundAlpha: 0
            });
            
            if (!success) {
                throw new Error('Failed to initialize PIXI application');
            }

            // Load available models
            await this.modelManager.loadAvailableModels();

            this.initialized = true;
            this.logger.log('Live2D Integration initialized successfully!', 'success');
            
            return true;
        } catch (error) {
            if (this.logger) {
                this.logger.log('Failed to initialize Live2D Integration: ' + error.message, 'error');
            } else {
                console.error('Failed to initialize Live2D Integration:', error);
            }
            return false;
        }
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

    scaleModel(scale) {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }

        this.modelManager.scaleModel(scale);
    }

    centerModel() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }

        if (this.core && this.core.centerModel) {
            this.core.centerModel();
        }
    }

    // Motion management methods
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

    // UI Controls
    toggleCanvasFrame() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }
        
        this.core.toggleCanvasFrame();
    }

    toggleModelFrame() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }
        
        this.core.toggleModelFrame();
    }

    toggleHitBoxes() {
        if (!this.initialized) {
            console.error('Live2D Integration not initialized');
            return;
        }
        
        this.core.toggleHitBoxes();
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
