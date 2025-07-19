# AI Companion Installation Guide

This directory contains two installation scripts:

## 🚀 PRODUCTION INSTALL (Recommended for end users)

**Script:** `scripts/install.py`  
**Purpose:** Install AI Companion as a system-wide application  
**Command:** `python scripts/install.py [--force]`

**What it does:**
- ✅ Builds wheel package
- ✅ Installs via pipx (isolated environment)  
- ✅ Sets up user data directories (`~/.config/ai2d_chat/`, `~/.local/share/ai2d_chat/`)
- ✅ Downloads models and initializes databases
- ✅ Configures Live2D integration
- ✅ Uses production port: **19080**

**After installation:**
- Run with: `ai2d_chat`
- Access at: http://localhost:19080
- System-wide command available

## 🔧 DEVELOPMENT INSTALL (For developers)

**Script:** `scripts/dev_install.py`  
**Purpose:** Set up AI Companion for development from repository source  
**Command:** `python scripts/dev_install.py [--force]`

**What it does:**
- ✅ Sets up Poetry environment
- ✅ Uses same user data directories (shares with production)
- ✅ Downloads models and initializes databases  
- ✅ Configures Live2D integration
- ✅ Uses development port: **19081** (avoids conflicts)

**After installation:**
- Run with: `python src/app.py`
- Access at: http://localhost:19081
- Code changes reflected immediately

## 📊 KEY DIFFERENCES

| Feature             | Production                  | Development                 |
|---------------------|-----------------------------|-----------------------------|
| **Installation**    | pipx/pip package            | Poetry repo setup           |
| **Command**         | `ai2d_chat`                 | `python src/app.py`         |
| **Port**            | 19080                       | 19081                       |
| **Data Location**   | `~/.local/share/ai2d_chat/` |*(SAME)*                     |
| **Config Location** | `~/.config/ai2d_chat/`      |*(SAME)*                     |
| **Environment**     | Isolated                    | Repository                  |
| **Updates**         | Reinstall package           | Git pull                    |

**Important:** Both installations share the same data directories, so you can switch between them without losing configuration, models, or databases.

## 🚀 Quick Start (Most Users)

```bash
python scripts/install.py --force
ai2d_chat
```

## 🔧 Quick Start (Developers)

```bash
python scripts/dev_install.py --force
python src/app.py
```

## Options

Both scripts support:
- `--force`: Clean existing configuration and start fresh
- `--skip-live2d`: Skip Live2D Viewer Web setup
- `--skip-deps`: Skip dependency installation
