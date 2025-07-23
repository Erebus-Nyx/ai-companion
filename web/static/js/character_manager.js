/**
 * Character Management Module - Handles character operations and model import
 * Provides functionality for creating, editing, and importing character data
 */

class CharacterManager {
    constructor() {
        this.currentCharacter = null;
        this.characters = new Map();
        this.init();
    }

    init() {
        console.log('👥 Character Manager initialized');
        this.loadAvailableCharacters();
    }

    // Character Selection and Loading
    async loadAvailableCharacters() {
        try {
            const response = await fetch('/api/live2d/characters');
            if (response.ok) {
                const characters = await response.json();
                this.characters.clear();
                characters.forEach(char => {
                    this.characters.set(char.model_id, char);
                });
                console.log(`👥 Loaded ${characters.length} characters`);
                return characters;
            } else {
                console.error('Failed to load characters:', response.statusText);
                return [];
            }
        } catch (error) {
            console.error('Error loading characters:', error);
            return [];
        }
    }

    async onCharacterChange() {
        const select = document.getElementById('characterSelect');
        if (!select || !select.value) {
            this.clearCharacterForm();
            return;
        }

        try {
            const response = await fetch(`/api/live2d/models/${select.value}/character`);
            if (response.ok) {
                const character = await response.json();
                this.currentCharacter = character;
                this.populateCharacterForm(character);
                console.log('👤 Character loaded:', character.name);
            } else {
                console.error('Failed to load character:', response.statusText);
            }
        } catch (error) {
            console.error('Error loading character:', error);
        }
    }

    populateCharacterForm(character) {
        // Basic Information
        this.setFieldValue('characterName', character.name);
        this.setFieldValue('characterDescription', character.description);
        this.setFieldValue('characterAge', this.extractAge(character));
        this.setFieldValue('characterPersonality', this.formatTraits(character.base_traits));
        
        // Appearance
        this.setFieldValue('characterAppearance', character.appearance_notes);
        this.setFieldValue('characterOutfit', this.extractOutfit(character));
        
        // Background
        this.setFieldValue('characterBackground', character.background_story);
        this.setFieldValue('characterGoals', this.extractGoals(character));
    }

    clearCharacterForm() {
        const fields = [
            'characterName', 'characterDescription', 'characterAge', 'characterPersonality',
            'characterAppearance', 'characterOutfit', 'characterBackground', 'characterGoals'
        ];
        
        fields.forEach(field => this.setFieldValue(field, ''));
        this.currentCharacter = null;
    }

    setFieldValue(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = value || '';
        }
    }

    // Character CRUD Operations
    async createNewCharacter() {
        const name = prompt('Enter character name:');
        if (!name) return;

        const characterData = {
            name: name,
            description: 'New character',
            base_traits: { friendly: 0.7, helpful: 0.8 },
            current_traits: { friendly: 0.7, helpful: 0.8 },
            background_story: '',
            favorite_things: '',
            personality_notes: '',
            appearance_notes: ''
        };

        try {
            const response = await fetch(`/api/live2d/models/${name.toLowerCase()}/character`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(characterData)
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Character created:', result);
                await this.loadAvailableCharacters();
                this.selectCharacter(name.toLowerCase());
            } else {
                console.error('Failed to create character:', response.statusText);
                alert('Failed to create character. Please try again.');
            }
        } catch (error) {
            console.error('Error creating character:', error);
            alert('Error creating character. Please check the console for details.');
        }
    }

    async duplicateCharacter() {
        if (!this.currentCharacter) {
            alert('Please select a character to duplicate.');
            return;
        }

        const name = prompt('Enter name for duplicated character:');
        if (!name) return;

        const characterData = {
            ...this.currentCharacter,
            name: name
        };

        try {
            const response = await fetch(`/api/live2d/models/${name.toLowerCase()}/character`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(characterData)
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Character duplicated:', result);
                await this.loadAvailableCharacters();
                this.selectCharacter(name.toLowerCase());
            } else {
                console.error('Failed to duplicate character:', response.statusText);
                alert('Failed to duplicate character. Please try again.');
            }
        } catch (error) {
            console.error('Error duplicating character:', error);
            alert('Error duplicating character. Please check the console for details.');
        }
    }

    async deleteCharacter() {
        if (!this.currentCharacter) {
            alert('Please select a character to delete.');
            return;
        }

        const confirmDelete = confirm(`Are you sure you want to delete ${this.currentCharacter.name}? This action cannot be undone.`);
        if (!confirmDelete) return;

        try {
            const modelId = document.getElementById('characterSelect').value;
            const response = await fetch(`/api/live2d/models/${modelId}/character`, {
                method: 'DELETE'
            });

            if (response.ok) {
                console.log('✅ Character deleted');
                await this.loadAvailableCharacters();
                this.clearCharacterForm();
            } else {
                console.error('Failed to delete character:', response.statusText);
                alert('Failed to delete character. Please try again.');
            }
        } catch (error) {
            console.error('Error deleting character:', error);
            alert('Error deleting character. Please check the console for details.');
        }
    }

    async saveCharacterProfile() {
        if (!this.currentCharacter) {
            alert('Please select a character to save.');
            return;
        }

        const characterData = this.collectFormData();
        const modelId = document.getElementById('characterSelect').value;

        try {
            const response = await fetch(`/api/live2d/models/${modelId}/character`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(characterData)
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Character saved:', result);
                this.currentCharacter = { ...this.currentCharacter, ...characterData };
                alert('Character profile saved successfully!');
            } else {
                console.error('Failed to save character:', response.statusText);
                alert('Failed to save character. Please try again.');
            }
        } catch (error) {
            console.error('Error saving character:', error);
            alert('Error saving character. Please check the console for details.');
        }
    }

    collectFormData() {
        return {
            name: this.getFieldValue('characterName'),
            description: this.getFieldValue('characterDescription'),
            background_story: this.getFieldValue('characterBackground'),
            personality_notes: this.getFieldValue('characterPersonality'),
            appearance_notes: this.getFieldValue('characterAppearance'),
            favorite_things: this.extractFavoriteThings(),
            base_traits: this.parseTraits(this.getFieldValue('characterPersonality')),
            current_traits: this.parseTraits(this.getFieldValue('characterPersonality'))
        };
    }

    getFieldValue(fieldId) {
        const field = document.getElementById(fieldId);
        return field ? field.value : '';
    }

    // Import/Export Functions
    async exportCharacter() {
        if (!this.currentCharacter) {
            alert('Please select a character to export.');
            return;
        }

        const characterData = {
            ...this.currentCharacter,
            ...this.collectFormData(),
            exported_at: new Date().toISOString(),
            version: '1.0'
        };

        const blob = new Blob([JSON.stringify(characterData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `${characterData.name.toLowerCase()}_character.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log('📤 Character exported:', characterData.name);
    }

    async importCharacter() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = async (event) => {
            const file = event.target.files[0];
            if (!file) return;

            try {
                const text = await file.text();
                const characterData = JSON.parse(text);
                
                // Validate character data
                if (!characterData.name) {
                    alert('Invalid character file: missing name.');
                    return;
                }

                // Import the character
                const response = await fetch(`/api/live2d/models/${characterData.name.toLowerCase()}/character`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(characterData)
                });

                if (response.ok) {
                    console.log('📥 Character imported:', characterData.name);
                    await this.loadAvailableCharacters();
                    this.selectCharacter(characterData.name.toLowerCase());
                    alert('Character imported successfully!');
                } else {
                    console.error('Failed to import character:', response.statusText);
                    alert('Failed to import character. Please try again.');
                }
            } catch (error) {
                console.error('Error importing character:', error);
                alert('Error importing character. Please ensure the file is valid JSON.');
            }
        };

        input.click();
    }

    // Model Import Dialog Functions
    showAddModelDialog() {
        const dialog = document.getElementById('modelImportDialog') || this.createModelImportDialog();
        if (dialog) {
            dialog.style.display = 'block';
            dialog.classList.add('open');
            this.loadAvailableModelsForDialog();
            console.log('📁 Model import dialog opened');
        }
    }

    closeAddModelDialog() {
        const dialog = document.getElementById('modelImportDialog');
        if (dialog) {
            dialog.classList.remove('open');
            setTimeout(() => {
                dialog.style.display = 'none';
            }, 300);
            console.log('📁 Model import dialog closed');
        }
    }

    createModelImportDialog() {
        // Create modal dialog for model import
        const dialog = document.createElement('div');
        dialog.id = 'modelImportDialog';
        dialog.className = 'modal-dialog';
        dialog.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Import Live2D Model</h3>
                    <button class="close-btn" onclick="window.characterManager.closeAddModelDialog()">×</button>
                </div>
                <div class="modal-body">
                    <div class="import-section">
                        <h4>Upload Model Files</h4>
                        <div class="form-group">
                            <label for="modelFileInput">Select Model Files (ZIP or individual files):</label>
                            <input type="file" id="modelFileInput" multiple accept=".zip,.json,.moc3,.model3.json">
                        </div>
                        <div class="form-group">
                            <label for="modelNameInput">Model Name:</label>
                            <input type="text" id="modelNameInput" placeholder="Enter model name">
                        </div>
                        <button class="btn btn-primary" onclick="window.characterManager.handleModelUpload()">Upload Model</button>
                    </div>
                    
                    <div class="import-section">
                        <h4>Or Select Existing Model</h4>
                        <div class="form-group">
                            <label for="existingModelSelect">Available Models:</label>
                            <select id="existingModelSelect">
                                <option value="">Loading models...</option>
                            </select>
                        </div>
                        <button class="btn btn-secondary" onclick="window.characterManager.addExistingModel()">Add Selected Model</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
        return dialog;
    }

    async loadAvailableModelsForDialog() {
        try {
            const response = await fetch('/api/live2d/models');
            if (response.ok) {
                const models = await response.json();
                const select = document.getElementById('existingModelSelect');
                if (select) {
                    select.innerHTML = '<option value="">Select a model...</option>';
                    models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model.model_name;
                        option.textContent = `${model.model_name} (${model.model_type})`;
                        select.appendChild(option);
                    });
                }
            }
        } catch (error) {
            console.error('Error loading models for dialog:', error);
        }
    }

    async handleModelUpload() {
        const fileInput = document.getElementById('modelFileInput');
        const nameInput = document.getElementById('modelNameInput');
        
        if (!fileInput.files.length) {
            alert('Please select files to upload.');
            return;
        }

        if (!nameInput.value.trim()) {
            alert('Please enter a model name.');
            return;
        }

        const formData = new FormData();
        Array.from(fileInput.files).forEach(file => {
            formData.append('files', file);
        });
        formData.append('model_name', nameInput.value.trim());

        try {
            const response = await fetch('/api/live2d/models/import', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Model uploaded:', result);
                alert('Model uploaded successfully!');
                this.closeAddModelDialog();
                await this.loadAvailableCharacters();
            } else {
                const error = await response.json();
                console.error('Failed to upload model:', error);
                alert(`Failed to upload model: ${error.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error uploading model:', error);
            alert('Error uploading model. Please check the console for details.');
        }
    }

    async addExistingModel() {
        const select = document.getElementById('existingModelSelect');
        if (!select.value) {
            alert('Please select a model.');
            return;
        }

        try {
            // Add the existing model to the character system
            const response = await fetch(`/api/live2d/models/${select.value}/character`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: select.value.charAt(0).toUpperCase() + select.value.slice(1),
                    description: `Character for ${select.value} model`,
                    base_traits: { friendly: 0.7, helpful: 0.8 },
                    current_traits: { friendly: 0.7, helpful: 0.8 }
                })
            });

            if (response.ok) {
                console.log('✅ Existing model added to character system');
                alert('Model added successfully!');
                this.closeAddModelDialog();
                await this.loadAvailableCharacters();
            } else {
                console.error('Failed to add existing model');
                alert('Failed to add model. It may already be in the character system.');
            }
        } catch (error) {
            console.error('Error adding existing model:', error);
            alert('Error adding model. Please try again.');
        }
    }

    // Utility Functions
    selectCharacter(modelId) {
        const select = document.getElementById('characterSelect');
        if (select) {
            select.value = modelId;
            this.onCharacterChange();
        }
    }

    extractAge(character) {
        // Extract age from appearance notes or other fields
        const ageMatch = character.appearance_notes?.match(/age[:\s]+(\d+)/i);
        return ageMatch ? ageMatch[1] : '';
    }

    formatTraits(traits) {
        if (typeof traits === 'object') {
            return Object.entries(traits).map(([key, value]) => `${key}: ${value}`).join(', ');
        }
        return traits || '';
    }

    parseTraits(traitString) {
        if (!traitString) return {};
        
        const traits = {};
        traitString.split(',').forEach(trait => {
            const [key, value] = trait.split(':').map(s => s.trim());
            if (key && value) {
                traits[key] = parseFloat(value) || 0.5;
            }
        });
        return traits;
    }

    extractOutfit(character) {
        // Extract outfit information from appearance notes
        const outfitMatch = character.appearance_notes?.match(/outfit[:\s]+([^;]+)/i);
        return outfitMatch ? outfitMatch[1] : '';
    }

    extractGoals(character) {
        // Extract goals from background story or other fields
        return character.favorite_things || '';
    }

    extractFavoriteThings() {
        const goals = this.getFieldValue('characterGoals');
        const outfit = this.getFieldValue('characterOutfit');
        return [goals, outfit].filter(Boolean).join(', ');
    }
}

// Create global instance
window.characterManager = new CharacterManager();

// Export global functions for onclick handlers
window.onCharacterChange = () => window.characterManager.onCharacterChange();
window.createNewCharacter = () => window.characterManager.createNewCharacter();
window.duplicateCharacter = () => window.characterManager.duplicateCharacter();
window.deleteCharacter = () => window.characterManager.deleteCharacter();
window.saveCharacterProfile = () => window.characterManager.saveCharacterProfile();
window.exportCharacter = () => window.characterManager.exportCharacter();
window.importCharacter = () => window.characterManager.importCharacter();
window.showAddModelDialog = () => window.characterManager.showAddModelDialog();
window.closeAddModelDialog = () => window.characterManager.closeAddModelDialog();

console.log('✅ Character Manager module loaded');
