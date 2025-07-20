# Live2D Models Directory

This directory contains Live2D models that will be installed to the user's data directory (`~/.local/share/ai2d_chat/live2d_models/`) during setup.

## Directory Structure

Each model should be in its own subdirectory with the following structure:

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
