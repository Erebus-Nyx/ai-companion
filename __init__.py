# AI Companion v0.4.0
# Main package initialization

__version__ = "0.4.0"

# Import main components for easy access
try:
    from cli import main as cli_main
    from main import main as server_main
except ImportError:
    # Fallback for development mode
    cli_main = None
    server_main = None

__all__ = ['cli_main', 'server_main', '__version__']
