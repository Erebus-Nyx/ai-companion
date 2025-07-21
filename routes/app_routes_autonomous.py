"""
Autonomous Avatar Routes for Flask Backend
==========================================

Handles autonomous avatar conversations and WebSocket events
for avatar-to-avatar interaction without user input.
"""

from flask import Blueprint, request, jsonify
from flask_socketio import emit
import logging
import asyncio
import time
from datetime import datetime
import app_globals

logger = logging.getLogger(__name__)

# Blueprint for autonomous avatar routes
autonomous_bp = Blueprint('autonomous', __name__)

# Global autonomous manager instance
autonomous_manager = None

@autonomous_bp.route('/api/autonomous/status', methods=['GET'])
def get_autonomous_status():
    """Get status of autonomous avatar system"""
    try:
        global autonomous_manager
        
        if not autonomous_manager:
            return jsonify({
                'enabled': False,
                'status': 'not_initialized',
                'active_avatars': 0,
                'last_conversation': None
            })
        
        # Get active avatars from live2d manager if available
        active_avatars = []
        if hasattr(app_globals, 'live2d_manager'):
            # This would integrate with your existing live2d system
            active_avatars = ['haruka', 'haru', 'epsilon']  # Mock for now
        
        return jsonify({
            'enabled': autonomous_manager.is_running if autonomous_manager else False,
            'status': 'running' if (autonomous_manager and autonomous_manager.is_running) else 'stopped',
            'active_avatars': len(active_avatars),
            'avatar_names': active_avatars,
            'last_user_interaction': getattr(autonomous_manager, 'last_user_interaction', time.time()),
            'autonomous_conversations_count': 0  # Would track actual count
        })
        
    except Exception as e:
        logger.error(f"Error getting autonomous status: {e}")
        return jsonify({'error': str(e)}), 500

@autonomous_bp.route('/api/autonomous/enable', methods=['POST'])
def enable_autonomous_system():
    """Enable autonomous avatar conversations"""
    try:
        global autonomous_manager
        
        # Initialize if not already done
        if not autonomous_manager:
            autonomous_manager = initialize_autonomous_manager()
        
        if autonomous_manager and not autonomous_manager.is_running:
            autonomous_manager.start_autonomous_system()
            
            return jsonify({
                'status': 'enabled',
                'message': 'Autonomous avatar conversations enabled'
            })
        else:
            return jsonify({
                'status': 'already_enabled',
                'message': 'Autonomous system already running'
            })
            
    except Exception as e:
        logger.error(f"Error enabling autonomous system: {e}")
        return jsonify({'error': str(e)}), 500

@autonomous_bp.route('/api/autonomous/disable', methods=['POST'])
def disable_autonomous_system():
    """Disable autonomous avatar conversations"""
    try:
        global autonomous_manager
        
        if autonomous_manager and autonomous_manager.is_running:
            autonomous_manager.stop_autonomous_system()
            
            return jsonify({
                'status': 'disabled',
                'message': 'Autonomous avatar conversations disabled'
            })
        else:
            return jsonify({
                'status': 'already_disabled',
                'message': 'Autonomous system not running'
            })
            
    except Exception as e:
        logger.error(f"Error disabling autonomous system: {e}")
        return jsonify({'error': str(e)}), 500

def initialize_autonomous_manager():
    """Initialize the autonomous avatar manager"""
    try:
        from models.autonomous_avatar_manager import create_autonomous_avatar_manager
        
        # Get required dependencies from app_globals
        chat_manager = getattr(app_globals, 'chat_manager', None)
        llm_handler = getattr(app_globals, 'llm_handler', None)
        
        if not llm_handler:
            logger.warning("LLM handler not available for autonomous system")
            return None
            
        manager = create_autonomous_avatar_manager(chat_manager, llm_handler)
        logger.info("🤖 Autonomous avatar manager initialized")
        return manager
        
    except Exception as e:
        logger.error(f"Failed to initialize autonomous manager: {e}")
        return None

# SocketIO event handlers for autonomous system
def setup_autonomous_socketio_handlers(socketio):
    """Setup SocketIO handlers for autonomous avatar system"""
    
    @socketio.on('enable_autonomous_avatars')
    def handle_enable_autonomous(data):
        """Handle request to enable/disable autonomous avatars"""
        try:
            global autonomous_manager
            
            enabled = data.get('enabled', False)
            
            if enabled:
                if not autonomous_manager:
                    autonomous_manager = initialize_autonomous_manager()
                
                if autonomous_manager:
                    autonomous_manager.start_autonomous_system()
                    emit('autonomous_status_changed', {
                        'enabled': True,
                        'message': 'Autonomous conversations enabled'
                    })
                    logger.info("🤖 Autonomous system enabled via SocketIO")
            else:
                if autonomous_manager:
                    autonomous_manager.stop_autonomous_system()
                    emit('autonomous_status_changed', {
                        'enabled': False,
                        'message': 'Autonomous conversations disabled'
                    })
                    logger.info("🤖 Autonomous system disabled via SocketIO")
                    
        except Exception as e:
            logger.error(f"Error handling autonomous enable/disable: {e}")
            emit('error', {'message': 'Failed to toggle autonomous system'})
    
    @socketio.on('user_activity')
    def handle_user_activity(data):
        """Handle user activity updates to pause autonomous conversations"""
        try:
            global autonomous_manager
            
            if autonomous_manager:
                autonomous_manager.update_user_interaction_time()
                logger.debug("User activity updated, autonomous system paused")
                
        except Exception as e:
            logger.error(f"Error handling user activity: {e}")
    
    @socketio.on('get_autonomous_status')
    def handle_get_autonomous_status():
        """Send autonomous system status to client"""
        try:
            global autonomous_manager
            
            status = {
                'enabled': autonomous_manager.is_running if autonomous_manager else False,
                'active_avatars': 3,  # Mock - would get from actual system
                'last_user_activity': time.time()
            }
            
            emit('autonomous_status', status)
            
        except Exception as e:
            logger.error(f"Error getting autonomous status: {e}")
            emit('error', {'message': 'Failed to get autonomous status'})

# Enhanced autonomous message emission
async def emit_autonomous_message(avatar_data, message, metadata=None):
    """Emit autonomous message via SocketIO to all clients"""
    try:
        if not hasattr(app_globals, 'socketio') or not app_globals.socketio:
            logger.warning("SocketIO not available for autonomous message emission")
            return
        
        message_data = {
            'avatar': {
                'id': avatar_data['id'],
                'name': avatar_data['name'],
                'displayName': avatar_data.get('displayName', avatar_data['name'])
            },
            'message': message,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'is_autonomous': True,
                'emotion': metadata.get('emotion', 'neutral') if metadata else 'neutral',
                **(metadata or {})
            }
        }
        
        # Emit to all connected clients
        app_globals.socketio.emit('autonomous_avatar_message', message_data)
        logger.info(f"📡 Emitted autonomous message from {avatar_data['name']}")
        
    except Exception as e:
        logger.error(f"Failed to emit autonomous message: {e}")

async def emit_self_reflection(avatar_data, message, metadata=None):
    """Emit self-reflection message via SocketIO"""
    try:
        if not hasattr(app_globals, 'socketio') or not app_globals.socketio:
            logger.warning("SocketIO not available for self-reflection emission")
            return
        
        reflection_data = {
            'avatar': {
                'id': avatar_data['id'],
                'name': avatar_data['name'],
                'displayName': avatar_data.get('displayName', avatar_data['name'])
            },
            'message': message,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'is_self_reflection': True,
                'emotion': metadata.get('emotion', 'thoughtful') if metadata else 'thoughtful',
                **(metadata or {})
            }
        }
        
        app_globals.socketio.emit('avatar_self_reflection', reflection_data)
        logger.info(f"🧠 Emitted self-reflection from {avatar_data['name']}")
        
    except Exception as e:
        logger.error(f"Failed to emit self-reflection: {e}")

# Auto-initialization when Flask app starts
def initialize_autonomous_system_on_startup():
    """Initialize autonomous system when Flask app starts"""
    try:
        global autonomous_manager
        
        # Check if cross-avatar interactions are enabled in config
        from config.config_manager import is_cross_avatar_enabled
        
        if is_cross_avatar_enabled():
            autonomous_manager = initialize_autonomous_manager()
            
            if autonomous_manager:
                # Auto-enable if multiple avatars are available
                # This would check actual avatar availability
                available_avatars = 3  # Mock count
                
                if available_avatars >= 2:
                    autonomous_manager.start_autonomous_system()
                    logger.info(f"🤖 Auto-enabled autonomous system ({available_avatars} avatars available)")
                else:
                    logger.info("🤖 Autonomous system initialized but not started (need 2+ avatars)")
            else:
                logger.warning("🤖 Failed to initialize autonomous system")
        else:
            logger.info("🤖 Cross-avatar interactions disabled in config")
            
    except Exception as e:
        logger.error(f"Error during autonomous system startup: {e}")

# Export functions for app integration
__all__ = [
    'autonomous_bp',
    'setup_autonomous_socketio_handlers', 
    'initialize_autonomous_system_on_startup',
    'emit_autonomous_message',
    'emit_self_reflection'
]
