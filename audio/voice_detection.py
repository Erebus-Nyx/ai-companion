import logging
import asyncio
import pyaudio
import webrtcvad
import numpy as np
import threading
import queue
import time
from typing import List, Callable, Optional, Dict, Any
from dataclasses import dataclass
import speech_recognition as sr
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class AudioConfig:
    """Audio configuration settings"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    format: int = pyaudio.paInt16
    vad_aggressiveness: int = 1  # 0-3, higher is more aggressive
    silence_timeout: float = 2.0  # seconds
    wake_word_timeout: float = 10.0  # seconds
    min_audio_length: float = 0.5  # minimum recording length

@dataclass
class VoiceActivity:
    """Voice activity detection result"""
    is_speech: bool
    confidence: float
    audio_data: bytes
    timestamp: float

class VoiceActivityDetector:
    """Voice Activity Detection using WebRTC VAD"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.vad = webrtcvad.Vad(config.vad_aggressiveness)
        
    def is_speech(self, audio_chunk: bytes) -> bool:
        """Check if audio chunk contains speech"""
        try:
            # WebRTC VAD expects 10ms, 20ms, or 30ms frames
            frame_duration = 30  # ms
            frame_size = int(self.config.sample_rate * frame_duration / 1000)
            
            if len(audio_chunk) < frame_size * 2:  # 2 bytes per sample
                return False
                
            # Take first frame of appropriate size
            frame = audio_chunk[:frame_size * 2]
            return self.vad.is_speech(frame, self.config.sample_rate)
        except Exception as e:
            logger.debug(f"VAD error: {e}")
            return False

class WakeWordDetector:
    """Wake word detection using keyword spotting"""
    
    def __init__(self, wake_words: List[str], sensitivity: float = 0.5):
        self.wake_words = [word.lower() for word in wake_words]
        self.sensitivity = sensitivity
        self.recognizer = sr.Recognizer()
        
        # Adjust recognizer settings
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
    def detect_wake_word(self, audio_data: bytes) -> Optional[str]:
        """Detect wake words in audio data"""
        try:
            # Convert audio data to AudioData object
            audio = sr.AudioData(audio_data, 16000, 2)
            
            # Use Google Speech Recognition (fastest for wake words)
            text = self.recognizer.recognize_google(audio, language='en-US')
            text_lower = text.lower()
            
            # Check for wake words
            for wake_word in self.wake_words:
                if wake_word in text_lower:
                    logger.info(f"Wake word detected: {wake_word}")
                    return wake_word
                    
        except sr.UnknownValueError:
            # No speech detected
            pass
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
        except Exception as e:
            logger.debug(f"Wake word detection error: {e}")
            
        return None

class VoiceDetection:
    """Main voice detection system with wake word and VAD"""
    
    def __init__(self, wake_words: List[str], config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.wake_words = wake_words
        self.is_listening = False
        self.is_recording = False
        
        # Audio components
        self.audio = None
        self.stream = None
        self.vad = VoiceActivityDetector(self.config)
        self.wake_word_detector = WakeWordDetector(wake_words)
        
        # Audio buffers
        self.audio_buffer = deque(maxlen=int(self.config.sample_rate * 10))  # 10 seconds
        self.recording_buffer = bytearray()
        
        # Threading
        self.audio_thread = None
        self.processing_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Callbacks
        self.wake_word_callback: Optional[Callable[[str], None]] = None
        self.speech_start_callback: Optional[Callable[[], None]] = None
        self.speech_end_callback: Optional[Callable[[bytes], None]] = None
        self.error_callback: Optional[Callable[[Exception], None]] = None
        
        # State tracking
        self.last_speech_time = 0
        self.speech_started = False
        self.speech_buffer = bytearray()
        
    def set_callbacks(self, 
                     wake_word_callback: Optional[Callable[[str], None]] = None,
                     speech_start_callback: Optional[Callable[[], None]] = None,
                     speech_end_callback: Optional[Callable[[bytes], None]] = None,
                     error_callback: Optional[Callable[[Exception], None]] = None):
        """Set event callbacks"""
        self.wake_word_callback = wake_word_callback
        self.speech_start_callback = speech_start_callback
        self.speech_end_callback = speech_end_callback
        self.error_callback = error_callback
        
    def start_listening(self):
        """Start voice detection system"""
        if self.is_listening:
            return
            
        try:
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
            # Open audio stream
            self.stream = self.audio.open(
                format=self.config.format,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                frames_per_buffer=self.config.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_listening = True
            self.stop_event.clear()
            
            # Start audio processing thread
            self.audio_thread = threading.Thread(target=self._audio_processing_loop, daemon=True)
            self.audio_thread.start()
            
            self.stream.start_stream()
            logger.info("Voice detection started")
            
        except Exception as e:
            logger.error(f"Failed to start voice detection: {e}")
            if self.error_callback:
                self.error_callback(e)
                
    def stop_listening(self):
        """Stop voice detection system"""
        if not self.is_listening:
            return
            
        self.is_listening = False
        self.stop_event.set()
        
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                
            if self.audio:
                self.audio.terminate()
                
            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=2.0)
                
        except Exception as e:
            logger.error(f"Error stopping voice detection: {e}")
            
        logger.info("Voice detection stopped")
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio stream callback"""
        if not self.is_listening:
            return (None, pyaudio.paComplete)
            
        try:
            # Add to processing queue
            self.processing_queue.put((in_data, time.time()))
            return (None, pyaudio.paContinue)
        except Exception as e:
            logger.error(f"Audio callback error: {e}")
            return (None, pyaudio.paAbort)
            
    def _audio_processing_loop(self):
        """Main audio processing loop"""
        while not self.stop_event.is_set():
            try:
                # Get audio data with timeout
                audio_data, timestamp = self.processing_queue.get(timeout=0.1)
                self._process_audio_chunk(audio_data, timestamp)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Audio processing error: {e}")
                if self.error_callback:
                    self.error_callback(e)
                    
    def _process_audio_chunk(self, audio_data: bytes, timestamp: float):
        """Process individual audio chunk"""
        # Add to circular buffer
        self.audio_buffer.extend(audio_data)
        
        # Voice Activity Detection
        is_speech = self.vad.is_speech(audio_data)
        
        if is_speech:
            self.last_speech_time = timestamp
            
            # Start recording if not already
            if not self.speech_started:
                self.speech_started = True
                self.speech_buffer = bytearray()
                if self.speech_start_callback:
                    self.speech_start_callback()
                    
            # Add to speech buffer
            self.speech_buffer.extend(audio_data)
            
        else:
            # Check for end of speech
            if self.speech_started:
                silence_duration = timestamp - self.last_speech_time
                
                if silence_duration > self.config.silence_timeout:
                    # End of speech detected
                    self._end_speech_recording()
                    
        # Check for wake words in recent audio
        if len(self.audio_buffer) > self.config.sample_rate * 2:  # 2 seconds
            self._check_wake_words()
            
    def _end_speech_recording(self):
        """End speech recording and process"""
        if not self.speech_started:
            return
            
        self.speech_started = False
        
        # Check minimum length
        duration = len(self.speech_buffer) / (self.config.sample_rate * 2)  # 2 bytes per sample
        
        if duration >= self.config.min_audio_length:
            speech_data = bytes(self.speech_buffer)
            
            if self.speech_end_callback:
                self.speech_end_callback(speech_data)
        else:
            logger.debug(f"Speech too short: {duration:.2f}s")
            
        self.speech_buffer.clear()
        
    def _check_wake_words(self):
        """Check recent audio for wake words"""
        try:
            # Get recent audio (last 3 seconds)
            recent_samples = int(self.config.sample_rate * 3 * 2)  # 2 bytes per sample
            recent_audio = bytes(list(self.audio_buffer)[-recent_samples:])
            
            if len(recent_audio) < recent_samples // 2:
                return
                
            # Detect wake words
            wake_word = self.wake_word_detector.detect_wake_word(recent_audio)
            
            if wake_word and self.wake_word_callback:
                self.wake_word_callback(wake_word)
                
        except Exception as e:
            logger.debug(f"Wake word check error: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            'is_listening': self.is_listening,
            'is_recording': self.speech_started,
            'buffer_size': len(self.audio_buffer),
            'wake_words': self.wake_words,
            'last_speech_time': self.last_speech_time
        }
        
    def adjust_sensitivity(self, vad_aggressiveness: int, wake_word_sensitivity: float):
        """Adjust detection sensitivity"""
        if 0 <= vad_aggressiveness <= 3:
            self.config.vad_aggressiveness = vad_aggressiveness
            self.vad = VoiceActivityDetector(self.config)
            
        if 0.0 <= wake_word_sensitivity <= 1.0:
            self.wake_word_detector.sensitivity = wake_word_sensitivity
            
    def get_audio_devices(self) -> List[Dict[str, Any]]:
        """Get available audio input devices"""
        devices = []
        if not self.audio:
            temp_audio = pyaudio.PyAudio()
        else:
            temp_audio = self.audio
            
        try:
            for i in range(temp_audio.get_device_count()):
                device_info = temp_audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'sample_rate': int(device_info['defaultSampleRate']),
                        'channels': device_info['maxInputChannels']
                    })
        finally:
            if not self.audio:
                temp_audio.terminate()
                
        return devices
        return []  # Placeholder for detected cue words

    def on_cue_word_detected(self, cue_word):
        # Code to handle the event when a cue word is detected
        pass  # Placeholder for handling cue word detection
