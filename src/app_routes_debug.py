"""
app_routes_debug.py
Debug and legacy Flask route definitions for the AI Companion backend.
"""
from flask import Blueprint, jsonify, request, send_from_directory
import app_globals
import logging

debug_bp = Blueprint('debug', __name__)
logger = logging.getLogger(__name__)

@debug_bp.route('/get_personality', methods=['GET'])
def get_personality():
    personality_system = app_globals.personality_system
    if personality_system:
        traits = personality_system.get_traits()
        return jsonify(traits)
    else:
        return jsonify({'error': 'Personality system not available'}), 503

# ...add other debug/legacy endpoints as needed...
