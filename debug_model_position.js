// Debug script to check and fix model positioning
console.log('=== MANUAL MODEL DEBUG ===');

// Get the PIXI app
const app = window.pixiApp || window.live2dApp;
console.log('PIXI App:', app);

if (app) {
    console.log('Canvas dimensions:', {
        width: app.screen.width,
        height: app.screen.height,
        view: {
            width: app.view.width,
            height: app.view.height,
            clientWidth: app.view.clientWidth,
            clientHeight: app.view.clientHeight
        }
    });
    
    console.log('Stage children count:', app.stage.children.length);
    app.stage.children.forEach((child, index) => {
        console.log(`Child ${index}:`, {
            type: child.constructor.name,
            position: { x: child.x, y: child.y },
            scale: { x: child.scale.x, y: child.scale.y },
            visible: child.visible,
            alpha: child.alpha,
            bounds: child.getBounds ? child.getBounds() : 'no bounds'
        });
    });
}

// Get the model manager
const manager = window.live2dMultiModelManager;
console.log('Model Manager:', manager);

if (manager && manager.models) {
    console.log('Models in manager:', manager.models.size);
    
    for (const [id, modelData] of manager.models) {
        console.log(`Model ${id}:`, {
            name: modelData.name,
            visible: modelData.visible,
            pixiModel: {
                position: { x: modelData.pixiModel.x, y: modelData.pixiModel.y },
                scale: { x: modelData.pixiModel.scale.x, y: modelData.pixiModel.scale.y },
                visible: modelData.pixiModel.visible,
                alpha: modelData.pixiModel.alpha,
                bounds: modelData.pixiModel.getBounds ? modelData.pixiModel.getBounds() : 'no bounds',
                parent: modelData.pixiModel.parent ? 'has parent' : 'no parent'
            }
        });
        
        // Try to make the model more visible
        console.log(`Fixing model ${id}...`);
        
        // Increase scale significantly
        modelData.pixiModel.scale.set(1.0);
        
        // Move to center of screen
        const centerX = app.screen.width / 2;
        const centerY = app.screen.height / 2;
        modelData.pixiModel.position.set(centerX, centerY);
        
        // Ensure visibility
        modelData.pixiModel.visible = true;
        modelData.pixiModel.alpha = 1.0;
        
        // Ensure it's in the stage
        if (!app.stage.children.includes(modelData.pixiModel)) {
            app.stage.addChild(modelData.pixiModel);
            console.log(`Added model ${id} to stage`);
        }
        
        console.log(`Model ${id} repositioned to:`, {
            position: { x: modelData.pixiModel.x, y: modelData.pixiModel.y },
            scale: { x: modelData.pixiModel.scale.x, y: modelData.pixiModel.scale.y },
            visible: modelData.pixiModel.visible,
            bounds: modelData.pixiModel.getBounds()
        });
    }
}

console.log('=== DEBUG COMPLETE ===');
