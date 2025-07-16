// Live2D Model Manager - Handles model selection and management
class Live2DModelManager {
    constructor(core, logger) {
        this.core = core;
        this.logger = logger;
        this.currentModel = null;
        this.modelList = [];
    }

    log(message, type = 'info') {
        if (this.logger) {
            this.logger.log(message, type);
        }
    }

    async loadAvailableModels() {
        try {
            // Use the existing Flask API endpoint
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
                url: `http://localhost:13443${model.model_path}/${model.config_file}`,
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

    async loadModel(modelName) {
        const modelInfo = this.modelList.find(m => m.name === modelName);
        if (!modelInfo) {
            const errorMessage = `Model "${modelName}" not found in available models`;
            this.log(errorMessage, 'error');
            throw new Error(errorMessage);
        }

        this.log(`Loading model: ${modelInfo.name}`, 'info');
        
        try {
            const model = await this.core.loadModel(modelInfo.url);
            
            this.currentModel = {
                name: modelInfo.name,
                path: modelInfo.path,
                url: modelInfo.url,
                info: modelInfo.info,
                pixiModel: model
            };
            
            this.log(`Successfully loaded model: ${modelInfo.name}`, 'success');
            return model;
            
        } catch (error) {
            const errorMessage = `Failed to load model ${modelInfo.name}: ${error.message}`;
            this.log(errorMessage, 'error');
            throw new Error(errorMessage);
        }
    }

    getCurrentModel() {
        return this.currentModel;
    }

    getModelList() {
        return this.modelList;
    }

    async switchModel(modelName) {
        this.log(`Switching to model: ${modelName}`, 'info');
        return await this.loadModel(modelName);
    }

    scaleModel(zoomMultiplier) {
        if (this.core && this.core.scaleModel) {
            this.core.scaleModel(zoomMultiplier);
        } else {
            this.log('Core scale method not available', 'error');
        }
    }

    cycleModelScales() {
        if (!this.currentModel || !this.currentModel.pixiModel) {
            this.log('No model loaded to scale', 'error');
            return;
        }

        const scales = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0];
        let currentScale = 0;
        
        const cycleScale = () => {
            const scale = scales[currentScale];
            this.scaleModel(scale);
            
            currentScale = (currentScale + 1) % scales.length;
            
            if (currentScale !== 0) {
                setTimeout(cycleScale, 2000);
            } else {
                this.log('Scaling test complete. Choose best scale and update code.', 'success');
            }
        };
        
        cycleScale();
    }
}

// Export for use in other modules
window.Live2DModelManager = Live2DModelManager;
