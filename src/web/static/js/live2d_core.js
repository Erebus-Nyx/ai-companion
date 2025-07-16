// Live2D Core Module - Essential Live2D functionality
class Live2DCore {
    constructor() {
        this.app = null;
        this.model = null;
        this.logger = null;
        this.baseScale = 1.0;
        this.hitBoxGraphics = null;
        this.modelFrameGraphics = null;
    }

    setLogger(logger) {
        this.logger = logger;
    }

    checkLive2DLibrary() {
        // Check if essential Live2D components are available
        const checks = {
            'PIXI': typeof PIXI !== 'undefined',
            'PIXI.live2d': typeof PIXI !== 'undefined' && typeof PIXI.live2d !== 'undefined',
            'Live2DCubismCore': typeof Live2DCubismCore !== 'undefined',
            'EventEmitter': typeof EventEmitter !== 'undefined'
        };

        this.log('=== Live2D Library Check ===', 'info');
        Object.entries(checks).forEach(([component, available]) => {
            this.log(`${component}: ${available ? '✓' : '✗'}`, available ? 'success' : 'error');
        });

        // Check if PIXI.live2d has the necessary components
        if (checks['PIXI.live2d']) {
            const live2dKeys = Object.keys(PIXI.live2d);
            this.log(`PIXI.live2d components: ${live2dKeys.join(', ')}`, 'info');
            
            // Look for model-related classes
            const hasModelClass = live2dKeys.some(key => 
                key.includes('Model') || key.includes('Factory') || key.includes('Live2D')
            );
            
            if (!hasModelClass) {
                this.log('PIXI.live2d missing model classes', 'warning');
                return false;
            }
        }

        const allBasicChecks = Object.values(checks).every(check => check === true);
        this.log(`Library check result: ${allBasicChecks ? 'PASS' : 'FAIL'}`, allBasicChecks ? 'success' : 'error');
        
        return allBasicChecks;
    }

    log(message, type = 'info') {
        if (this.logger) {
            this.logger.log(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    async initApp(canvasElement, options = {}) {
        // Dynamic canvas sizing based on container
        const containerRect = canvasElement.getBoundingClientRect();
        const margin = options.canvasMargin || 40;
        
        // Calculate dimensions - if options width/height are 0, use dynamic sizing
        let targetWidth = options.width || 0;
        let targetHeight = options.height || 0;
        
        // If explicit dimensions are 0 or not provided, use dynamic sizing
        if (targetWidth === 0 || targetHeight === 0) {
            const dynamicWidth = containerRect.width - (margin * 2);
            const dynamicHeight = containerRect.height - (margin * 2);
            
            // Use container dimensions if available, otherwise use minimum
            targetWidth = dynamicWidth > 0 ? dynamicWidth : 800;
            targetHeight = dynamicHeight > 0 ? dynamicHeight : 600;
        }
        
        // Ensure minimum canvas size
        const minWidth = 400;
        const minHeight = 400;
        
        const finalWidth = Math.max(targetWidth, minWidth);
        const finalHeight = Math.max(targetHeight, minHeight);
        
        const defaultOptions = {
            width: finalWidth,
            height: finalHeight,
            backgroundColor: 0x000000,
            backgroundAlpha: 0,
            resolution: 1
        };

        const finalOptions = { ...defaultOptions, ...options };
        
        // Store canvas dimensions for model scaling
        this.canvasWidth = finalOptions.width;
        this.canvasHeight = finalOptions.height;
        this.canvasMargin = margin;

        try {
            // Pre-configure canvas element dimensions before PIXI initialization
            canvasElement.style.width = finalOptions.width + 'px';
            canvasElement.style.height = finalOptions.height + 'px';
            
            if (PIXI.VERSION.startsWith('8.')) {
                this.app = new PIXI.Application();
                await this.app.init(finalOptions);
                canvasElement.appendChild(this.app.canvas);
            } else {
                this.app = new PIXI.Application(finalOptions);
                canvasElement.appendChild(this.app.view);
            }
            
            // Get the actual canvas element
            const canvas = this.app.canvas || this.app.view;
            
            // CRITICAL: Force canvas dimensions at multiple levels
            canvas.width = finalOptions.width;
            canvas.height = finalOptions.height;
            canvas.style.width = finalOptions.width + 'px';
            canvas.style.height = finalOptions.height + 'px';
            
            // Set explicit size on the canvas element
            canvas.setAttribute('width', finalOptions.width);
            canvas.setAttribute('height', finalOptions.height);
            
            // Force WebGL context dimensions if available
            if (this.app.renderer.gl) {
                this.app.renderer.gl.canvas.width = finalOptions.width;
                this.app.renderer.gl.canvas.height = finalOptions.height;
            }
            
            // Multiple resize attempts with different approaches
            this.app.renderer.resize(finalOptions.width, finalOptions.height);
            
            // Force screen dimensions
            if (this.app.screen) {
                this.app.screen.width = finalOptions.width;
                this.app.screen.height = finalOptions.height;
            }
            
            // Try direct renderer view manipulation
            if (this.app.renderer.view) {
                this.app.renderer.view.width = finalOptions.width;
                this.app.renderer.view.height = finalOptions.height;
            }
            
            // Force internal renderer properties
            if (this.app.renderer._width !== undefined) {
                this.app.renderer._width = finalOptions.width;
            }
            if (this.app.renderer._height !== undefined) {
                this.app.renderer._height = finalOptions.height;
            }
            
            // Immediate render to apply changes
            this.app.render();
            
            // Verify and retry if needed
            let actualWidth = this.app.renderer.width || this.app.screen.width;
            let actualHeight = this.app.renderer.height || this.app.screen.height;
            
            // If still 0x0, force one more time with alternative approach
            if (actualWidth === 0 || actualHeight === 0) {
                this.log('Renderer dimensions still 0x0, forcing final resize...', 'warning');
                
                // Try to force using renderer internal methods
                if (this.app.renderer.gl) {
                    const gl = this.app.renderer.gl;
                    gl.canvas.width = finalOptions.width;
                    gl.canvas.height = finalOptions.height;
                    gl.viewport(0, 0, finalOptions.width, finalOptions.height);
                }
                
                // Try to force through the renderer's framebuffer
                if (this.app.renderer.framebuffer) {
                    this.app.renderer.framebuffer.resize(finalOptions.width, finalOptions.height);
                }
                
                // One more resize attempt
                this.app.renderer.resize(finalOptions.width, finalOptions.height);
                this.app.render();
                
                // Re-check
                actualWidth = this.app.renderer.width || this.app.screen.width || finalOptions.width;
                actualHeight = this.app.renderer.height || this.app.screen.height || finalOptions.height;
            }
            
            // Store actual dimensions for fallback use - force use of target dimensions
            this.actualWidth = finalOptions.width;  // Force use of target dimensions
            this.actualHeight = finalOptions.height;
            
            // Center the canvas within the container and ensure visibility
            canvas.style.position = 'absolute';
            canvas.style.left = '50%';
            canvas.style.top = '50%';
            canvas.style.transform = 'translate(-50%, -50%)';
            canvas.style.border = '1px solid rgba(74, 144, 226, 0.3)';
            canvas.style.borderRadius = '8px';
            canvas.style.backgroundColor = 'rgba(0, 0, 0, 0.05)';  // Slight background to make canvas visible
            canvas.style.display = 'block';
            canvas.style.visibility = 'visible';
            canvas.style.zIndex = '1';
            
            // Force canvas to be visible in the DOM
            canvas.removeAttribute('hidden');
            canvas.setAttribute('data-canvas-initialized', 'true');
            
            this.log(`PIXI application initialized: ${finalOptions.width}x${finalOptions.height} (container: ${containerRect.width}x${containerRect.height})`, 'success');
            this.log(`Final canvas dimensions: ${canvas.width}x${canvas.height}, Renderer size: ${actualWidth}x${actualHeight}`, 'info');
            
            return true;
        } catch (error) {
            this.log('Failed to initialize PIXI: ' + error.message, 'error');
            return false;
        }
    }

    // Debug function to check model visibility
    debugModelVisibility() {
        if (!this.model) {
            this.log('No model loaded', 'warning');
            return;
        }
        
        this.log('=== MODEL VISIBILITY DEBUG ===', 'info');
        this.log(`Model visible: ${this.model.visible}`, 'info');
        this.log(`Model alpha: ${this.model.alpha}`, 'info');
        this.log(`Model position: ${this.model.position.x}, ${this.model.position.y}`, 'info');
        this.log(`Model scale: ${this.model.scale.x}, ${this.model.scale.y}`, 'info');
        this.log(`Model bounds: ${JSON.stringify(this.model.getBounds())}`, 'info');
        this.log(`Canvas size: ${this.canvasWidth || 800}x${this.canvasHeight || 600}`, 'info');
        this.log(`Stage children count: ${this.app.stage.children.length}`, 'info');
        
        // Check if model is within screen bounds using forced dimensions
        const canvasWidth = this.canvasWidth || 800;
        const canvasHeight = this.canvasHeight || 600;
        const bounds = this.model.getBounds();
        const onScreen = bounds.x < canvasWidth && 
                        bounds.x + bounds.width > 0 && 
                        bounds.y < canvasHeight && 
                        bounds.y + bounds.height > 0;
        
        this.log(`Model on screen: ${onScreen}`, onScreen ? 'success' : 'warning');
        this.log('=== END DEBUG ===', 'info');
    }

    // Clear current model and all associated graphics
    clearModel() {
        // Clear model
        if (this.model) {
            this.app.stage.removeChild(this.model);
            this.model.destroy();
            this.model = null;
        }

        // Clear hit box graphics
        if (this.hitBoxGraphics) {
            this.app.stage.removeChild(this.hitBoxGraphics);
            this.hitBoxGraphics.destroy();
            this.hitBoxGraphics = null;
        }

        // Clear model frame graphics
        if (this.modelFrameGraphics) {
            this.app.stage.removeChild(this.modelFrameGraphics);
            this.modelFrameGraphics.destroy();
            this.modelFrameGraphics = null;
        }

        this.log('Model and graphics cleared', 'info');
    }

    async loadModel(modelUrl) {
        if (!this.app) {
            this.log('No app initialized!', 'error');
            throw new Error('PIXI application not initialized');
        }

        this.log('Loading Live2D model: ' + modelUrl);

        // Clear existing model and all graphics
        this.clearModel();

        // Try standard PIXI.live2d approach first
        this.log('=== DIAGNOSTIC: Checking Live2D constructors ===', 'info');
        this.log(`PIXI.live2d exists: ${typeof PIXI.live2d !== 'undefined'}`, 'info');
        if (typeof PIXI.live2d !== 'undefined') {
            this.log(`PIXI.live2d keys: ${Object.keys(PIXI.live2d).join(', ')}`, 'info');
            
            // Check if Live2DModel is nested somewhere
            Object.keys(PIXI.live2d).forEach(key => {
                const value = PIXI.live2d[key];
                if (typeof value === 'object' && value !== null) {
                    this.log(`PIXI.live2d.${key} keys: ${Object.keys(value).join(', ')}`, 'info');
                }
            });
        }
        this.log(`window.Live2DModel exists: ${typeof window.Live2DModel !== 'undefined'}`, 'info');
        this.log(`PIXI.Live2DModel exists: ${typeof PIXI.Live2DModel !== 'undefined'}`, 'info');
        this.log(`Live2DModel global exists: ${typeof Live2DModel !== 'undefined'}`, 'info');
        
        // Check for alternative Live2D namespaces
        this.log(`window.LIVE2DCUBISMCORE exists: ${typeof window.LIVE2DCUBISMCORE !== 'undefined'}`, 'info');
        this.log(`Live2DCubismCore exists: ${typeof Live2DCubismCore !== 'undefined'}`, 'info');
        
        // If Live2DCubismCore exists, log its structure
        if (typeof Live2DCubismCore !== 'undefined') {
            this.log(`Live2DCubismCore keys: ${Object.keys(Live2DCubismCore).join(', ')}`, 'info');
        this.log(`Live2DCubismCore.Moc exists: ${typeof Live2DCubismCore.Moc !== 'undefined'}`, 'info');
        this.log(`Live2DCubismCore.Model exists: ${typeof Live2DCubismCore.Model !== 'undefined'}`, 'info');
        }
        
        // Check if the library is available globally
        const live2dGlobals = Object.keys(window).filter(k => k.toLowerCase().includes('live2d'));
        this.log(`Live2D globals: ${live2dGlobals.join(', ')}`, 'info');
        
        // Try to manually install if needed
        if (typeof PIXI.live2d !== 'undefined' && typeof PIXI.live2d.Live2DModel === 'undefined') {
            this.log('Attempting to install Live2D plugin...', 'warning');
            try {
                if (typeof PIXI.live2d.install === 'function') {
                    PIXI.live2d.install();
                    this.log('Live2D plugin installed', 'success');
                } else {
                    this.log('No install function found', 'warning');
                }
            } catch (error) {
                this.log(`Install failed: ${error.message}`, 'error');
            }
        }
        
        // Try alternative initialization approaches
        if (typeof Live2DCubismCore !== 'undefined' && typeof PIXI.live2d !== 'undefined') {
            this.log('Attempting manual Live2D-PIXI integration...', 'warning');
            try {
                // Try to create a Live2DModel constructor manually
                if (typeof window.Live2DModel === 'undefined' && typeof PIXI.live2d.Live2DModel === 'undefined') {
                    // Check if we can access the library through alternative means
                    this.log('Checking for alternative Live2D access patterns...', 'info');
                    
                    // Try common patterns
                    if (typeof PIXI.live2d.Application !== 'undefined') {
                        this.log('Found PIXI.live2d.Application', 'info');
                    }
                    
                    // Try to find the actual Live2D model loader
                    const possiblePaths = [
                        'PIXI.live2d.Live2DModel',
                        'PIXI.live2d.Model',
                        'window.Live2DModel',
                        'Live2DModel'
                    ];
                    
                    for (const path of possiblePaths) {
                        const parts = path.split('.');
                        let obj = window;
                        let pathExists = true;
                        
                        for (const part of parts) {
                            if (obj && typeof obj[part] !== 'undefined') {
                                obj = obj[part];
                            } else {
                                pathExists = false;
                                break;
                            }
                        }
                        
                        if (pathExists && obj && typeof obj.from === 'function') {
                            this.log(`Found Live2D model constructor at: ${path}`, 'success');
                            // Try to assign it to a known location
                            if (!PIXI.live2d.Live2DModel) {
                                PIXI.live2d.Live2DModel = obj;
                                this.log('Assigned Live2DModel to PIXI.live2d.Live2DModel', 'success');
                            }
                            break;
                        }
                    }
                }
            } catch (error) {
                this.log(`Manual integration failed: ${error.message}`, 'error');
            }
        }
        
        this.log('=== END DIAGNOSTIC ===', 'info');

        const constructors = [
            { name: 'PIXI.live2d.Live2DModel', constructor: PIXI.live2d && PIXI.live2d.Live2DModel },
            { name: 'window.Live2DModel', constructor: window.Live2DModel },
            { name: 'PIXI.Live2DModel', constructor: PIXI.Live2DModel },
            { name: 'Live2DModel (global)', constructor: typeof Live2DModel !== 'undefined' ? Live2DModel : null }
        ];

        for (const { name, constructor } of constructors) {
            if (constructor && typeof constructor.from === 'function') {
                this.log(`Trying to load model with ${name}...`, 'warning');
                
                try {
                    const model = await constructor.from(modelUrl);
                    this.log(`Successfully loaded model with ${name}!`, 'success');
                    
                    // Add more detailed logging
                    this.log(`Model dimensions: ${model.width}x${model.height}`, 'info');
                    this.log(`Model bounds: ${JSON.stringify(model.getBounds())}`, 'info');
                    
                    // Configure model (Live2D Viewer Web style)
                    if (model.anchor && model.anchor.set) {
                        model.anchor.set(0.5, 0.5);
                    }
                    
                    // FORCE use of stored canvas dimensions - bypass renderer issue
                    const rendererWidth = this.canvasWidth || 800;
                    const rendererHeight = this.canvasHeight || 600;
                    
                    this.log(`Using forced dimensions: ${rendererWidth}x${rendererHeight}`, 'info');
                    
                    const centerX = rendererWidth / 2;
                    const centerY = rendererHeight / 2;
                    
                    // Smart model scaling using Live2D Viewer Web pattern (before positioning)
                    const modelScale = this.calculateOptimalModelScale(model);
                    model.scale.set(modelScale);
                    
                    // Position model in center AFTER scaling
                    model.position.set(centerX, centerY);
                    
                    this.log(`Model positioned at: ${centerX}, ${centerY}`, 'info');
                    this.log(`Model scaled to: ${modelScale}`, 'info');
                    this.log(`Final model bounds: ${JSON.stringify(model.getBounds())}`, 'info');
                    
                    // Make model visible
                    model.visible = true;
                    model.alpha = 1.0;
                    
                    this.app.stage.addChild(model);
                    this.model = model;
                    
                    // Force render update
                    this.app.render();
                    
                    this.log(`Model added to stage! Stage children count: ${this.app.stage.children.length}`, 'success');
                    
                    // Enable mouse interaction
                    this.setupMouseInteraction(model);
                    
                    this.log('Model added to stage successfully!', 'success');
                    return model;
                    
                } catch (error) {
                    this.log(`Failed to load with ${name}: ${error.message}`, 'error');
                }
            }
        }

        // If we have Live2DCubismCore but no PIXI.live2d.Live2DModel, try raw implementation
        if (typeof Live2DCubismCore !== 'undefined' && (!PIXI.live2d || !PIXI.live2d.Live2DModel)) {
            this.log('Attempting raw Live2DCubismCore implementation...', 'warning');
            return await this.loadModelWithRawCubism(modelUrl);
        }

        // All loading methods failed
        const errorMessage = 'All Live2D loading methods failed. Live2D libraries may not be properly initialized.';
        this.log(errorMessage, 'error');
        throw new Error(errorMessage);
    }

    async loadModelWithRawCubism(modelUrl) {
        this.log('=== LOADING WITH RAW CUBISM CORE ===', 'info');
        
        try {
            // Load model JSON
            const response = await fetch(modelUrl);
            if (!response.ok) {
                throw new Error(`Failed to load model JSON: ${response.status} ${response.statusText}`);
            }
            
            const modelData = await response.json();
            this.log('Model JSON loaded successfully', 'success');
            
            // Load MOC file
            const baseUrl = modelUrl.substring(0, modelUrl.lastIndexOf('/') + 1);
            const mocUrl = baseUrl + modelData.FileReferences.Moc;
            
            const mocResponse = await fetch(mocUrl);
            if (!mocResponse.ok) {
                throw new Error(`Failed to load MOC file: ${mocResponse.status} ${mocResponse.statusText}`);
            }
            
            const mocBuffer = await mocResponse.arrayBuffer();
            
            // Create Cubism model
            const moc = Live2DCubismCore.Moc.fromArrayBuffer(mocBuffer);
            const cubismModel = Live2DCubismCore.Model.fromMoc(moc);
            
            this.log(`Cubism Model created: ${cubismModel.parameters.count} parameters, ${cubismModel.drawables.count} drawables`, 'success');
            
            // Initialize model parameters
            for (let i = 0; i < cubismModel.parameters.count; i++) {
                cubismModel.parameters.values[i] = cubismModel.parameters.defaultValues[i];
            }
            cubismModel.update();
            
            // Load textures
            const texturePromises = modelData.FileReferences.Textures.map(async (texturePath) => {
                const textureUrl = baseUrl + texturePath;
                return await PIXI.Assets.load(textureUrl);
            });
            
            const textures = await Promise.all(texturePromises);
            this.log(`Loaded ${textures.length} textures successfully`, 'success');
            
            // Create model container
            const modelContainer = new PIXI.Container();
            modelContainer.position.set(this.app.screen.width / 2, this.app.screen.height / 2);
            
            // Create drawable sprites for proper Live2D rendering
            const drawableSprites = [];
            const atlasTexture = textures[0];
            
            // Smart model scaling: 75% of canvas height unless model is already smaller
            const modelScale = this.calculateOptimalModelScale(null, modelContainer);
            modelContainer.scale.set(modelScale);
            
            // --- UV Remapping for Atlas Fix ---
            // Helper: get per-drawable UV rects from modelData (if available)
            function getDrawableUvRect(i) {
                // Try Cubism 4+ format: modelData.Drawables && modelData.Drawables.UvRects
                if (modelData && modelData.Drawables && Array.isArray(modelData.Drawables.UvRects)) {
                    return modelData.Drawables.UvRects[i]; // [x, y, w, h] in normalized [0,1]
                }
                // Try Cubism 2/3 format: modelData.MeshUvs or similar
                if (modelData && Array.isArray(modelData.MeshUvs) && modelData.MeshUvs[i]) {
                    return modelData.MeshUvs[i];
                }
                // Try userData or custom fields
                if (modelData && modelData.UserData && Array.isArray(modelData.UserData.UvRects)) {
                    return modelData.UserData.UvRects[i];
                }
                return null;
            }

            // Create meshes for each drawable using vertex data
            for (let i = 0; i < cubismModel.drawables.count; i++) {
                const drawable = cubismModel.drawables;
                // Get counts and offsets
                const vertexCount = drawable.vertexCounts[i];
                const vertexOffset = drawable.vertexPositionIndices[i];
                const uvOffset = drawable.uvIndices[i];
                const indexCount = drawable.indexCounts[i];
                const indexOffset = drawable.indexOffsets[i];
                // Flat arrays
                const allVertexPositions = drawable.vertexPositions;
                const allVertexUvs = drawable.vertexUvs;
                const allIndices = drawable.indices;
                if (vertexCount > 0 && indexCount > 0) {
                    // Extract per-drawable vertex positions
                    const vertexPositions = allVertexPositions.slice(vertexOffset, vertexOffset + vertexCount * 2);
                    let vertexUvs = allVertexUvs.slice(uvOffset, uvOffset + vertexCount * 2);
                    const indices = allIndices.slice(indexOffset, indexOffset + indexCount);
                    // --- UV Remapping ---
                    const uvRect = getDrawableUvRect(i);
                    if (uvRect) {
                        // Remap UVs from [0,1] to atlas subrect
                        // uvRect: [x, y, w, h] in normalized [0,1]
                        for (let j = 0; j < vertexCount; j++) {
                            const u = vertexUvs[j * 2];
                            const v = vertexUvs[j * 2 + 1];
                            vertexUvs[j * 2] = uvRect[0] + u * uvRect[2];
                            vertexUvs[j * 2 + 1] = uvRect[1] + v * uvRect[3];
                        }
                        this.log(`Drawable ${i}: UVs remapped to rect [${uvRect.join(', ')}]`, 'info');
                    } else {
                        this.log(`Drawable ${i}: No UV rect found, using original UVs.`, 'warning');
                    }
                    // Use correct texture for this drawable
                    let texture = atlasTexture;
                    if (Array.isArray(textures) && drawable.textureIndices && typeof drawable.textureIndices[i] === 'number' && textures[drawable.textureIndices[i]]) {
                        texture = textures[drawable.textureIndices[i]];
                    }
                    // Create mesh geometry with correct attribute names for PIXI v8
                    const geometry = new PIXI.MeshGeometry();
                    geometry.addAttribute('aVertexPosition', new Float32Array(vertexPositions), 2);
                    geometry.addAttribute('aTextureCoord', new Float32Array(vertexUvs), 2);
                    geometry.addIndex(new Uint16Array(indices));
                    // Create shader
                    const shader = PIXI.Shader.from(
                        `precision mediump float;\nattribute vec2 aVertexPosition;\nattribute vec2 aTextureCoord;\nuniform mat3 translationMatrix;\nuniform mat3 projectionMatrix;\nvarying vec2 vUV;\nvoid main() { vUV = aTextureCoord; gl_Position = vec4((projectionMatrix * translationMatrix * vec3(aVertexPosition, 1.0)).xy, 0.0, 1.0); }`,
                        `precision mediump float;\nvarying vec2 vUV;\nuniform sampler2D uTexture;\nuniform float alpha;\nvoid main() { gl_FragColor = texture2D(uTexture, vUV) * alpha; }`,
                        { uTexture: texture, alpha: drawable.opacities[i] }
                    );
                    // Create mesh
                    const mesh = new PIXI.Mesh(geometry, shader);
                    mesh.alpha = drawable.opacities[i];
                    mesh.visible = true; // For debug, force visible
                    mesh.zIndex = drawable.renderOrders[i];
                    mesh.position.set(0, 0);
                    mesh.scale.set(1, 1);
                    drawableSprites.push(mesh);
                    modelContainer.addChild(mesh);
                } else {
                    // Error: Drawable has no geometry, log and skip
                    this.log(`Drawable ${i} has no geometry (vertexCount=${vertexCount}, indexCount=${indexCount}), skipping.`, 'warning');
                }
            }
            
            // Set container scale to fit model
            modelContainer.scale.set(containerScale, -containerScale); // Y flip for Live2D
            modelContainer.sortableChildren = true;

            // Add comprehensive interactivity
            modelContainer.interactive = true;
            modelContainer.eventMode = 'static';

            // Eye tracking on mouse move
            modelContainer.on('pointermove', (event) => {
                const localPos = event.data.getLocalPosition(modelContainer);
                const normalizedX = (localPos.x / (this.app.screen.width * 0.3)) * 2 - 1; // -1 to 1
                const normalizedY = (localPos.y / (this.app.screen.height * 0.3)) * 2 - 1; // -1 to 1

                // Find eye tracking parameters
                this.updateModelParameter(cubismModel, 'ParamEyeLOpen', Math.max(0, 1 - Math.abs(normalizedY * 0.3)));
                this.updateModelParameter(cubismModel, 'ParamEyeROpen', Math.max(0, 1 - Math.abs(normalizedY * 0.3)));
                this.updateModelParameter(cubismModel, 'ParamEyeBallX', normalizedX * 0.8);
                this.updateModelParameter(cubismModel, 'ParamEyeBallY', -normalizedY * 0.5);
                this.updateModelParameter(cubismModel, 'ParamAngleX', normalizedX * 15);
                this.updateModelParameter(cubismModel, 'ParamAngleY', -normalizedY * 10);

                // Update model and redraw
                cubismModel.update();
                this.updateDrawables(cubismModel, drawableSprites);
            });

            // Click for expressions
            modelContainer.on('pointerdown', () => {
                this.log('Model clicked! Triggering expression...', 'info');
                this.triggerRandomExpression(cubismModel);
                cubismModel.update();
                this.updateDrawables(cubismModel, drawableSprites);
            });

            // Start breathing animation
            this.startBreathingAnimation(cubismModel, drawableSprites);

            // Store references for animation
            modelContainer.cubismModel = cubismModel;
            modelContainer.textures = textures;
            modelContainer.drawableSprites = drawableSprites;

            this.app.stage.addChild(modelContainer);
            this.model = modelContainer;

            // Enable mouse interaction
            this.setupMouseInteraction(modelContainer);

            this.log(`Enhanced Live2D model loaded! ${cubismModel.drawables.count} drawables, ${cubismModel.parameters.count} parameters`, 'success');

            return modelContainer;
            
        } catch (error) {
            this.log(`Raw Cubism loading failed: ${error.message}`, 'error');
            throw error;
        }
    }
    
    // Helper method to update model parameters by name
    updateModelParameter(cubismModel, paramName, value) {
        for (let i = 0; i < cubismModel.parameters.count; i++) {
            const id = cubismModel.parameters.ids[i];
            if (id === paramName) {
                const min = cubismModel.parameters.minimumValues[i];
                const max = cubismModel.parameters.maximumValues[i];
                cubismModel.parameters.values[i] = Math.max(min, Math.min(max, value));
                return true;
            }
        }
        return false;
    }
    
    // Update drawable sprites based on model state
    updateDrawables(cubismModel, drawableSprites) {
        for (let i = 0; i < cubismModel.drawables.count; i++) {
            const graphics = drawableSprites[i];
            if (graphics) {
                graphics.alpha = cubismModel.drawables.opacities[i];
                graphics.visible = (cubismModel.drawables.dynamicFlags[i] & 0x01) !== 0;
                graphics.zIndex = cubismModel.drawables.renderOrders[i];
                
                // Update vertex positions if they changed
                if (graphics.children.length > 0 && graphics.children[0] instanceof PIXI.Mesh) {
                    const mesh = graphics.children[0];
                    const geometry = mesh.geometry;
                    const vertexCount = cubismModel.drawables.vertexCounts[i];
                    const vertexPositions = cubismModel.drawables.vertexPositions[i];
                    
                    if (vertexCount > 0 && geometry.buffers && geometry.buffers.length > 0) {
                        const positionBuffer = geometry.buffers.find(b => b.data instanceof Float32Array);
                        if (positionBuffer) {
                            const positions = positionBuffer.data;
                            const scale = 0.23 * 200; // Use the same scale as before
                            
                            for (let j = 0; j < vertexCount; j++) {
                                positions[j * 2] = vertexPositions[j * 2] * scale;
                                positions[j * 2 + 1] = vertexPositions[j * 2 + 1] * scale;
                            }
                            
                            positionBuffer.update();
                        }
                    }
                }
            }
        }
    }
    
    // Trigger random facial expressions
    triggerRandomExpression(cubismModel) {
        const expressions = [
            { name: 'Smile', params: { 'ParamMouthForm': 1, 'ParamMouthOpenY': 0.3 } },
            { name: 'Surprised', params: { 'ParamEyeLOpen': 1.2, 'ParamEyeROpen': 1.2, 'ParamMouthOpenY': 0.8 } },
            { name: 'Wink', params: { 'ParamEyeLOpen': 0, 'ParamEyeROpen': 1 } },
            { name: 'Happy', params: { 'ParamMouthForm': 1, 'ParamBrowLY': 0.5, 'ParamBrowRY': 0.5 } }
        ];
        
        const expression = expressions[Math.floor(Math.random() * expressions.length)];
        this.log(`Triggering expression: ${expression.name}`, 'info');
        
        for (const [paramName, value] of Object.entries(expression.params)) {
            this.updateModelParameter(cubismModel, paramName, value);
        }
        
        // Reset after 2 seconds
        setTimeout(() => {
            for (const paramName of Object.keys(expression.params)) {
                this.updateModelParameter(cubismModel, paramName, 0);
            }
            cubismModel.update();
            this.updateDrawables(cubismModel, this.model.drawableSprites);
        }, 2000);
    }
    
    // Start breathing animation
    startBreathingAnimation(cubismModel, drawableSprites) {
        const breathingInterval = setInterval(() => {
            if (!this.model || !this.model.cubismModel) {
                clearInterval(breathingInterval);
                return;
            }
            
            const time = Date.now() * 0.001; // Convert to seconds
            const breathValue = Math.sin(time * 2) * 0.3; // Breathing cycle
            
            this.updateModelParameter(cubismModel, 'ParamBreath', breathValue);
            this.updateModelParameter(cubismModel, 'ParamBodyAngleX', Math.sin(time * 0.8) * 2);
            
            cubismModel.update();
            this.updateDrawables(cubismModel, drawableSprites);
        }, 33); // ~30 FPS
    }
    
    // Calculate optimal model scale based on canvas size (Live2D Viewer Web pattern)
    calculateOptimalModelScale(model, container) {
        if (!this.app) return 1.0;
        
        // FORCE use of stored canvas dimensions - bypass renderer issue
        const canvasWidth = this.canvasWidth || 800;
        const canvasHeight = this.canvasHeight || 600;
        
        // Use Live2D Viewer Web's fit method pattern
        if (model && (model.width || model.getBounds)) {
            // Get model dimensions - try direct properties first (Live2D Viewer Web style)
            let modelWidth, modelHeight;
            
            if (model.width && model.height) {
                modelWidth = model.width;
                modelHeight = model.height;
            } else if (model.getBounds) {
                const bounds = model.getBounds();
                modelWidth = bounds.width;
                modelHeight = bounds.height;
            }
            
            if (modelWidth > 0 && modelHeight > 0 && canvasWidth > 0 && canvasHeight > 0) {
                // Live2D Viewer Web fit() method pattern
                let scale = Math.min(
                    canvasWidth / modelWidth,
                    canvasHeight / modelHeight
                );
                
                // Apply the same rounding as Live2D Viewer Web
                scale = Math.round(scale * 10) / 10;
                
                // Store as base scale
                this.baseScale = scale;
                
                this.log(`Model scaling (FORCED dimensions): canvas=${canvasWidth}x${canvasHeight}, model=${modelWidth}x${modelHeight}, scale=${scale}`, 'info');
                return scale;
            }
        }
        
        // Default scale if no model bounds available
        this.baseScale = 1.0;
        this.log(`Model scaling (default): using scale=1.0`, 'info');
        return 1.0;
    }

    // Scale model with zoom multiplier
    scaleModel(zoomMultiplier) {
        if (!this.model) {
            this.log('No model loaded to scale', 'warning');
            return;
        }

        const baseScale = this.baseScale || 1.0;
        const finalScale = baseScale * zoomMultiplier;
        
        this.model.scale.set(finalScale);
        this.log(`Model zoom: base=${baseScale}, multiplier=${zoomMultiplier}, final=${finalScale}`, 'info');
        
        // Update any frame visualizations
        if (this.modelFrameGraphics && this.modelFrameGraphics.visible) {
            this.drawModelFrame();
        }
        if (this.hitBoxGraphics && this.hitBoxGraphics.visible) {
            this.drawHitBoxes();
        }
    }

    // Setup mouse interaction for model dragging (Live2D Viewer Web pattern)
    setupMouseInteraction(model) {
        if (!model) return;
        
        // Make model interactive
        model.interactive = true;
        model.eventMode = 'static';
        
        // Add draggable behavior using Live2D Viewer Web pattern
        model.dragging = false;
        model._pointerX = 0;
        model._pointerY = 0;
        
        // Mouse/touch event handlers (Live2D Viewer Web pattern)
        model.on('pointerdown', (e) => {
            model.dragging = true;
            model._pointerX = e.data.global.x - model.x;
            model._pointerY = e.data.global.y - model.y;
            model.alpha = 0.8; // Visual feedback
            this.log('Model drag started', 'info');
        });
        
        model.on('pointermove', (e) => {
            if (model.dragging) {
                model.position.x = e.data.global.x - model._pointerX;
                model.position.y = e.data.global.y - model._pointerY;
                
                // Update frame visualizations if visible
                if (this.modelFrameGraphics && this.modelFrameGraphics.visible) {
                    this.drawModelFrame();
                }
                if (this.hitBoxGraphics && this.hitBoxGraphics.visible) {
                    this.drawHitBoxes();
                }
            }
        });
        
        model.on('pointerup', (e) => {
            if (model.dragging) {
                model.dragging = false;
                model.alpha = 1.0; // Restore normal opacity
                this.log(`Model positioned at: ${model.position.x.toFixed(0)}, ${model.position.y.toFixed(0)}`, 'info');
            }
        });
        
        model.on('pointerupoutside', (e) => {
            if (model.dragging) {
                model.dragging = false;
                model.alpha = 1.0; // Restore normal opacity
                this.log(`Model positioned at: ${model.position.x.toFixed(0)}, ${model.position.y.toFixed(0)}`, 'info');
            }
        });
        
        // Click handler for hit testing (separate from drag)
        model.on('pointerdown', (e) => {
            if (!model.dragging) {
                // Get click position relative to model
                const localPoint = model.toLocal(e.data.global);
                
                // Check for hit areas (if model supports it)
                if (model.hitTest && typeof model.hitTest === 'function') {
                    const hitAreas = model.hitTest(localPoint.x, localPoint.y);
                    if (hitAreas && hitAreas.length > 0) {
                        this.log(`Hit areas clicked: ${hitAreas.join(', ')}`, 'info');
                        // Could trigger motions based on hit areas here
                    }
                }
                
                this.log(`Model clicked at: ${localPoint.x.toFixed(0)}, ${localPoint.y.toFixed(0)}`, 'info');
            }
        });
        
        this.log('Mouse interaction enabled for model (Live2D Viewer Web pattern)', 'info');
    }

    // Center model in canvas
    centerModel() {
        if (!this.model) {
            this.log('No model loaded to center', 'warning');
            return;
        }

        const canvasWidth = this.app.renderer ? this.app.renderer.width : this.app.screen.width;
        const canvasHeight = this.app.renderer ? this.app.renderer.height : this.app.screen.height;
        
        const centerX = canvasWidth / 2;
        const centerY = canvasHeight / 2;
        
        this.model.position.set(centerX, centerY);
        
        // Update frame visualizations if visible
        if (this.modelFrameGraphics && this.modelFrameGraphics.visible) {
            this.drawModelFrame();
        }
        if (this.hitBoxGraphics && this.hitBoxGraphics.visible) {
            this.drawHitBoxes();
        }
        
        this.log(`Model centered at: ${centerX.toFixed(0)}, ${centerY.toFixed(0)}`, 'info');
    }

    // Toggle canvas frame visibility
    toggleCanvasFrame() {
        const canvas = this.app.canvas || this.app.view;
        const currentBorder = canvas.style.border;
        
        if (currentBorder && currentBorder !== 'none') {
            canvas.style.border = 'none';
            this.log('Canvas frame hidden', 'info');
        } else {
            canvas.style.border = '2px solid #4a90e2';
            this.log('Canvas frame shown', 'info');
        }
    }

    // Toggle model frame visualization
    toggleModelFrame() {
        if (!this.model) {
            this.log('No model loaded for frame visualization', 'warning');
            return;
        }
        
        // Create or toggle model frame graphics
        if (!this.modelFrameGraphics) {
            this.modelFrameGraphics = new PIXI.Graphics();
            this.app.stage.addChild(this.modelFrameGraphics);
        }
        
        if (this.modelFrameGraphics.visible) {
            this.modelFrameGraphics.visible = false;
            this.log('Model frame hidden', 'info');
        } else {
            this.drawModelFrame();
            this.modelFrameGraphics.visible = true;
            this.log('Model frame shown', 'info');
        }
    }

    // Draw model frame visualization
    drawModelFrame() {
        if (!this.modelFrameGraphics || !this.model) return;
        
        this.modelFrameGraphics.clear();
        this.modelFrameGraphics.lineStyle(2, 0xff0000, 0.8);
        
        // Get model bounds
        const bounds = this.model.getBounds();
        
        // Draw bounding box
        this.modelFrameGraphics.drawRect(
            bounds.x, bounds.y, bounds.width, bounds.height
        );
        
        // Draw center cross
        this.modelFrameGraphics.lineStyle(1, 0xff0000, 0.6);
        const centerX = bounds.x + bounds.width / 2;
        const centerY = bounds.y + bounds.height / 2;
        
        // Horizontal line
        this.modelFrameGraphics.moveTo(bounds.x, centerY);
        this.modelFrameGraphics.lineTo(bounds.x + bounds.width, centerY);
        
        // Vertical line
        this.modelFrameGraphics.moveTo(centerX, bounds.y);
        this.modelFrameGraphics.lineTo(centerX, bounds.y + bounds.height);
        
        // Add label
        const style = new PIXI.TextStyle({
            fontSize: 12,
            fill: 0xff0000,
            backgroundColor: 0x000000,
            backgroundAlpha: 0.8
        });
        
        const label = new PIXI.Text(`Model: ${bounds.width.toFixed(0)}×${bounds.height.toFixed(0)}`, style);
        label.position.set(bounds.x, bounds.y - 20);
        this.modelFrameGraphics.addChild(label);
    }

    // Toggle hit box visualization
    toggleHitBoxes() {
        if (!this.model) {
            this.log('No model loaded for hit box visualization', 'warning');
            return;
        }
        
        // Check if hit areas exist
        if (this.model.hitAreas && this.model.hitAreas.length > 0) {
            // Create or toggle hit box graphics
            if (!this.hitBoxGraphics) {
                this.hitBoxGraphics = new PIXI.Graphics();
                this.app.stage.addChild(this.hitBoxGraphics);
            }
            
            if (this.hitBoxGraphics.visible) {
                this.hitBoxGraphics.visible = false;
                this.log('Hit boxes hidden', 'info');
            } else {
                this.drawHitBoxes();
                this.hitBoxGraphics.visible = true;
                this.log('Hit boxes shown', 'info');
            }
        } else {
            this.log('No hit areas defined for this model', 'warning');
        }
    }

    // Draw hit box visualization
    drawHitBoxes() {
        if (!this.hitBoxGraphics || !this.model) return;
        
        this.hitBoxGraphics.clear();
        this.hitBoxGraphics.lineStyle(2, 0x00ff00, 0.8);
        
        // Draw hit areas if they exist
        if (this.model.hitAreas) {
            this.model.hitAreas.forEach((hitArea, index) => {
                const bounds = hitArea.getBounds();
                this.hitBoxGraphics.drawRect(
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
                this.hitBoxGraphics.addChild(label);
            });
        }
    }

    // Draw a Live2D drawable using vertex data
    // drawLive2DDrawable is now unused in mesh-based rendering
    drawLive2DDrawable() { /* no-op for mesh-based fallback */ }

    getModel() {
        return this.model;
    }

    getApp() {
        return this.app;
    }

    destroy() {
        if (this.hitBoxGraphics) {
            this.app.stage.removeChild(this.hitBoxGraphics);
            this.hitBoxGraphics = null;
        }
        if (this.modelFrameGraphics) {
            this.app.stage.removeChild(this.modelFrameGraphics);
            this.modelFrameGraphics = null;
        }
        if (this.model && this.app) {
            this.app.stage.removeChild(this.model);
            this.model = null;
        }
        if (this.app) {
            this.app.destroy();
            this.app = null;
        }
    }
}

// Export for use in other modules
window.Live2DCore = Live2DCore;
