"""
Voice Management API Routes
Handles voice model uploads, management, and character assignments
"""

import os
import json
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import sqlite3
from databases.database_manager import get_voices_connection, get_database_path
from models.tts_handler import EmotionalTTSHandler
from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)
voices_bp = Blueprint('voices', __name__)

# Allowed voice file extensions
ALLOWED_VOICE_EXTENSIONS = {'.pth', '.onnx', '.zip', '.bin', '.json'}

def allowed_voice_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return Path(filename).suffix.lower() in ALLOWED_VOICE_EXTENSIONS

def init_voices_database():
    """Initialize the voices database with required tables"""
    try:
        conn = get_voices_connection()
        cursor = conn.cursor()
        
        # Create voices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voices (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create character voice assignments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_voice_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_name TEXT NOT NULL,
                voice_id TEXT,
                default_model TEXT,
                voice_settings TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (voice_id) REFERENCES voices (id),
                UNIQUE(character_name)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Voices database initialized successfully")
        
        # Scan for existing voice files after initialization
        scan_existing_voices()
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize voices database: {e}")
        raise

def scan_existing_voices():
    """Scan the voices directory for existing files and add them to database"""
    try:
        voices_dir = get_voices_directory()
        if not voices_dir.exists():
            logger.info("📁 Voices directory doesn't exist yet")
            return
        
        logger.info(f"🔍 Scanning voices directory: {voices_dir}")
        
        conn = get_voices_connection()
        cursor = conn.cursor()
        
        scanned_count = 0
        added_count = 0
        
        for file_path in voices_dir.glob("*"):
            if file_path.is_file() and allowed_voice_file(file_path.name):
                scanned_count += 1
                
                # Check if already in database
                cursor.execute('SELECT id FROM voices WHERE file_path = ?', (str(file_path),))
                if cursor.fetchone():
                    continue
                
                # Add to database
                voice_id = file_path.stem
                voice_name = voice_id.replace('_', ' ').replace('-', ' ').title()
                voice_type = file_path.suffix.lower()[1:]
                file_size = file_path.stat().st_size
                
                metadata = {
                    'original_filename': file_path.name,
                    'file_extension': file_path.suffix.lower(),
                    'scan_source': 'directory_scan'
                }
                
                cursor.execute('''
                    INSERT INTO voices (id, name, type, file_path, file_size, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (voice_id, voice_name, voice_type, str(file_path), file_size, json.dumps(metadata)))
                
                added_count += 1
                logger.info(f"➕ Added voice from directory: {voice_name}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Voice scan complete: {scanned_count} files scanned, {added_count} added to database")
        
    except Exception as e:
        logger.error(f"❌ Failed to scan existing voices: {e}")

def get_voices_directory():
    """Get the voices directory path"""
    try:
        config_manager = ConfigManager()
        return config_manager.data_dir / "models" / "voices"
    except:
        # Fallback
        return Path.home() / ".local/share/ai2d_chat/models/voices"

@voices_bp.route('/upload', methods=['POST'])
def upload_voice():
    """Upload a voice model file"""
    try:
        if 'voice_file' not in request.files:
            return jsonify({'error': 'No voice file provided'}), 400
        
        file = request.files['voice_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_voice_file(file.filename):
            return jsonify({'error': f'File type not allowed. Supported: {", ".join(ALLOWED_VOICE_EXTENSIONS)}'}), 400
        
        # Create voices directory
        voices_dir = get_voices_directory()
        voices_dir.mkdir(parents=True, exist_ok=True)
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        file_path = voices_dir / filename
        
        # Check if file already exists
        if file_path.exists():
            return jsonify({'error': 'Voice file already exists'}), 409
        
        # Save the file
        file.save(str(file_path))
        file_size = file_path.stat().st_size
        
        # Determine voice type based on file extension
        voice_type = Path(filename).suffix.lower()[1:]  # Remove the dot
        
        # Generate voice ID and metadata
        voice_id = Path(filename).stem  # Filename without extension
        voice_name = voice_id.replace('_', ' ').replace('-', ' ').title()
        
        metadata = {
            'original_filename': file.filename,
            'file_extension': Path(filename).suffix.lower(),
            'upload_source': 'web_interface'
        }
        
        # Save to database
        conn = get_voices_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO voices (id, name, type, file_path, file_size, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (voice_id, voice_name, voice_type, str(file_path), file_size, json.dumps(metadata)))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Voice uploaded successfully: {voice_name} ({filename})")
        
        return jsonify({
            'id': voice_id,
            'name': voice_name,
            'type': voice_type,
            'file_size': file_size,
            'message': 'Voice uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Voice upload failed: {e}")
        return jsonify({'error': str(e)}), 500

@voices_bp.route('/list', methods=['GET'])
def list_voices():
    """Get list of available voice models"""
    try:
        conn = get_voices_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, type, file_size, created_at, metadata
            FROM voices
            ORDER BY name
        ''')
        
        voices = []
        for row in cursor.fetchall():
            voice_data = {
                'id': row['id'],
                'name': row['name'],
                'type': row['type'],
                'file_size': row['file_size'],
                'created_at': row['created_at']
            }
            
            # Parse metadata if available
            if row['metadata']:
                try:
                    voice_data['metadata'] = json.loads(row['metadata'])
                except:
                    pass
            
            voices.append(voice_data)
        
        conn.close()
        
        logger.info(f"📋 Listed {len(voices)} voice models")
        return jsonify(voices)
        
    except Exception as e:
        logger.error(f"❌ Failed to list voices: {e}")
        return jsonify({'error': str(e)}), 500

@voices_bp.route('/<voice_id>', methods=['DELETE'])
def remove_voice(voice_id):
    """Remove a voice model"""
    try:
        conn = get_voices_connection()
        cursor = conn.cursor()
        
        # Get voice info first
        cursor.execute('SELECT file_path, name FROM voices WHERE id = ?', (voice_id,))
        voice_row = cursor.fetchone()
        
        if not voice_row:
            return jsonify({'error': 'Voice not found'}), 404
        
        file_path = Path(voice_row['file_path'])
        voice_name = voice_row['name']
        
        # Remove from database
        cursor.execute('DELETE FROM voices WHERE id = ?', (voice_id,))
        
        # Remove character assignments
        cursor.execute('UPDATE character_voice_assignments SET voice_id = NULL WHERE voice_id = ?', (voice_id,))
        
        conn.commit()
        conn.close()
        
        # Remove file if it exists
        if file_path.exists():
            file_path.unlink()
            logger.info(f"🗑️ Removed voice file: {file_path}")
        
        logger.info(f"✅ Voice removed successfully: {voice_name}")
        
        return jsonify({
            'message': f'Voice "{voice_name}" removed successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to remove voice: {e}")
        return jsonify({'error': str(e)}), 500

@voices_bp.route('/test', methods=['POST'])
def test_voice():
    """Test a voice model with provided text"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        voice_id = data.get('voice_id')
        text = data.get('text', 'Hello, this is a voice test.')
        settings = data.get('settings', {})
        
        if not voice_id:
            return jsonify({'error': 'Voice ID required'}), 400
        
        # Get voice info from database
        conn = get_voices_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT file_path, name, type FROM voices WHERE id = ?', (voice_id,))
        voice_row = cursor.fetchone()
        conn.close()
        
        if not voice_row:
            return jsonify({'error': 'Voice not found'}), 404
        
        # For now, use the existing TTS system for testing
        # In the future, this will be enhanced to use .pth models
        try:
            tts_handler = EmotionalTTSHandler()
            
            # Apply voice settings if provided
            emotion = 'neutral'
            intensity = 0.5
            
            if settings:
                # Map settings to TTS parameters
                if settings.get('pitch'):
                    # Pitch adjustment could affect emotion selection
                    pass
                if settings.get('speed'):
                    # Speed adjustment
                    pass
                if settings.get('volume'):
                    # Volume adjustment
                    pass
            
            # Generate speech
            audio_data = tts_handler.synthesize_emotional_speech(text, emotion, intensity)
            
            if audio_data is None:
                return jsonify({'error': 'Failed to generate speech'}), 500
            
            # Convert numpy array to audio file (simplified)
            # In a real implementation, you would convert to WAV/MP3 format
            import tempfile
            import wave
            import numpy as np
            
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Convert float32 to int16
                audio_int16 = (audio_data * 32767).astype(np.int16)
                
                with wave.open(temp_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(24000)  # 24kHz
                    wav_file.writeframes(audio_int16.tobytes())
                
                # Send the audio file
                return send_file(temp_path, mimetype='audio/wav', as_attachment=False)
        
        except Exception as tts_error:
            logger.error(f"❌ TTS generation failed: {tts_error}")
            return jsonify({'error': f'TTS generation failed: {str(tts_error)}'}), 500
        
    except Exception as e:
        logger.error(f"❌ Voice test failed: {e}")
        return jsonify({'error': str(e)}), 500

@voices_bp.route('/character-assignment', methods=['POST'])
def save_character_voice_assignment():
    """Save voice assignment for a character"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        character_name = data.get('character_name')
        if not character_name:
            return jsonify({'error': 'Character name required'}), 400
        
        voice_id = data.get('voice_id')
        default_model = data.get('default_model')
        voice_settings = data.get('voice_settings', {})
        
        conn = get_voices_connection()
        cursor = conn.cursor()
        
        # Insert or update character voice assignment
        cursor.execute('''
            INSERT OR REPLACE INTO character_voice_assignments 
            (character_name, voice_id, default_model, voice_settings, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (character_name, voice_id, default_model, json.dumps(voice_settings)))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Character voice assignment saved: {character_name} -> {voice_id}")
        
        return jsonify({
            'message': 'Character voice assignment saved successfully',
            'character_name': character_name,
            'voice_id': voice_id,
            'default_model': default_model
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to save character voice assignment: {e}")
        return jsonify({'error': str(e)}), 500

@voices_bp.route('/character-assignment/<character_name>', methods=['GET'])
def get_character_voice_assignment(character_name):
    """Get voice assignment for a character"""
    try:
        conn = get_voices_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT voice_id, default_model, voice_settings
            FROM character_voice_assignments
            WHERE character_name = ?
        ''', (character_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Character voice assignment not found'}), 404
        
        result = {
            'character_name': character_name,
            'voice_id': row['voice_id'],
            'default_model': row['default_model']
        }
        
        # Parse voice settings
        if row['voice_settings']:
            try:
                result['voice_settings'] = json.loads(row['voice_settings'])
            except:
                result['voice_settings'] = {}
        else:
            result['voice_settings'] = {}
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Failed to get character voice assignment: {e}")
        return jsonify({'error': str(e)}), 500

@voices_bp.route('/character-assignment/<character_name>', methods=['DELETE'])
def delete_character_voice_assignment(character_name):
    """Delete voice assignment for a character"""
    try:
        conn = get_voices_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM character_voice_assignments WHERE character_name = ?', (character_name,))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Character voice assignment not found'}), 404
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Character voice assignment deleted: {character_name}")
        
        return jsonify({
            'message': f'Voice assignment for "{character_name}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to delete character voice assignment: {e}")
        return jsonify({'error': str(e)}), 500

# Initialize database when module is imported
try:
    init_voices_database()
except Exception as e:
    logger.error(f"❌ Failed to initialize voices database: {e}")
