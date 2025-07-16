"""
Enhanced Audio Pipeline with Advanced VAD and Speaker Diarization
Extends the basic audio pipeline with ML-based VAD and faster-whisper STT
"""

import logging
import asyncio
import threading
import time
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass
from enum import Enum

from .audio_pipeline import AudioPipeline, AudioPipelineState, AudioEvent, AudioConfig
from .enhanced_vad import (
    EnhancedAudioPipeline as CoreEnhancedPipeline,
    EnhancedVADConfig,
    create_enhanced_pipeline,
    create_lightweight_enhanced_pipeline,
    create_high_accuracy_pipeline
)
from .speech_to_text import STTConfig, STTResult, STTEngine

logger = logging.getLogger(__name__)

@dataclass
class EnhancedAudioConfig:
    """Configuration for enhanced audio pipeline"""
    # Basic audio config
    basic_config: AudioConfig
    
    # Enhanced VAD config
    enhanced_vad_config: EnhancedVADConfig
    
    # Pipeline selection
    use_enhanced_vad: bool = True
    enhanced_mode: str = "lightweight"  # "lightweight", "balanced", "high_accuracy"
    
    # Fallback settings
    fallback_to_basic: bool = True
    enhanced_vad_timeout: float = 5.0

class EnhancedAudioPipelineWrapper:
    """
    Enhanced audio pipeline that wraps both basic and enhanced VAD systems
    Provides seamless fallback and configuration management
    """
    
    def __init__(self, 
                 wake_words: List[str],
                 config: EnhancedAudioConfig):
        
        self.wake_words = wake_words
        self.config = config
        
        # Initialize pipelines
        self.basic_pipeline = None
        self.enhanced_pipeline = None
        self.active_pipeline = None
        
        # State management
        self.state = AudioPipelineState.IDLE
        self.using_enhanced = False
        self.initialization_complete = False
        
        # Event handling
        self.event_callbacks: Dict[str, List[Callable]] = {
            'wake_word_detected': [],
            'speech_started': [],
            'speech_ended': [],
            'transcription_ready': [],
            'state_changed': [],
            'error': [],
            'pipeline_switched': [],
            'enhanced_vad_ready': []
        }
        
        # Performance monitoring
        self.performance_stats = {
            'enhanced_vad_successes': 0,
            'enhanced_vad_failures': 0,
            'fallback_activations': 0,
            'avg_processing_time': 0.0
        }
        
        # Initialize pipelines
        self._initialize_pipelines()
        
    def _initialize_pipelines(self):
        """Initialize both basic and enhanced pipelines"""
        try:            # Always initialize basic pipeline as fallback
            logger.info("Initializing basic audio pipeline...")
            self.basic_pipeline = AudioPipeline(
                wake_words=self.wake_words,
                audio_config=self.config.basic_config,
                stt_config=STTConfig()
            )
            self._setup_basic_callbacks()
            
            # Try to initialize enhanced pipeline
            if self.config.use_enhanced_vad:
                logger.info("Initializing enhanced VAD pipeline...")
                self._initialize_enhanced_pipeline()
            else:
                logger.info("Enhanced VAD disabled in configuration")
                self.active_pipeline = self.basic_pipeline
                
            self.initialization_complete = True
            
        except Exception as e:
            logger.error(f"Error during pipeline initialization: {e}")
            self._fallback_to_basic("Initialization error")
    
    def _initialize_enhanced_pipeline(self):
        """Initialize enhanced pipeline with error handling"""
        try:
            # Create enhanced pipeline based on mode
            if self.config.enhanced_mode == "lightweight":
                self.enhanced_pipeline = create_lightweight_enhanced_pipeline()
            elif self.config.enhanced_mode == "high_accuracy":
                self.enhanced_pipeline = create_high_accuracy_pipeline()
            else:  # balanced
                self.enhanced_pipeline = create_enhanced_pipeline()
            
            # Setup enhanced pipeline callbacks
            self._setup_enhanced_callbacks()
            
            # Test enhanced pipeline
            self._test_enhanced_pipeline()
            
            # Set as active if successful
            self.active_pipeline = self.enhanced_pipeline
            self.using_enhanced = True
            
            logger.info(f"Enhanced VAD pipeline initialized in {self.config.enhanced_mode} mode")
            self._emit_event('enhanced_vad_ready', {
                'mode': self.config.enhanced_mode,
                'config': self.config.enhanced_vad_config
            })
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced pipeline: {e}")
            if self.config.fallback_to_basic:
                self._fallback_to_basic("Enhanced pipeline initialization failed")
            else:
                raise
    
    def _test_enhanced_pipeline(self):
        """Test enhanced pipeline components"""
        if not self.enhanced_pipeline:
            raise RuntimeError("Enhanced pipeline not initialized")
        
        # Test VAD initialization
        if not hasattr(self.enhanced_pipeline, 'vad') or not self.enhanced_pipeline.vad:
            raise RuntimeError("Enhanced VAD not properly initialized")
        
        # Test STT initialization  
        if not hasattr(self.enhanced_pipeline, 'stt') or not self.enhanced_pipeline.stt:
            raise RuntimeError("Enhanced STT not properly initialized")
        
        logger.info("Enhanced pipeline components tested successfully")
    
    def _setup_basic_callbacks(self):
        """Setup callbacks for basic pipeline"""
        if not self.basic_pipeline:
            return
            
        self.basic_pipeline.add_event_callback('wake_word_detected', self._on_wake_word_detected)
        self.basic_pipeline.add_event_callback('speech_started', self._on_speech_started)
        self.basic_pipeline.add_event_callback('speech_ended', self._on_speech_ended)
        self.basic_pipeline.add_event_callback('transcription_ready', self._on_transcription_ready)
        self.basic_pipeline.add_event_callback('state_changed', self._on_state_changed)
        self.basic_pipeline.add_event_callback('error', self._on_pipeline_error)
    
    def _setup_enhanced_callbacks(self):
        """Setup callbacks for enhanced pipeline"""
        if not self.enhanced_pipeline:
            return
        
        # Enhanced pipeline uses different callback structure
        # We'll need to adapt the interface
        # For now, we'll handle this in the process_audio method
        pass
    
    def _fallback_to_basic(self, reason: str):
        """Fallback to basic pipeline"""
        logger.warning(f"Falling back to basic pipeline: {reason}")
        
        self.active_pipeline = self.basic_pipeline
        self.using_enhanced = False
        self.performance_stats['fallback_activations'] += 1
        
        self._emit_event('pipeline_switched', {
            'from': 'enhanced',
            'to': 'basic',
            'reason': reason
        })
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """Add event callback"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """Remove event callback"""
        if event_type in self.event_callbacks and callback in self.event_callbacks[event_type]:
            self.event_callbacks[event_type].remove(callback)
    
    def _emit_event(self, event_type: str, data: Any = None, metadata: Dict[str, Any] = None):
        """Emit event to callbacks"""
        event = AudioEvent(event_type, time.time(), data, metadata or {})
        
        for callback in self.event_callbacks.get(event_type, []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback for {event_type}: {e}")
    
    def start(self):
        """Start the audio pipeline"""
        if not self.initialization_complete:
            raise RuntimeError("Pipeline not properly initialized")
        
        try:
            logger.info(f"Starting audio pipeline (using {'enhanced' if self.using_enhanced else 'basic'} VAD)")
            
            if self.using_enhanced and self.enhanced_pipeline:
                # Enhanced pipeline handles its own lifecycle
                # We'll manage it through process_audio calls
                pass
            else:
                self.basic_pipeline.start()
            
            self.state = AudioPipelineState.LISTENING
            logger.info("Enhanced audio pipeline started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start audio pipeline: {e}")
            if self.config.fallback_to_basic and not self.using_enhanced:
                raise
            else:
                self._fallback_to_basic("Start failure")
                self.basic_pipeline.start()
    
    def stop(self):
        """Stop the audio pipeline"""
        logger.info("Stopping enhanced audio pipeline...")
        
        if self.basic_pipeline:
            self.basic_pipeline.stop()
        
        # Enhanced pipeline cleanup handled automatically
        
        self.state = AudioPipelineState.IDLE
        logger.info("Enhanced audio pipeline stopped")
    
    def process_audio_chunk(self, audio_data: bytes) -> Optional[str]:
        """
        Process audio chunk through enhanced pipeline
        Returns transcription if speech detected and processed
        """
        if not self.using_enhanced or not self.enhanced_pipeline:
            # Use basic pipeline behavior
            return None
        
        try:
            start_time = time.time()
            
            # Use enhanced pipeline
            result = self.enhanced_pipeline.process_audio_chunk(audio_data)
            
            if result and result.get('transcription'):
                # Update performance stats
                processing_time = time.time() - start_time
                self._update_performance_stats(processing_time, success=True)
                
                # Emit transcription event
                stt_result = STTResult(
                    text=result['transcription'],
                    confidence=result.get('confidence', 1.0),
                    language=result.get('language', 'en'),
                    engine=STTEngine.FASTER_WHISPER,
                    processing_time=processing_time
                )
                
                self._emit_event('transcription_ready', {
                    'result': stt_result,
                    'enhanced_result': result,
                    'timestamp': time.time()
                })
                
                return result['transcription']
            
            return None
            
        except Exception as e:
            logger.error(f"Enhanced audio processing failed: {e}")
            self.performance_stats['enhanced_vad_failures'] += 1
            
            if self.config.fallback_to_basic:
                self._fallback_to_basic("Processing error")
            
            return None
    
    def _update_performance_stats(self, processing_time: float, success: bool):
        """Update performance statistics"""
        if success:
            self.performance_stats['enhanced_vad_successes'] += 1
            # Update rolling average
            total_ops = self.performance_stats['enhanced_vad_successes']
            self.performance_stats['avg_processing_time'] = (
                (self.performance_stats['avg_processing_time'] * (total_ops - 1) + processing_time) / total_ops
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            **self.performance_stats,
            'using_enhanced': self.using_enhanced,
            'enhanced_mode': self.config.enhanced_mode if self.using_enhanced else None,
            'pipeline_type': 'enhanced' if self.using_enhanced else 'basic'
        }
    
    def switch_to_enhanced(self, mode: Optional[str] = None):
        """Switch to enhanced pipeline"""
        if not self.enhanced_pipeline:
            logger.warning("Enhanced pipeline not available")
            return False
        
        if mode and mode != self.config.enhanced_mode:
            # Reinitialize with new mode
            self.config.enhanced_mode = mode
            self._initialize_enhanced_pipeline()
        
        self.active_pipeline = self.enhanced_pipeline
        self.using_enhanced = True
        
        self._emit_event('pipeline_switched', {
            'from': 'basic',
            'to': 'enhanced',
            'mode': mode or self.config.enhanced_mode
        })
        
        return True
    
    def switch_to_basic(self):
        """Switch to basic pipeline"""
        self.active_pipeline = self.basic_pipeline
        self.using_enhanced = False
        
        self._emit_event('pipeline_switched', {
            'from': 'enhanced',
            'to': 'basic'
        })
    
    def adjust_sensitivity(self, **kwargs):
        """Adjust detection sensitivity"""
        if self.active_pipeline and hasattr(self.active_pipeline, 'adjust_sensitivity'):
            self.active_pipeline.adjust_sensitivity(**kwargs)
    
    def force_listen(self):
        """Force the pipeline to start listening"""
        if self.active_pipeline and hasattr(self.active_pipeline, 'force_listen'):
            self.active_pipeline.force_listen()
    
    # Event handlers for basic pipeline
    def _on_wake_word_detected(self, event: AudioEvent):
        """Forward wake word detection event"""
        self._emit_event('wake_word_detected', event.data, event.metadata)
    
    def _on_speech_started(self, event: AudioEvent):
        """Forward speech start event"""
        self._emit_event('speech_started', event.data, event.metadata)
    
    def _on_speech_ended(self, event: AudioEvent):
        """Forward speech end event"""
        self._emit_event('speech_ended', event.data, event.metadata)
    
    def _on_transcription_ready(self, event: AudioEvent):
        """Forward transcription event"""
        self._emit_event('transcription_ready', event.data, event.metadata)
    
    def _on_state_changed(self, event: AudioEvent):
        """Forward state change event"""
        self.state = AudioPipelineState(event.data['new_state'])
        self._emit_event('state_changed', event.data, event.metadata)
    
    def _on_pipeline_error(self, event: AudioEvent):
        """Handle pipeline error"""
        logger.error(f"Pipeline error: {event.data}")
        
        if self.using_enhanced and self.config.fallback_to_basic:
            self._fallback_to_basic("Pipeline error")
        else:
            self._emit_event('error', event.data, event.metadata)

def create_enhanced_audio_pipeline(
    wake_words: List[str],
    enhanced_mode: str = "lightweight",
    use_enhanced_vad: bool = True,
    fallback_to_basic: bool = True
) -> EnhancedAudioPipelineWrapper:
    """
    Factory function to create enhanced audio pipeline
    
    Args:
        wake_words: List of wake words to detect
        enhanced_mode: "lightweight", "balanced", or "high_accuracy"
        use_enhanced_vad: Whether to use enhanced VAD
        fallback_to_basic: Whether to fallback to basic VAD on error
    
    Returns:
        Configured enhanced audio pipeline
    """
    
    # Create configurations
    basic_config = AudioConfig()
    enhanced_vad_config = EnhancedVADConfig()
    
    config = EnhancedAudioConfig(
        basic_config=basic_config,
        enhanced_vad_config=enhanced_vad_config,
        use_enhanced_vad=use_enhanced_vad,
        enhanced_mode=enhanced_mode,
        fallback_to_basic=fallback_to_basic
    )
    
    return EnhancedAudioPipelineWrapper(wake_words, config)
