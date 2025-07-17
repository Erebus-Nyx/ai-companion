"""
app_routes_system.py
System information and status endpoints for the AI Companion backend.
"""
import time
import psutil
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

import app_globals

# Import version information
try:
    from __version__ import get_version_info, get_version_string, __version__, API_VERSION_FULL
except ImportError:
    # Fallback for development
    __version__ = "0.4.0"
    API_VERSION_FULL = "1.0.0"
    def get_version_info():
        return {
            "version": __version__,
            "api_version": API_VERSION_FULL,
            "title": "AI Companion",
            "description": "An interactive AI companion with Live2D visual avatar"
        }
    def get_version_string():
        return f"AI Companion v{__version__}"

system_bp = Blueprint('system', __name__)
logger = logging.getLogger(__name__)

# Track server start time
SERVER_START_TIME = time.time()

@system_bp.route('/api/system/version', methods=['GET'])
def api_system_version():
    """Get comprehensive version information."""
    try:
        version_info = get_version_info()
        return jsonify(version_info)
    except Exception as e:
        logger.error(f"Error getting version info: {e}")
        return jsonify({
            "error": "Failed to get version information",
            "version": __version__,
            "api_version": API_VERSION_FULL
        }), 500

@system_bp.route('/api/system/status', methods=['GET'])
def api_system_status():
    """Get system health and status information."""
    try:
        # Calculate uptime
        uptime = time.time() - SERVER_START_TIME
        
        # Get memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Get loaded models
        models_loaded = []
        if hasattr(app_globals, 'live2d_manager') and app_globals.live2d_manager:
            try:
                # This would depend on your Live2D manager implementation
                models_loaded = getattr(app_globals.live2d_manager, 'loaded_models', [])
            except:
                pass
        
        # Check component status
        components_status = {}
        
        # Check LLM handler
        if hasattr(app_globals, 'llm_handler') and app_globals.llm_handler:
            components_status['llm'] = 'loaded'
        else:
            components_status['llm'] = 'not_loaded'
        
        # Check TTS handler
        if hasattr(app_globals, 'tts_handler') and app_globals.tts_handler:
            components_status['tts'] = 'loaded'
        else:
            components_status['tts'] = 'not_loaded'
        
        # Check audio pipeline
        if hasattr(app_globals, 'audio_pipeline') and app_globals.audio_pipeline:
            components_status['audio'] = 'loaded'
        else:
            components_status['audio'] = 'not_loaded'
        
        # Check Live2D manager
        if hasattr(app_globals, 'live2d_manager') and app_globals.live2d_manager:
            components_status['live2d'] = 'loaded'
        else:
            components_status['live2d'] = 'not_loaded'
        
        status_data = {
            "status": "running",
            "uptime": round(uptime, 2),
            "timestamp": datetime.now().isoformat(),
            "version": __version__,
            "api_version": API_VERSION_FULL,
            "memory_usage": {
                "rss": memory_info.rss,
                "vms": memory_info.vms,
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2)
            },
            "components": components_status,
            "models_loaded": models_loaded,
            "system": {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "memory_percent": psutil.virtual_memory().percent
            }
        }
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            "error": "Failed to get system status",
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }), 500

@system_bp.route('/api/system/health', methods=['GET'])
def api_system_health():
    """Simple health check endpoint."""
    try:
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": __version__
        })
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@system_bp.route('/api/system/info', methods=['GET'])
def api_system_info():
    """Get general system information."""
    try:
        info = {
            "name": "AI Companion",
            "version": __version__,
            "api_version": API_VERSION_FULL,
            "description": "Interactive AI companion with Live2D visual avatar",
            "features": [
                "Live2D Visual Avatar",
                "Voice Activity Detection",
                "Text-to-Speech with Emotions",
                "Local LLM Processing",
                "Real-time WebSocket Communication",
                "Enhanced Audio Pipeline"
            ],
            "endpoints": {
                "base_url": "http://localhost:19443",
                "live2d_interface": "http://localhost:19443/live2d",
                "api_docs": "http://localhost:19443/api/system/version"
            }
        }
        
        return jsonify(info)
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({
            "error": "Failed to get system information"
        }), 500
