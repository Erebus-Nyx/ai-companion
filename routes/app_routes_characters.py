# app_routes_characters.py
# Character management API routes

from flask import Blueprint, request, jsonify
import logging
import traceback
import json
import os
from datetime import datetime

# Blueprint definition
characters_routes = Blueprint('characters_routes', __name__)

@characters_routes.route('/api/characters', methods=['GET'])
def api_get_characters():
    """Get all character data"""
    try:
        from app_globals import app_state
        
        # Try to get from database first
        characters_data = get_characters_from_database()
        
        if not characters_data:
            # Fallback to characters.json
            characters_data = load_characters_from_json()
        
        return jsonify(characters_data)
        
    except Exception as e:
        error_msg = f"Characters API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@characters_routes.route('/api/characters/<character_id>', methods=['GET'])
def api_get_character(character_id):
    """Get specific character data"""
    try:
        characters_data = get_characters_from_database()
        
        if not characters_data:
            characters_data = load_characters_from_json()
        
        if 'characters' in characters_data and character_id in characters_data['characters']:
            return jsonify(characters_data['characters'][character_id])
        else:
            return jsonify({'error': f'Character {character_id} not found'}), 404
            
    except Exception as e:
        error_msg = f"Character GET API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@characters_routes.route('/api/characters/<character_id>', methods=['PUT'])
def api_update_character(character_id):
    """Update or create character data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Update character in database
        success = update_character_in_database(character_id, data)
        
        if success:
            logging.info(f"Character {character_id} updated successfully")
            return jsonify({'message': 'Character updated successfully'})
        else:
            return jsonify({'error': 'Failed to update character'}), 500
            
    except Exception as e:
        error_msg = f"Character PUT API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@characters_routes.route('/api/characters/<character_id>', methods=['DELETE'])
def api_delete_character(character_id):
    """Delete character data"""
    try:
        success = delete_character_from_database(character_id)
        
        if success:
            logging.info(f"Character {character_id} deleted successfully")
            return jsonify({'message': 'Character deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete character'}), 500
            
    except Exception as e:
        error_msg = f"Character DELETE API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@characters_routes.route('/api/characters/<character_id>/icon', methods=['POST'])
def api_upload_character_icon(character_id):
    """Upload character icon"""
    try:
        data = request.get_json()
        if not data or 'iconData' not in data:
            return jsonify({'error': 'No icon data provided'}), 400
        
        icon_data = data['iconData']
        
        # Validate icon data structure
        if not isinstance(icon_data, dict) or 'processed' not in icon_data:
            return jsonify({'error': 'Invalid icon data format'}), 400
        
        # Get existing character data
        characters_data = get_characters_from_database()
        if not characters_data or 'characters' not in characters_data or character_id not in characters_data['characters']:
            return jsonify({'error': f'Character {character_id} not found'}), 404
        
        character_data = characters_data['characters'][character_id]
        
        # Update character with icon data
        if 'basic_info' not in character_data:
            character_data['basic_info'] = {}
        
        character_data['basic_info']['icon'] = icon_data
        character_data['basic_info']['last_updated'] = datetime.now().isoformat()
        
        # Save updated character
        success = update_character_in_database(character_id, character_data)
        
        if success:
            logging.info(f"Icon uploaded successfully for character {character_id}")
            return jsonify({'message': 'Icon uploaded successfully'})
        else:
            return jsonify({'error': 'Failed to save icon'}), 500
            
    except Exception as e:
        error_msg = f"Character icon upload API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

def load_characters_from_json():
    """Load characters from the JSON file"""
    try:
        json_path = os.path.join(os.path.dirname(__file__), '..', 'databases', 'characters.json')
        json_path = os.path.abspath(json_path)
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logging.warning(f"Characters JSON file not found: {json_path}")
            return {'characters': {}}
            
    except Exception as e:
        logging.error(f"Error loading characters from JSON: {e}")
        return {'characters': {}}

def load_avatar_framework():
    """Load avatar framework from the JSON file"""
    try:
        json_path = os.path.join(os.path.dirname(__file__), '..', 'databases', 'avatar_framework.json')
        json_path = os.path.abspath(json_path)
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logging.warning(f"Avatar framework JSON file not found: {json_path}")
            return {}
            
    except Exception as e:
        logging.error(f"Error loading avatar framework from JSON: {e}")
        return {}

def save_avatar_framework(framework_data):
    """Save avatar framework to the JSON file"""
    try:
        json_path = os.path.join(os.path.dirname(__file__), '..', 'databases', 'avatar_framework.json')
        json_path = os.path.abspath(json_path)
        
        # Update timestamp
        if 'metadata' in framework_data:
            framework_data['metadata']['last_updated'] = datetime.now().isoformat()
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(framework_data, f, indent=2, ensure_ascii=False)
            
        logging.info("Avatar framework saved successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error saving avatar framework: {e}")
        return False

def update_framework_for_character(character_id, character_data):
    """Update framework with new character information for trigger phrases and content enforcement"""
    try:
        framework = load_avatar_framework()
        
        if not framework:
            logging.warning("Could not load avatar framework for update")
            return False
        
        # Extract character info
        content_rating = character_data.get('personality', {}).get('content_rating', 'SFW')
        core_traits = character_data.get('personality', {}).get('core_traits', [])
        archetype = character_data.get('basic_info', {}).get('archetype', '')
        
        # Update content rating enforcement
        if 'usage_guidelines' in framework and 'content_rating_enforcement' in framework['usage_guidelines']:
            enforcement = framework['usage_guidelines']['content_rating_enforcement']
            
            # Remove character from both lists first
            if character_id in enforcement.get('sfw_only_characters', []):
                enforcement['sfw_only_characters'].remove(character_id)
            if character_id in enforcement.get('nsfw_capable_characters', []):
                enforcement['nsfw_capable_characters'].remove(character_id)
            
            # Add to appropriate list
            if content_rating == 'NSFW':
                if 'nsfw_capable_characters' not in enforcement:
                    enforcement['nsfw_capable_characters'] = []
                enforcement['nsfw_capable_characters'].append(character_id)
            else:
                if 'sfw_only_characters' not in enforcement:
                    enforcement['sfw_only_characters'] = []
                enforcement['sfw_only_characters'].append(character_id)
        
        # Update trigger phrases
        if 'usage_guidelines' in framework and 'character_switching' in framework['usage_guidelines']:
            switching = framework['usage_guidelines']['character_switching']
            
            if 'trigger_phrases' not in switching:
                switching['trigger_phrases'] = {}
            
            # Generate trigger phrases from traits and archetype
            trigger_phrases = [character_id]  # Always include the character name
            
            # Add relevant traits as triggers
            trait_keywords = {
                'cheerful': 'cheerful', 'happy': 'happy', 'optimistic': 'optimistic',
                'mysterious': 'mysterious', 'enigmatic': 'mysterious', 'dark': 'dark',
                'seductive': 'seductive', 'flirtatious': 'flirtatious',
                'gentle': 'gentle', 'calming': 'calming', 'peaceful': 'peaceful',
                'intellectual': 'intellectual', 'analytical': 'books', 'thoughtful': 'thoughtful',
                'studious': 'studying', 'curious': 'learning',
                'playful': 'playful', 'mischievous': 'playful',
                'athletic': 'athletic', 'energetic': 'sports', 'competitive': 'sports',
                'elegant': 'elegant', 'serene': 'calm'
            }
            
            for trait in core_traits:
                if trait.lower() in trait_keywords:
                    keyword = trait_keywords[trait.lower()]
                    if keyword not in trigger_phrases:
                        trigger_phrases.append(keyword)
            
            # Add archetype-based triggers
            archetype_keywords = {
                'fox_spirit': 'fox', 'fox_maiden': 'fox',
                'athlete': 'sports', 'energetic_athlete': 'sports',
                'student': 'studying', 'gentle_student': 'studying',
                'intellectual': 'books', 'calm_intellectual': 'books',
                'seductress': 'seductive', 'mysterious_seductress': 'seductive',
                'sensualist': 'gentle', 'gentle_sensualist': 'gentle'
            }
            
            if archetype and archetype.lower() in archetype_keywords:
                keyword = archetype_keywords[archetype.lower()]
                if keyword not in trigger_phrases:
                    trigger_phrases.append(keyword)
            
            switching['trigger_phrases'][character_id] = trigger_phrases[:3]  # Limit to 3 triggers
        
        # Save updated framework
        return save_avatar_framework(framework)
        
    except Exception as e:
        logging.error(f"Error updating framework for character {character_id}: {e}")
        return False

def get_characters_from_database():
    """Get characters from database"""
    try:
        from databases.live2d_models_separated import get_live2d_connection
        
        with get_live2d_connection() as conn:
            cursor = conn.cursor()
            
            # Check if characters table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='characters'
            """)
            
            if not cursor.fetchone():
                # Table doesn't exist, create it
                create_characters_table()
                # Load initial data from JSON
                initialize_characters_from_json()
            
            # Get all characters
            cursor.execute("""
                SELECT character_id, character_data 
                FROM characters 
                ORDER BY character_id
            """)
            
            rows = cursor.fetchall()
            characters = {}
            
            for row in rows:
                character_id = row['character_id']
                character_data = json.loads(row['character_data'])
                characters[character_id] = character_data
            
            return {'characters': characters}
            
    except Exception as e:
        logging.error(f"Error getting characters from database: {e}")
        return None

def create_characters_table():
    """Create the characters table"""
    try:
        from databases.live2d_models_separated import get_live2d_connection
        
        with get_live2d_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id TEXT NOT NULL UNIQUE,
                    character_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logging.info("Characters table created successfully")
            
    except Exception as e:
        logging.error(f"Error creating characters table: {e}")

def initialize_characters_from_json():
    """Initialize database with characters from JSON"""
    try:
        characters_data = load_characters_from_json()
        
        if 'characters' in characters_data:
            for character_id, character_info in characters_data['characters'].items():
                update_character_in_database(character_id, character_info)
            
            logging.info(f"Initialized {len(characters_data['characters'])} characters from JSON")
            
    except Exception as e:
        logging.error(f"Error initializing characters from JSON: {e}")

def update_character_in_database(character_id, character_data):
    """Update or insert character in database"""
    try:
        from databases.live2d_models_separated import get_live2d_connection
        
        # Ensure the table exists
        create_characters_table()
        
        with get_live2d_connection() as conn:
            cursor = conn.cursor()
            
            # Add timestamp
            character_data['last_updated'] = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO characters 
                (character_id, character_data, last_updated)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (character_id, json.dumps(character_data)))
            
            conn.commit()
        
        # Update framework with new character information
        framework_updated = update_framework_for_character(character_id, character_data)
        if not framework_updated:
            logging.warning(f"Failed to update framework for character {character_id}")
            
        return True
            
    except Exception as e:
        logging.error(f"Error updating character {character_id}: {e}")
        return False

def delete_character_from_database(character_id):
    """Delete character from database"""
    try:
        from databases.live2d_models_separated import get_live2d_connection
        
        with get_live2d_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM characters WHERE character_id = ?", (character_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
        
        if deleted:
            # Remove character from framework
            remove_character_from_framework(character_id)
            
        return deleted
            
    except Exception as e:
        logging.error(f"Error deleting character {character_id}: {e}")
        return False

def remove_character_from_framework(character_id):
    """Remove character from framework lists and trigger phrases"""
    try:
        framework = load_avatar_framework()
        
        if not framework:
            logging.warning("Could not load avatar framework for character removal")
            return False
        
        # Remove from content rating enforcement
        if 'usage_guidelines' in framework and 'content_rating_enforcement' in framework['usage_guidelines']:
            enforcement = framework['usage_guidelines']['content_rating_enforcement']
            
            if character_id in enforcement.get('sfw_only_characters', []):
                enforcement['sfw_only_characters'].remove(character_id)
            if character_id in enforcement.get('nsfw_capable_characters', []):
                enforcement['nsfw_capable_characters'].remove(character_id)
        
        # Remove trigger phrases
        if 'usage_guidelines' in framework and 'character_switching' in framework['usage_guidelines']:
            switching = framework['usage_guidelines']['character_switching']
            
            if 'trigger_phrases' in switching and character_id in switching['trigger_phrases']:
                del switching['trigger_phrases'][character_id]
        
        # Save updated framework
        return save_avatar_framework(framework)
        
    except Exception as e:
        logging.error(f"Error removing character {character_id} from framework: {e}")
        return False
