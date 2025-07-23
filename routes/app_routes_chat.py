"""
app_routes_chat.py
Chat and personality-related Flask route definitions for the AI Companion backend.
"""
from flask import Blueprint, jsonify, request
import time
import app_globals
import logging
import json
from datetime import datetime
import traceback
import sqlite3
from databases.database_manager import get_database_path

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)

# app_routes_chat.py
# Chat API routes with multi-avatar support

from flask import Blueprint, request, jsonify
import logging
import traceback
from datetime import datetime

# Blueprint definition
chat_routes = Blueprint('chat_routes', __name__)

@chat_routes.route('/api/chat', methods=['POST'])
def api_chat():
    """Main chat endpoint for LLM conversations with multi-avatar support and user context"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Multi-avatar context
        avatar_id = data.get('avatar_id')
        avatar_name = data.get('avatar_name', 'Assistant')
        active_avatars = data.get('active_avatars', [])
        conversation_context = data.get('conversation_context', [])
        
        # User context from frontend
        user_info = data.get('user_info', {})
        user_id = user_info.get('user_id')
        user_display_name = user_info.get('display_name', 'User')
        user_preferences = user_info.get('preferences', {})
        
        # Import global handlers here to avoid circular imports
        from app_globals import llm_handler, personality_system, app_state
        
        if llm_handler is None:
            return jsonify({'error': 'LLM handler not initialized'}), 503
        
        # Prepare context for multi-avatar chat with user information
        chat_context = {
            'user_message': user_message,
            'avatar_id': avatar_id,
            'avatar_name': avatar_name,
            'active_avatars_count': len(active_avatars),
            'active_avatars': active_avatars,
            'conversation_history': conversation_context,
            'user_info': {
                'user_id': user_id,
                'display_name': user_display_name,
                'preferences': user_preferences
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Get avatar-specific information from database if available
        avatar_info = get_avatar_database_info(avatar_id) if avatar_id else None
        if avatar_info:
            chat_context['avatar_description'] = avatar_info.get('description', '')
            chat_context['avatar_motions'] = list(avatar_info.get('motions', {}).keys())
        
        # Generate response with avatar context
        if avatar_id:
            # Multi-avatar mode: include avatar context in prompt with model isolation
            enhanced_prompt = build_avatar_prompt(user_message, chat_context)
            response_text = llm_handler.generate_response(
                enhanced_prompt,
                user_id=str(user_id) if user_id else "default_user",
                model_id=avatar_id  # Use avatar_id as model_id for isolation
            )
        else:
            # Legacy single chat mode
            response_text = llm_handler.generate_response(
                user_message,
                user_id=str(user_id) if user_id else "default_user"
            )
        
        # Basic emotion detection (enhanced emotion system will be rebuilt later)
        emotions, primary_emotion = detect_basic_emotions(response_text)
        
        # Store conversation in memory system if available and user is authenticated
        try:
            if (hasattr(llm_handler, 'memory_system') and llm_handler.memory_system and 
                user_id is not None and user_id != ''):
                llm_handler.memory_system.store_conversation(
                    user_message, 
                    response_text,
                    metadata={
                        'avatar_id': avatar_id,
                        'avatar_name': avatar_name,
                        'primary_emotion': primary_emotion,
                        'active_avatars_count': len(active_avatars),
                        'user_id': user_id,
                        'user_display_name': user_display_name
                    }
                )
                logging.info(f"Stored conversation in memory for user {user_id}")
            else:
                logging.info("Skipping memory storage - no authenticated user or memory system unavailable")
        except Exception as e:
            logging.warning(f"Failed to store conversation in memory: {e}")

        # Store in conversation history database (only if user is authenticated)
        try:
            if user_id is not None and user_id != '':
                store_conversation_message(user_id, avatar_id, user_message, response_text, {
                    'user_display_name': user_display_name,
                    'avatar_name': avatar_name,
                    'primary_emotion': primary_emotion,
                    'active_avatars_count': len(active_avatars)
                })
                logging.info(f"Stored conversation in database for user {user_id}")
            else:
                logging.info("Skipping database storage - no authenticated user")
        except Exception as e:
            logging.warning(f"Failed to store conversation in database: {e}")        # Log chat interaction
        logging.info(f"Chat - User: {user_display_name} ({user_id}), "
                    f"Avatar: {avatar_name} ({avatar_id}), "
                    f"Active: {len(active_avatars)}, "
                    f"Emotion: {primary_emotion}, "
                    f"Message: {user_message[:50]}...")
        
        return jsonify({
            'reply': response_text,
            'emotions': emotions,
            'primary_emotion': primary_emotion,
            'avatar_id': avatar_id,
            'avatar_name': avatar_name,
            'timestamp': datetime.now().isoformat(),
            'active_avatars_count': len(active_avatars)
        })
        
    except Exception as e:
        error_msg = f"Chat API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({
            'error': error_msg,
            'reply': 'Sorry, I encountered an error while processing your message.',
            'emotions': ['neutral'],
            'primary_emotion': 'neutral'
        }), 500


def get_avatar_database_info(avatar_id):
    """Get avatar information from database"""
    try:
        from databases.live2d_models_separated import get_model_info
        return get_model_info(avatar_id)
    except Exception as e:
        logging.warning(f"Failed to get avatar database info for {avatar_id}: {e}")
        return None


def build_avatar_prompt(user_message, context):
    """Build enhanced prompt with avatar context"""
    avatar_name = context.get('avatar_name', 'Assistant')
    avatar_description = context.get('avatar_description', '')
    active_count = context.get('active_avatars_count', 1)
    
    # Base prompt with avatar context
    prompt_parts = []
    
    if active_count > 1:
        prompt_parts.append(f"You are {avatar_name}, one of {active_count} active AI avatars in a conversation.")
        prompt_parts.append("Respond naturally as your individual character.")
    else:
        prompt_parts.append(f"You are {avatar_name}, an AI assistant avatar.")
    
    if avatar_description:
        prompt_parts.append(f"Character description: {avatar_description}")
    
    # Add conversation context if available
    conversation_history = context.get('conversation_history', [])
    if conversation_history:
        prompt_parts.append("Recent conversation:")
        for msg in conversation_history[-3:]:  # Last 3 messages
            if msg.get('type') == 'user':
                prompt_parts.append(f"User: {msg.get('message', '')}")
            elif msg.get('type') == 'avatar' and msg.get('avatar'):
                speaker = msg['avatar'].get('displayName', 'Avatar')
                prompt_parts.append(f"{speaker}: {msg.get('message', '')}")
    
    prompt_parts.append(f"User: {user_message}")
    prompt_parts.append(f"{avatar_name}:")
    
    return "\n".join(prompt_parts)


def detect_basic_emotions(text):
    """Basic emotion detection - will be enhanced when emotion system is rebuilt"""
    text_lower = text.lower()
    
    # Simple keyword-based emotion detection
    emotion_keywords = {
        'happy': ['happy', 'joy', 'excited', 'great', 'wonderful', 'fantastic', 'excellent', '!'],
        'sad': ['sad', 'sorry', 'unfortunate', 'disappointed', 'regret'],
        'angry': ['angry', 'frustrated', 'annoyed', 'upset'],
        'surprised': ['wow', 'amazing', 'incredible', 'unexpected', 'surprise'],
        'confused': ['confused', 'puzzled', 'unclear', 'not sure', "don't understand"],
        'neutral': ['okay', 'alright', 'understood', 'yes', 'no']
    }
    
    detected_emotions = []
    emotion_scores = {}
    
    for emotion, keywords in emotion_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            emotion_scores[emotion] = score
            detected_emotions.append(emotion)
    
    # Determine primary emotion
    if emotion_scores:
        primary_emotion = max(emotion_scores, key=emotion_scores.get)
    else:
        primary_emotion = 'neutral'
    
    # Default to neutral if no emotions detected
    if not detected_emotions:
        detected_emotions = ['neutral']
    
    return detected_emotions, primary_emotion


def store_conversation_message(user_id, avatar_id, user_message, ai_response, metadata):
    """Store conversation message in database"""
    try:
        from databases.database_manager import get_conversations_connection
        
        with get_conversations_connection() as conn:
            cursor = conn.cursor()
            
            # Create conversation_history table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    avatar_id TEXT,
                    user_message TEXT,
                    ai_response TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Store the conversation
            cursor.execute("""
                INSERT INTO conversation_history 
                (user_id, avatar_id, user_message, ai_response, metadata) 
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, avatar_id, user_message, ai_response, json.dumps(metadata)))
            
            conn.commit()
            
    except Exception as e:
        logging.error(f"Failed to store conversation: {e}")


@chat_routes.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """Get chat history for a user with optional filtering"""
    try:
        user_id = request.args.get('user_id')
        avatar_id = request.args.get('avatar_id')  # Optional filter by avatar
        limit = int(request.args.get('limit', 50))
        
        if not user_id:
            return jsonify({'error': 'user_id parameter required'}), 400
        
        from databases.database_manager import get_conversations_connection
        
        with get_conversations_connection() as conn:
            cursor = conn.cursor()
            
            # Build query with optional avatar filter
            if avatar_id:
                query = """
                    SELECT user_message, ai_response, avatar_id, metadata, created_at 
                    FROM conversation_history 
                    WHERE user_id = ? AND avatar_id = ?
                    ORDER BY created_at DESC LIMIT ?
                """
                cursor.execute(query, (user_id, avatar_id, limit))
            else:
                query = """
                    SELECT user_message, ai_response, avatar_id, metadata, created_at 
                    FROM conversation_history 
                    WHERE user_id = ?
                    ORDER BY created_at DESC LIMIT ?
                """
                cursor.execute(query, (user_id, limit))
            
            rows = cursor.fetchall()
            
            # Format history
            history = []
            for row in rows:
                user_message, ai_response, avatar_id, metadata_str, created_at = row
                try:
                    metadata = json.loads(metadata_str) if metadata_str else {}
                except:
                    metadata = {}
                
                history.append({
                    'user_message': user_message,
                    'ai_response': ai_response,
                    'avatar_id': avatar_id,
                    'avatar_name': metadata.get('avatar_name', avatar_id),
                    'user_display_name': metadata.get('user_display_name', 'User'),
                    'primary_emotion': metadata.get('primary_emotion', 'neutral'),
                    'timestamp': created_at
                })
            
            # Reverse to get chronological order (oldest first)
            history.reverse()
            
            return jsonify({
                'history': history,
                'total_messages': len(history),
                'user_id': user_id,
                'avatar_filter': avatar_id
            })
            
    except Exception as e:
        error_msg = f"Chat history API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500


@chat_routes.route('/api/chat/users/<user_id>/summary', methods=['GET'])
def get_user_chat_summary(user_id):
    """Get chat summary statistics for a user"""
    try:
        from databases.database_manager import get_conversations_connection
        
        with get_conversations_connection() as conn:
            cursor = conn.cursor()
            
            # Get total message count
            cursor.execute("""
                SELECT COUNT(*) FROM conversation_history WHERE user_id = ?
            """, (user_id,))
            total_messages = cursor.fetchone()[0]
            
            # Get unique avatars interacted with
            cursor.execute("""
                SELECT DISTINCT avatar_id, COUNT(*) as message_count
                FROM conversation_history 
                WHERE user_id = ? 
                GROUP BY avatar_id
                ORDER BY message_count DESC
            """, (user_id,))
            avatar_stats = cursor.fetchall()
            
            # Get recent activity (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) FROM conversation_history 
                WHERE user_id = ? AND created_at >= datetime('now', '-7 days')
            """, (user_id,))
            recent_messages = cursor.fetchone()[0]
            
            return jsonify({
                'user_id': user_id,
                'total_messages': total_messages,
                'avatars_interacted': len(avatar_stats),
                'avatar_stats': [{'avatar_id': row[0], 'message_count': row[1]} for row in avatar_stats],
                'recent_activity': recent_messages
            })
            
    except Exception as e:
        error_msg = f"Chat summary API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@chat_routes.route('/api/chat/generate', methods=['POST'])
def api_chat_generate():
    """Enhanced chat generation endpoint with full avatar identity support"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Get comprehensive avatar and context information
        avatar_id = data.get('avatar_id')
        avatar_info = data.get('avatar_info', {})
        message_type = data.get('message_type', 'greeting')
        context = data.get('context', {})
        character_identity = data.get('character_identity', {})
        
        if not avatar_id:
            return jsonify({'error': 'Avatar ID is required'}), 400
        
        # Use the enhanced LLM handler
        llm_handler = app_globals.llm_handler
        if not llm_handler:
            return jsonify({'error': 'LLM handler not available'}), 500
        
        # Extract character identity information
        character_name = character_identity.get('name_to_use') or avatar_info.get('character_name') or avatar_info.get('name', 'Avatar')
        character_instructions = character_identity.get('character_identity', f'You are {character_name}')
        identity_enforcement = character_identity.get('identity_enforcement', f'Always introduce yourself as {character_name} and maintain this identity throughout the conversation.')
        
        # Build enhanced prompt with explicit character identity
        if message_type == 'greeting':
            prompt = f"""{character_instructions}

{identity_enforcement}

Context: {context.get('context', 'You just loaded and are greeting the user')}
Intent: {context.get('intent', 'welcome_user')}
Emotion: {context.get('emotion', 'friendly')}

Generate a natural, friendly greeting where you introduce yourself correctly as {character_name}.
Keep it brief and welcoming. Do not use asterisks or action descriptions.
Remember: You are {character_name}, not any other character."""
        else:
            prompt = f"""{character_instructions}

{identity_enforcement}

Generate a {message_type} message as {character_name}.
Context: {context.get('context', str(context)) if isinstance(context, dict) else str(context)}
Keep the response natural and appropriate for {character_name}.
Remember: You are {character_name}, not any other character."""
        
        # Generate response using LLM with character identity enforcement
        response = llm_handler.generate_response(
            prompt,
            user_id=data.get('user_id', "autonomous_user"),
            model_id=avatar_id  # Use avatar_id for isolation
        )
        
        if response and response.strip():
            return jsonify({
                'message': response.strip(),
                'avatar_id': avatar_id,
                'character_name': character_name,
                'message_type': message_type,
                'emotion': context.get('emotion', 'neutral'),
                'success': True
            })
        else:
            return jsonify({'error': 'Failed to generate message'}), 500
            
    except Exception as e:
        error_msg = f"Chat generation API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@chat_routes.route('/api/chat/autonomous', methods=['POST'])
def api_chat_autonomous():
    """Autonomous chat endpoint for avatar-generated messages - Enhanced with character identity"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Get avatar and context information
        avatar_id = data.get('avatar_id')
        avatar_name = data.get('avatar_name', 'Avatar')
        message_type = data.get('message_type', 'greeting')
        user_id = data.get('user_id')
        context = data.get('context', {})
        
        if not avatar_id:
            return jsonify({'error': 'Avatar ID is required'}), 400
        
        # Use the enhanced LLM handler for autonomous message generation
        llm_handler = app_globals.llm_handler
        if not llm_handler:
            return jsonify({'error': 'LLM handler not available'}), 500
        
        # Ensure context is a dictionary
        if isinstance(context, str):
            context = {'context': context}
        elif not isinstance(context, dict):
            context = {}
        
        # Enhanced character identity enforcement
        # Use proper character name (capitalized from avatar_id if needed)
        proper_character_name = avatar_name if avatar_name != 'Avatar' else avatar_id.capitalize()
        
        # Build prompt with explicit character identity enforcement
        if message_type == 'greeting':
            prompt = f"""You are {proper_character_name}. This is very important: You must introduce yourself as {proper_character_name}, not as any other name or character.

Your name is {proper_character_name}. You are {proper_character_name}. When introducing yourself, say "I'm {proper_character_name}" or "My name is {proper_character_name}".

Context: {context.get('context', 'You just loaded and are greeting the user')}
Intent: {context.get('intent', 'welcome_user')}
Emotion: {context.get('emotion', 'friendly')}

Generate a natural, friendly greeting where you correctly introduce yourself as {proper_character_name}.
Keep it brief and welcoming. Do not use asterisks or action descriptions.
Remember: You are {proper_character_name}, not Nyx or any other character."""
        else:
            prompt = f"""You are {proper_character_name}. This is very important: Your name is {proper_character_name}.

Generate a {message_type} message as {proper_character_name}.
Context: {context.get('context', str(context)) if isinstance(context, dict) else str(context)}
Keep the response natural and appropriate for {proper_character_name}.
Remember: You are {proper_character_name}, not any other character."""
        
        # Generate response using LLM with character identity enforcement
        response = llm_handler.generate_response(
            prompt,
            user_id=str(user_id) if user_id else "autonomous_user",
            model_id=avatar_id  # Use avatar_id as model_id for isolation
        )
        
        if response and response.strip():
            return jsonify({
                'message': response.strip(),
                'avatar_id': avatar_id,
                'avatar_name': proper_character_name,
                'message_type': message_type,
                'emotion': context.get('emotion', 'neutral'),
                'success': True
            })
        else:
            return jsonify({'error': 'Failed to generate message'}), 500
            
    except Exception as e:
        error_msg = f"Autonomous chat API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@chat_bp.route('/api/chat/clear-cache', methods=['POST'])
def clear_chat_cache():
    """Clear LLM cache for specific avatar or all cache"""
    try:
        data = request.get_json() or {}
        avatar_id = data.get('avatar_id')
        
        # Get database path using config - use conversations.db where llm_cache table is located
        db_path = get_database_path("conversations.db")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        if avatar_id:
            # Clear cache for specific avatar - use model_id column
            cursor.execute("DELETE FROM llm_cache WHERE model_id = ?", (avatar_id,))
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            return jsonify({
                "success": True,
                "message": f"Cleared {deleted} cached responses for avatar {avatar_id}"
            })
        else:
            # Clear all cache
            cursor.execute("DELETE FROM llm_cache")
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            return jsonify({
                "success": True,
                "message": f"Cleared {deleted} cached responses for all avatars"
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}"
        }), 500

@chat_routes.route('/api/chat/clear-cache', methods=['POST'])
def api_chat_clear_cache():
    """Clear LLM response cache to force fresh generation"""
    try:
        data = request.get_json() or {}
        
        # Get optional parameters
        avatar_id = data.get('avatar_id')  # Clear cache for specific avatar
        user_id = data.get('user_id')      # Clear cache for specific user
        
        # Use the enhanced LLM handler to clear cache
        llm_handler = app_globals.llm_handler
        if not llm_handler:
            return jsonify({'error': 'LLM handler not available'}), 500
        
        # Access the database manager through the LLM handler
        db_manager = llm_handler.db_manager
        if not db_manager:
            return jsonify({'error': 'Database manager not available'}), 500
        
        # Clear cache based on parameters
        cleared_count = 0
        
        try:
            # Get database connection using config-based path
            db_path = get_database_path("conversations.db")
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            if avatar_id and user_id:
                # Clear cache for specific avatar and user - note: no user_id in llm_cache, use input_hash pattern
                cursor.execute(
                    'DELETE FROM llm_cache WHERE model_id = ? AND input_hash LIKE ?',
                    (avatar_id, f'%{user_id}%')
                )
                cleared_count = cursor.rowcount
                cache_scope = f"avatar '{avatar_id}' and user '{user_id}'"
            elif avatar_id:
                # Clear cache for specific avatar - use model_id column
                cursor.execute('DELETE FROM llm_cache WHERE model_id = ?', (avatar_id,))
                cleared_count = cursor.rowcount
                cache_scope = f"avatar '{avatar_id}'"
            elif user_id:
                # Clear cache for specific user - search by input_hash pattern
                cursor.execute('DELETE FROM llm_cache WHERE input_hash LIKE ?', (f'%{user_id}%',))
                cleared_count = cursor.rowcount
                cache_scope = f"user '{user_id}'"
            else:
                # Clear all cache
                cursor.execute('DELETE FROM llm_cache')
                cleared_count = cursor.rowcount
                cache_scope = "all cached responses"
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleared {cleared_count} cached LLM responses for {cache_scope}")
            
            return jsonify({
                'success': True,
                'cleared_count': cleared_count,
                'scope': cache_scope,
                'message': f'Successfully cleared {cleared_count} cached responses for {cache_scope}'
            })
            
        except Exception as db_error:
            logger.error(f"Database error while clearing cache: {str(db_error)}")
            return jsonify({'error': f'Database error: {str(db_error)}'}), 500
            
    except Exception as e:
        error_msg = f"Clear cache API error: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@chat_bp.route('/api/v1/chat', methods=['POST'])
def api_v1_chat():
    return api_chat()

@chat_bp.route('/api/personality')
def api_personality():
    # ...copy personality logic from app.py...
    return jsonify({'error': 'Not implemented'})
