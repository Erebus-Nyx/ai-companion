/**
 * Live2D Modules Index
 * All Live2D avatar functionality organized by component
 */

/*
LIVE2D MODULES ORGANIZATION:
===========================

CORE SYSTEM:
- live2d_core.js - Main Live2D engine integration and initialization
- live2d_config.js - Configuration management for Live2D settings
- live2d_integration.js - Integration layer with the main application

MODEL MANAGEMENT:
- live2d_model_loader.js - Handles loading Live2D model files
- live2d_model_manager.js - Manages multiple Live2D models
- live2d_multi_model_manager.js - Advanced multi-model coordination
- live2d_state_manager.js - Manages Live2D model states and transitions

MOTION & ANIMATION:
- live2d_motion_manager.js - Controls Live2D motion playback
- live2d_motions.js - Motion definitions and management
- live2d_core_simple.js - Simplified motion control interface

INTERACTION:
- live2d_interaction.js - General Live2D interaction handling
- live2d_mouse_interaction.js - Mouse-specific interactions (clicking, dragging)
- live2d_ui_controller.js - UI controls for Live2D avatars

UTILITIES:
- live2d_logger.js - Logging specific to Live2D operations
- live2d_tester.js - Testing utilities for Live2D functionality
- live2d_simple_fix.js - Bug fixes and compatibility patches

LOADING ORDER FOR HTML:
=======================
Include these scripts in this order for proper Live2D functionality:

<!-- Core Live2D -->
<script src="/static/js/live2d_modules/live2d_config.js"></script>
<script src="/static/js/live2d_modules/live2d_logger.js"></script>
<script src="/static/js/live2d_modules/live2d_core.js"></script>

<!-- Model Management -->
<script src="/static/js/live2d_modules/live2d_model_loader.js"></script>
<script src="/static/js/live2d_modules/live2d_state_manager.js"></script>
<script src="/static/js/live2d_modules/live2d_model_manager.js"></script>
<script src="/static/js/live2d_modules/live2d_multi_model_manager.js"></script>

<!-- Motion System -->
<script src="/static/js/live2d_modules/live2d_motions.js"></script>
<script src="/static/js/live2d_modules/live2d_motion_manager.js"></script>

<!-- Interaction -->
<script src="/static/js/live2d_modules/live2d_mouse_interaction.js"></script>
<script src="/static/js/live2d_modules/live2d_interaction.js"></script>
<script src="/static/js/live2d_modules/live2d_ui_controller.js"></script>

<!-- Integration -->
<script src="/static/js/live2d_modules/live2d_integration.js"></script>

ARCHITECTURE:
============

Live2D Core System:
- Handles PIXI.js integration
- Manages WebGL contexts
- Provides basic Live2D functionality

Model Management:
- Loads .model3.json files
- Manages texture resources
- Handles model lifecycle

Motion System:
- Controls facial expressions
- Manages body animations
- Handles lipsync integration

Interaction Layer:
- Mouse/touch input handling
- Hit detection
- UI control integration

Integration:
- Connects with chat system
- Provides API for other modules
- Handles state synchronization

DEPENDENCIES:
============
- PIXI.js (WebGL rendering)
- Live2D Cubism SDK
- Chat modules (for avatar communication)
- UI modules (for controls)

*/

console.log('🎭 Live2D Modules Documentation Loaded');
console.log('📖 See live2d_modules/index.js for Live2D architecture details');
