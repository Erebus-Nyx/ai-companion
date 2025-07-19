"""AI Companion Version Information"""

__version__ = "0.4.0"
__title__ = "AI Companion"
__description__ = "An interactive AI live2d chat with Live2D visual avatar, voice capabilities, and advanced AI integration"
__author__ = "AI Companion Team"
__email__ = "contact@ai2d_chat.com"
__license__ = "MIT"
__url__ = "https://github.com/Erebus-Nyx/ai2d_chat"

# API Version for compatibility tracking
API_VERSION = "v1"
API_VERSION_FULL = "1.0.0"

# Component versions
LIVE2D_INTEGRATION_VERSION = "0.4.0"
VAD_SYSTEM_VERSION = "0.4.0"
TTS_SYSTEM_VERSION = "0.4.0"
LLM_SYSTEM_VERSION = "0.4.0"

def get_version_info():
    """Return comprehensive version information."""
    return {
        "version": __version__,
        "api_version": API_VERSION_FULL,
        "title": __title__,
        "description": __description__,
        "components": {
            "live2d": LIVE2D_INTEGRATION_VERSION,
            "vad": VAD_SYSTEM_VERSION,
            "tts": TTS_SYSTEM_VERSION,
            "llm": LLM_SYSTEM_VERSION
        }
    }

def get_version_string():
    """Return a formatted version string."""
    return f"{__title__} v{__version__} (API {API_VERSION_FULL})"
