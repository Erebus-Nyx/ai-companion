/**
 * Live2D Model Import Manager
 * Handles model imports, character association, and runtime model management
 * Integrates with the backend API for complete model lifecycle management
 */

class Live2DModelImportManager {
    constructor() {
        this.apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || '';
        this.uploadProgress = new Map();
        this.importQueue = [];
        this.init();
    }

    init() {
        console.log('📦 Live2D Model Import Manager initialized');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Set up drag and drop for model files
        const dropZone = document.getElementById('modelDropZone');
        if (dropZone) {
            dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
            dropZone.addEventListener('drop', this.handleFileDrop.bind(this));
        }

        // Set up file input change listener
        const fileInput = document.getElementById('modelFileInput');
        if (fileInput) {
            fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }
    }

    // File Upload Handling
    handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        event.dataTransfer.dropEffect = 'copy';
        
        const dropZone = event.currentTarget;
        dropZone.classList.add('drag-over');
    }

    handleFileDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        
        const dropZone = event.currentTarget;
        dropZone.classList.remove('drag-over');
        
        const files = Array.from(event.dataTransfer.files);
        this.processFiles(files);
    }

    handleFileSelect(event) {
        const files = Array.from(event.target.files);
        this.processFiles(files);
    }

    processFiles(files) {
        console.log('📁 Processing files:', files.map(f => f.name));
        
        // Filter for zip files only - Live2D models require complete directory structure
        const zipFiles = files.filter(file => {
            const ext = file.name.toLowerCase().split('.').pop();
            return ext === 'zip';
        });

        if (zipFiles.length === 0) {
            this.showError('Please upload Live2D models as .zip archives to preserve the complete directory structure with motions, textures, and other assets.');
            return;
        }

        // Process each zip file
        zipFiles.forEach(file => {
            this.uploadModelFile(file);
        });
    }

    async uploadModelFile(file) {
        const uploadId = this.generateUploadId();
        this.uploadProgress.set(uploadId, { file: file.name, progress: 0, status: 'uploading' });
        
        try {
            // Verify it's a ZIP file
            if (!file.name.toLowerCase().endsWith('.zip')) {
                throw new Error('Only ZIP archives are supported to preserve Live2D model directory structure');
            }
            
            const formData = new FormData();
            formData.append('model_files', file);  // Backend expects 'model_files'
            
            // Extract model name from file name (without extension)
            const modelName = file.name.replace(/\.zip$/i, '');
            formData.append('model_name', modelName);
            formData.append('upload_id', uploadId);

            const response = await fetch(`${this.apiBaseUrl}/api/live2d/models/import`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.uploadProgress.set(uploadId, { 
                    file: file.name, 
                    progress: 100, 
                    status: 'success',
                    modelName: result.model_name
                });
                
                console.log('✅ Model uploaded successfully:', result);
                this.showSuccess(`Model "${result.model_name}" imported successfully with complete directory structure`);
                
                // Show character association dialog
                this.showCharacterAssociationDialog(result.model_name);
                
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Upload failed');
            }
            
        } catch (error) {
            console.error('❌ Model upload failed:', error);
            this.uploadProgress.set(uploadId, { 
                file: file.name, 
                progress: 0, 
                status: 'error',
                error: error.message
            });
            this.showError(`Failed to upload ${file.name}: ${error.message}`);
        }
        
        this.updateUploadUI();
    }

    // Character Association
    showCharacterAssociationDialog(modelName) {
        const dialog = document.getElementById('characterAssociationDialog');
        if (!dialog) {
            this.createCharacterAssociationDialog();
        }
        
        // Populate model name
        const modelNameField = document.getElementById('associationModelName');
        if (modelNameField) {
            modelNameField.value = modelName;
        }
        
        // Load existing character data options
        this.loadCharacterOptions();
        
        // Show dialog
        const associationDialog = document.getElementById('characterAssociationDialog');
        if (associationDialog) {
            associationDialog.style.display = 'block';
            associationDialog.classList.add('open');
        }
    }

    createCharacterAssociationDialog() {
        const dialogHTML = `
            <div id="characterAssociationDialog" class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Associate Character Data</h3>
                        <button class="close-btn" onclick="closeCharacterAssociationDialog()">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label for="associationModelName">Model Name:</label>
                            <input type="text" id="associationModelName" readonly>
                        </div>
                        
                        <div class="form-group">
                            <label for="characterDataSource">Character Data Source:</label>
                            <select id="characterDataSource" onchange="onCharacterSourceChange()">
                                <option value="">Select source...</option>
                                <option value="existing">Use Existing Character</option>
                                <option value="new">Create New Character</option>
                                <option value="import">Import Character Data</option>
                            </select>
                        </div>
                        
                        <div id="existingCharacterSection" class="form-section" style="display: none;">
                            <div class="form-group">
                                <label for="existingCharacterSelect">Select Character:</label>
                                <select id="existingCharacterSelect">
                                    <option value="">Loading characters...</option>
                                </select>
                            </div>
                        </div>
                        
                        <div id="newCharacterSection" class="form-section" style="display: none;">
                            <div class="form-group">
                                <label for="newCharacterName">Character Name:</label>
                                <input type="text" id="newCharacterName" placeholder="Enter character name">
                            </div>
                            <div class="form-group">
                                <label for="newCharacterDescription">Description:</label>
                                <textarea id="newCharacterDescription" placeholder="Character description..." rows="3"></textarea>
                            </div>
                            <div class="form-group">
                                <label for="newCharacterPersonality">Personality Traits:</label>
                                <textarea id="newCharacterPersonality" placeholder="Personality traits (comma-separated)..." rows="2"></textarea>
                            </div>
                        </div>
                        
                        <div id="importCharacterSection" class="form-section" style="display: none;">
                            <div class="form-group">
                                <label for="characterDataFile">Character Data File:</label>
                                <input type="file" id="characterDataFile" accept=".json">
                                <small>Upload a JSON file with character data</small>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="closeCharacterAssociationDialog()">Cancel</button>
                        <button class="btn btn-primary" onclick="saveCharacterAssociation()">Save Association</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', dialogHTML);
    }

    async loadCharacterOptions() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/live2d/characters`);
            if (response.ok) {
                const characters = await response.json();
                this.populateCharacterSelect(characters);
            } else {
                console.error('Failed to load characters:', response.statusText);
            }
        } catch (error) {
            console.error('Error loading characters:', error);
        }
    }

    populateCharacterSelect(characters) {
        const select = document.getElementById('existingCharacterSelect');
        if (select) {
            select.innerHTML = '<option value="">Select a character...</option>';
            characters.forEach(character => {
                const option = document.createElement('option');
                option.value = character.model_id;
                option.textContent = character.name;
                select.appendChild(option);
            });
        }
    }

    // Character Association Saving
    async saveCharacterAssociation() {
        const modelName = document.getElementById('associationModelName')?.value;
        const source = document.getElementById('characterDataSource')?.value;
        
        if (!modelName || !source) {
            this.showError('Please fill in all required fields');
            return;
        }
        
        try {
            let characterData = null;
            
            switch (source) {
                case 'existing':
                    const existingId = document.getElementById('existingCharacterSelect')?.value;
                    if (!existingId) {
                        this.showError('Please select an existing character');
                        return;
                    }
                    // Link to existing character
                    characterData = { link_to_existing: existingId };
                    break;
                    
                case 'new':
                    const name = document.getElementById('newCharacterName')?.value;
                    const description = document.getElementById('newCharacterDescription')?.value;
                    const personality = document.getElementById('newCharacterPersonality')?.value;
                    
                    if (!name) {
                        this.showError('Please enter a character name');
                        return;
                    }
                    
                    characterData = {
                        basic_info: {
                            display_name: name
                        },
                        personality: {
                            core_traits: personality.split(',').map(t => t.trim()).filter(t => t),
                            archetype: description || `AI companion ${name}`
                        },
                        backstory: {
                            origin: description || `An AI assistant companion named ${name}`
                        }
                    };
                    break;
                    
                case 'import':
                    const fileInput = document.getElementById('characterDataFile');
                    if (!fileInput?.files?.length) {
                        this.showError('Please select a character data file');
                        return;
                    }
                    
                    const file = fileInput.files[0];
                    const fileContent = await this.readFileAsText(file);
                    characterData = JSON.parse(fileContent);
                    break;
            }
            
            // Save character association using the proper API endpoint
            const response = await fetch(`${this.apiBaseUrl}/api/live2d/models/${modelName}/character`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(characterData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showSuccess(`Character association saved for ${modelName}`);
                this.closeCharacterAssociationDialog();
                
                // Refresh available models
                this.refreshModelList();
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Failed to save association');
            }
            
        } catch (error) {
            console.error('❌ Failed to save character association:', error);
            this.showError(`Failed to save association: ${error.message}`);
        }
    }

    closeCharacterAssociationDialog() {
        const dialog = document.getElementById('characterAssociationDialog');
        if (dialog) {
            dialog.classList.remove('open');
            setTimeout(() => {
                dialog.style.display = 'none';
            }, 300);
        }
    }

    // Model Management
    async refreshModelList() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/live2d/models`);
            if (response.ok) {
                const models = await response.json();
                this.updateModelListUI(models);
                
                // Trigger model refresh in other managers
                if (window.live2dModelManager) {
                    window.live2dModelManager.refreshModels();
                }
            }
        } catch (error) {
            console.error('Error refreshing model list:', error);
        }
    }

    updateModelListUI(models) {
        // Update the model selection dialog if it exists
        const modelSelect = document.getElementById('modelDialogSelect');
        if (modelSelect && window.uiPanelManager) {
            window.uiPanelManager.populateModelDialogSelect(models);
        }
        
        // Update character selection dropdowns
        const characterSelect = document.getElementById('characterSelect');
        if (characterSelect && window.uiPanelManager) {
            window.uiPanelManager.loadCharacterData();
        }
    }

    // Utility Functions
    generateUploadId() {
        return 'upload_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    updateUploadProgress(uploadId, progress) {
        const upload = this.uploadProgress.get(uploadId);
        if (upload) {
            upload.progress = progress;
            this.updateUploadUI();
        }
    }

    updateUploadUI() {
        // Update progress indicators in the UI
        const progressContainer = document.getElementById('uploadProgressContainer');
        if (progressContainer) {
            progressContainer.innerHTML = '';
            
            this.uploadProgress.forEach((upload, id) => {
                const progressItem = document.createElement('div');
                progressItem.className = `upload-item upload-${upload.status}`;
                progressItem.innerHTML = `
                    <div class="upload-filename">${upload.file}</div>
                    <div class="upload-progress">
                        <div class="progress-bar" style="width: ${upload.progress}%"></div>
                    </div>
                    <div class="upload-status">${upload.status}</div>
                `;
                progressContainer.appendChild(progressItem);
            });
        }
    }

    async readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(reader.error);
            reader.readAsText(file);
        });
    }

    showSuccess(message) {
        console.log('✅', message);
        // Could integrate with a notification system
        if (window.showNotification) {
            window.showNotification(message, 'success');
        } else {
            alert(message);
        }
    }

    showError(message) {
        console.error('❌', message);
        // Could integrate with a notification system
        if (window.showNotification) {
            window.showNotification(message, 'error');
        } else {
            alert('Error: ' + message);
        }
    }

    // Bulk Operations
    async scanForModels() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/live2d/models/scan`, {
                method: 'POST'
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showSuccess(`Scan complete. Found ${result.models_found} models, created ${result.personalities_created} personalities.`);
                this.refreshModelList();
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Scan failed');
            }
        } catch (error) {
            console.error('❌ Model scan failed:', error);
            this.showError(`Model scan failed: ${error.message}`);
        }
    }
    
    // Simplified Model Management for Settings Panel
    loadExistingModelsForSettings() {
        const select = document.getElementById('existingModelSelect');
        if (!select) return;
        
        select.innerHTML = '<option value="">Loading models...</option>';
        
        fetch(`${this.apiBaseUrl}/api/live2d/models`)
            .then(response => response.json())
            .then(data => {
                select.innerHTML = '<option value="">Select existing model...</option>';
                if (data.status === 'success' && data.models) {
                    data.models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model.id || model.name;
                        option.textContent = model.name;
                        select.appendChild(option);
                    });
                }
            })
            .catch(error => {
                console.error('Error loading models:', error);
                select.innerHTML = '<option value="">Error loading models</option>';
            });
    }
    
    loadCanvasModelsForSettings() {
        const select = document.getElementById('canvasModelSelect');
        const removeBtn = document.getElementById('removeModelBtn');
        if (!select) return;
        
        select.innerHTML = '<option value="">No models on canvas...</option>';
        if (removeBtn) removeBtn.disabled = true;
        
        // Get currently loaded models on canvas
        if (window.Live2DManager && window.Live2DManager.getLoadedModels) {
            const loadedModels = window.Live2DManager.getLoadedModels();
            if (loadedModels && loadedModels.length > 0) {
                select.innerHTML = '<option value="">Select model to remove...</option>';
                loadedModels.forEach((model, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = model.name || `Model ${index + 1}`;
                    select.appendChild(option);
                });
            }
        }
        
        select.addEventListener('change', function() {
            if (removeBtn) removeBtn.disabled = !this.value;
        });
    }
    
    addExistingModelToCanvas() {
        const select = document.getElementById('existingModelSelect');
        const selectedValue = select.value;
        
        if (!selectedValue) {
            this.showToast('Please select a model to add', 'warning');
            return;
        }
        
        // Use existing model loading functionality
        if (window.Live2DManager && window.Live2DManager.loadModel) {
            window.Live2DManager.loadModel(selectedValue)
                .then(() => {
                    this.showToast('Model added to canvas successfully', 'success');
                    this.loadCanvasModelsForSettings(); // Refresh the canvas models list
                })
                .catch(error => {
                    console.error('Error adding model to canvas:', error);
                    this.showToast('Error adding model to canvas', 'error');
                });
        } else {
            console.error('Live2DManager not available');
            this.showToast('Model manager not available', 'error');
        }
    }
    
    removeModelFromCanvas() {
        const select = document.getElementById('canvasModelSelect');
        const selectedIndex = select.value;
        
        if (!selectedIndex) {
            return;
        }
        
        const modelName = select.options[select.selectedIndex].textContent;
        
        if (confirm(`Are you sure you want to remove "${modelName}" from the canvas?`)) {
            // Use existing model removal functionality
            if (window.Live2DManager && window.Live2DManager.removeModel) {
                window.Live2DManager.removeModel(parseInt(selectedIndex))
                    .then(() => {
                        this.showToast('Model removed from canvas', 'success');
                        this.loadCanvasModelsForSettings(); // Refresh the canvas models list
                    })
                    .catch(error => {
                        console.error('Error removing model from canvas:', error);
                        this.showToast('Error removing model', 'error');
                    });
            } else {
                console.error('Live2DManager not available');
                this.showToast('Model manager not available', 'error');
            }
        }
    }
    
    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#2196f3'};
            color: white;
            border-radius: 6px;
            z-index: 10000;
            font-size: 14px;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        // Fade in
        requestAnimationFrame(() => {
            toast.style.opacity = '1';
        });
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast.parentNode) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }
}

// Global functions for dialog management
window.closeCharacterAssociationDialog = () => {
    if (window.live2dModelImportManager) {
        window.live2dModelImportManager.closeCharacterAssociationDialog();
    }
};

window.saveCharacterAssociation = () => {
    if (window.live2dModelImportManager) {
        window.live2dModelImportManager.saveCharacterAssociation();
    }
};

window.onCharacterSourceChange = () => {
    const source = document.getElementById('characterDataSource')?.value;
    const sections = ['existingCharacterSection', 'newCharacterSection', 'importCharacterSection'];
    
    // Hide all sections
    sections.forEach(sectionId => {
        const section = document.getElementById(sectionId);
        if (section) section.style.display = 'none';
    });
    
    // Show relevant section
    if (source) {
        const targetSection = document.getElementById(`${source}CharacterSection`);
        if (targetSection) targetSection.style.display = 'block';
    }
};

// Global functions for simplified model management
window.loadExistingModelsForSettings = () => {
    if (window.live2dModelImportManager) {
        window.live2dModelImportManager.loadExistingModelsForSettings();
    }
};

window.loadCanvasModelsForSettings = () => {
    if (window.live2dModelImportManager) {
        window.live2dModelImportManager.loadCanvasModelsForSettings();
    }
};

window.addExistingModelToCanvas = () => {
    if (window.live2dModelImportManager) {
        window.live2dModelImportManager.addExistingModelToCanvas();
    }
};

window.removeModelFromCanvas = () => {
    if (window.live2dModelImportManager) {
        window.live2dModelImportManager.removeModelFromCanvas();
    }
};

window.uploadModelZip = (file) => {
    if (window.live2dModelImportManager && file) {
        window.live2dModelImportManager.uploadModelFile(file);
    }
};

// Create global instance
window.live2dModelImportManager = new Live2DModelImportManager();

console.log('✅ Live2D Model Import Manager loaded');
