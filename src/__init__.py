# AI Companion v0.4.0
# Main package initialization

__version__ = "0.4.0"

# Import main components for easy access
from .cli import main as cli_main
from .main import main as server_main

__all__ = ['cli_main', 'server_main', '__version__']
