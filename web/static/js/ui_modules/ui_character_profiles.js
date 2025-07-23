// character-sheet.js
// Character Sheet Management System

class CharacterSheetManager {
    constructor() {
        this.charactersData = null;
        this.currentCharacter = null;
        this.isDirty = false;
        this.isVisible = false;
        this.initializePanel();
    }

    async initializePanel() {
        try {
            // Load characters data from the server
            await this.loadCharactersData();
            
            // Populate the character selection dropdown
            this.populateCharacterSelect();
            
            console.log('✅ Character Sheet Manager initialized');
        } catch (error) {
            console.error('Failed to initialize Character Sheet Manager:', error);
        }
    }

    async loadCharactersData() {
        try {
            // First try to load from API (database)
            const response = await fetch('/api/characters');
            if (response.ok) {
                this.charactersData = await response.json();
                console.log('📦 Loaded characters from database');
            } else {
                // Fallback to characters.json
                const jsonResponse = await fetch('/static/data/characters.json');
                if (jsonResponse.ok) {
                    this.charactersData = await jsonResponse.json();
                    console.log('📦 Loaded characters from characters.json');
                } else {
                    throw new Error('Could not load characters data');
                }
            }
        } catch (error) {
            console.error('Error loading characters data:', error);
            // Initialize with empty data
            this.charactersData = { characters: {} };
        }
    }

    populateCharacterSelect() {
        const select = document.getElementById('characterSelect');
        if (!select) return;

        // Clear existing options except the first one
        select.innerHTML = '<option value="">Choose a character...</option>';

        if (this.charactersData && this.charactersData.characters) {
            Object.keys(this.charactersData.characters).forEach(characterId => {
                const character = this.charactersData.characters[characterId];
                const option = document.createElement('option');
                option.value = characterId;
                option.textContent = character.basic_info?.display_name || characterId;
                select.appendChild(option);
            });
        }
    }

    onCharacterChange() {
        const select = document.getElementById('characterSelect');
        const characterId = select.value;
        
        if (this.isDirty) {
            if (confirm('You have unsaved changes. Do you want to save them before switching characters?')) {
                this.saveCharacterSheet();
            }
        }

        if (characterId) {
            this.loadCharacter(characterId);
        } else {
            this.hideCharacterForm();
        }
    }

    loadCharacter(characterId) {
        if (!this.charactersData || !this.charactersData.characters[characterId]) {
            console.error('Character not found:', characterId);
            return;
        }

        this.currentCharacter = characterId;
        const character = this.charactersData.characters[characterId];
        
        // Show the form
        this.showCharacterForm();
        
        // Populate form fields
        this.populateForm(character);
        
        // Reset dirty flag
        this.isDirty = false;
        
        console.log('📋 Loaded character:', character.basic_info?.display_name || characterId);
    }

    populateForm(character) {
        // Basic Information
        this.setFieldValue('displayName', character.basic_info?.display_name || '');
        this.setFieldValue('ageAppearance', character.basic_info?.age_appearance || 'young_adult');
        this.setFieldValue('archetype', character.basic_info?.archetype || '');

        // Character Icon
        if (typeof loadCharacterIcon === 'function') {
            loadCharacterIcon(character.basic_info?.icon || null);
        }

        // Personality
        this.setFieldValue('contentRating', character.personality?.content_rating || 'SFW');
        this.setFieldValue('interactionStyle', character.personality?.interaction_style || 'playful');
        this.setFieldValue('formalityLevel', character.personality?.formality_level || 'casual');
        
        // Set trait categories checkboxes
        const traitCategories = character.personality?.trait_categories || [];
        document.querySelectorAll('input[name="traitCategories"]').forEach(checkbox => {
            checkbox.checked = traitCategories.includes(checkbox.value);
        });

        // Core traits (array to comma-separated string)
        const coreTraits = character.personality?.core_traits || [];
        this.setFieldValue('coreTraits', coreTraits.join(', '));

        // Appearance
        this.setFieldValue('skinTone', character.appearance?.physical?.skin_tone || 'light');
        this.setFieldValue('eyeColor', character.appearance?.physical?.eye_color || '');
        this.setFieldValue('hairColor', character.appearance?.hair?.color || '');
        this.setFieldValue('hairLength', character.appearance?.hair?.length || 'medium');
        
        // Hair style (array to comma-separated string)
        const hairStyle = character.appearance?.hair?.style || [];
        this.setFieldValue('hairStyle', hairStyle.join(', '));
        
        // Default outfit (array to comma-separated string)
        const defaultOutfit = character.appearance?.clothing?.default_outfit || [];
        this.setFieldValue('defaultOutfit', defaultOutfit.join(', '));

        // Behavioral Patterns
        this.setFieldValue('speechFormality', character.behavioral_patterns?.speech_style?.formality || 'casual');
        
        const commonPhrases = character.behavioral_patterns?.speech_style?.common_phrases || [];
        this.setFieldValue('commonPhrases', commonPhrases.join(', '));
        
        const verbalTics = character.behavioral_patterns?.speech_style?.verbal_tics || [];
        this.setFieldValue('verbalTics', verbalTics.join(', '));
        
        const interests = character.behavioral_patterns?.interests || [];
        this.setFieldValue('interests', interests.join(', '));
        
        const dislikes = character.behavioral_patterns?.dislikes || [];
        this.setFieldValue('dislikes', dislikes.join(', '));

        // Backstory
        this.setFieldValue('origin', character.backstory?.origin || '');
        this.setFieldValue('motivation', character.backstory?.motivation || '');
    }

    setFieldValue(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = value;
        }
    }

    showCharacterForm() {
        const form = document.getElementById('characterForm');
        if (form) {
            form.style.display = 'block';
        }
    }

    hideCharacterForm() {
        const form = document.getElementById('characterForm');
        if (form) {
            form.style.display = 'none';
        }
        this.currentCharacter = null;
        this.isDirty = false;
    }

    buildCharacterData() {
        if (!this.currentCharacter) return null;

        // Get trait categories from checkboxes
        const traitCategories = [];
        document.querySelectorAll('input[name="traitCategories"]:checked').forEach(checkbox => {
            traitCategories.push(checkbox.value);
        });

        // Helper function to split comma-separated values
        const splitCommaSeparated = (value) => {
            return value ? value.split(',').map(item => item.trim()).filter(item => item.length > 0) : [];
        };

        return {
            basic_info: {
                display_name: this.getFieldValue('displayName'),
                internal_name: this.currentCharacter,
                age_appearance: this.getFieldValue('ageAppearance'),
                archetype: this.getFieldValue('archetype'),
                icon: typeof getCharacterIconData === 'function' ? getCharacterIconData() : null
            },
            personality: {
                content_rating: this.getFieldValue('contentRating'),
                trait_categories: traitCategories,
                core_traits: splitCommaSeparated(this.getFieldValue('coreTraits')),
                interaction_style: this.getFieldValue('interactionStyle'),
                formality_level: this.getFieldValue('formalityLevel')
            },
            appearance: {
                physical: {
                    skin_tone: this.getFieldValue('skinTone'),
                    eye_color: this.getFieldValue('eyeColor')
                },
                hair: {
                    color: this.getFieldValue('hairColor'),
                    length: this.getFieldValue('hairLength'),
                    style: splitCommaSeparated(this.getFieldValue('hairStyle'))
                },
                clothing: {
                    default_outfit: splitCommaSeparated(this.getFieldValue('defaultOutfit'))
                }
            },
            behavioral_patterns: {
                speech_style: {
                    formality: this.getFieldValue('speechFormality'),
                    common_phrases: splitCommaSeparated(this.getFieldValue('commonPhrases')),
                    verbal_tics: splitCommaSeparated(this.getFieldValue('verbalTics'))
                },
                interests: splitCommaSeparated(this.getFieldValue('interests')),
                dislikes: splitCommaSeparated(this.getFieldValue('dislikes'))
            },
            backstory: {
                origin: this.getFieldValue('origin'),
                motivation: this.getFieldValue('motivation')
            },
            technical_info: {
                model_path: this.currentCharacter,
                last_updated: new Date().toISOString()
            }
        };
    }

    getFieldValue(fieldId) {
        const field = document.getElementById(fieldId);
        return field ? field.value : '';
    }

    async saveCharacterSheet() {
        if (!this.currentCharacter) {
            alert('No character selected');
            return;
        }

        try {
            const characterData = this.buildCharacterData();
            
            // Send to backend API
            const response = await fetch(`/api/characters/${this.currentCharacter}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(characterData)
            });

            if (response.ok) {
                // Update local data
                if (!this.charactersData.characters) {
                    this.charactersData.characters = {};
                }
                this.charactersData.characters[this.currentCharacter] = characterData;
                
                this.isDirty = false;
                console.log('✅ Character saved successfully');
                alert('Character saved successfully!');
                
                // Refresh people panel to show updated icon
                if (typeof debouncedPopulatePeopleModels === 'function') {
                    debouncedPopulatePeopleModels(150);
                } else if (typeof populatePeopleModels === 'function') {
                    setTimeout(() => populatePeopleModels(), 100);
                }
            } else {
                throw new Error(`Server error: ${response.status}`);
            }
        } catch (error) {
            console.error('Error saving character:', error);
            alert('Failed to save character: ' + error.message);
        }
    }

    resetCharacterForm() {
        if (this.currentCharacter) {
            const character = this.charactersData.characters[this.currentCharacter];
            this.populateForm(character);
            this.isDirty = false;
        }
    }

    async deleteCharacter() {
        if (!this.currentCharacter) {
            alert('No character selected');
            return;
        }

        const characterName = this.charactersData.characters[this.currentCharacter]?.basic_info?.display_name || this.currentCharacter;
        
        if (!confirm(`Are you sure you want to delete "${characterName}"? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/characters/${this.currentCharacter}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                // Remove from local data
                delete this.charactersData.characters[this.currentCharacter];
                
                // Update UI
                this.populateCharacterSelect();
                this.hideCharacterForm();
                
                console.log('✅ Character deleted successfully');
                alert('Character deleted successfully!');
            } else {
                throw new Error(`Server error: ${response.status}`);
            }
        } catch (error) {
            console.error('Error deleting character:', error);
            alert('Failed to delete character: ' + error.message);
        }
    }

    createNewCharacter() {
        // Create a new character with default values
        const newCharacterId = 'character_' + Date.now();
        const newCharacter = {
            basic_info: {
                display_name: 'New Character',
                character_id: newCharacterId,
                description: '',
                personality: '',
                scenario: ''
            },
            avatar_config: {
                model_path: '',
                scale: 1.0,
                position: { x: 0, y: 0 }
            },
            dialogue_config: {
                voice_style: 'neutral',
                speaking_style: 'casual',
                response_length: 'medium'
            }
        };

        // Add to local data
        this.charactersData.characters[newCharacterId] = newCharacter;
        
        // Update UI
        this.populateCharacterSelect();
        
        // Select the new character
        const characterSelect = document.getElementById('characterSelect');
        if (characterSelect) {
            characterSelect.value = newCharacterId;
            this.onCharacterChange();
        }

        console.log('✅ New character created:', newCharacterId);
    }

    duplicateCharacter() {
        if (!this.currentCharacter) {
            alert('No character selected to duplicate');
            return;
        }

        const sourceCharacter = this.charactersData.characters[this.currentCharacter];
        if (!sourceCharacter) {
            alert('Selected character not found');
            return;
        }

        // Create a deep copy of the character
        const duplicatedCharacter = JSON.parse(JSON.stringify(sourceCharacter));
        
        // Generate new ID and update name
        const newCharacterId = 'character_' + Date.now();
        const originalName = duplicatedCharacter.basic_info?.display_name || 'Unnamed';
        
        duplicatedCharacter.basic_info.character_id = newCharacterId;
        duplicatedCharacter.basic_info.display_name = `${originalName} (Copy)`;

        // Add to local data
        this.charactersData.characters[newCharacterId] = duplicatedCharacter;
        
        // Update UI
        this.populateCharacterSelect();
        
        // Select the duplicated character
        const characterSelect = document.getElementById('characterSelect');
        if (characterSelect) {
            characterSelect.value = newCharacterId;
            this.onCharacterChange();
        }

        console.log('✅ Character duplicated:', newCharacterId);
    }

    exportCharacter() {
        if (!this.currentCharacter) {
            alert('No character selected');
            return;
        }

        const characterData = this.buildCharacterData();
        const dataStr = JSON.stringify(characterData, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `${this.currentCharacter}_character.json`;
        link.click();
        
        console.log('📤 Character exported');
    }

    markDirty() {
        this.isDirty = true;
    }

    // Panel visibility methods
    show() {
        const panel = document.getElementById('characterSheetPanel');
        if (panel) {
            panel.classList.add('open');
            this.isVisible = true;
        }
    }

    hide() {
        const panel = document.getElementById('characterSheetPanel');
        if (panel) {
            panel.classList.remove('open');
            this.isVisible = false;
        }
    }

    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
}

// Global character sheet manager instance
let characterSheetManager = null;

// Panel control functions (called by HTML onclick handlers)
function openCharacterSheet() {
    if (!characterSheetManager) {
        characterSheetManager = new CharacterSheetManager();
    }
    characterSheetManager.show();
}

function closeCharacterSheet() {
    if (characterSheetManager) {
        characterSheetManager.hide();
    }
}

function toggleCharacterSheetSnap() {
    const panel = document.getElementById('characterSheetPanel');
    if (panel) {
        // Simple snap toggle - cycle between left and right
        if (panel.classList.contains('snapped-left')) {
            panel.classList.remove('snapped-left');
            panel.classList.add('snapped-right');
        } else {
            panel.classList.remove('snapped-right');
            panel.classList.add('snapped-left');
        }
    }
}

// Form interaction handlers
function onCharacterChange() {
    if (characterSheetManager) {
        characterSheetManager.onCharacterChange();
    }
}

function saveCharacterSheet() {
    if (characterSheetManager) {
        characterSheetManager.saveCharacterSheet();
    }
}

function resetCharacterForm() {
    if (characterSheetManager) {
        characterSheetManager.resetCharacterForm();
    }
}

function deleteCharacter() {
    if (characterSheetManager) {
        characterSheetManager.deleteCharacter();
    }
}

function createNewCharacter() {
    if (characterSheetManager) {
        characterSheetManager.createNewCharacter();
    }
}

function duplicateCharacter() {
    if (characterSheetManager) {
        characterSheetManager.duplicateCharacter();
    }
}

function exportCharacter() {
    if (characterSheetManager) {
        characterSheetManager.exportCharacter();
    }
}

// Set up form change detection
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the character sheet manager
    window.characterSheetManager = new CharacterSheetManager();
    
    // Add change listeners to all form fields to track dirty state
    const formSelector = '#characterForm input, #characterForm select, #characterForm textarea';
    
    document.addEventListener('change', (event) => {
        if (event.target.matches(formSelector)) {
            if (characterSheetManager) {
                characterSheetManager.markDirty();
            }
        }
    });

    document.addEventListener('input', (event) => {
        if (event.target.matches(formSelector)) {
            if (characterSheetManager) {
                characterSheetManager.markDirty();
            }
        }
    });
});

// Export for global access
window.CharacterSheetManager = CharacterSheetManager;
window.characterSheetManager = null;
