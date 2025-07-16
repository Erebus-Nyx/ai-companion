"""
app_routes_chat.py
Chat and personality-related Flask route definitions for the AI Companion backend.
"""
from flask import Blueprint, jsonify, request
import time
import app_globals
import logging

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chat', methods=['POST'])
def api_chat():
    """Main chat endpoint for LLM conversations"""
    try:
        llm_handler = app_globals.llm_handler
        personality_system = app_globals.personality_system
        
        if not llm_handler:
            return jsonify({'error': 'LLM handler not initialized'}), 500
            
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing message in request'}), 400
            
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
            
        # Get LLM response
        user_id = data.get('user_id', 'default_user')
        response_text = llm_handler.generate_response(user_message, user_id)
        
        # Extract basic emotions from response (simple pattern matching)
        emotions = []
        primary_emotion = 'neutral'
        
        # Basic emotion detection in response
        emotion_patterns = {
            'happy': ['😊', '😄', '🎉', 'happy', 'excited', 'joy', 'wonderful', 'amazing'],
            'sad': ['😢', '😔', '💔', 'sad', 'sorry', 'unfortunately', 'disappointed'],
            'surprised': ['😮', '😯', '🤔', 'wow', 'really', 'surprising', 'unexpected'],
            'curious': ['🤔', '💭', 'interesting', 'wonder', 'curious', 'hmm'],
            'caring': ['❤️', '💕', 'care', 'support', 'here for you', 'understand']
        }
        
        response_lower = response_text.lower()
        for emotion, patterns in emotion_patterns.items():
            for pattern in patterns:
                if pattern in response_lower:
                    emotions.append(emotion)
                    if not primary_emotion or primary_emotion == 'neutral':
                        primary_emotion = emotion
                    break
        
        return jsonify({
            'reply': response_text,
            'emotions': emotions,
            'primary_emotion': primary_emotion,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Error in chat API: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@chat_bp.route('/api/v1/chat', methods=['POST'])
def api_v1_chat():
    return api_chat()

@chat_bp.route('/api/personality')
def api_personality():
    # ...copy personality logic from app.py...
    return jsonify({'error': 'Not implemented'})
