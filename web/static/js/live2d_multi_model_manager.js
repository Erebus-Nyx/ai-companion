// Live2D Multi-Model Manager - Handles multiple models with character icons
class Live2DMultiModelManager {
    constructor(core, logger, interactionManager) {
        this.core = core;
        this.logger = logger;
        this.interactionManager = interactionManager;
        this.models = new Map(); // Store multiple models with their data
        this.activeModelId = null;
        this.maxModels = 5; // System limitation
        this.modelCounter = 0;
        this.modelList = [];
        this.uiController = null; // Reference to UI controller for notifications
        
        // Model state tracking
        this.modelStates = new Map(); // Store scale, position, etc. for each model
        
        this.initializeUI();
    }

    // Set UI controller reference for notifications
    setUIController(uiController) {
        this.uiController = uiController;
    }

    log(message, type = 'info') {
        if (this.logger) {
            this.logger.log(message, type);
        }
    }

    // Helper function for API calls with automatic fallback
    async fetchWithFallback(endpoint) {
        const primaryUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || 'http://localhost:19443';
        const fallbackUrls = window.ai2d_chat_CONFIG?.FALLBACK_URLS || [];
        const urlsToTry = [primaryUrl, ...fallbackUrls];
        
        let lastError = null;
        
        for (const apiBaseUrl of urlsToTry) {
            try {
                const fullUrl = `${apiBaseUrl}${endpoint}`;
                console.log(`Trying API URL: ${fullUrl}`);
                const response = await fetch(fullUrl);
                
                if (response.ok) {
                    // Update global config with working URL
                    if (window.ai2d_chat_CONFIG) {
                        window.ai2d_chat_CONFIG.API_BASE_URL = apiBaseUrl;
                    }
                    return response;
                }
                
                throw new Error(`API request failed: ${response.status} ${response.statusText}`);
                
            } catch (error) {
                lastError = error;
                console.warn(`Failed to fetch from ${apiBaseUrl}: ${error.message}`);
                continue; // Try next URL
            }
        }
        
        throw lastError || new Error(`Failed to fetch ${endpoint} from any API endpoint`);
    }

    initializeUI() {
        // Create character icons container at bottom of canvas
        this.createCharacterIconsContainer();
    }

    createCharacterIconsContainer() {
        const canvasContainer = document.querySelector('.canvas-container');
        if (!canvasContainer) return;

        // The character icons are now handled by the people panel
        // No need to create the bottom character icons container
        this.log('Multi-model manager initialized - using people panel for model selection', 'info');
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
                // Get cached preview image or generate it
                const previewUrl = await this.getCachedPreview(model.name);
                
                const card = `
                    <div class="model-card" data-model-name="${model.name}">
                        <div class="model-preview">
                            ${previewUrl ? 
                                `<img src="${previewUrl}" alt="${model.name}" class="model-preview-image" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';">
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
        // Get primary URL and fallback URLs
        const primaryUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || 'http://localhost:19443';
        const fallbackUrls = window.ai2d_chat_CONFIG?.FALLBACK_URLS || [];
        const urlsToTry = [primaryUrl, ...fallbackUrls];
        
        let lastError = null;
        
        for (const apiBaseUrl of urlsToTry) {
            try {
                console.log(`Trying API URL: ${apiBaseUrl}/api/live2d/models`);
                const response = await fetch(`${apiBaseUrl}/api/live2d/models`);
                
                if (!response.ok) {
                    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
                }
                
                const models = await response.json();
                
                if (!Array.isArray(models) || models.length === 0) {
                    throw new Error('No models returned from API');
                }
                
                // Update global config with working URL
                if (window.ai2d_chat_CONFIG) {
                    window.ai2d_chat_CONFIG.API_BASE_URL = apiBaseUrl;
                }
                
                this.modelList = models.map(model => ({
                    name: model.model_name,
                    path: model.model_path,
                    configFile: model.config_file,
                    url: `${apiBaseUrl}/${model.model_path}/${model.config_file}`,
                    info: model.info || model.model_name
                }));
                
                this.log(`Successfully loaded ${this.modelList.length} available models from API (${apiBaseUrl})`, 'success');
                return this.modelList;
                
            } catch (error) {
                lastError = error;
                console.warn(`Failed to load from ${apiBaseUrl}: ${error.message}`);
                continue; // Try next URL
            }
        }
        
        // If all URLs failed
        this.log(`Failed to load model list from any API endpoint. Last error: ${lastError?.message}`, 'error');
        this.modelList = [];
        throw lastError || new Error('Failed to load from any API endpoint');
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
            // Enable autoMotion to prevent T-pose, then add our custom motions
            const pixiModel = await this.loadModelWithoutClearing(modelInfo.url, { autoMotion: true });
            
            // Store model data
            const modelData = {
                id: modelId,
                name: modelInfo.name,
                path: modelInfo.path,
                url: modelInfo.url,
                info: modelInfo.info,
                pixiModel: pixiModel,
                baseScale: 0.2, // Default scale based on requirements
                // position: { x: 0, y: 0 },
                visible: true
            };

            this.models.set(modelId, modelData);
            
            // Initialize model state
            this.modelStates.set(modelId, {
                scale: 1.0, // Zoom level (multiplied by baseScale)
                position: { x: 0, y: 0 },
                visible: true,
                motions: {
                    idle: null,
                    expressions: new Map()
                }
            });
            
            // Set initial scale (0.2 for default zoom 1.0)
            if (pixiModel && pixiModel.scale) {
                modelData.baseScale = 0.2;
                pixiModel.baseScale = modelData.baseScale; // Store base scale on model for interaction manager
                pixiModel.scale.set(modelData.baseScale);
            }

            // Start neutral random motions
            await this.startNeutralMotions(modelId);

            // Set initial position via interaction manager (after model is loaded and updateModel is called)
            if (this.interactionManager) {
                this.interactionManager.centerModel();
            }

            // Set as active model
            this.setActiveModel(modelId);
            
            // Extract character image in background and update People panel when done
            this.extractCharacterImage(modelData).then(characterImage => {
                // Store the character image on the model data for People panel
                modelData.characterImage = characterImage;
                
                // Refresh people panel to show the new model with image
                if (typeof populatePeopleModels === 'function') {
                    populatePeopleModels();
                }
            }).catch(error => {
                this.log(`Failed to load character image for ${modelData.name}: ${error.message}`, 'warning');
                // Still refresh people panel even without image
                if (typeof populatePeopleModels === 'function') {
                    populatePeopleModels();
                }
            });
            
            // Refresh people panel immediately to show the new model (will show loading state)
            if (typeof populatePeopleModels === 'function') {
                populatePeopleModels();
            }
            
            this.log(`Successfully added model: ${modelInfo.name}`, 'success');
            return true;
            
        } catch (error) {
            const errorMessage = `Failed to add model ${modelName}: ${error.message}`;
            this.log(errorMessage, 'error');
            throw new Error(errorMessage);
        }
    }

    async loadModelWithoutClearing(modelUrl, options = {}) {
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
                    const model = await constructor.from(modelUrl, options);
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
                    
                    // Update interaction manager with new model
                    if (this.interactionManager) {
                        this.interactionManager.updateModel(model);
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

    async startNeutralMotions(modelId) {
        const modelData = this.models.get(modelId);
        if (!modelData || !modelData.pixiModel) return;

        try {
            // Load motions for the model
            const motionsData = await this.loadModelMotions(modelData);
            
            // Extract motion array from the API response
            let motionArray = [];
            if (motionsData && motionsData.motions) {
                this.log(`Processing motions data for ${modelData.name}`, 'info');
                console.log('Motions data structure:', motionsData);
                
                // Convert the motion groups object to an array
                Object.keys(motionsData.motions).forEach(groupName => {
                    const groupMotions = motionsData.motions[groupName];
                    this.log(`Processing group ${groupName} with ${groupMotions.length} motions`, 'info');
                    
                    if (Array.isArray(groupMotions)) {
                        groupMotions.forEach(motion => {
                            motionArray.push({
                                ...motion,
                                group: groupName
                            });
                        });
                    }
                });
            } else {
                this.log(`No motions data found for ${modelData.name}`, 'warning');
                console.log('Full response:', motionsData);
            }
            
            this.log(`Built motion array with ${motionArray.length} motions`, 'info');
            
            // Filter for idle/neutral motions
            const neutralMotions = motionArray.filter(motion => {
                if (!motion.group) return false;
                const groupLower = motion.group.toLowerCase();
                return groupLower.includes('idle') || 
                       groupLower.includes('neutral') ||
                       groupLower.includes('default');
            });

            if (neutralMotions.length === 0) {
                this.log(`No neutral motions found for ${modelData.name}, using any available motion`, 'warning');
                // If no neutral motions, use the first available motion
                if (motionArray.length > 0) {
                    neutralMotions.push(motionArray[0]);
                }
            } else {
                this.log(`Found ${neutralMotions.length} neutral motions for ${modelData.name}`, 'info');
            }

            if (neutralMotions.length > 0) {
                this.log(`Starting neutral motions for ${modelData.name}`, 'info');
                // Start periodic motion playback
                this.setupPeriodicMotions(modelId, neutralMotions);
            } else {
                this.log(`No motions available for ${modelData.name}`, 'warning');
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
            const response = await this.fetchWithFallback(`/api/live2d/motions/${modelData.name}`);
            if (!response.ok) {
                throw new Error(`Failed to load motions: ${response.status}`);
            }
            
            const result = await response.json();
            
            // Return the full result object, not just the motions array
            return result;
        } catch (error) {
            this.log(`Failed to load motions for ${modelData.name}: ${error.message}`, 'warning');
            return { motions: {} };
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
            <button class="remove-character" onclick="event.stopPropagation(); removeModel('${modelData.id}')">×</button>
        `;

        // Add click handler to focus model
        iconElement.addEventListener('click', () => {
            this.setActiveModel(modelData.id);
        });

        iconsList.appendChild(iconElement);
        
        // Extract character image in background
        this.extractCharacterImage(modelData).then(characterImage => {
            // Store the character image on the model data for People panel
            modelData.characterImage = characterImage;
            
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
            
            // No fallback - if snapshot creation fails, use emoji
            this.log(`Could not create preview for ${modelData.name}`, 'warning');
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
            // Use dynamic API base URL from global config
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || 'http://localhost:19443';
            const textureResponse = await fetch(`${apiBaseUrl}/api/live2d/textures/${modelData.name}`);
            if (textureResponse.ok) {
                const textureInfo = await textureResponse.json();
                if (textureInfo.primary_texture && textureInfo.primary_texture.exists) {
                    return `${apiBaseUrl}${textureInfo.primary_texture.url}`;
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

        // Save current model state if there is one
        if (this.activeModelId && this.models.has(this.activeModelId)) {
            this.saveCurrentModelState();
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

        // Update interaction manager to track the active model
        const modelData = this.models.get(modelId);
        if (this.interactionManager && modelData.pixiModel) {
            this.interactionManager.updateModel(modelData.pixiModel);
            this.core.model = modelData.pixiModel; // Update core reference
            
            // Set up interaction for the active model
            this.interactionManager.setupModelInteraction();
        }

        // Restore model state
        this.restoreModelState(modelId);

        // Update UI to show active model info
        this.updateUIForActiveModel(modelData);

        // Notify UI controller to load motions and expressions for the active model
        if (this.uiController) {
            this.uiController.onModelFocusChanged(modelData.name);
        }

        this.log(`Active model set to: ${modelData.name}`, 'info');
    }

    saveCurrentModelState() {
        if (!this.activeModelId) return;
        
        const modelData = this.models.get(this.activeModelId);
        if (!modelData || !modelData.pixiModel) return;
        
        const state = this.modelStates.get(this.activeModelId);
        if (!state) return;
        
        // Save scale from UI
        const scaleSlider = document.getElementById('zoomSlider');
        if (scaleSlider) {
            state.scale = parseFloat(scaleSlider.value);
        }
        
        // Save position
        state.position = {
            x: modelData.pixiModel.x,
            y: modelData.pixiModel.y
        };
        
        // Save visibility
        state.visible = modelData.pixiModel.visible;
    }

    restoreModelState(modelId) {
        const modelData = this.models.get(modelId);
        const state = this.modelStates.get(modelId);
        
        if (!modelData || !state || !modelData.pixiModel) return;
        
        // Restore scale
        const finalScale = modelData.baseScale * state.scale;
        modelData.pixiModel.scale.set(finalScale);
        
        // Update UI scale slider
        const scaleSlider = document.getElementById('zoomSlider');
        if (scaleSlider) {
            scaleSlider.value = state.scale;
        }
        
        // Update zoom value display
        const zoomValue = document.getElementById('zoomValue');
        if (zoomValue) {
            zoomValue.textContent = state.scale.toFixed(2);
        }
        
        // Restore position
        modelData.pixiModel.x = state.position.x;
        modelData.pixiModel.y = state.position.y;
        
        // Restore visibility
        modelData.pixiModel.visible = state.visible;
        
        this.log(`Model scaled to: ${finalScale.toFixed(2)} (base: ${modelData.baseScale.toFixed(2)}, zoom: ${state.scale.toFixed(2)})`, 'info');
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
        
        // Refresh people panel to reflect the removal
        if (typeof populatePeopleModels === 'function') {
            populatePeopleModels();
        }
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
            // Use dynamic API base URL from global config
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || 'http://localhost:19443';
            const response = await fetch(`${apiBaseUrl}/api/live2d/preview/${encodeURIComponent(modelName)}`);
            
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
            // Use dynamic API base URL from global config
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || 'http://localhost:19443';
            const response = await fetch(`${apiBaseUrl}/api/live2d/preview/${encodeURIComponent(modelName)}`, {
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
            // Use dynamic API base URL from global config
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || 'http://localhost:19443';
            const response = await fetch(`${apiBaseUrl}/api/live2d/preview/${encodeURIComponent(modelName)}/check`);
            
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
