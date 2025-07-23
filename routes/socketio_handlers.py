"""
socketio_handlers.py
SocketIO event handlers for the AI Companion backend.
"""
from flask_socketio import emit
from app_globals import socketio, ai_app, app_state, audio_pipeline
import time
import logging

logger = logging.getLogger(__name__)

# Import autonomous handlers
try:
    from routes.app_routes_autonomous import setup_autonomous_socketio_handlers
    autonomous_handlers_available = True
except ImportError:
    autonomous_handlers_available = False
    logger.warning("Autonomous SocketIO handlers not available")

@socketio.on('connect')
def handle_connect():
    app_state['connected_clients'] += 1
    emit('status_update', app_state)
    logger.info(f"Client connected. Total clients: {app_state['connected_clients']}")

@socketio.on('disconnect')
def handle_disconnect():
    app_state['connected_clients'] = max(0, app_state['connected_clients'] - 1)
    logger.info(f"Client disconnected. Total clients: {app_state['connected_clients']}")

@socketio.on('send_message')
def handle_message(data):
    if app_state['is_initializing']:
        emit('error', {'message': 'System is initializing'})
        return
    user_input = data.get('message', '').strip()
    if user_input:
        app_state['last_interaction'] = time.time()
        socketio.start_background_task(ai_app._process_user_input_async, user_input)

@socketio.on('chat_message')
def handle_chat_message(data):
    if app_state['is_initializing']:
        emit('error', {'message': 'System is initializing'})
        return
    user_input = data.get('message', '').strip()
    if user_input:
        app_state['last_interaction'] = time.time()
        socketio.start_background_task(ai_app._process_user_input_async, user_input)

@socketio.on('start_audio')
def handle_start_audio():
    ai_app.start_audio()
    emit('audio_status', {'enabled': app_state['audio_enabled']})

@socketio.on('stop_audio')
def handle_stop_audio():
    ai_app.stop_audio()
    emit('audio_status', {'enabled': app_state['audio_enabled']})

@socketio.on('force_listen')
def handle_force_listen():
    if audio_pipeline:
        audio_pipeline.force_listen()
        emit('audio_status', {'listening': True})

# Initialize autonomous SocketIO handlers
def init_socketio_handlers():
    """Initialize all SocketIO handlers including autonomous ones"""
    if autonomous_handlers_available:
        try:
            setup_autonomous_socketio_handlers(socketio)
            logger.info("🤖 Autonomous SocketIO handlers initialized")
        except Exception as e:
            logger.error(f"Failed to setup autonomous handlers: {e}")
    else:
        logger.warning("Autonomous handlers not available")
