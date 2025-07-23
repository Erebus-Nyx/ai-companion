# Packaged Live2D Models

This directory contains Live2D models packaged as ZIP archives for distribution with AI2D Chat.

## Overview

Instead of storing unpacked model directories in the repository, we now use ZIP packages that are extracted during installation. This approach:

- **Reduces repository size** through compression
- **Simplifies distribution** with single-file packages
- **Preserves directory structure** when extracted
- **Uses the same import system** as user uploads

## Contents

The following Live2D models are included:

- **Allium.zip** (18M) - Ariu character model
- **Rei.zip** (2.7M) - Rei character model  
- **chino.zip** (6.0M) - 香風智乃 (Chino) character model
- **epsilon.zip** (15M) - Epsilon character model
- **haru.zip** (15M) - Haru character model
- **haruka.zip** (2.4M) - Haruka character model
- **hiyori.zip** (4.3M) - Hiyori character model
- **iori.zip** (27M) - Iori character model
- **maomao.zip** (5.4M) - Maomao character model
- **march.zip** (12M) - March character model
- **tsumiki.zip** (12M) - Tsumiki character model

## Installation

These models are automatically installed during the AI2D Chat setup process via:

```bash
python3 scripts/install_packaged_models.py
```

### Manual Installation

To manually install or reinstall the models:

```bash
# Install (skips existing models)
python3 scripts/install_packaged_models.py

# Force reinstall all models
python3 scripts/install_packaged_models.py --force
```

## Model Manifest

The `models_manifest.json` file contains metadata about all packaged models, including:
- Model names and filenames
- File sizes
- Descriptions

## Directory Structure

After extraction, each model maintains its original directory structure:

```
~/.local/share/ai2d_chat/live2d_models/
├── Allium/
│   ├── ariu/
│   │   ├── ariu.model3.json
│   │   ├── ariu.moc3
│   │   └── textures/
│   └── motions/
├── epsilon/
│   ├── runtime/
│   │   ├── Epsilon.model3.json
│   │   └── ...
│   └── ...
└── ...
```

## Creating New Packages

To package additional models:

1. Place the model directory in `live2d_models/`
2. Run the packaging script:
   ```bash
   python3 scripts/package_models_for_distribution.py
   ```
3. The new ZIP will be created in `live2d_models_packaged/`

## Technical Details

- **Compression**: Uses ZIP deflate compression
- **Structure**: Preserves exact directory hierarchy
- **Validation**: Verifies .model3.json files exist
- **Database**: Models are registered with motion/expression parsing
- **Import System**: Uses the same ZIP processing as user uploads

## Notes

- Original unpacked directories in `live2d_models/` are excluded from repository via `.gitignore`
- Only the README.md and this `live2d_models_packaged/` directory are tracked
- Installation extracts to user data directory, not repository location
