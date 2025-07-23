/**
 * UI Modules Index
 * All user interface components organized by functionality
 */

/*
UI MODULES ORGANIZATION:
=======================

USER INTERFACE PANELS:
- ui_panel_manager.js - Main panel coordination and layout management
- ui_people_panel.js - People/avatar selection panel
- ui_character_profiles.js - Character profile display and editing

USER MANAGEMENT:
- ui_user_management.js - User account and profile management
- ui_user_selection.js - User selection interface components

VISUAL SYSTEMS:
- ui_drawing_system.js - 2D drawing and canvas utilities
- ui_icon_manager.js - Icon loading and management system

DEBUG & DEVELOPMENT:
- ui_debug_console.js - Development console interface
- ui_debug_logger.js - UI-specific debug logging utilities

LOADING ORDER FOR HTML:
=======================
Include these scripts in this order for proper UI functionality:

<!-- Core UI Systems -->
<script src="/static/js/ui_modules/ui_icon_manager.js"></script>
<script src="/static/js/ui_modules/ui_debug_logger.js"></script>

<!-- Visual Systems -->
<script src="/static/js/ui_modules/ui_drawing_system.js"></script>

<!-- Panel Management -->
<script src="/static/js/ui_modules/ui_panel_manager.js"></script>
<script src="/static/js/ui_modules/ui_people_panel.js"></script>
<script src="/static/js/ui_modules/ui_character_profiles.js"></script>

<!-- User Management -->
<script src="/static/js/ui_modules/ui_user_management.js"></script>
<script src="/static/js/ui_modules/ui_user_selection.js"></script>

<!-- Debug Tools (Development only) -->
<script src="/static/js/ui_modules/ui_debug_console.js"></script>

ARCHITECTURE:
============

Panel System:
- Manages layout and visibility
- Handles panel interactions
- Coordinates between different UI sections

User Interface:
- Profile management
- User selection workflows
- Character customization

Visual Systems:
- Icon rendering and caching
- 2D drawing capabilities
- Canvas-based utilities

Debug Tools:
- Console interface for development
- UI state inspection
- Performance monitoring

INTEGRATION POINTS:
==================

With Chat Modules:
- Character profile data
- User selection events
- Panel state synchronization

With Live2D Modules:
- Avatar selection interface
- Live2D control panels
- Model state display

With Core Application:
- Global state management
- Event coordination
- Data persistence

FEATURES:
=========

ui_panel_manager.js:
- Panel layout coordination
- Show/hide animations
- Responsive design handling

ui_people_panel.js:
- Avatar browsing interface
- Selection callbacks
- Thumbnail generation

ui_character_profiles.js:
- Profile editing forms
- Character customization
- Data validation

ui_user_management.js:
- User authentication UI
- Profile management
- Settings interface

ui_user_selection.js:
- User picker interface
- Multi-user support
- Selection state management

ui_drawing_system.js:
- Canvas-based drawing
- Shape rendering utilities
- Animation helpers

ui_icon_manager.js:
- Icon loading and caching
- SVG/PNG support
- Dynamic icon generation

ui_debug_console.js:
- Development console
- Command interface
- State inspection tools

ui_debug_logger.js:
- UI-specific logging
- Error display
- Performance metrics

*/

console.log('🎨 UI Modules Documentation Loaded');
console.log('📖 See ui_modules/index.js for UI architecture details');
