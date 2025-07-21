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
            return cursor.rowcount > 0
            
    except Exception as e:
        logging.error(f"Error deleting character {character_id}: {e}")
        return False
