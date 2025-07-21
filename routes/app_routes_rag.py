"""
RAG (Retrieval-Augmented Generation) API Routes
Provides endpoints for RAG system management and semantic search
"""

import logging
from flask import Blueprint, request, jsonify
from app_globals import app_state, config_manager
from models.rag_system import RAGEnhancedMemorySystem

logger = logging.getLogger(__name__)
rag_blueprint = Blueprint('rag', __name__)

# Global RAG system instance
rag_memory_system = None

def initialize_rag_system():
    """Initialize the RAG system if enabled in config"""
    global rag_memory_system
    
    try:
        config = config_manager.get_config()
        rag_config = config.get('rag', {})
        
        if rag_config.get('enabled', False):
            from databases.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            # Enhanced memory system with RAG capabilities
            from models.memory_system import MemorySystem
            memory_system = MemorySystem(db_manager, config)
            
            # Set global instance
            rag_memory_system = memory_system
            
            logger.info("RAG system initialized successfully")
            return True
        else:
            logger.info("RAG system disabled in configuration")
            return False
            
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        return False

@rag_blueprint.route('/api/rag/status', methods=['GET'])
def get_rag_status():
    """Get RAG system status and statistics"""
    try:
        if not rag_memory_system:
            return jsonify({
                'enabled': False,
                'error': 'RAG system not initialized'
            }), 200
        
        # Get RAG statistics
        stats = rag_memory_system.get_rag_stats()
        
        return jsonify({
            'enabled': True,
            'status': 'active',
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting RAG status: {e}")
        return jsonify({
            'error': str(e),
            'enabled': False
        }), 500

@rag_blueprint.route('/api/rag/search', methods=['POST'])
def semantic_search():
    """Perform semantic search on conversation history"""
    try:
        if not rag_memory_system:
            return jsonify({
                'error': 'RAG system not initialized'
            }), 400
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Query parameter required'
            }), 400
        
        query = data['query']
        user_id = data.get('user_id', 'default')
        limit = data.get('limit', 5)
        
        # Perform semantic search
        results = rag_memory_system.search_conversation_history(
            user_id=user_id,
            query=query,
            limit=limit
        )
        
        return jsonify({
            'query': query,
            'results': results,
            'count': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error performing semantic search: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@rag_blueprint.route('/api/rag/context', methods=['POST'])
def get_relevant_context():
    """Get relevant context for a query using RAG"""
    try:
        if not rag_memory_system:
            return jsonify({
                'error': 'RAG system not initialized'
            }), 400
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Query parameter required'
            }), 400
        
        query = data['query']
        user_id = data.get('user_id', 'default')
        max_length = data.get('max_length', 2000)
        model_id = data.get('model_id', 'default')
        
        # Get relevant context
        context = rag_memory_system.get_semantic_context(
            user_id=user_id,
            query=query,
            max_length=max_length,
            model_id=model_id
        )
        
        return jsonify({
            'query': query,
            'context': context,
            'context_length': len(context)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting relevant context: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@rag_blueprint.route('/api/rag/add_conversation', methods=['POST'])
def add_conversation():
    """Add a conversation to the RAG system"""
    try:
        if not rag_memory_system:
            return jsonify({
                'error': 'RAG system not initialized'
            }), 400
        
        data = request.get_json()
        required_fields = ['user_message', 'assistant_response']
        
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                'error': 'user_message and assistant_response required'
            }), 400
        
        user_message = data['user_message']
        assistant_response = data['assistant_response']
        user_id = data.get('user_id', 'default')
        model_id = data.get('model_id', 'default')
        importance = data.get('importance', 'medium')
        
        # Add conversation to RAG system
        memory_id = rag_memory_system.add_conversation_memory(
            user_id=user_id,
            user_message=user_message,
            assistant_response=assistant_response,
            model_id=model_id,
            importance=importance
        )
        
        return jsonify({
            'memory_id': memory_id,
            'status': 'added'
        }), 200
        
    except Exception as e:
        logger.error(f"Error adding conversation to RAG: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@rag_blueprint.route('/api/rag/sync', methods=['POST'])
def sync_rag_system():
    """Sync existing conversations with RAG system"""
    try:
        if not rag_memory_system:
            return jsonify({
                'error': 'RAG system not initialized'
            }), 400
        
        # Sync existing conversations
        synced_count = rag_memory_system.sync_rag_system()
        
        return jsonify({
            'synced_conversations': synced_count,
            'status': 'synced'
        }), 200
        
    except Exception as e:
        logger.error(f"Error syncing RAG system: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@rag_blueprint.route('/api/rag/initialize', methods=['POST'])
def initialize_rag():
    """Initialize or reinitialize the RAG system"""
    try:
        success = initialize_rag_system()
        
        if success:
            return jsonify({
                'status': 'initialized',
                'enabled': True
            }), 200
        else:
            return jsonify({
                'status': 'failed',
                'enabled': False,
                'error': 'RAG system initialization failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Error initializing RAG system: {e}")
        return jsonify({
            'error': str(e),
            'enabled': False
        }), 500

# Initialize RAG system when blueprint is loaded
initialize_rag_system()
