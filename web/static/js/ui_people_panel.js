/**
 * People Panel Management System
 * Handles model selection, loading, and people panel UI
 */

// People panel functionality
function populatePeopleModels() {
    const modelsList = document.getElementById('peopleModelsList');
    
    // Clear existing models
    modelsList.innerHTML = '';
    
    // Get loaded models from multi-model manager
    if (!live2dMultiModelManager) {
        modelsList.innerHTML = '<div style="text-align: center; padding: 20px; color: #aaa;">No models loaded</div>';
        return;
    }
    
    const loadedModels = live2dMultiModelManager.getAllModels();
    
    if (loadedModels.length === 0) {
        modelsList.innerHTML = '<div style="text-align: center; padding: 20px; color: #aaa;">No models loaded</div>';
        return;
    }
    
    loadedModels.forEach(modelData => {
        const isActive = live2dMultiModelManager.activeModelId === modelData.id;
        
        const modelItem = document.createElement('div');
        modelItem.className = `people-model-item ${isActive ? 'active' : ''}`;
        modelItem.innerHTML = `
            <div class="people-model-avatar">${modelData.characterImage ? `<img src="${modelData.characterImage}" alt="${modelData.name}">` : '👤'}</div>
            <div class="people-model-info">
                <div class="people-model-name">${modelData.name}</div>
                <div class="people-model-status">${isActive ? 'Active' : 'Inactive'}</div>
            </div>
            <button class="people-model-remove" onclick="event.stopPropagation(); removeModel('${modelData.id}'); return false;">×</button>
        `;
        
        // Add click handler for model selection
        modelItem.addEventListener('click', (e) => {
            // Only handle clicks that aren't on the remove button
            if (!e.target.classList.contains('people-model-remove')) {
                // Only switch if it's not already the active model
                if (live2dMultiModelManager && live2dMultiModelManager.activeModelId !== modelData.id) {
                    live2dMultiModelManager.setActiveModel(modelData.id);
                    
                    // Update current model reference for mouse interaction
                    setTimeout(() => {
                        updateCurrentModelReference();
                        updateModelInfoDisplay(`Switched to model: ${modelData.name}\nTry clicking or dragging the model`);
                    }, 200);
                    
                    // Refresh the panel to update active states
                    setTimeout(() => populatePeopleModels(), 100);
                } else {
                    // Still update the reference in case it got lost
                    updateCurrentModelReference();
                    updateModelInfoDisplay(`Model ${modelData.name} is already active\nTry clicking or dragging the model`);
                }
            }
        });
        
        modelsList.appendChild(modelItem);
    });
}

function selectModel(modelId) {
    // Update active model
    document.querySelectorAll('.people-model-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Set the clicked model as active
    event.currentTarget.classList.add('active');
    
    // Update model name in settings
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect) {
        modelSelect.value = modelId;
        onModelChange();
    }
}

function removeModel(modelId) {
    console.log('Removing model:', modelId);
    
    // Remove model from multi-model manager
    if (live2dMultiModelManager) {
        live2dMultiModelManager.removeModel(modelId);
        // Refresh the people panel after a short delay to allow cleanup
        setTimeout(() => populatePeopleModels(), 200);
    }
    
    // Prevent event bubbling
    return false;
}

function showAddModelDialog() {
    console.log('Opening add model dialog...');
    const dialog = document.getElementById('modelSelectionDialog');
    if (dialog) {
        dialog.style.display = 'flex';
        loadAvailableModelsForDialog();
    }
}

function closeAddModelDialog() {
    console.log('Closing add model dialog...');
    const dialog = document.getElementById('modelSelectionDialog');
    if (dialog) {
        dialog.style.display = 'none';
    }
}

async function loadAvailableModelsForDialog() {
    console.log('Loading available models for dialog...');
    const modelGrid = document.getElementById('modelGrid');
    
    try {
        // Use the already-loaded model list from the multi-model manager
        if (!live2dMultiModelManager || !live2dMultiModelManager.modelList || live2dMultiModelManager.modelList.length === 0) {
            // If not loaded yet, try to load
            await live2dMultiModelManager.loadAvailableModels();
        }
        
        const availableModels = live2dMultiModelManager.modelList;
        
        if (!availableModels || availableModels.length === 0) {
            modelGrid.innerHTML = '<div style="text-align: center; padding: 20px; color: #aaa;">No models available. Please check your model directory.</div>';
            return;
        }
        
        // Create model cards
        modelGrid.innerHTML = '';
        availableModels.forEach(model => {
            const modelCard = document.createElement('div');
            modelCard.className = 'model-card';
            modelCard.onclick = () => selectModelFromDialog(model.name, model.name);
            
            modelCard.innerHTML = `
                <div class="model-preview">
                    <div class="model-icon">🎭</div>
                </div>
                <div class="model-info">
                    <div class="model-name">${model.name}</div>
                    <div class="model-description">Live2D Model</div>
                </div>
            `;
            
            modelGrid.appendChild(modelCard);
        });
        
    } catch (error) {
        console.error('Error loading models for dialog:', error);
        modelGrid.innerHTML = '<div style="text-align: center; padding: 20px; color: #f44;">Error loading models. Please try again.</div>';
    }
}

function selectModelFromDialog(modelValue, modelName) {
    console.log('Selected model from dialog:', modelName, modelValue);
    
    // Add model using the multi-model manager
    if (live2dMultiModelManager) {
        live2dMultiModelManager.addModel(modelName).then(() => {
            console.log('Model added successfully:', modelName);
            // The people panel will be refreshed automatically by the multi-model manager
        }).catch(error => {
            console.error('Failed to add model:', error);
            addSystemMessage(`Failed to add model: ${error.message}`, 'error');
        });
    } else {
        console.error('Multi-model manager not available');
        addSystemMessage('Live2D system not ready', 'error');
    }
    
    // Close dialog
    closeAddModelDialog();
}

// Export functions for global access
window.populatePeopleModels = populatePeopleModels;
window.selectModel = selectModel;
window.removeModel = removeModel;
window.showAddModelDialog = showAddModelDialog;
window.closeAddModelDialog = closeAddModelDialog;
window.loadAvailableModelsForDialog = loadAvailableModelsForDialog;
window.selectModelFromDialog = selectModelFromDialog;
