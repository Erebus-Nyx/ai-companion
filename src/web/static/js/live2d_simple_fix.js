// Simple Live2D fix for immediate testing
// This provides basic functionality while we fix the main issues

// Fix for panel controls
document.addEventListener('DOMContentLoaded', function() {
    console.log('Simple Live2D fix loading...');
    
    // Add click handlers for panel controls
    const panelCloseButton = document.querySelector('.panel-close');
    const panelToggleButton = document.querySelector('.panel-toggle');
    const leftPanel = document.querySelector('.left-panel');
    const appContainer = document.querySelector('.app-container');
    
    if (panelCloseButton && leftPanel && appContainer) {
        panelCloseButton.addEventListener('click', function() {
            console.log('Panel close button clicked');
            leftPanel.classList.add('collapsed');
            appContainer.classList.add('panel-collapsed');
            if (panelToggleButton) {
                panelToggleButton.style.display = 'block';
                panelToggleButton.classList.remove('panel-open');
            }
        });
    }
    
    if (panelToggleButton && leftPanel && appContainer) {
        panelToggleButton.addEventListener('click', function() {
            console.log('Panel toggle button clicked');
            leftPanel.classList.remove('collapsed');
            appContainer.classList.remove('panel-collapsed');
            panelToggleButton.style.display = 'none';
            panelToggleButton.classList.add('panel-open');
        });
    }
    
    // Add settings panel toggle functionality
    const settingsPanel = document.querySelector('.settings-panel');
    
    // Function to toggle settings panel
    window.toggleSettingsPanel = function() {
        console.log('Settings panel toggle clicked');
        if (settingsPanel) {
            settingsPanel.classList.toggle('visible');
        }
    };
    
    // Add event listener for settings panel close button
    const settingsCloseButton = document.querySelector('.settings-panel .panel-close');
    if (settingsCloseButton) {
        settingsCloseButton.addEventListener('click', function() {
            console.log('Settings panel close button clicked');
            if (settingsPanel) {
                settingsPanel.classList.remove('visible');
            }
        });
    }
    
    // Enhanced Live2D model loading based on Live2D Viewer Web approach
    window.simpleLive2DFix = {
        loadModel: async function(modelUrl) {
            console.log('Enhanced Live2D model loading:', modelUrl);
            
            try {
                // Get PIXI app
                const pixiContainer = document.getElementById('pixiContainer');
                if (!pixiContainer || !pixiContainer.children.length) {
                    console.error('PIXI container not found or empty');
                    return null;
                }
                
                const canvas = pixiContainer.querySelector('canvas');
                if (!canvas) {
                    console.error('PIXI canvas not found');
                    return null;
                }
                
                const app = canvas.__pixiApp;
                if (!app) {
                    console.error('PIXI app not found on canvas');
                    return null;
                }
                
                // Clear existing models
                app.stage.removeChildren();
                
                // Try to load Live2D model using the proper approach
                if (window.Live2DModel) {
                    console.log('Attempting to load Live2D model with Live2DModel class');
                    
                    try {
                        // Try Live2D Viewer Web approach
                        const pixiModel = new window.Live2DModel();
                        
                        // Check if Live2DFactory exists
                        if (typeof Live2DFactory !== 'undefined' && Live2DFactory.setupLive2DModel) {
                            await Live2DFactory.setupLive2DModel(pixiModel, modelUrl);
                        } else {
                            // Fallback to direct loading
                            await pixiModel.from(modelUrl);
                        }
                        
                        // Center the model
                        pixiModel.anchor.set(0.5, 0.5);
                        pixiModel.x = app.screen.width / 2;
                        pixiModel.y = app.screen.height / 2;
                        
                        // Scale to fit
                        const scale = Math.min(
                            app.screen.width / pixiModel.width * 0.8,
                            app.screen.height / pixiModel.height * 0.8
                        );
                        pixiModel.scale.set(scale);
                        
                        app.stage.addChild(pixiModel);
                        
                        console.log('Live2D model loaded successfully');
                        return pixiModel;
                        
                    } catch (live2dError) {
                        console.error('Live2D model loading failed:', live2dError);
                        // Fall through to texture loading
                    }
                }
                
                // Fallback: Try to load as texture/sprite
                console.log('Falling back to texture loading');
                
                const response = await fetch(modelUrl);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const modelData = await response.json();
                console.log('Model data loaded:', modelData);
                
                // Try to load texture
                if (modelData.FileReferences && modelData.FileReferences.Textures) {
                    const texturePath = modelData.FileReferences.Textures[0];
                    const baseUrl = modelUrl.substring(0, modelUrl.lastIndexOf('/') + 1);
                    const textureUrl = baseUrl + texturePath;
                    
                    console.log('Loading texture:', textureUrl);
                    
                    try {
                        const texture = await PIXI.Assets.load(textureUrl);
                        const sprite = new PIXI.Sprite(texture);
                        sprite.anchor.set(0.5);
                        sprite.x = app.screen.width / 2;
                        sprite.y = app.screen.height / 2;
                        sprite.scale.set(0.8);
                        app.stage.addChild(sprite);
                        
                        console.log('Texture loaded successfully');
                        return sprite;
                    } catch (textureError) {
                        console.error('Failed to load texture:', textureError);
                    }
                }
                
                // Final fallback: Create placeholder
                const graphics = new PIXI.Graphics();
                graphics.beginFill(0x4a90e2);
                graphics.drawRect(-100, -150, 200, 300);
                graphics.endFill();
                graphics.x = app.screen.width / 2;
                graphics.y = app.screen.height / 2;
                app.stage.addChild(graphics);
                
                console.log('Created placeholder model');
                return graphics;
                
            } catch (error) {
                console.error('Enhanced model loading failed:', error);
                return null;
            }
        }
    };
    
    console.log('Simple Live2D fix loaded');
});

// Override the global model loading if needed
window.addEventListener('load', function() {
    if (window.live2dIntegration && window.live2dIntegration.core) {
        const originalLoadModel = window.live2dIntegration.core.loadModel;
        window.live2dIntegration.core.loadModel = async function(modelUrl) {
            console.log('Using simple Live2D fix for model loading');
            return await window.simpleLive2DFix.loadModel(modelUrl);
        };
    }
});
