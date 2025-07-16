"""
Audio processing module for AI companion.

This module provides comprehensive audio processing capabilities including:
- Voice Activity Detection (VAD)
- Wake word detection
- Speech-to-text (STT) with multiple engine support
- Audio pipeline coordination

Components:
- VoiceDetection: Wake word detection and voice activity detection
- SpeechToText: Multi-engine speech recognition
- AudioPipeline: Coordinated audio processing pipeline
"""

from .voice_detection import (
    VoiceDetection,
    AudioConfig,
    VoiceActivityDetector,
    WakeWordDetector,
    VoiceActivity
)

from .speech_to_text import (
    SpeechToText,
    SpeechToTextEngine,
    STTConfig,
    STTResult,
    STTEngine,
    WhisperSTT
)

from .audio_pipeline import (
    AudioPipeline,
    AudioPipelineState,
    AudioEvent,
    create_basic_pipeline,
    create_offline_pipeline,
    create_high_performance_pipeline
)

from .enhanced_audio_pipeline import (
    EnhancedAudioPipelineWrapper,
    EnhancedAudioConfig,
    create_enhanced_audio_pipeline
)

from .enhanced_vad import (
    EnhancedVADConfig,
    PyannoteVAD,
    SileroVAD,
    HybridVAD,
    FasterWhisperSTT,
    EnhancedAudioPipeline,
    create_enhanced_pipeline,
    create_lightweight_enhanced_pipeline,
    create_high_accuracy_pipeline
)

from .config_loader import (
    AudioConfigLoader,
    load_enhanced_audio_config,
    create_audio_pipeline_from_config
)

__all__ = [
    # Voice detection
    'VoiceDetection',
    'AudioConfig', 
    'VoiceActivityDetector',
    'WakeWordDetector',
    'VoiceActivity',
    
    # Speech to text
    'SpeechToText',
    'SpeechToTextEngine',
    'STTConfig',
    'STTResult', 
    'STTEngine',
    'WhisperSTT',
    
    # Audio pipeline
    'AudioPipeline',
    'AudioPipelineState',
    'AudioEvent',
    'create_basic_pipeline',
    'create_offline_pipeline', 
    'create_high_performance_pipeline',
    
    # Enhanced audio pipeline
    'EnhancedAudioPipelineWrapper',
    'EnhancedAudioConfig',
    'create_enhanced_audio_pipeline',    # Enhanced VAD components
    'EnhancedVADConfig',
    'PyannoteVAD',
    'SileroVAD',
    'HybridVAD',
    'FasterWhisperSTT',
    'EnhancedAudioPipeline',
    'create_enhanced_pipeline',
    'create_lightweight_enhanced_pipeline',
    'create_high_accuracy_pipeline',
    
    # Configuration
    'AudioConfigLoader',
    'load_enhanced_audio_config',
    'create_audio_pipeline_from_config'
]

# Version info
__version__ = '1.0.0'
__author__ = 'AI Companion Project'
__description__ = 'Audio processing and speech recognition module'
