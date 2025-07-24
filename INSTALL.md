# AI2D Chat Installation Guide

## Quick Installation

### Production Installation
```bash
python3 dev_install.py
```

### Development Installation
```bash
python3 dev_install.py --dev
```

## Installation Options

| Flag | Description |
|------|-------------|
| `--dev` | Install in development mode (editable, port 5001) |
| `--force` | Force reinstall (removes existing installation) |
| `--no-auto-setup` | Skip automatic model downloads and setup |
| `--verbose` | Show detailed output |
| `--build-only` | Only build package, don't install |

## What Gets Installed

### Production Mode
- **Port**: Reads from `config.yaml` (default: 19080)
- **Environment**: Production optimized
- **Dependencies**: Core dependencies only

### Development Mode (`--dev`)
- **Port**: Reads from `config.yaml` dev_port (default: 5001)
- **Environment**: Development with debug logging
- **Dependencies**: All dev dependencies (pytest, kokoro-onnx, etc.)
- **Editable Install**: Changes reflect immediately
- **Commands**: `dev_ai2d_chat` CLI available

## Configuration

The installer automatically:
1. **Detects port from config files**:
   - First checks: `~/.config/ai2d_chat/config.yaml`
   - Falls back to: `config/config.yaml`
   - Uses `dev_port` for dev mode, `port` for production

2. **Installs dependencies from pyproject.toml**:
   - Core dependencies always installed
   - Dev dependencies (`[dev]`) installed in dev mode
   - Hardware-optimized variants (`[cuda]`, `[rpi]`, etc.)

3. **Sets up user directories**:
   - Config: `~/.config/ai2d_chat/`
   - Data: `~/.local/share/ai2d_chat/`
   - Logs: `~/.local/share/ai2d_chat/logs/`

## Usage After Installation

### Production
```bash
ai2d_chat_server
# Opens on configured port (default: 19080)
```

### Development
```bash
dev_ai2d_chat server
# Opens on configured dev_port (default: 5001)

dev_ai2d_chat test    # Run tests
dev_ai2d_chat debug   # Debug mode
dev_ai2d_chat reset   # Reset environment
```

## Why No Bash Script?

The Python installer (`dev_install.py`) handles everything:
- ✅ Dynamic port configuration from YAML files
- ✅ Automatic dependency management via pyproject.toml
- ✅ Hardware detection and optimization
- ✅ User directory setup
- ✅ Database initialization
- ✅ Model downloads
- ✅ Development vs production modes

No separate bash scripts needed!
