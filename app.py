# =============================================================================
# Imports & Logging
# =============================================================================
import logging
import asyncio
import json
import time
import logging
import os
import psutil
import signal
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading
import re

from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, Blueprint
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

# Base imports that should always work
try:
    from models.enhanced_llm_handler import EnhancedLLMHandler
except ImportError:
    from .models.enhanced_llm_handler import EnhancedLLMHandler

try:
    from models.tts_handler import TTSHandler
except ImportError:
    from .models.tts_handler import TTSHandler

try:
    from models.personality import PersonalitySystem
except ImportError:
    from .models.personality import PersonalitySystem

# Advanced imports with fallbacks
try:
    from models.memory_system import MemorySystem
except ImportError:
    try:
        from .models.memory_system import MemorySystem
    except ImportError:
        # Minimal fallback for MemorySystem
        class MemorySystem:
            def __init__(self, *args, **kwargs): pass
            def store_conversation(self, *args, **kwargs): return {}
            def get_relevant_memories(self, *args, **kwargs): return []

try:
    from databases.database_manager import DatabaseManager as DBManager
except ImportError:
    try:
        from .databases.database_manager import DatabaseManager as DBManager
    except ImportError:
        # Minimal fallback for DBManager
        class DBManager:
            def __init__(self, *args, **kwargs): pass
            def get_connection(self): return None

try:
    from databases.live2d_models_separated import Live2DModelManager
except ImportError:
    try:
        from .databases.live2d_models_separated import Live2DModelManager
    except ImportError:
        # Minimal fallback for Live2DModelManager
        class Live2DModelManager:
            def __init__(self, *args, **kwargs): pass
            def get_available_models(self): return []

try:
    from audio import AudioPipeline, create_basic_pipeline, AudioEvent, AudioPipelineState
except ImportError:
    try:
        from .audio import AudioPipeline, create_basic_pipeline, AudioEvent, AudioPipelineState
    except ImportError:
        # Minimal fallbacks for audio
        class AudioPipeline:
            def __init__(self, *args, **kwargs): pass
        def create_basic_pipeline(*args, **kwargs): return AudioPipeline()
        AudioEvent = type('AudioEvent', (), {})
        AudioPipelineState = type('AudioPipelineState', (), {})

try:
    from utils.system_detector import SystemDetector
except ImportError:
    try:
        from .utils.system_detector import SystemDetector
    except ImportError:
        # Minimal fallback for SystemDetector
        class SystemDetector:
            @staticmethod
            def get_system_info(): return {"platform": "unknown"}
            @staticmethod
            def get_hardware_info(): return {"cpu": "unknown", "memory": "unknown"}

try:
    from config.config_manager import ConfigManager
except ImportError:
    try:
        from .config.config_manager import ConfigManager
    except ImportError:
        # Minimal fallback for ConfigManager
        class ConfigManager:
            def __init__(self, *args, **kwargs): pass
            def load_config(self): return {"server": {"host": "0.0.0.0", "port": 19080, "dev_port": 19081}}

try:
    from utils.model_downloader import ModelDownloader
except ImportError:
    try:
        from .utils.model_downloader import ModelDownloader
    except ImportError:
        # Minimal fallback for ModelDownloader
        class ModelDownloader:
            def __init__(self, *args, **kwargs): pass
            def download_model(self, *args, **kwargs): return False

# API specification imports with fallbacks
try:
    from api.api_spec import get_openapi_spec, get_swagger_ui_html
except ImportError:
    try:
        from .api.api_spec import get_openapi_spec, get_swagger_ui_html
    except ImportError:
        # Minimal fallback
        def get_openapi_spec():
            return {"openapi": "3.0.0", "info": {"title": "AI Companion API", "version": "0.5.0a"}}
        def get_swagger_ui_html():
            return "<html><body><h1>API Documentation</h1><p>Use /api/spec for OpenAPI specification</p></body></html>"

# Route imports with fallbacks
try:
    from routes.app_routes_live2d import live2d_bp
except ImportError:
    try:
        from .routes.app_routes_live2d import live2d_bp
    except ImportError:
        live2d_bp = Blueprint('live2d', __name__)

try:
    from routes.app_routes_chat import chat_bp, chat_routes
except ImportError:
    try:
        from .routes.app_routes_chat import chat_bp
    except ImportError:
        chat_bp = Blueprint('chat', __name__)

try:
    from routes.app_routes_tts import tts_bp
except ImportError:
    try:
        from .routes.app_routes_tts import tts_bp
    except ImportError:
        tts_bp = Blueprint('tts', __name__)

try:
    from routes.app_routes_audio import audio_bp
except ImportError:
    try:
        from .routes.app_routes_audio import audio_bp
    except ImportError:
        audio_bp = Blueprint('audio', __name__)

try:
    from routes.app_routes_debug import debug_bp
except ImportError:
    try:
        from .routes.app_routes_debug import debug_bp
    except ImportError:
        debug_bp = Blueprint('debug', __name__)

try:
    from routes.app_routes_system import system_bp
except ImportError:
    try:
        from .routes.app_routes_system import system_bp
    except ImportError:
        system_bp = Blueprint('system', __name__)

try:
    from routes.app_routes_characters import characters_routes
except ImportError:
    try:
        from .routes.app_routes_characters import characters_routes
    except ImportError:
        characters_routes = Blueprint('characters_routes', __name__)

try:
    from routes.app_routes_users import users_routes
except ImportError:
    try:
        from .routes.app_routes_users import users_routes
    except ImportError:
        users_routes = Blueprint('users_routes', __name__)

try:
    from routes.app_routes_rag import rag_blueprint
except ImportError:
    try:
        from .routes.app_routes_rag import rag_blueprint
    except ImportError:
        rag_blueprint = Blueprint('rag', __name__)

try:
    import app_globals
except ImportError:
    try:
        from . import app_globals
    except ImportError:
        # Minimal fallback for app_globals
        class AppGlobals:
            def __init__(self):
                self.socketio = None
                self.app_state = {}
        app_globals = AppGlobals()

# Configure logging with reduced verbosity
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Reduce verbosity for specific modules
logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Reduce Flask request logs
logging.getLogger('socketio').setLevel(logging.WARNING)  # Reduce SocketIO logs
logging.getLogger('engineio').setLevel(logging.WARNING)  # Reduce EngineIO logs
logging.getLogger('urllib3').setLevel(logging.WARNING)  # Reduce HTTP logs

# =============================================================================
# Flask App & Global State
# =============================================================================
app = Flask(__name__, 
           template_folder='web/templates',
           static_folder='web/static')
app.config['SECRET_KEY'] = 'ai2d_chat-secret-key-change-in-production'
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", 
                   async_mode='threading',
                   logger=False, engineio_logger=False)

# Set globals for blueprints
app_globals.socketio = socketio

db_manager = None
llm_handler = None
memory_system = None
tts_handler = None
personality_system = None
audio_pipeline = None
system_detector = None
model_downloader = None
live2d_manager = None

app_state = {
    'is_initializing': True,
    'initialization_progress': 0,
    'initialization_status': 'Starting...',
    'audio_enabled': False,
    'connected_clients': 0,
    'last_interaction': None,
    'system_info': {}
}

# Register the Live2D blueprint
app.register_blueprint(live2d_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(chat_routes)
app.register_blueprint(tts_bp)
app.register_blueprint(audio_bp)
app.register_blueprint(debug_bp)
app.register_blueprint(system_bp)
app.register_blueprint(characters_routes)
app.register_blueprint(users_routes)
app.register_blueprint(rag_blueprint)

# Register autonomous avatar blueprint
try:
    from routes.app_routes_autonomous import autonomous_bp
    app.register_blueprint(autonomous_bp)
    print("✅ Autonomous avatar routes registered")
except ImportError as e:
    print(f"⚠️ Could not register autonomous routes: {e}")

# Set app_state to globals for blueprint access
app_globals.app_state = app_state

# =============================================================================
# Main Routes
# =============================================================================
@app.route('/')
def index():
    """Serve the main application page - redirects to Live2D interface"""
    return send_from_directory('web/static', 'live2d_pixi.html')

@app.route('/live2d')
def live2d_interface():
    """Serve the Live2D interface"""
    return send_from_directory('web/static', 'live2d_pixi.html')

@app.route('/live2d_models/<path:filename>')
def serve_live2d_models(filename):
    """Serve Live2D models from user data directory"""
    user_data_dir = os.path.expanduser("~/.local/share/ai2d_chat")
    live2d_models_path = os.path.join(user_data_dir, "live2d_models")
    return send_from_directory(live2d_models_path, filename)

@app.route('/api/docs')
def api_docs():
    """Serve Swagger UI documentation"""
    json_param = request.args.get('json')
    if json_param:
        return jsonify(get_openapi_spec())
    return get_swagger_ui_html()

@app.route('/docs') 
def docs_redirect():
    """Redirect /docs to /api/docs"""
    return redirect('/api/docs')

@app.route('/api/status')
def api_status():
    """Get application status"""
    return jsonify({
        'status': 'running',
        'initialized': not app_state['is_initializing'],
        'initialization_progress': app_state['initialization_progress'],
        'initialization_status': app_state['initialization_status'],
        'connected_clients': app_state['connected_clients'],
        'audio_enabled': app_state['audio_enabled']
    })

# Import SocketIO event handlers to register them
from routes import socketio_handlers

# Setup autonomous avatar SocketIO handlers
try:
    from routes.app_routes_autonomous import setup_autonomous_socketio_handlers
    setup_autonomous_socketio_handlers(socketio)
    print("✅ Autonomous avatar SocketIO handlers registered")
except ImportError as e:
    print(f"⚠️ Could not setup autonomous SocketIO handlers: {e}")

# =============================================================================
# Helper Functions
# =============================================================================
def _extract_emotion_tags(response):
    """Extract emotion tags from the LLM or API response (robust for string or dict)."""
    if isinstance(response, dict) and 'emotions' in response:
        return response['emotions']
    if isinstance(response, str):
        return re.findall(r'\\*([^*]+)\\*', response)
    if isinstance(response, dict) and 'response' in response:
        return re.findall(r'\\*([^*]+)\\*', response['response'])
    return []

def _determine_primary_emotion(emotion_tags, user_input, response):
    """Determine the primary emotion from tags, user input, or response context (priority-based)."""
    emotion_priority = {
        'excited': 10, 'happy': 9, 'joyful': 9, 'cheerful': 8,
        'surprised': 7, 'amazed': 7,
        'empathetic': 8, 'supportive': 7, 'caring': 7,
        'sad': 6, 'disappointed': 5,
        'curious': 4, 'thoughtful': 3,
        'neutral': 2, 'calm': 2
    }
    if emotion_tags:
        return max(emotion_tags, key=lambda e: emotion_priority.get(e.lower(), 0))
    if isinstance(response, dict) and 'primary_emotion' in response:
        return response['primary_emotion']
    if isinstance(response, str):
        tags = re.findall(r'\\*([^*]+)\\*', response)
        if tags:
            return max(tags, key=lambda e: emotion_priority.get(e.lower(), 0))
    return 'neutral'

def _calculate_emotion_intensity(emotion_tags, bond_level):
    """Calculate emotion intensity based on tags and bond level (float 0-1, with scaling)."""
    base_intensity = len(emotion_tags) * 0.3
    bond_multiplier = min(bond_level / 5.0, 2.0)
    final_intensity = min(base_intensity * bond_multiplier, 1.0)
    if any(e in ['excited', 'amazed', 'shocked', 'celebratory'] for e in emotion_tags):
        final_intensity = min(final_intensity + 0.4, 1.0)
    return final_intensity

def _get_dominant_traits(personality_data):
    """Extract dominant personality traits from personality data."""
    if isinstance(personality_data, dict) and 'dominant_traits' in personality_data:
        return personality_data['dominant_traits']
    return []

# =============================================================================
# Main Application Class
# =============================================================================
class AICompanionApp:
    """Main application class"""
    
    def __init__(self):
        self.app = app
        self.socketio = socketio
        self.is_running = False
        
    async def initialize_components(self):
        """Initialize all AI live2d chat components"""
        global db_manager, llm_handler, tts_handler, personality_system
        global audio_pipeline, system_detector, model_downloader, app_state, live2d_manager
        
        try:
            # Update initialization status
            app_state['initialization_status'] = 'Detecting system capabilities...'
            app_state['initialization_progress'] = 10
            self._broadcast_status()
            
            # Initialize system detector
            system_detector = SystemDetector()
            app_globals.system_detector = system_detector
            system_info = system_detector.get_system_info()
            app_state['system_info'] = system_info
            logger.info(f"System detected: {system_info['tier']} tier")
            
            # Update status
            app_state['initialization_status'] = 'Setting up database...'
            app_state['initialization_progress'] = 20
            self._broadcast_status()
            
            # Initialize database
            db_manager = DBManager()
            app_globals.db_manager = db_manager
            # Database is already initialized in the constructor
            logger.info("Database initialized")
            
            # Initialize Live2D model manager
            global live2d_manager
            # Use separated databases architecture - no need to pass db_path
            live2d_manager = Live2DModelManager()
            app_globals.live2d_manager = live2d_manager
            # Use user data directory for Live2D models
            user_data_dir = os.path.expanduser("~/.local/share/ai2d_chat")
            live2d_models_path = os.path.join(user_data_dir, "live2d_models")
            live2d_manager.scan_models_directory(live2d_models_path)
            logger.info(f"Live2D model manager initialized with separated databases and models scanned from: {live2d_models_path}")
            
            # Update status
            app_state['initialization_status'] = 'Downloading models...'
            app_state['initialization_progress'] = 30
            self._broadcast_status()
            
            # Initialize model downloader and download models
            model_downloader = ModelDownloader()  # Use default user data directories
            app_globals.model_downloader = model_downloader
            await self._download_models_async()
            
            # Update status
            app_state['initialization_status'] = 'Loading personality system...'
            app_state['initialization_progress'] = 50
            self._broadcast_status()
            
            # Initialize personality system
            personality_system = PersonalitySystem(db_manager)
            app_globals.personality_system = personality_system
            logger.info("Personality system initialized")
            
            # Update status
            app_state['initialization_status'] = 'Loading language model...'
            app_state['initialization_progress'] = 65
            self._broadcast_status()
            
            # Initialize LLM handler
            llm_handler = EnhancedLLMHandler(db_manager=db_manager)
            app_globals.llm_handler = llm_handler
            success = llm_handler.initialize_model()
            if not success:
                logger.error("Failed to initialize LLM model")
            else:
                logger.info("✅ Enhanced LLM handler initialized")
            
            # Initialize memory system
            memory_system = MemorySystem(db_manager)
            app_globals.memory_system = memory_system
            logger.info("✅ Memory system initialized")
            
            # Update status
            app_state['initialization_status'] = 'Loading text-to-speech...'
            app_state['initialization_progress'] = 80
            self._broadcast_status()
            
            # Initialize TTS handler
            tts_handler = TTSHandler()
            app_globals.tts_handler = tts_handler
            success = tts_handler.initialize_model()
            if not success:
                logger.error("Failed to initialize TTS model")
            else:
                logger.info("✅ TTS handler initialized")
            
            # Update status
            app_state['initialization_status'] = 'Setting up audio pipeline...'
            app_state['initialization_progress'] = 90
            self._broadcast_status()
            
            # Initialize audio pipeline
            audio_pipeline = create_basic_pipeline(["hey nyx", "nyx", "companion"])
            app_globals.audio_pipeline = audio_pipeline
            self._setup_audio_callbacks()
            logger.info("Audio pipeline initialized")
            
            # Final update
            app_state['initialization_status'] = 'Ready!'
            app_state['initialization_progress'] = 100
            app_state['is_initializing'] = False
            self._broadcast_status()
            
            logger.info("AI Companion fully initialized and ready")
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            app_state['initialization_status'] = f'Error: {str(e)}'
            app_state['is_initializing'] = False
            self._broadcast_status()
            raise
            
    async def _download_models_async(self):
        """Download required models asynchronously"""
        try:
            # Download recommended models based on system
            results = await asyncio.to_thread(
                model_downloader.download_recommended_models
            )
            logger.info(f"Models downloaded: {results}")
            
        except Exception as e:
            logger.error(f"Model download error: {e}")
            # Continue without models for graceful degradation
            
    def _setup_audio_callbacks(self):
        """Setup audio pipeline event callbacks"""
        if audio_pipeline:
            audio_pipeline.add_event_callback('wake_word_detected', self._on_wake_word)
            audio_pipeline.add_event_callback('transcription_ready', self._on_transcription)
            audio_pipeline.add_event_callback('state_changed', self._on_audio_state_change)
            audio_pipeline.add_event_callback('error', self._on_audio_error)
            
    def _on_wake_word(self, event: AudioEvent):
        """Handle wake word detection"""
        logger.info(f"Wake word detected: {event.data}")
        socketio.emit('wake_word_detected', {
            'wake_word': event.data['wake_word'],
            'timestamp': event.timestamp
        })
        
    def _on_transcription(self, event: AudioEvent):
        """Handle speech transcription"""
        result = event.data['result']
        logger.info(f"Transcription: {result.text}")
        
        if result.text.strip():
            # Process the transcribed text as user input
            socketio.start_background_task(self._process_user_input_async, result.text)
        
    def _on_audio_state_change(self, event: AudioEvent):
        """Handle audio pipeline state changes"""
        socketio.emit('audio_state_changed', {
            'old_state': event.data['old_state'],
            'new_state': event.data['new_state'],
            'timestamp': event.timestamp
        })
        
    def _on_audio_error(self, event: AudioEvent):
        """Handle audio pipeline errors"""
        logger.error(f"Audio error: {event.data}")
        socketio.emit('audio_error', {
            'error': event.data,
            'timestamp': event.timestamp
        })
        
    def _process_user_input_async(self, user_input: str):
        """Process user input asynchronously"""
        try:
            # Update personality based on input
            if personality_system:
                personality_system.update_traits(user_input)
                
            # Get LLM response
            if llm_handler:
                # Use the synchronous method instead of async
                response = llm_handler.generate_response(user_input)
                
                # Store conversation
                if db_manager:
                    db_manager.add_conversation("default_user", "user", user_input, None, None)
                    db_manager.add_conversation("default_user", "assistant", response, None, None)
                
                # Emit response to clients
                socketio.emit('ai_response', {
                    'user_input': user_input,
                    'response': response,
                    'timestamp': time.time(),
                    'personality_state': personality_system.get_personality_summary() if personality_system else None
                })
                
                # Generate TTS if enabled
                if tts_handler:
                    self._generate_tts_sync(response)
                    
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            socketio.emit('error', {'message': str(e)})
            
    def _generate_tts_sync(self, text: str):
        """Generate TTS audio synchronously"""
        try:
            if tts_handler and hasattr(tts_handler, 'synthesize_speech'):
                audio_data = tts_handler.synthesize_speech(text)
                if audio_data:
                    # Emit audio data to clients
                    socketio.emit('tts_audio', {
                        'audio_data': audio_data,
                        'text': text,
                        'timestamp': time.time()
                    })
        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            
    async def _generate_tts_async(self, text: str):
        """Generate TTS audio asynchronously"""
        try:
            if tts_handler:
                audio_data = await tts_handler.synthesize_async(text)
                if audio_data:
                    # Emit audio data to clients
                    socketio.emit('tts_audio', {
                        'audio_data': audio_data,
                        'text': text,
                        'timestamp': time.time()
                    })
        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            
    def _broadcast_status(self):
        """Broadcast current status to all clients"""
        socketio.emit('status_update', app_state)
        
    def start_audio(self):
        """Start audio processing"""
        if audio_pipeline and not app_state['audio_enabled']:
            audio_pipeline.start()
            app_state['audio_enabled'] = True
            logger.info("Audio processing started")
            
    def stop_audio(self):
        """Stop audio processing"""
        if audio_pipeline and app_state['audio_enabled']:
            audio_pipeline.stop()
            app_state['audio_enabled'] = False
            logger.info("Audio processing stopped")

# =============================================================================
# Process Management
# =============================================================================
def kill_existing_instances():
    """Kill any existing instances of the Flask app running on the same port"""
    current_pid = os.getpid()
    
    # Don't run this function if we're likely in a Flask reloader subprocess
    # Flask reloader creates a subprocess that we don't want to kill
    try:
        import sys
        if '--reloader' in sys.argv or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            logger.info("Running in Flask reloader subprocess, skipping process cleanup")
            return
    except Exception:
        pass
    
    # Get port from config instead of hardcoding
    try:
        from config.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.load_config()
        server_config = config.get('server', {})
        
        # Use dev_port in dev mode, regular port otherwise
        is_dev_mode = config_manager.is_dev_mode
        if is_dev_mode:
            port = server_config.get('dev_port', server_config.get('port', 19080) + 1)
        else:
            port = server_config.get('port', 19080)
    except Exception:
        port = 19080  # Fallback to default from config.yaml
        
    killed_count = 0
    
    try:
        # First, try to find processes using lsof (more reliable for port detection)
        try:
            import subprocess
            result = subprocess.run(['lsof', '-i', f':{port}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = int(parts[1])
                            if pid != current_pid:
                                try:
                                    proc = psutil.Process(pid)
                                    # Double-check this isn't our current process
                                    if proc.pid == current_pid:
                                        continue
                                        
                                    logger.info(f"Killing process using port {port}: PID {pid}, CMD: {' '.join(proc.cmdline())}")
                                    
                                    # Try graceful termination first
                                    proc.terminate()
                                    try:
                                        proc.wait(timeout=3)
                                    except psutil.TimeoutExpired:
                                        # Force kill if graceful termination fails
                                        proc.kill()
                                        proc.wait(timeout=1)
                                    
                                    killed_count += 1
                                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                                    continue
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            # lsof not available or failed, fall back to psutil method
            pass
        
        # Fallback: Find processes using psutil (less reliable for port detection)
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'connections']):
            try:
                # Skip current process
                if proc.info['pid'] == current_pid:
                    continue
                
                # Check if process is using our port or is a Flask/Python process running our app
                connections = proc.info.get('connections', [])
                cmdline = proc.info.get('cmdline', [])
                
                # Check for port usage
                port_match = any(
                    hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == port
                    for conn in connections
                )
                
                # Check for Flask app process (look for app.py in command line)
                # But exclude current process even if it matches
                app_match = any(
                    'app.py' in str(arg) for arg in cmdline
                ) if cmdline else False
                
                if (port_match or app_match) and proc.info['pid'] != current_pid:
                    logger.info(f"Killing existing instance: PID {proc.info['pid']}, CMD: {' '.join(cmdline) if cmdline else 'N/A'}")
                    
                    # Try graceful termination first
                    try:
                        proc.terminate()
                        proc.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        # Force kill if graceful termination fails
                        proc.kill()
                        proc.wait(timeout=1)
                    
                    killed_count += 1
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process already dead or no permission
                continue
                
    except Exception as e:
        logger.warning(f"Error while killing existing instances: {e}")
    
    if killed_count > 0:
        logger.info(f"Killed {killed_count} existing instance(s)")
        # Give a moment for ports to be released
        time.sleep(2)
    else:
        logger.info("No existing instances found to kill")

# =============================================================================
# Application Instance
# =============================================================================
ai_app = AICompanionApp()

# Set global for blueprints
app_globals.ai_app = ai_app

# =============================================================================
# SocketIO Event Handlers
# =============================================================================
# Move SocketIO event handlers to a new module for further modularization
# Remove all @socketio.on handlers from app.py

# =============================================================================
# Initialization & Entrypoint
# =============================================================================
def initialize_app():
    """Initialize the application"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(ai_app.initialize_components())
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
    finally:
        loop.close()

# Run initialization in background thread only when imported, not when running as main
if __name__ != '__main__':
    # When imported, start initialization in background
    init_thread = threading.Thread(target=initialize_app, daemon=True)
    init_thread.start()
else:
    # When running as main, don't auto-initialize in background
    pass

def run_server():
    """Entry point for pipx installation to run the server."""
    # Load configuration first
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    # Get server settings from config
    server_config = config.get('server', {})
    host = server_config.get('host', '0.0.0.0')
    
    # Determine if we're running in development mode
    is_dev_mode = config_manager.is_dev_mode
    
    if is_dev_mode:
        # Development mode: use dev_port
        port = server_config.get('dev_port', server_config.get('port', 19080) + 1)
        debug = True  # Always use debug in dev mode
        logger.info("🔧 Running in DEVELOPMENT mode")
        # Don't kill existing instances in dev mode - Flask debug mode handles this
    else:
        # Production mode: use regular port
        port = server_config.get('port', 19080)
        debug = server_config.get('debug', False)
        logger.info("📦 Running in PRODUCTION mode")
        # Only kill existing instances in production mode
        kill_existing_instances()
    
    # Initialize the app
    initialize_app()
    
    # Run the application
    logger.info(f"Starting AI Companion on http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)

def main():
    """Main entry point for the application."""
    # Check for first-time installation and run setup if needed
    try:
        from config.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        # Check if this is a fresh installation
        config_path = config_manager.get_config_path()
        if not config_path.exists():
            print("🚀 First-time installation detected - running initial setup...")
            
            # Run post-install hook to set up configuration
            try:
                from scripts.install_command import post_install_hook
                post_install_hook()
            except ImportError:
                # Fallback to basic config setup
                config_manager = ConfigManager.setup_fresh_installation(clean_databases=True)
                print("✅ Basic configuration setup completed!")
                print("🔧 Run 'ai2d_chat-setup' to complete setup with models and Live2D")
    
    except Exception as e:
        print(f"⚠️  Setup check failed: {e}")
        print("🔧 Continuing with server startup...")
    
    # Run the server
    run_server()

if __name__ == '__main__':
    run_server()
