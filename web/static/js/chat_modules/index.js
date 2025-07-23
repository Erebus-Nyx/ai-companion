/**
 * Chat Modules Index
 * This file documents the modular chat system architecture and loading order
 */

/*
MODULAR SYSTEM ORGANIZATION:
============================

CHAT MODULES (/chat_modules/):
- Core conversation and AI interaction functionality
- Personality management and response generation
- Multi-avatar conversation orchestration

LIVE2D MODULES (/live2d_modules/):
- Live2D avatar rendering and animation
- Model loading and motion management
- Avatar interaction and display systems

UI MODULES (/ui_modules/):
- User interface panels and controls
- User management and profile systems
- Debug tools and visual utilities

CHAT MODULES LOADING ORDER:
===========================

1. avatar_personality_manager.js - Handles personality traits and content capabilities
2. conversation_context_manager.js - Manages conversation analysis and context
3. response_generation_manager.js - Handles AI response generation
4. avatar_interaction_manager.js - Manages multi-avatar interactions
5. module_loader.js - Initializes all modules and provides coordination
6. chat_manager.js - Main chat manager using modular architecture

HTML INCLUSION ORDER:
====================
FULL SYSTEM LOADING ORDER (All Modules):

<!-- Core Dependencies -->
<script src="/static/js/eventemitter_preloader_v6.js"></script>
<script src="/static/js/compatibility_functions.js"></script>
<script src="/static/js/config_api_helpers.js"></script>

<!-- Live2D System -->
<script src="/static/js/live2d_modules/live2d_config.js"></script>
<script src="/static/js/live2d_modules/live2d_logger.js"></script>
<script src="/static/js/live2d_modules/live2d_core.js"></script>
<script src="/static/js/live2d_modules/live2d_model_loader.js"></script>
<script src="/static/js/live2d_modules/live2d_state_manager.js"></script>
<script src="/static/js/live2d_modules/live2d_model_manager.js"></script>
<script src="/static/js/live2d_modules/live2d_multi_model_manager.js"></script>
<script src="/static/js/live2d_modules/live2d_motions.js"></script>
<script src="/static/js/live2d_modules/live2d_motion_manager.js"></script>
<script src="/static/js/live2d_modules/live2d_mouse_interaction.js"></script>
<script src="/static/js/live2d_modules/live2d_interaction.js"></script>
<script src="/static/js/live2d_modules/live2d_ui_controller.js"></script>
<script src="/static/js/live2d_modules/live2d_integration.js"></script>

<!-- UI System -->
<script src="/static/js/ui_modules/ui_icon_manager.js"></script>
<script src="/static/js/ui_modules/ui_debug_logger.js"></script>
<script src="/static/js/ui_modules/ui_drawing_system.js"></script>
<script src="/static/js/ui_modules/ui_panel_manager.js"></script>
<script src="/static/js/ui_modules/ui_people_panel.js"></script>
<script src="/static/js/ui_modules/ui_character_profiles.js"></script>
<script src="/static/js/ui_modules/ui_user_management.js"></script>
<script src="/static/js/ui_modules/ui_user_selection.js"></script>

<!-- Chat System -->
<script src="/static/js/chat_modules/avatar_personality_manager.js"></script>
<script src="/static/js/chat_modules/conversation_context_manager.js"></script>
<script src="/static/js/chat_modules/response_generation_manager.js"></script>
<script src="/static/js/chat_modules/avatar_interaction_manager.js"></script>
<script src="/static/js/chat_modules/module_loader.js"></script>
<script src="/static/js/chat_modules/chat_manager.js"></script>

<!-- Application Core -->
<script src="/static/js/main_initialization.js"></script>

CHAT-ONLY LOADING ORDER (Minimal):
==================================
For chat functionality without Live2D or advanced UI:

<script src="/static/js/chat_modules/avatar_personality_manager.js"></script>
<script src="/static/js/chat_modules/conversation_context_manager.js"></script>
<script src="/static/js/chat_modules/response_generation_manager.js"></script>
<script src="/static/js/chat_modules/avatar_interaction_manager.js"></script>
<script src="/static/js/chat_modules/module_loader.js"></script>
<script src="/static/js/chat_modules/chat_manager.js"></script>

USAGE:
======

// The system auto-initializes when DOM is ready, or you can manually initialize:
await window.chatSystemModules.initializeAllModules();

// Access the main chat manager:
const chatManager = window.avatarChatManager;

// Send a message:
await chatManager.sendMessage("Hello!");

// Get system status:
const status = chatManager.getSystemStatus();

// Access individual modules if needed:
const personalityManager = window.avatarPersonalityManager;
const conversationManager = window.conversationContextManager;
const responseManager = window.responseGenerationManager;
const interactionManager = window.avatarInteractionManager;

MIGRATION FROM OLD CHAT_MANAGER:
===============================

The old monolithic chat_manager.js (~10k lines) has been broken down into:

1. Core chat coordination (chat_manager.js - ~800 lines)
2. Personality management (avatar_personality_manager.js - ~250 lines)
3. Conversation analysis (conversation_context_manager.js - ~400 lines)
4. Response generation (response_generation_manager.js - ~350 lines)
5. Avatar interactions (avatar_interaction_manager.js - ~450 lines)
6. Module coordination (module_loader.js - ~100 lines)

BENEFITS:
=========

- Modularity: Each component has a single responsibility
- Maintainability: Easier to debug and update individual components
- Reusability: Modules can be used independently or in different combinations
- Performance: Only load what you need
- Testing: Each module can be tested in isolation
- Database Integration: Personality traits are now fetched from database instead of hardcoded
- Extensibility: Easy to add new modules or extend existing ones

FEATURES MOVED TO MODULES:
=========================

avatar_personality_manager.js:
- getAvatarPersonalityTraits() -> fetches from database with fallback
- getAvatarContentCapabilities()
- calculateBehavioralConstraints()
- Content filtering logic

conversation_context_manager.js:
- analyzeUserConversationPattern()
- detectUserAttentionFocus()
- analyzeUserInteractionStyle()
- getEnvironmentalFactors()
- analyzeAddressingContext()

response_generation_manager.js:
- generateAutonomousMessage() -> uses AI API
- buildAIGenerationContext()
- validateContentAppropriateness()
- Fallback response generation

avatar_interaction_manager.js:
- determineResponder() -> intelligent avatar selection
- checkForAvatarToAvatarInteractions()
- Multi-avatar conversation flow
- Interaction history tracking

chat_manager.js (streamlined):
- Core initialization and coordination
- Avatar loading and management
- UI integration
- Module orchestration
- Event handling

*/

// This file is for documentation only - no executable code
console.log('📚 Chat Modules Documentation Loaded');
console.log('📖 See chat_modules/index.js for architecture details');
