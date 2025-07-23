/**
 * Audio Modules Index
 * All audio processing functionality organized by component
 */

/*
AUDIO MODULES ORGANIZATION:
==========================

SPEECH SYNTHESIS:
- audio_tts.js - Text-to-speech generation and voice management

VOICE RECORDING:
- audio_voice_recording.js - Voice input recording and processing

LOADING ORDER FOR HTML:
=======================
Include these scripts in this order for proper audio functionality:

<!-- Audio Processing -->
<script src="/static/js/audio_modules/audio_tts.js"></script>
<script src="/static/js/audio_modules/audio_voice_recording.js"></script>

ARCHITECTURE:
============

Text-to-Speech System:
- Voice synthesis and generation
- Voice selection and configuration
- Audio playback management
- Lipsync integration hooks

Voice Recording System:
- Microphone input capture
- Audio format processing
- Voice activity detection
- Speech-to-text integration

INTEGRATION POINTS:
==================

With Chat Modules:
- TTS for avatar responses
- Voice input for user messages
- Lipsync data generation

With Live2D Modules:
- Mouth movement synchronization
- Audio-visual coordination
- Expression timing

With Core Application:
- Audio pipeline management
- Configuration settings
- Event coordination

FEATURES:
=========

audio_tts.js:
- Text-to-speech generation
- Voice parameter control
- Audio playback management
- Lipsync data extraction
- Voice switching capabilities

audio_voice_recording.js:
- Microphone access management
- Audio recording controls
- Voice activity detection
- Audio format conversion
- Recording state management

DEPENDENCIES:
============
- Web Audio API
- MediaDevices API
- Speech Synthesis API
- Audio processing libraries

*/

console.log('🔊 Audio Modules Documentation Loaded');
console.log('📖 See audio_modules/index.js for audio architecture details');
