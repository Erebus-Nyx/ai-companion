// Live2D Multi-Model Manager - Handles multiple models with character icons
class Live2DMultiModelManager {
    constructor(core, logger) {
        this.core = core;
        this.logger = logger;
        this.models = new Map(); // Store multiple models with their data
        this.activeModelId = null;
        this.maxModels = 5; // System limitation
        this.modelCounter = 0;
        this.modelList = [];
        
        this.initializeUI();
    }

    log(message, type = 'info') {
        if (this.logger) {
            this.logger.log(message, type);
        }
    }

    initializeUI() {
        // Create character icons container at bottom of canvas
        this.createCharacterIconsContainer();
    }

    createCharacterIconsContainer() {
        const canvasContainer = document.querySelector('.canvas-container');
        if (!canvasContainer) return;

        // Create character icons bar
        const iconsContainer = document.createElement('div');
        iconsContainer.id = 'characterIcons';
        iconsContainer.className = 'character-icons-container';
        iconsContainer.innerHTML = `
            <div class="character-icons-bar">
                <div class="character-icons-list" id="characterIconsList">
                    <!-- Character icons will be populated here -->
                </div>
                <div class="character-icons-controls">
                    <button class="add-model-btn" id="addModelBtn" title="Add new model">
                        <span class="add-icon">+</span>
                    </button>
                </div>
            </div>
        `;

        canvasContainer.appendChild(iconsContainer);

        // Add event listener for add model button
        document.getElementById('addModelBtn').addEventListener('click', () => {
            this.showAddModelDialog();
        });

        this.log('Character icons container created', 'info');
    }

    showAddModelDialog() {
        // If we have available models, show selection
        if (this.modelList.length > 0) {
            this.showModelSelectionDialog();
        } else {
            // Load models first
            this.loadAvailableModels().then(() => {
                this.showModelSelectionDialog();
            }).catch(error => {
                this.log(`Failed to load models: ${error.message}`, 'error');
            });
        }
    }

    async showModelSelectionDialog() {
        // Create modal dialog for model selection
        const dialog = document.createElement('div');
        dialog.className = 'model-selection-dialog';
        dialog.innerHTML = `
            <div class="dialog-overlay"></div>
            <div class="dialog-content">
                <div class="dialog-header">
                    <h3>Select a model to add</h3>
                    <button class="dialog-close" onclick="this.closest('.model-selection-dialog').remove()">×</button>
                </div>
                <div class="dialog-body">
                    <div class="model-grid">
                        ${await this.generateModelCards()}
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        // Add click handlers for model cards
        dialog.querySelectorAll('.model-card').forEach(card => {
            card.addEventListener('click', () => {
                const modelName = card.getAttribute('data-model-name');
                this.addModel(modelName);
                dialog.remove();
            });
        });

        // Close dialog when clicking overlay
        dialog.querySelector('.dialog-overlay').addEventListener('click', () => {
            dialog.remove();
        });
    }

    async generateModelCards() {
        const cards = [];
        
        for (const model of this.modelList) {
            try {
                // Get model texture for preview
                const textureUrl = await this.getModelTexture(model);
                
                const card = `
                    <div class="model-card" data-model-name="${model.name}">
                        <div class="model-preview">
                            ${textureUrl ? 
                                `<img src="${textureUrl}" alt="${model.name}" class="model-preview-image" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';">
                                 <span class="model-icon" style="display: none;">🎭</span>` : 
                                `<span class="model-icon">🎭</span>`
                            }
                        </div>
                        <div class="model-info">
                            <div class="model-name">${model.name}</div>
                            <div class="model-description">${model.info}</div>
                        </div>
                    </div>
                `;
                
                cards.push(card);
            } catch (error) {
                this.log(`Failed to generate card for ${model.name}: ${error.message}`, 'warning');
                // Add card with fallback icon
                const fallbackCard = `
                    <div class="model-card" data-model-name="${model.name}">
                        <div class="model-preview">
                            <span class="model-icon">🎭</span>
                        </div>
                        <div class="model-info">
                            <div class="model-name">${model.name}</div>
                            <div class="model-description">${model.info}</div>
                        </div>
                    </div>
                `;
                cards.push(fallbackCard);
            }
        }
        
        return cards.join('');
    }

    async loadAvailableModels() {
        try {
            const response = await fetch('http://localhost:13443/api/live2d/models');
            
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status} ${response.statusText}`);
            }
            
            const models = await response.json();
            
            if (!Array.isArray(models) || models.length === 0) {
                throw new Error('No models returned from API');
            }
            
            this.modelList = models.map(model => ({
                name: model.model_name,
                path: model.model_path,
                configFile: model.config_file,
                url: `http://localhost:13443/${model.model_path}/${model.config_file}`,
                info: model.info || model.model_name
            }));
            
            this.log(`Successfully loaded ${this.modelList.length} available models from API`, 'success');
            return this.modelList;
            
        } catch (error) {
            this.log(`Failed to load model list from API: ${error.message}`, 'error');
            this.modelList = [];
            throw error;
        }
    }

    async addModel(modelName) {
        // Check if we've reached the limit
        if (this.models.size >= this.maxModels) {
            this.log(`Maximum number of models (${this.maxModels}) reached`, 'warning');
            return false;
        }

        // Check if model is already loaded
        for (const [id, modelData] of this.models) {
            if (modelData.name === modelName) {
                this.log(`Model "${modelName}" is already loaded`, 'warning');
                this.setActiveModel(id);
                return false;
            }
        }

        try {
            const modelInfo = this.modelList.find(m => m.name === modelName);
            if (!modelInfo) {
                throw new Error(`Model "${modelName}" not found in available models`);
            }

            this.log(`Adding model: ${modelInfo.name}`, 'info');
            
            // Generate unique ID for this model
            const modelId = `model_${++this.modelCounter}`;
            
            // Load the model using core without clearing existing models
            const pixiModel = await this.loadModelWithoutClearing(modelInfo.url);
            
            // Store model data
            const modelData = {
                id: modelId,
                name: modelInfo.name,
                path: modelInfo.path,
                url: modelInfo.url,
                info: modelInfo.info,
                pixiModel: pixiModel,
                baseScale: 0.2, // Default scale based on requirements
                position: { x: 0, y: 0 },
                visible: true
            };

            this.models.set(modelId, modelData);
            
            // Set initial scale (0.2 for default zoom 1.0)
            if (pixiModel && pixiModel.scale) {
                pixiModel.scale.set(modelData.baseScale);
            }

            // Position the model slightly offset from center for multiple models
            this.positionModelForMultiple(pixiModel, this.models.size);

            // Start neutral random motions
            await this.startNeutralMotions(modelId);

            // Create character icon with image
            await this.createCharacterIcon(modelData);
            
            // Set as active model
            this.setActiveModel(modelId);
            
            this.log(`Successfully added model: ${modelInfo.name}`, 'success');
            return true;
            
        } catch (error) {
            const errorMessage = `Failed to add model ${modelName}: ${error.message}`;
            this.log(errorMessage, 'error');
            throw new Error(errorMessage);
        }
    }

    async loadModelWithoutClearing(modelUrl) {
        if (!this.core.app) {
            throw new Error('PIXI application not initialized');
        }

        this.log('Loading Live2D model (without clearing): ' + modelUrl);

        // Try standard PIXI.live2d approach first
        const constructors = [
            { name: 'PIXI.live2d.Live2DModel', constructor: PIXI.live2d && PIXI.live2d.Live2DModel },
            { name: 'window.Live2DModel', constructor: window.Live2DModel },
            { name: 'PIXI.Live2DModel', constructor: PIXI.Live2DModel },
            { name: 'Live2DModel (global)', constructor: typeof Live2DModel !== 'undefined' ? Live2DModel : null }
        ];

        for (const { name, constructor } of constructors) {
            if (constructor && typeof constructor.from === 'function') {
                this.log(`Trying to load model with ${name}...`, 'info');
                
                try {
                    const model = await constructor.from(modelUrl);
                    this.log(`Successfully loaded model with ${name}!`, 'success');
                    
                    // Configure model
                    if (model.anchor && model.anchor.set) {
                        model.anchor.set(0.5, 0.5);
                    }
                    
                    // Set base scale
                    this.core.baseScale = 0.2;
                    model.scale.set(this.core.baseScale);
                    
                    // Position model at center initially
                    const centerX = this.core.canvasWidth / 2;
                    const centerY = this.core.canvasHeight / 2;
                    model.position.set(centerX, centerY);
                    
                    // Add to stage
                    this.core.app.stage.addChild(model);
                    
                    // Update canvas manager with new model (for active model)
                    if (this.core.canvasManager) {
                        this.core.canvasManager.updateModel(model);
                    }
                    
                    this.log('Model added to stage successfully!', 'success');
                    return model;
                    
                } catch (error) {
                    this.log(`Failed to load with ${name}: ${error.message}`, 'error');
                }
            }
        }

        throw new Error('All Live2D loading methods failed');
    }

    positionModelForMultiple(model, modelCount) {
        if (!model || !this.core.canvasWidth || !this.core.canvasHeight) return;

        const centerX = this.core.canvasWidth / 2;
        const centerY = this.core.canvasHeight / 2;
        
        // Create slight offset for multiple models so they don't overlap exactly
        const offsetX = (modelCount - 1) * 20; // 20px offset for each additional model
        const offsetY = (modelCount - 1) * 10; // 10px offset for each additional model
        
        model.position.set(centerX + offsetX, centerY + offsetY);
        
        this.log(`Model positioned at: ${centerX + offsetX}, ${centerY + offsetY}`, 'info');
    }

    async startNeutralMotions(modelId) {
        const modelData = this.models.get(modelId);
        if (!modelData || !modelData.pixiModel) return;

        try {
            // Load motions for the model
            const motions = await this.loadModelMotions(modelData);
            
            // Filter for idle/neutral motions
            const neutralMotions = motions.filter(motion => 
                motion.group.toLowerCase().includes('idle') || 
                motion.group.toLowerCase().includes('neutral') ||
                motion.group.toLowerCase().includes('breathing')
            );

            if (neutralMotions.length > 0) {
                // Start random neutral motion
                const randomMotion = neutralMotions[Math.floor(Math.random() * neutralMotions.length)];
                await this.playMotion(modelId, randomMotion);
                
                // Set up periodic random motion playback
                this.setupPeriodicMotions(modelId, neutralMotions);
            }
        } catch (error) {
            this.log(`Failed to start neutral motions for ${modelData.name}: ${error.message}`, 'warning');
        }
    }

    setupPeriodicMotions(modelId, motions) {
        // Play random motion every 10-30 seconds
        const playRandomMotion = () => {
            if (this.models.has(modelId)) {
                const randomMotion = motions[Math.floor(Math.random() * motions.length)];
                this.playMotion(modelId, randomMotion).catch(error => {
                    this.log(`Failed to play periodic motion: ${error.message}`, 'warning');
                });
            }
        };

        // Initial delay and then periodic
        setTimeout(() => {
            playRandomMotion();
            setInterval(playRandomMotion, 15000 + Math.random() * 15000); // 15-30 seconds
        }, 5000 + Math.random() * 10000); // 5-15 seconds initial delay
    }

    async loadModelMotions(modelData) {
        try {
            const response = await fetch(`http://localhost:13443/api/live2d/motions/${modelData.name}`);
            if (!response.ok) {
                throw new Error(`Failed to load motions: ${response.status}`);
            }
            
            const result = await response.json();
            
            // Ensure we return an array
            if (Array.isArray(result)) {
                return result;
            } else if (result && Array.isArray(result.motions)) {
                return result.motions;
            } else {
                this.log(`Motions API returned unexpected format for ${modelData.name}: ${typeof result}`, 'warning');
                return [];
            }
        } catch (error) {
            this.log(`Failed to load motions for ${modelData.name}: ${error.message}`, 'warning');
            return [];
        }
    }

    async playMotion(modelId, motion) {
        const modelData = this.models.get(modelId);
        if (!modelData || !modelData.pixiModel) return;

        try {
            // Use the existing motion system
            if (modelData.pixiModel.motion && typeof modelData.pixiModel.motion === 'function') {
                await modelData.pixiModel.motion(motion.group, motion.index);
            }
        } catch (error) {
            this.log(`Failed to play motion: ${error.message}`, 'warning');
        }
    }

    async createCharacterIcon(modelData) {
        const iconsList = document.getElementById('characterIconsList');
        if (!iconsList) return;

        const iconElement = document.createElement('div');
        iconElement.className = 'character-icon';
        iconElement.setAttribute('data-model-id', modelData.id);
        
        // Create with loading state first
        iconElement.innerHTML = `
            <div class="character-avatar">
                <div class="loading-spinner-small"></div>
            </div>
            <div class="character-name">${modelData.name}</div>
            <button class="remove-character" onclick="event.stopPropagation(); live2dMultiModelManager.removeModel('${modelData.id}')">×</button>
        `;

        // Add click handler to focus model
        iconElement.addEventListener('click', () => {
            this.setActiveModel(modelData.id);
        });

        iconsList.appendChild(iconElement);
        
        // Extract character image in background
        this.extractCharacterImage(modelData).then(characterImage => {
            const avatarDiv = iconElement.querySelector('.character-avatar');
            if (avatarDiv) {
                avatarDiv.innerHTML = characterImage ? 
                    `<img src="${characterImage}" alt="${modelData.name}" class="character-image">` : 
                    `<span class="character-emoji">🎭</span>`;
            }
        }).catch(error => {
            this.log(`Failed to load character image for ${modelData.name}: ${error.message}`, 'warning');
            const avatarDiv = iconElement.querySelector('.character-avatar');
            if (avatarDiv) {
                avatarDiv.innerHTML = `<span class="character-emoji">🎭</span>`;
            }
        });
    }

    async extractCharacterImage(modelData) {
        try {
            // First, check if we have a cached preview in the database
            const cachedPreview = await this.getCachedPreview(modelData.name);
            if (cachedPreview) {
                this.log(`Using cached database preview for ${modelData.name}`, 'success');
                return cachedPreview;
            }
            
            // Create a snapshot from the loaded model (best quality)
            if (modelData.pixiModel && this.core.app) {
                const snapshotUrl = await this.createModelSnapshot(modelData);
                if (snapshotUrl) {
                    this.log(`Created model snapshot for ${modelData.name}`, 'success');
                    
                    // Save this snapshot to database for future use
                    this.saveCachedPreview(modelData.name, snapshotUrl).catch(error => {
                        this.log(`Failed to cache preview for ${modelData.name}: ${error.message}`, 'warning');
                    });
                    
                    return snapshotUrl;
                }
            }
            
            // Fallback: Get the model's texture files and try to crop them
            const textureUrl = await this.getModelTexture(modelData);
            if (textureUrl) {
                this.log(`Using cropped texture for ${modelData.name}`, 'info');
                // Create a cropped version of the texture for better character icon
                const croppedImage = await this.createCroppedIcon(textureUrl);
                return croppedImage || textureUrl;
            }
            
            return null;
        } catch (error) {
            this.log(`Failed to extract character image for ${modelData.name}: ${error.message}`, 'warning');
            return null;
        }
    }

    async createCroppedIcon(textureUrl) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            
            img.onload = () => {
                try {
                    // Create canvas for cropping
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    
                    // Set canvas size for icon
                    canvas.width = 80;
                    canvas.height = 80;
                    
                    // Calculate crop area (focus on upper portion - likely head/face)
                    const sourceWidth = img.width;
                    const sourceHeight = img.height;
                    
                    // Crop to upper 60% of image and center horizontally
                    const cropHeight = sourceHeight * 0.6;
                    const cropWidth = Math.min(sourceWidth, cropHeight); // Square crop
                    const cropX = (sourceWidth - cropWidth) / 2;
                    const cropY = 0;
                    
                    // Draw cropped and scaled image
                    ctx.drawImage(
                        img,
                        cropX, cropY, cropWidth, cropHeight,
                        0, 0, canvas.width, canvas.height
                    );
                    
                    // Convert to data URL
                    const dataUrl = canvas.toDataURL('image/png');
                    resolve(dataUrl);
                    
                } catch (error) {
                    this.log(`Failed to crop icon: ${error.message}`, 'warning');
                    resolve(null);
                }
            };
            
            img.onerror = () => {
                this.log('Failed to load texture image for cropping', 'warning');
                resolve(null);
            };
            
            img.src = textureUrl;
        });
    }

    async getModelTexture(modelData) {
        try {
            // First, try to get texture info from the API
            const textureResponse = await fetch(`http://localhost:13443/api/live2d/textures/${modelData.name}`);
            if (textureResponse.ok) {
                const textureInfo = await textureResponse.json();
                if (textureInfo.primary_texture && textureInfo.primary_texture.exists) {
                    return `http://localhost:13443${textureInfo.primary_texture.url}`;
                }
            }
            
            // Fallback: Load the model.json file directly
            const response = await fetch(modelData.url);
            if (!response.ok) {
                throw new Error(`Failed to load model config: ${response.status}`);
            }
            
            const modelConfig = await response.json();
            
            // Find the first texture file
            let textureFile = null;
            
            // Check different possible texture locations in model config
            if (modelConfig.textures && modelConfig.textures.length > 0) {
                textureFile = modelConfig.textures[0];
            } else if (modelConfig.FileReferences && modelConfig.FileReferences.Textures && modelConfig.FileReferences.Textures.length > 0) {
                textureFile = modelConfig.FileReferences.Textures[0];
            } else if (modelConfig.FileReferences && modelConfig.FileReferences.Texture) {
                textureFile = modelConfig.FileReferences.Texture;
            }
            
            if (textureFile) {
                // Construct the full texture URL
                const baseUrl = modelData.url.substring(0, modelData.url.lastIndexOf('/') + 1);
                const textureUrl = baseUrl + textureFile;
                
                // Verify the texture exists
                const textureResponse = await fetch(textureUrl, { method: 'HEAD' });
                if (textureResponse.ok) {
                    return textureUrl;
                }
            }
            
            return null;
        } catch (error) {
            this.log(`Failed to get texture for ${modelData.name}: ${error.message}`, 'warning');
            return null;
        }
    }

    async createModelSnapshot(modelData) {
        try {
            if (!modelData.pixiModel || !this.core.app || !this.core.app.renderer) {
                this.log(`Cannot create snapshot: missing required components`, 'warning');
                return null;
            }

            // Check if extract plugin is available
            if (!this.core.app.renderer.extract) {
                this.log(`Extract plugin not available for snapshot creation`, 'warning');
                return null;
            }

            // Store original settings and properties
            const originalResolution = PIXI.settings.RESOLUTION;
            const originalPos = { x: modelData.pixiModel.position.x, y: modelData.pixiModel.position.y };
            const originalScale = { x: modelData.pixiModel.scale.x, y: modelData.pixiModel.scale.y };
            
            // Optimize for thumbnail generation (following Live2D Viewer Web approach)
            PIXI.settings.RESOLUTION = 0.2; // Lower resolution for smaller file size
            
            // Hide any extra UI elements for cleaner thumbnail
            // (Live2D Viewer Web hides hit areas and background here)
            
            // Position and scale model for optimal thumbnail view
            const thumbnailSize = 80; // Match our icon size
            modelData.pixiModel.position.set(thumbnailSize / 2, thumbnailSize / 2);
            
            // Calculate scale to fit model nicely in thumbnail
            const maxDimension = Math.max(modelData.pixiModel.width, modelData.pixiModel.height);
            const scale = (thumbnailSize * 0.8) / maxDimension; // 80% of thumbnail size
            modelData.pixiModel.scale.set(scale, scale);
            
            // Use renderer extract to capture as canvas (Live2D Viewer Web method)
            let canvas;
            try {
                canvas = this.core.app.renderer.extract.canvas(modelData.pixiModel);
            } catch (extractError) {
                this.log(`Extract canvas failed: ${extractError.message}`, 'warning');
                // Restore settings before returning null
                PIXI.settings.RESOLUTION = originalResolution;
                modelData.pixiModel.position.set(originalPos.x, originalPos.y);
                modelData.pixiModel.scale.set(originalScale.x, originalScale.y);
                return null;
            }
            
            // Restore original settings
            PIXI.settings.RESOLUTION = originalResolution;
            modelData.pixiModel.position.set(originalPos.x, originalPos.y);
            modelData.pixiModel.scale.set(originalScale.x, originalScale.y);
            
            if (!canvas) {
                this.log(`Canvas extraction returned null`, 'warning');
                return null;
            }
            
            // Convert to WebP for better compression (like Live2D Viewer Web)
            // Fall back to PNG if WebP not supported
            return new Promise((resolve) => {
                canvas.toBlob(blob => {
                    if (blob) {
                        resolve(URL.createObjectURL(blob));
                    } else {
                        // Fallback to dataURL
                        resolve(canvas.toDataURL('image/png'));
                    }
                }, 'image/webp', 0.8); // Higher quality than Live2D Viewer Web's 0.01
            });
            
        } catch (error) {
            this.log(`Failed to create snapshot for ${modelData.name}: ${error.message}`, 'warning');
            return null;
        }
    }

    setActiveModel(modelId) {
        if (!this.models.has(modelId)) {
            this.log(`Model ID ${modelId} not found`, 'error');
            return;
        }

        // Update active model
        this.activeModelId = modelId;
        
        // Update visual indicators
        document.querySelectorAll('.character-icon').forEach(icon => {
            icon.classList.remove('active');
        });
        
        const activeIcon = document.querySelector(`[data-model-id="${modelId}"]`);
        if (activeIcon) {
            activeIcon.classList.add('active');
        }

        // Update canvas manager to track the active model
        const modelData = this.models.get(modelId);
        if (this.core.canvasManager && modelData.pixiModel) {
            this.core.canvasManager.updateModel(modelData.pixiModel);
            this.core.model = modelData.pixiModel; // Update core reference
        }

        // Update UI to show active model info
        this.updateUIForActiveModel(modelData);

        this.log(`Active model set to: ${modelData.name}`, 'info');
    }

    updateUIForActiveModel(modelData) {
        // Update model name and info in UI
        const modelNameElement = document.getElementById('modelName');
        const modelIdElement = document.getElementById('modelId');
        
        if (modelNameElement) {
            modelNameElement.textContent = modelData.name;
        }
        
        if (modelIdElement) {
            modelIdElement.textContent = `#${modelData.id}`;
        }

        // Update model status
        const modelStatus = document.getElementById('modelStatus');
        if (modelStatus) {
            modelStatus.innerHTML = `
                <span class="status-indicator status-success"></span>
                Active model loaded
            `;
        }
    }

    removeModel(modelId) {
        if (!this.models.has(modelId)) {
            this.log(`Model ID ${modelId} not found`, 'error');
            return;
        }

        const modelData = this.models.get(modelId);
        this.log(`Removing model: ${modelData.name}`, 'info');

        // Remove from PIXI stage
        if (modelData.pixiModel && this.core.app) {
            this.core.app.stage.removeChild(modelData.pixiModel);
            modelData.pixiModel.destroy();
        }

        // Remove from models map
        this.models.delete(modelId);

        // Remove character icon
        const iconElement = document.querySelector(`[data-model-id="${modelId}"]`);
        if (iconElement) {
            iconElement.remove();
        }

        // If this was the active model, set another as active
        if (this.activeModelId === modelId) {
            if (this.models.size > 0) {
                const nextModelId = this.models.keys().next().value;
                this.setActiveModel(nextModelId);
            } else {
                this.activeModelId = null;
                this.clearUIForNoModel();
            }
        }

        this.log(`Model removed: ${modelData.name}`, 'success');
    }

    clearUIForNoModel() {
        const modelNameElement = document.getElementById('modelName');
        const modelIdElement = document.getElementById('modelId');
        const modelStatus = document.getElementById('modelStatus');
        
        if (modelNameElement) {
            modelNameElement.textContent = 'Select a model to begin';
        }
        
        if (modelIdElement) {
            modelIdElement.textContent = '#1';
        }

        if (modelStatus) {
            modelStatus.innerHTML = `
                <span class="status-indicator status-warning"></span>
                No model loaded
            `;
        }
    }

    getActiveModel() {
        return this.activeModelId ? this.models.get(this.activeModelId) : null;
    }

    getAllModels() {
        return Array.from(this.models.values());
    }

    scaleActiveModel(zoomMultiplier) {
        const activeModel = this.getActiveModel();
        if (!activeModel || !activeModel.pixiModel) return;

        const finalScale = activeModel.baseScale * zoomMultiplier;
        activeModel.pixiModel.scale.set(finalScale);
        
        this.log(`Scaled active model to: ${finalScale.toFixed(2)}`, 'info');
    }

    // Database preview caching methods
    async getCachedPreview(modelName) {
        try {
            const response = await fetch(`http://localhost:13443/api/live2d/preview/${encodeURIComponent(modelName)}`);
            
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.preview) {
                    this.log(`Retrieved cached preview for ${modelName}`, 'info');
                    return data.preview;
                }
            } else if (response.status === 404) {
                // No cached preview found - this is normal for first time
                this.log(`No cached preview found for ${modelName}`, 'info');
            } else {
                this.log(`Failed to check cached preview for ${modelName}: ${response.status}`, 'warning');
            }
            
            return null;
        } catch (error) {
            this.log(`Error retrieving cached preview for ${modelName}: ${error.message}`, 'warning');
            return null;
        }
    }

    async saveCachedPreview(modelName, previewData) {
        try {
            const response = await fetch(`http://localhost:13443/api/live2d/preview/${encodeURIComponent(modelName)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    preview: previewData
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.log(`Cached preview saved for ${modelName}`, 'info');
                    return true;
                } else {
                    this.log(`Failed to save preview for ${modelName}: ${data.error || 'Unknown error'}`, 'warning');
                }
            } else {
                this.log(`Failed to save preview for ${modelName}: HTTP ${response.status}`, 'warning');
            }
            
            return false;
        } catch (error) {
            this.log(`Error saving cached preview for ${modelName}: ${error.message}`, 'warning');
            return false;
        }
    }

    async hasCachedPreview(modelName) {
        try {
            const response = await fetch(`http://localhost:13443/api/live2d/preview/${encodeURIComponent(modelName)}/check`);
            
            if (response.ok) {
                const data = await response.json();
                return data.success && data.has_preview;
            }
            
            return false;
        } catch (error) {
            this.log(`Error checking cached preview for ${modelName}: ${error.message}`, 'warning');
            return false;
        }
    }

    // Legacy compatibility methods
    async loadModel(modelName) {
        return await this.addModel(modelName);
    }

    getCurrentModel() {
        return this.getActiveModel();
    }

    async switchModel(modelName) {
        return await this.addModel(modelName);
    }

    scaleModel(zoomMultiplier) {
        this.scaleActiveModel(zoomMultiplier);
    }

    getModelList() {
        return this.modelList;
    }
}
