"""
app_rou@audio_bp.route('/api/audio/start', methods=['POST'])
def api_audio_start():
    ai_app = app_globals.ai_app
    app_state = app_globals.app_state
    ai_app.start_audio()
    return jsonify({'status': 'started', 'enabled': app_state['audio_enabled']})

@audio_bp.route('/api/audio/stop', methods=['POST'])
def api_audio_stop():
    ai_app = app_globals.ai_app
    app_state = app_globals.app_state
    ai_app.stop_audio()
    return jsonify({'status': 'stopped', 'enabled': app_state['audio_enabled']})

@audio_bp.route('/api/audio/status')
def api_audio_status():
    audio_pipeline = app_globals.audio_pipeline
    if audio_pipeline:
        return jsonify(audio_pipeline.get_status())
    else:
        return jsonify({'error': 'Audio pipeline not initialized'}), 500io-related Flask route definitions for the AI Companion backend.
"""
from flask import Blueprint, jsonify, request
import app_globals
import logging

audio_bp = Blueprint('audio', __name__)
logger = logging.getLogger(__name__)

@audio_bp.route('/api/audio/start', methods=['POST'])
def api_audio_start():
    ai_app.start_audio()
    return jsonify({'status': 'started', 'enabled': app_state['audio_enabled']})

@audio_bp.route('/api/audio/stop', methods=['POST'])
def api_audio_stop():
    ai_app.stop_audio()
    return jsonify({'status': 'stopped', 'enabled': app_state['audio_enabled']})

@audio_bp.route('/api/audio/status')
def api_audio_status():
    if audio_pipeline:
        return jsonify(audio_pipeline.get_status())
    else:
        return jsonify({'error': 'Audio pipeline not available'}), 503
