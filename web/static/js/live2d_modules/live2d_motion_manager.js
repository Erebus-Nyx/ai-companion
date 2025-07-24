// Live2D Motion Manager - Enhanced motion management for the modular system
class Live2DMotionManager {
    constructor(core, logger) {
        this.core = core;
        this.logger = logger;
        this.motionGroups = {};
        this.availableMotions = [];
        this.currentMotion = null;
        this.motionQueue = [];
    }

    log(message, type = 'info') {
        if (this.logger) {
            this.logger.log(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    async loadModelMotions(modelName) {
        try {
            this.log(`Loading motions for model: ${modelName}`, 'info');
            
            // Load motions from Flask API using dynamic configuration
            const baseUrl = await getApiBaseUrl();
            const response = await fetch(`${baseUrl}/api/live2d/model/${modelName}/motions`);
            
            if (!response.ok) {
                throw new Error(`Failed to load motions: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Process the motion groups data from the API
            this.processMotionGroups(data.motions || {}, data.motion_groups || []);
            
            this.log(`Loaded ${this.availableMotions.length} motions in ${Object.keys(this.motionGroups).length} groups for ${modelName}`, 'success');
            return this.availableMotions;
            
        } catch (error) {
            this.log(`Failed to load motions for ${modelName}: ${error.message}`, 'error');
            this.availableMotions = [];
            this.motionGroups = {};
            throw error;
        }
    }

    processMotions(motions) {
        this.availableMotions = [];
        this.motionGroups = {};
        
        motions.forEach(motionName => {
            const motion = this.createMotionObject(motionName);
            this.availableMotions.push(motion);
            
            // Group motions by category
            if (!this.motionGroups[motion.group]) {
                this.motionGroups[motion.group] = [];
            }
            this.motionGroups[motion.group].push(motion);
        });
    }

    processMotionGroups(motionGroups, groupNames) {
        this.availableMotions = [];
        this.motionGroups = {};
        
        // Process each motion group from the API response
        Object.keys(motionGroups).forEach(groupName => {
            const motions = motionGroups[groupName];
            
            motions.forEach(motionData => {
                const motion = {
                    name: motionData.name,
                    group: groupName,
                    type: this.classifyMotionType(groupName),
                    displayName: this.formatDisplayName(motionData.name),
                    priority: this.getMotionPriority(this.classifyMotionType(groupName)),
                    file: motionData.file,
                    fadeInTime: motionData.fadeInTime || 0.5,
                    fadeOutTime: motionData.fadeOutTime || 0.5,
                    index: motionData.index || 0
                };
                
                this.availableMotions.push(motion);
                
                // Group motions by category
                if (!this.motionGroups[groupName]) {
                    this.motionGroups[groupName] = [];
                }
                this.motionGroups[groupName].push(motion);
            });
        });
    }

    createMotionObject(motionName) {
        const parts = motionName.split('_');
        const group = parts[0] || 'default';
        const type = this.classifyMotionType(group);
        
        return {
            name: motionName,
            group: group,
            type: type,
            displayName: this.formatDisplayName(motionName),
            priority: this.getMotionPriority(type)
        };
    }

    classifyMotionType(groupName) {
        const name = groupName.toLowerCase();
        
        if (name.includes('idle') || name.includes('wait') || name.includes('breath')) {
            return 'idle';
        }
        if (name.includes('head') || name.includes('face') || name.includes('eye') || 
            name.includes('nod') || name.includes('tilt') || name.includes('think')) {
            return 'head';
        }
        if (name.includes('body') || name.includes('pose') || name.includes('arm') || 
            name.includes('hand') || name.includes('wave') || name.includes('gesture')) {
            return 'body';
        }
        if (name.includes('expression') || name.includes('expr') || name.includes('emotion')) {
            return 'expression';
        }
        if (name.includes('special') || name.includes('unique') || name.includes('event')) {
            return 'special';
        }
        if (name.includes('talk') || name.includes('speak') || name.includes('voice')) {
            return 'talk';
        }
        
        return 'body'; // Default category
    }

    formatDisplayName(motionName) {
        return motionName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    getMotionPriority(type) {
        const priorities = {
            'idle': 0,
            'head': 1,
            'body': 2,
            'talk': 3,
            'expression': 4,
            'special': 5
        };
        return priorities[type] || 2;
    }

    extractModelMotions() {
        // Try to extract motions from the loaded Live2D model
        if (!this.core.model) return;
        
        try {
            const model = this.core.model;
            
            // Check for motion groups in the model
            if (model.internalModel && model.internalModel.motionManager) {
                const motionManager = model.internalModel.motionManager;
                
                if (motionManager.groups) {
                    Object.keys(motionManager.groups).forEach(groupName => {
                        const group = motionManager.groups[groupName];
                        if (group && group.length > 0) {
                            group.forEach((motion, index) => {
                                const motionName = `${groupName}_${index}`;
                                const motionObj = this.createMotionObject(motionName);
                                
                                // Add if not already exists
                                if (!this.availableMotions.find(m => m.name === motionName)) {
                                    this.availableMotions.push(motionObj);
                                    
                                    if (!this.motionGroups[motionObj.group]) {
                                        this.motionGroups[motionObj.group] = [];
                                    }
                                    this.motionGroups[motionObj.group].push(motionObj);
                                }
                            });
                        }
                    });
                }
            }
            
            this.log(`Extracted ${this.availableMotions.length} total motions from model`, 'info');
            
        } catch (error) {
            this.log(`Failed to extract motions from model: ${error.message}`, 'warning');
        }
    }

    getAvailableMotions() {
        return this.availableMotions;
    }

    getMotionGroups() {
        return Object.keys(this.motionGroups);
    }

    getMotionsByGroup(groupName) {
        return this.motionGroups[groupName] || [];
    }

    getMotionsByType(type) {
        return this.availableMotions.filter(motion => motion.type === type);
    }

    async playMotion(motionName, priority = 2) {
        if (!this.core.model) {
            throw new Error('No model loaded');
        }

        try {
            const model = this.core.model;
            const motion = this.availableMotions.find(m => m.name === motionName);
            
            if (!motion) {
                throw new Error(`Motion "${motionName}" not found`);
            }

            // Try different ways to play the motion
            let success = false;
            
            // Method 1: Direct motion call
            if (model.motion && typeof model.motion === 'function') {
                try {
                    await model.motion(motionName, priority);
                    success = true;
                } catch (e) {
                    this.log(`Direct motion call failed: ${e.message}`, 'warning');
                }
            }

            // Method 2: Motion by group and index
            if (!success && model.internalModel && model.internalModel.motionManager) {
                try {
                    const parts = motionName.split('_');
                    const group = parts[0];
                    const index = parseInt(parts[1]) || 0;
                    
                    await model.internalModel.motionManager.startMotion(group, index, priority);
                    success = true;
                } catch (e) {
                    this.log(`Group/index motion call failed: ${e.message}`, 'warning');
                }
            }

            // Method 3: Motion file URL
            if (!success) {
                try {
                    const modelName = this.core.currentModel?.name;
                    if (modelName) {
                        const baseUrl = await getApiBaseUrl();
                        const motionUrl = `${baseUrl}/api/live2d/model/${modelName}/motion/${motionName}`;
                        await model.motion(motionUrl, priority);
                        success = true;
                    }
                } catch (e) {
                    this.log(`URL motion call failed: ${e.message}`, 'warning');
                }
            }

            if (success) {
                this.currentMotion = motion;
                this.log(`Playing motion: ${motion.displayName}`, 'success');
                return true;
            } else {
                throw new Error(`Failed to play motion: ${motionName}`);
            }
            
        } catch (error) {
            this.log(`Motion playback failed: ${error.message}`, 'error');
            throw error;
        }
    }

    async playRandomMotion(type = null) {
        let motions = this.availableMotions;
        
        if (type) {
            motions = this.getMotionsByType(type);
        }
        
        if (motions.length === 0) {
            throw new Error('No motions available');
        }
        
        const randomMotion = motions[Math.floor(Math.random() * motions.length)];
        return await this.playMotion(randomMotion.name);
    }

    async playMotionsByGroup(groupName) {
        const groupMotions = this.getMotionsByGroup(groupName);
        
        if (groupMotions.length === 0) {
            throw new Error(`No motions found in group: ${groupName}`);
        }
        
        const randomMotion = groupMotions[Math.floor(Math.random() * groupMotions.length)];
        return await this.playMotion(randomMotion.name);
    }

    stopCurrentMotion() {
        if (!this.core.model) {
            throw new Error('No model loaded');
        }

        try {
            const model = this.core.model;
            
            if (model.internalModel && model.internalModel.motionManager) {
                model.internalModel.motionManager.stopAllMotions();
            }
            
            this.currentMotion = null;
            this.log('All motions stopped', 'info');
            
        } catch (error) {
            this.log(`Failed to stop motions: ${error.message}`, 'error');
            throw error;
        }
    }

    getCurrentMotion() {
        return this.currentMotion;
    }

    isMotionPlaying() {
        if (!this.core.model) return false;
        
        try {
            const model = this.core.model;
            if (model.internalModel && model.internalModel.motionManager) {
                return model.internalModel.motionManager.isMotionPlaying();
            }
            return false;
        } catch (error) {
            return false;
        }
    }

    // Queue management
    addToQueue(motionName, priority = 2) {
        this.motionQueue.push({ motionName, priority });
        this.log(`Added to queue: ${motionName}`, 'info');
    }

    async playQueue() {
        while (this.motionQueue.length > 0) {
            const { motionName, priority } = this.motionQueue.shift();
            
            try {
                await this.playMotion(motionName, priority);
                
                // Wait for motion to finish before playing next
                await this.waitForMotionComplete();
                
            } catch (error) {
                this.log(`Queue motion failed: ${error.message}`, 'error');
            }
        }
    }

    async waitForMotionComplete() {
        return new Promise((resolve) => {
            const checkComplete = () => {
                if (!this.isMotionPlaying()) {
                    resolve();
                } else {
                    setTimeout(checkComplete, 100);
                }
            };
            checkComplete();
        });
    }

    clearQueue() {
        this.motionQueue = [];
        this.log('Motion queue cleared', 'info');
    }

    getQueueLength() {
        return this.motionQueue.length;
    }

    // Statistics
    getMotionStats() {
        const stats = {
            totalMotions: this.availableMotions.length,
            groups: Object.keys(this.motionGroups).length,
            types: {},
            currentMotion: this.currentMotion?.name || 'None',
            queueLength: this.motionQueue.length
        };

        // Count by type
        this.availableMotions.forEach(motion => {
            stats.types[motion.type] = (stats.types[motion.type] || 0) + 1;
        });

        return stats;
    }
}

// Lipsync and Avatar Control Functions for TTS Integration
function setAvatarMouthShape(avatarId, mouthShape, intensity = 0.7) {
    try {
        const pixiModel = findAvatarModel(avatarId);
        if (!pixiModel) {
            console.warn(`Avatar model not found for ${avatarId}`);
            return;
        }
        
        // Direct Live2D parameter manipulation for mouth shapes
        if (pixiModel.internalModel && pixiModel.internalModel.coreModel) {
            const coreModel = pixiModel.internalModel.coreModel;
            
            // Common Live2D mouth parameters
            const mouthParams = {
                'A': ['ParamMouthOpenY', 'PARAM_MOUTH_OPEN_Y'],
                'I': ['ParamMouthForm', 'PARAM_MOUTH_FORM'],
                'U': ['ParamMouthForm', 'PARAM_MOUTH_FORM'],
                'E': ['ParamMouthOpenY', 'PARAM_MOUTH_OPEN_Y'],
                'O': ['ParamMouthOpenY', 'PARAM_MOUTH_OPEN_Y'],
                'default': ['ParamMouthOpenY', 'PARAM_MOUTH_OPEN_Y']
            };
            
            const paramNames = mouthParams[mouthShape] || mouthParams['default'];
            let paramSet = false;
            
            for (const paramName of paramNames) {
                try {
                    // Try to set the parameter if it exists
                    const paramIndex = coreModel.getParameterIndex(paramName);
                    if (paramIndex >= 0) {
                        let value = 0;
                        
                        // Set parameter values based on mouth shape
                        switch (mouthShape) {
                            case 'A':
                                value = intensity * 1.0; // Wide open
                                break;
                            case 'I':
                                value = intensity * 0.3; // Slightly open, stretched
                                break;
                            case 'U':
                                value = intensity * -0.8; // Pursed lips
                                break;
                            case 'E':
                                value = intensity * 0.6; // Medium open
                                break;
                            case 'O':
                                value = intensity * 0.8; // Round open
                                break;
                            default:
                                value = 0; // Closed/neutral
                                break;
                        }
                        
                        coreModel.setParameterValueByIndex(paramIndex, value);
                        paramSet = true;
                        console.log(`👄 Set ${paramName} to ${value} for mouth shape "${mouthShape}"`);
                        break; // Use first available parameter
                    }
                } catch (paramError) {
                    // Continue to next parameter name
                }
            }
            
            if (!paramSet) {
                console.warn(`No mouth parameters found for ${avatarId}`);
            }
            
        } else if (pixiModel.setMouthShape && typeof pixiModel.setMouthShape === 'function') {
            // Fallback to custom setMouthShape if available
            pixiModel.setMouthShape(mouthShape, intensity);
            console.log(`👄 Mouth shape "${mouthShape}" set for ${avatarId} with intensity ${intensity}`);
        } else {
            console.warn(`Avatar model found but no mouth control available for ${avatarId}`);
        }
    } catch (error) {
        console.warn('Failed to set avatar mouth shape:', error);
    }
}

function setAvatarBlinkRate(avatarId, blinkRate = 1.0) {
    try {
        const pixiModel = findAvatarModel(avatarId);
        if (pixiModel && typeof pixiModel.setBlinkRate === 'function') {
            pixiModel.setBlinkRate(blinkRate);
            console.log(`👁️ Blink rate ${blinkRate} set for ${avatarId}`);
        }
    } catch (error) {
        console.warn('Failed to set avatar blink rate:', error);
    }
}

function setAvatarBodySway(avatarId, swayIntensity = 0.3) {
    try {
        const pixiModel = findAvatarModel(avatarId);
        if (pixiModel && typeof pixiModel.setBodySway === 'function') {
            pixiModel.setBodySway(swayIntensity);
            console.log(`🌊 Body sway ${swayIntensity} set for ${avatarId}`);
        }
    } catch (error) {
        console.warn('Failed to set avatar body sway:', error);
    }
}

function findAvatarModel(avatarId) {
    // Find the PIXI model for an avatar ID
    try {
        // Check if avatarId is already a PIXI model
        if (avatarId && typeof avatarId === 'object' && avatarId.motion) {
            return avatarId;
        }
        
        console.log(`🔍 Searching for avatar model: ${avatarId}`);
        
        // Look in loaded avatars
        if (window.loadedAvatars) {
            for (let avatar of window.loadedAvatars) {
                if (avatar.id === avatarId || avatar.name === avatarId) {
                    console.log(`✅ Found avatar in loadedAvatars: ${avatar.name || avatar.id}`);
                    return avatar.pixiModel;
                }
            }
        }
        
        // Look in Live2D multi-model manager
        if (window.live2dMultiModelManager && window.live2dMultiModelManager.getAllModels) {
            const models = window.live2dMultiModelManager.getAllModels();
            console.log(`🔍 Checking ${models.length} models in multi-model manager`);
            
            for (let model of models) {
                console.log(`Model found: name="${model.name}", id="${model.id}", fileName="${model.fileName}"`);
                
                // Check direct name/id match
                if (model.name === avatarId || model.id === avatarId) {
                    console.log(`✅ Found exact match for ${avatarId}`);
                    return model.pixiModel || model;
                }
                
                // Check filename match (e.g., "iori.model3.json" -> "iori")
                if (model.fileName && model.fileName.toLowerCase().includes(avatarId.toLowerCase())) {
                    console.log(`✅ Found filename match for ${avatarId}: ${model.fileName}`);
                    return model.pixiModel || model;
                }
                
                // Check if name contains avatarId
                if (model.name && model.name.toLowerCase().includes(avatarId.toLowerCase())) {
                    console.log(`✅ Found partial name match for ${avatarId}: ${model.name}`);
                    return model.pixiModel || model;
                }
            }
        }
        
        // Look in Live2D model manager
        if (window.live2dManager && window.live2dManager.models) {
            console.log(`🔍 Checking live2dManager models`);
            for (let [modelId, model] of window.live2dManager.models) {
                if (modelId === avatarId || model.name === avatarId) {
                    console.log(`✅ Found model in live2dManager: ${modelId}`);
                    return model.pixiModel || model;
                }
            }
        }
        
        console.warn(`❌ Avatar model not found for ID: ${avatarId}`);
        return null;
    } catch (error) {
        console.warn('Error finding avatar model:', error);
        return null;
    }
}

// Export for use in other modules
window.Live2DMotionManager = Live2DMotionManager;

// Export lipsync and avatar control functions to window for global access
window.setAvatarMouthShape = setAvatarMouthShape;
window.setAvatarBlinkRate = setAvatarBlinkRate;
window.setAvatarBodySway = setAvatarBodySway;
window.findAvatarModel = findAvatarModel;
