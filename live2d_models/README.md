# Live2D Models Directory

**Note:** Live2D models are now distributed as ZIP packages in `live2d_models_packaged/` instead of unpacked directories here.

This directory structure is maintained for reference, but the actual model directories are excluded from the repository to reduce size. During installation, models are extracted from ZIP packages in `live2d_models_packaged/` to the user's data directory.

## Current Approach

- **Distribution**: Models packaged as ZIP files in `live2d_models_packaged/`
- **Installation**: Automatic extraction during setup via `scripts/install_packaged_models.py`
- **User Location**: `~/.local/share/ai2d_chat/live2d_models/`
- **Repository**: Only README.md tracked here, model directories excluded via .gitignore

## Directory Structure (Reference)

When extracted, each model maintains this structure:

```
live2d_models/
├── model_name/
│   ├── model.model3.json    # Cubism 3 model file
│   ├── textures/            # Texture files
│   ├── motions/             # Motion files  
│   ├── expressions/         # Expression files
│   └── physics.physics3.json # Physics file (optional)
```

## Model Installation

Models are automatically installed during:
1. Initial setup (`pip install -e .`)
2. Manual refresh via CLI: `ai2d_chat live2d refresh`
3. Web interface "Refresh Models" button

## Adding New Models

1. Add model directory to this folder
2. Commit to git
3. Run `ai2d_chat live2d refresh` or restart application

## File Size Considerations

- Keep individual files under 100MB for git compatibility
- Use Git LFS for larger texture files if needed
- Consider model optimization for web delivery
