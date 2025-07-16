import logging
import asyncio
import threading
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum

from .voice_detection import VoiceDetection, AudioConfig
from .speech_to_text import SpeechToText, STTConfig, STTResult, STTEngine

logger = logging.getLogger(__name__)

class AudioPipelineState(Enum):
    """Audio pipeline states"""
    IDLE = "idle"
    LISTENING = "listening"
    WAKE_WORD_DETECTED = "wake_word_detected"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"

@dataclass
class AudioEvent:
    """Audio pipeline event"""
    event_type: str
    timestamp: float
    data: Any = None
    metadata: Dict[str, Any] = None

class AudioPipeline:
    """Main audio processing pipeline"""
    
    def __init__(self, 
                 wake_words: List[str],
                 audio_config: Optional[AudioConfig] = None,
                 stt_config: Optional[STTConfig] = None):
        
        self.wake_words = wake_words
        self.audio_config = audio_config or AudioConfig()
        self.stt_config = stt_config or STTConfig()
        
        # Components
        self.voice_detection = VoiceDetection(wake_words, self.audio_config)
        self.speech_to_text = SpeechToText(self.stt_config)
        
        # State management
        self.state = AudioPipelineState.IDLE
        self.last_wake_word_time = 0
        self.wake_word_timeout = 10.0  # seconds
        
        # Event handling
        self.event_callbacks: Dict[str, List[Callable]] = {
            'wake_word_detected': [],
            'speech_started': [],
            'speech_ended': [],
            'transcription_ready': [],
            'state_changed': [],
            'error': []
        }
        
        # Setup component callbacks
        self._setup_callbacks()
        
        # Background tasks
        self.monitoring_task = None
        self.is_running = False
        
    def _setup_callbacks(self):
        """Setup callbacks between components"""
        
        # Voice detection callbacks
        self.voice_detection.set_callbacks(
            wake_word_callback=self._on_wake_word_detected,
            speech_start_callback=self._on_speech_started,
            speech_end_callback=self._on_speech_ended,
            error_callback=self._on_voice_detection_error
        )
        
        # STT callbacks
        self.speech_to_text.add_result_callback(self._on_transcription_result)
        
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
                
    def _change_state(self, new_state: AudioPipelineState):
        """Change pipeline state"""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            logger.info(f"Audio pipeline state: {old_state.value} -> {new_state.value}")
            
            self._emit_event('state_changed', {
                'old_state': old_state.value,
                'new_state': new_state.value
            })
            
    def start(self):
        """Start the audio pipeline"""
        if self.is_running:
            return
            
        try:
            logger.info("Starting audio pipeline...")
            
            # Start components
            self.voice_detection.start_listening()
            self.speech_to_text.start_async_processing()
            
            # Start monitoring
            self.is_running = True
            self.monitoring_task = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_task.start()
            
            self._change_state(AudioPipelineState.LISTENING)
            logger.info("Audio pipeline started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start audio pipeline: {e}")
            self._emit_event('error', str(e))
            self._change_state(AudioPipelineState.ERROR)
            
    def stop(self):
        """Stop the audio pipeline"""
        if not self.is_running:
            return
            
        logger.info("Stopping audio pipeline...")
        
        self.is_running = False
        
        # Stop components
        self.voice_detection.stop_listening()
        self.speech_to_text.stop_async_processing()
        
        # Wait for monitoring thread
        if self.monitoring_task and self.monitoring_task.is_alive():
            self.monitoring_task.join(timeout=2.0)
            
        self._change_state(AudioPipelineState.IDLE)
        logger.info("Audio pipeline stopped")
        
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.is_running:
            try:
                # Check for wake word timeout
                if self.state == AudioPipelineState.WAKE_WORD_DETECTED:
                    if time.time() - self.last_wake_word_time > self.wake_word_timeout:
                        logger.info("Wake word timeout, returning to listening")
                        self._change_state(AudioPipelineState.LISTENING)
                        
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                
    def _on_wake_word_detected(self, wake_word: str):
        """Handle wake word detection"""
        logger.info(f"Wake word detected: {wake_word}")
        
        self.last_wake_word_time = time.time()
        self._change_state(AudioPipelineState.WAKE_WORD_DETECTED)
        
        self._emit_event('wake_word_detected', {
            'wake_word': wake_word,
            'timestamp': self.last_wake_word_time
        })
        
    def _on_speech_started(self):
        """Handle speech start"""
        logger.info("Speech recording started")
        
        # Only record if we're in wake word detected state or listening
        if self.state in [AudioPipelineState.WAKE_WORD_DETECTED, AudioPipelineState.LISTENING]:
            self._change_state(AudioPipelineState.RECORDING)
            
            self._emit_event('speech_started', {
                'timestamp': time.time()
            })
        
    def _on_speech_ended(self, audio_data: bytes):
        """Handle speech end"""
        logger.info("Speech recording ended")
        
        if self.state == AudioPipelineState.RECORDING:
            self._change_state(AudioPipelineState.PROCESSING)
            
            self._emit_event('speech_ended', {
                'audio_length': len(audio_data),
                'timestamp': time.time()
            })
            
            # Send to STT
            self.speech_to_text.transcribe_async(audio_data)
        
    def _on_transcription_result(self, result: STTResult):
        """Handle transcription result"""
        logger.info(f"Transcription result: '{result.text}' (confidence: {result.confidence:.2f})")
        
        # Return to listening state
        self._change_state(AudioPipelineState.LISTENING)
        
        self._emit_event('transcription_ready', {
            'result': result,
            'timestamp': time.time()
        })
        
    def _on_voice_detection_error(self, error: Exception):
        """Handle voice detection error"""
        logger.error(f"Voice detection error: {error}")
        
        self._change_state(AudioPipelineState.ERROR)
        self._emit_event('error', str(error))
        
    def force_listen(self):
        """Force the pipeline to start listening (skip wake word)"""
        if self.state == AudioPipelineState.LISTENING:
            logger.info("Force listen activated")
            self._change_state(AudioPipelineState.WAKE_WORD_DETECTED)
            self.last_wake_word_time = time.time()
            
    def adjust_sensitivity(self, 
                          vad_aggressiveness: Optional[int] = None,
                          wake_word_sensitivity: Optional[float] = None):
        """Adjust detection sensitivity"""
        if vad_aggressiveness is not None or wake_word_sensitivity is not None:
            self.voice_detection.adjust_sensitivity(
                vad_aggressiveness or self.audio_config.vad_aggressiveness,
                wake_word_sensitivity or 0.5
            )
            
    def change_stt_engine(self, engine: STTEngine):
        """Change speech-to-text engine"""
        self.speech_to_text.change_engine(engine)
        
    def change_stt_language(self, language: str):
        """Change speech-to-text language"""
        self.speech_to_text.change_language(language)
        
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline status"""
        return {
            'state': self.state.value,
            'is_running': self.is_running,
            'wake_words': self.wake_words,
            'last_wake_word_time': self.last_wake_word_time,
            'voice_detection': self.voice_detection.get_status(),
            'speech_to_text': self.speech_to_text.get_status(),
            'audio_config': {
                'sample_rate': self.audio_config.sample_rate,
                'channels': self.audio_config.channels,
                'vad_aggressiveness': self.audio_config.vad_aggressiveness
            },
            'stt_config': {
                'engine': self.stt_config.engine.value,
                'language': self.stt_config.language
            }
        }
        
    def get_audio_devices(self) -> List[Dict[str, Any]]:
        """Get available audio devices"""
        return self.voice_detection.get_audio_devices()
        
    def get_supported_languages(self) -> List[str]:
        """Get supported STT languages"""
        return self.speech_to_text.get_supported_languages()

# Example usage and factory functions
def create_basic_pipeline(wake_words: List[str] = None) -> AudioPipeline:
    """Create a basic audio pipeline with default settings"""
    wake_words = wake_words or ["hey nyx", "nyx", "companion"]
    
    # Default configs optimized for Raspberry Pi
    audio_config = AudioConfig(
        sample_rate=16000,
        channels=1,
        chunk_size=1024,
        vad_aggressiveness=2,
        silence_timeout=2.0
    )
    
    stt_config = STTConfig(
        engine=STTEngine.GOOGLE,  # Fallback to Google for reliability
        language="en-US",
        timeout=10.0
    )
    
    return AudioPipeline(wake_words, audio_config, stt_config)

def create_offline_pipeline(wake_words: List[str] = None) -> AudioPipeline:
    """Create an offline audio pipeline using local models"""
    wake_words = wake_words or ["hey nyx", "nyx", "companion"]
    
    audio_config = AudioConfig(
        sample_rate=16000,
        channels=1,
        chunk_size=1024,
        vad_aggressiveness=2,
        silence_timeout=2.0
    )
    
    stt_config = STTConfig(
        engine=STTEngine.WHISPER_LOCAL,
        whisper_model="tiny",  # Smallest model for Raspberry Pi
        whisper_device="cpu",
        language="en",
        timeout=15.0
    )
    
    return AudioPipeline(wake_words, audio_config, stt_config)

def create_high_performance_pipeline(wake_words: List[str] = None) -> AudioPipeline:
    """Create a high-performance pipeline for powerful systems"""
    wake_words = wake_words or ["hey nyx", "nyx", "companion"]
    
    audio_config = AudioConfig(
        sample_rate=16000,
        channels=1,
        chunk_size=512,  # Smaller chunks for lower latency
        vad_aggressiveness=3,  # More aggressive VAD
        silence_timeout=1.5
    )
    
    stt_config = STTConfig(
        engine=STTEngine.WHISPER_LOCAL,
        whisper_model="base",  # Better accuracy
        whisper_device="auto",  # Auto-detect best device
        language="en",
        timeout=10.0
    )
    
    return AudioPipeline(wake_words, audio_config, stt_config)
