// Live2D Testing Module - Test utilities and diagnostics
class Live2DTester {
    constructor(core, logger) {
        this.core = core;
        this.logger = logger;
    }

    log(message, type = 'info') {
        if (this.logger) {
            this.logger.log(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    testCubism4Library() {
        this.log('=== TESTING CUBISM 4 LIBRARY ===');
        
        // Test what's available after loading cubism4.min.js
        const windowProps = Object.getOwnPropertyNames(window);
        const live2dRelated = windowProps.filter(prop => 
            prop.toLowerCase().includes('live2d') || 
            prop.toLowerCase().includes('cubism')
        );
        this.log('Live2D related window properties: ' + live2dRelated.join(', '));
        
        // Check PIXI extensions
        if (PIXI.live2d) {
            this.log('PIXI.live2d after cubism4 load:');
            const keys = Object.keys(PIXI.live2d);
            this.log('Keys: ' + keys.join(', '));
            
            keys.forEach(key => {
                const value = PIXI.live2d[key];
                if (typeof value === 'function') {
                    this.log(`${key} is a function with properties: ${Object.getOwnPropertyNames(value).join(', ')}`);
                    
                    if (value.from) {
                        this.log(`${key}.from() is available!`, 'success');
                    }
                }
            });
        }
        
        // Check for Live2DModel in different locations
        const locations = [
            { name: 'Live2DModel (global)', obj: typeof Live2DModel !== 'undefined' ? Live2DModel : null },
            { name: 'window.Live2DModel', obj: window.Live2DModel },
            { name: 'PIXI.live2d.Live2DModel', obj: PIXI.live2d && PIXI.live2d.Live2DModel },
            { name: 'PIXI.Live2DModel', obj: PIXI.Live2DModel }
        ];
        
        locations.forEach(location => {
            if (location.obj) {
                this.log(`Found ${location.name}!`, 'success');
                this.log(`  Type: ${typeof location.obj}`);
                if (typeof location.obj === 'function') {
                    this.log(`  Has .from() method: ${typeof location.obj.from === 'function'}`);
                }
            } else {
                this.log(`${location.name}: not found`);
            }
        });
    }

    async testSimpleTexture() {
        if (!this.core.app) {
            this.log('No app initialized!', 'error');
            return;
        }
        
        this.log('Testing simple texture rendering...');
        
        try {
            // Clear stage
            this.core.app.stage.removeChildren();
            
            // Load a texture directly
            const textureUrl = 'http://localhost:13443/static/assets/miku_1/runtime/miku_sample_t04.2048/texture_00.png';
            const texture = await PIXI.Assets.load(textureUrl);
            
            // Create a simple sprite
            const sprite = new PIXI.Sprite(texture);
            sprite.position.set(this.core.app.screen.width / 2, this.core.app.screen.height / 2);
            sprite.anchor.set(0.5);
            sprite.scale.set(0.3);
            
            this.core.app.stage.addChild(sprite);
            
            this.log('Simple texture sprite added to stage', 'success');
            this.log(`Texture size: ${texture.width}x${texture.height}`);
            
        } catch (error) {
            this.log('Simple texture test failed: ' + error.message, 'error');
        }
    }

    async testSimpleMesh() {
        if (!this.core.app) {
            this.log('No app initialized!', 'error');
            return;
        }
        
        this.log('Testing simple mesh rendering...');
        
        try {
            // Clear stage
            this.core.app.stage.removeChildren();
            
            // Load a texture
            const textureUrl = 'http://localhost:13443/static/assets/miku_1/runtime/miku_sample_t04.2048/texture_00.png';
            const texture = await PIXI.Assets.load(textureUrl);
            
            // Create simple quad geometry
            const vertices = new Float32Array([
                -100, -100,   // bottom left
                 100, -100,   // bottom right
                 100,  100,   // top right
                -100,  100    // top left
            ]);
            
            const uvs = new Float32Array([
                0, 1,   // bottom left
                1, 1,   // bottom right
                1, 0,   // top right
                0, 0    // top left
            ]);
            
            const indices = new Uint16Array([0, 1, 2, 0, 2, 3]);
            
            const geometry = new PIXI.Geometry();
            geometry.addAttribute('aVertexPosition', vertices, 2);
            geometry.addAttribute('aTextureCoord', uvs, 2);
            geometry.addIndex(indices);
            
            const mesh = new PIXI.Mesh(geometry, texture);
            mesh.position.set(this.core.app.screen.width / 2, this.core.app.screen.height / 2);
            
            this.core.app.stage.addChild(mesh);
            
            this.log('Simple mesh added to stage', 'success');
            
        } catch (error) {
            this.log('Simple mesh test failed: ' + error.message, 'error');
        }
    }

    testPIXITexture() {
        this.log('=== TESTING PIXI TEXTURE API ===');
        
        // Test different texture loading methods in PIXI v8+
        this.log('PIXI.Texture.fromURL available: ' + (typeof PIXI.Texture.fromURL === 'function'));
        this.log('PIXI.Texture.from available: ' + (typeof PIXI.Texture.from === 'function'));
        this.log('PIXI.Assets available: ' + (typeof PIXI.Assets !== 'undefined'));
        this.log('PIXI.Assets.load available: ' + (typeof PIXI.Assets !== 'undefined' && typeof PIXI.Assets.load === 'function'));
        
        // Test PIXI.live2d after library loading
        setTimeout(() => {
            this.log('=== PIXI.live2d INSPECTION ===');
            this.log('PIXI.live2d available: ' + (typeof PIXI.live2d !== 'undefined'));
            if (typeof PIXI.live2d !== 'undefined') {
                const keys = Object.keys(PIXI.live2d);
                this.log('PIXI.live2d keys: ' + keys.join(', '));
                
                keys.forEach(key => {
                    const value = PIXI.live2d[key];
                    this.log(`PIXI.live2d.${key} = ${typeof value}`);
                    
                    if (typeof value === 'function' && value.from) {
                        this.log(`  └─ Found .from() method on ${key}`, 'success');
                    }
                });
            }
        }, 1000);
    }

    debugModelBounds() {
        const model = this.core.getModel();
        if (!model) {
            this.log('No model loaded. Please load a model first.', 'error');
            return;
        }
        
        this.log('=== MODEL BOUNDS DEBUG ===');
        
        // Get the actual bounds of the model
        const bounds = model.getBounds();
        this.log('Model bounds: ' + bounds.x + ', ' + bounds.y + ', ' + bounds.width + ', ' + bounds.height);
        
        // Check if bounds are within viewport
        const viewport = {
            x: 0,
            y: 0,
            width: this.core.app.screen.width,
            height: this.core.app.screen.height
        };
        
        this.log('Viewport: ' + viewport.x + ', ' + viewport.y + ', ' + viewport.width + ', ' + viewport.height);
        
        const boundsInViewport = !(bounds.x > viewport.width || 
                                  bounds.x + bounds.width < viewport.x ||
                                  bounds.y > viewport.height || 
                                  bounds.y + bounds.height < viewport.y);
        
        this.log('Model visible in viewport: ' + boundsInViewport);
        
        // Try different scales to find visible one
        const testScales = [0.1, 0.2, 0.5, 1, 2, 5];
        this.log('Testing visibility at different scales...');
        
        for (const scale of testScales) {
            model.scale.set(scale);
            const testBounds = model.getBounds();
            const testVisible = !(testBounds.x > viewport.width || 
                                 testBounds.x + testBounds.width < viewport.x ||
                                 testBounds.y > viewport.height || 
                                 testBounds.y + testBounds.height < viewport.y);
            
            this.log('Scale ' + scale + ': bounds(' + testBounds.x.toFixed(0) + ', ' + testBounds.y.toFixed(0) + 
                ', ' + testBounds.width.toFixed(0) + ', ' + testBounds.height.toFixed(0) + ') visible: ' + testVisible);
            
            if (testVisible) {
                this.log('✓ Model should be visible at scale ' + scale, 'success');
                return;
            }
        }
        
        this.log('Model not visible at any tested scale', 'error');
    }
}

// Export for use in other modules
window.Live2DTester = Live2DTester;
