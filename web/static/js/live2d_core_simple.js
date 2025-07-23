// Live2D Core Simple - Simple sekai-viewer style implementation
class Live2DCoreSimple {
    constructor() {
        this.app = null;
        this.model = null;
        this.logger = null;
    }

    setLogger(logger) {
        this.logger = logger;
    }

    log(message, type = 'info') {
        if (this.logger) {
            this.logger.log(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    async initApp(canvasElement, options = {}) {
        const defaultOptions = {
            width: 800,
            height: 600,
            backgroundColor: 0xffffff,
            resolution: 1,
            antialias: true,
            autoDensity: true
        };

        const finalOptions = { ...defaultOptions, ...options };

        try {
            if (PIXI.VERSION.startsWith('8.')) {
                this.app = new PIXI.Application();
                await this.app.init(finalOptions);
                canvasElement.appendChild(this.app.canvas);
            } else {
                this.app = new PIXI.Application(finalOptions);
                canvasElement.appendChild(this.app.view);
            }
            
            this.log('PIXI application initialized successfully', 'success');
            return true;
        } catch (error) {
            this.log('Failed to initialize PIXI: ' + error.message, 'error');
            return false;
        }
    }

    // Check Live2D library availability
    checkLive2DLibrary() {
        this.log('=== CHECKING LIVE2D LIBRARY ===', 'info');
        
        // Check basic PIXI availability
        if (typeof PIXI === 'undefined') {
            this.log('PIXI is not loaded', 'error');
            return false;
        }
        
        this.log('PIXI loaded successfully', 'success');
        this.log(`PIXI version: ${PIXI.VERSION}`, 'info');
        
        // Check if PIXI.live2d exists
        if (typeof PIXI.live2d === 'undefined') {
            this.log('PIXI.live2d is not loaded', 'error');
            
            // Try to install it manually if the library is available globally
            const globalLive2D = window.PIXI?.live2d || window.Live2D || window.PIXI_LIVE2D;
            if (globalLive2D) {
                this.log('Found global Live2D, trying to attach to PIXI', 'info');
                PIXI.live2d = globalLive2D;
                
                // Try to install if available
                if (typeof PIXI.live2d.install === 'function') {
                    try {
                        this.log('Installing Live2D plugin from global...', 'info');
                        PIXI.live2d.install();
                        this.log('Live2D plugin installed successfully', 'success');
                    } catch (error) {
                        this.log(`Plugin installation failed: ${error.message}`, 'error');
                    }
                }
            } else {
                this.log('No global Live2D found either', 'error');
                return false;
            }
        }
        
        this.log('PIXI.live2d loaded successfully', 'success');
        this.log(`PIXI.live2d keys: ${Object.keys(PIXI.live2d).join(', ')}`, 'info');
        
        // Try to install the plugin if not already installed
        if (typeof PIXI.live2d.install === 'function') {
            try {
                this.log('Installing Live2D plugin...', 'info');
                PIXI.live2d.install();
                this.log('Live2D plugin installed successfully', 'success');
                this.log(`PIXI.live2d keys after install: ${Object.keys(PIXI.live2d).join(', ')}`, 'info');
            } catch (error) {
                this.log(`Plugin installation failed: ${error.message}`, 'error');
            }
        }
        
        // Check for Live2DModel constructor
        if (typeof PIXI.live2d.Live2DModel !== 'undefined') {
            this.log('PIXI.live2d.Live2DModel constructor found', 'success');
            this.log(`Live2DModel.from type: ${typeof PIXI.live2d.Live2DModel.from}`, 'info');
            return true;
        } else {
            this.log('PIXI.live2d.Live2DModel constructor not found', 'warning');
        }
        
        // Check global Live2DModel
        if (typeof Live2DModel !== 'undefined') {
            this.log('Global Live2DModel found', 'success');
            this.log(`Global Live2DModel.from type: ${typeof Live2DModel.from}`, 'info');
            return true;
        } else {
            this.log('Global Live2DModel not found', 'warning');
        }
        
        // Check window.Live2DModel
        if (typeof window.Live2DModel !== 'undefined') {
            this.log('Window Live2DModel found', 'success');
            this.log(`Window Live2DModel.from type: ${typeof window.Live2DModel.from}`, 'info');
            return true;
        } else {
            this.log('Window Live2DModel not found', 'warning');
        }
        
        // Check window.PIXI_LIVE2D
        if (typeof window.PIXI_LIVE2D !== 'undefined' && typeof window.PIXI_LIVE2D.Live2DModel !== 'undefined') {
            this.log('Window PIXI_LIVE2D.Live2DModel found', 'success');
            this.log(`Window PIXI_LIVE2D.Live2DModel.from type: ${typeof window.PIXI_LIVE2D.Live2DModel.from}`, 'info');
            return true;
        } else {
            this.log('Window PIXI_LIVE2D not found', 'warning');
        }
        
        this.log('No Live2DModel constructor found anywhere', 'error');
        return false;
    }

    async loadModel(modelUrl) {
        if (!this.app) {
            this.log('PIXI application not initialized', 'error');
            return null;
        }

        this.log(`Loading Live2D model: ${modelUrl}`, 'info');
        
        try {
            // Clear existing model
            if (this.model) {
                this.app.stage.removeChild(this.model);
                this.model.destroy();
                this.model = null;
            }
            
            // Use the sekai-viewer method: Live2DModel.from()
            if (typeof PIXI.live2d !== 'undefined' && typeof PIXI.live2d.Live2DModel !== 'undefined') {
                this.log('Using PIXI.live2d.Live2DModel.from()', 'info');
                this.model = await PIXI.live2d.Live2DModel.from(modelUrl, {
                    autoFocus: false,
                    autoHitTest: false,
                    ticker: PIXI.Ticker.shared,
                });
            } else if (typeof Live2DModel !== 'undefined') {
                this.log('Using global Live2DModel.from()', 'info');
                this.model = await Live2DModel.from(modelUrl, {
                    autoFocus: false,
                    autoHitTest: false,
                    ticker: PIXI.Ticker.shared,
                });
            } else if (typeof window.Live2DModel !== 'undefined') {
                this.log('Using window.Live2DModel.from()', 'info');
                this.model = await window.Live2DModel.from(modelUrl, {
                    autoFocus: false,
                    autoHitTest: false,
                    ticker: PIXI.Ticker.shared,
                });
            } else if (typeof window.PIXI_LIVE2D !== 'undefined' && typeof window.PIXI_LIVE2D.Live2DModel !== 'undefined') {
                this.log('Using window.PIXI_LIVE2D.Live2DModel.from()', 'info');
                this.model = await window.PIXI_LIVE2D.Live2DModel.from(modelUrl, {
                    autoFocus: false,
                    autoHitTest: false,
                    ticker: PIXI.Ticker.shared,
                });
            } else {
                throw new Error('No Live2DModel constructor found');
            }

            if (!this.model) {
                throw new Error('Failed to create Live2D model');
            }

            // Position and scale the model like sekai-viewer
            this.setupModel();
            
            // Add to stage
            this.app.stage.addChild(this.model);
            
            this.log('Live2D model loaded successfully', 'success');
            this.log(`Model dimensions: ${this.model.width}x${this.model.height}`, 'info');
            
            return this.model;
            
        } catch (error) {
            this.log(`Failed to load model: ${error.message}`, 'error');
            throw error;
        }
    }

    setupModel() {
        if (!this.model) return;
        
        // Get model dimensions
        const modelWidth = this.model.width;
        const modelHeight = this.model.height;
        
        // Calculate scale to fit screen like sekai-viewer
        const scaleX = this.app.screen.width / modelWidth;
        const scaleY = this.app.screen.height / modelHeight;
        let scale = Math.min(scaleX, scaleY);
        
        // Apply additional scaling factor like sekai-viewer (1.3x)
        scale = (Math.round(scale * 100) / 100) * 1.3;
        
        // Set scale
        this.model.scale.set(scale);
        
        // Center the model
        this.model.x = (this.app.screen.width - modelWidth * scale) / 2;
        this.model.y = (this.app.screen.height - modelHeight * scale) / 2;
        
        this.log(`Model scaled to ${scale.toFixed(2)} and positioned at (${this.model.x.toFixed(0)}, ${this.model.y.toFixed(0)})`, 'info');
        
        // Add interactivity
        this.model.interactive = true;
        this.model.on('pointerdown', () => {
            this.log('Model clicked!', 'info');
            this.playRandomMotion();
        });
    }

    playRandomMotion() {
        if (!this.model || !this.model.internalModel) return;
        
        try {
            // Try to play a random motion like sekai-viewer
            const motionManager = this.model.internalModel.motionManager;
            if (motionManager && motionManager.motionGroups) {
                const groups = Object.keys(motionManager.motionGroups);
                if (groups.length > 0) {
                    const randomGroup = groups[Math.floor(Math.random() * groups.length)];
                    const groupMotions = motionManager.motionGroups[randomGroup];
                    if (groupMotions && groupMotions.length > 0) {
                        const randomIndex = Math.floor(Math.random() * groupMotions.length);
                        this.model.motion(randomGroup, randomIndex);
                        this.log(`Playing motion: ${randomGroup}[${randomIndex}]`, 'info');
                    }
                }
            }
        } catch (error) {
            this.log(`Motion play failed: ${error.message}`, 'warning');
        }
    }
}

// Export for global access
// Make Live2DCoreSimple globally available for sekai-viewer compatibility
window.Live2DCoreSimple = Live2DCoreSimple;
