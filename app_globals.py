"""
app_globals.py
Shared global state for the AI Companion Flask app.
"""
# This file is for globals that need to be imported by route blueprints

socketio = None
ai_app = None
db_manager = None
llm_handler = None
memory_system = None
tts_handler = None
personality_system = None
audio_pipeline = None
system_detector = None
model_downloader = None
live2d_manager = None

# Currently loaded Live2D models (updated by frontend via SocketIO)
loaded_models = []

# Import app_state from app.py to avoid circular import issues
app_state = None
