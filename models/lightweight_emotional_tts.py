#!/usr/bin/env python3
"""
Lightweight Emotional TTS Handler
Provides basic emotional text-to-speech without external dependencies
"""

import time
import logging
import base64
import numpy as np
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class LightweightEmotionalTTS:
    """
    Lightweight emotional TTS that modifies text presentation for emotional effect
    This is a fallback implementation when full TTS models are not available
    """
    
    def __init__(self):
        self.is_initialized = False
        self.emotion_modifiers = {
            'excited': {'pitch_mod': 1.2, 'speed_mod': 1.1, 'volume_mod': 1.1},
            'happy': {'pitch_mod': 1.1, 'speed_mod': 1.0, 'volume_mod': 1.0},
            'sad': {'pitch_mod': 0.9, 'speed_mod': 0.8, 'volume_mod': 0.8},
            'empathetic': {'pitch_mod': 0.95, 'speed_mod': 0.9, 'volume_mod': 0.9},
            'surprised': {'pitch_mod': 1.3, 'speed_mod': 1.2, 'volume_mod': 1.1},
            'curious': {'pitch_mod': 1.05, 'speed_mod': 1.0, 'volume_mod': 1.0},
            'supportive': {'pitch_mod': 0.98, 'speed_mod': 0.95, 'volume_mod': 1.0},
            'neutral': {'pitch_mod': 1.0, 'speed_mod': 1.0, 'volume_mod': 1.0}
        }
        
    def initialize_model(self) -> bool:
        """Initialize the lightweight TTS system"""
        try:
            logger.info("Initializing Lightweight Emotional TTS...")
            # No model loading needed for lightweight version
            self.is_initialized = True
            logger.info("✅ Lightweight Emotional TTS initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Lightweight TTS: {e}")
            return False
    
    def synthesize_emotional_speech(self, text: str, emotion: Optional[str] = None, intensity: Optional[float] = None) -> Optional[np.ndarray]:
        """
        Synthesize emotional speech and return numpy array (compatible with main TTS handler)
        Since this is lightweight, we generate silence with metadata for compatibility
        """
        import numpy as np
        
        if not self.is_initialized:
            if not self.initialize_model():
                return None
        
        try:
            # Clean text and validate
            if not text or len(text.strip()) == 0:
                return None
            
            emotion = emotion or 'neutral'
            intensity = intensity or 0.5
            
            # Get emotion modifiers for metadata
            emotion_config = self.emotion_modifiers.get(emotion, self.emotion_modifiers['neutral'])
            
            # Generate a short audio duration based on text length
            # Rough estimation: ~150 words per minute, 24kHz sample rate
            words = len(text.split())
            duration_seconds = max(1.0, min(10.0, words / 2.5))  # 1-10 seconds range
            sample_rate = 24000
            num_samples = int(duration_seconds * sample_rate)
            
            # Generate silence audio (lightweight TTS doesn't produce actual speech)
            audio_data = np.zeros(num_samples, dtype=np.float32)
            
            logger.info(f"🎭 Generated lightweight TTS: {emotion} ({intensity:.2f}) - {duration_seconds:.1f}s for '{text[:50]}...'")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error in lightweight emotional synthesis: {e}")
            return None

    def synthesize_emotional(self, text: str, emotion: str = 'neutral', intensity: float = 0.5) -> Optional[str]:
        """
        Synthesize emotional speech (lightweight version returns modified text metadata)
        """
        if not self.is_initialized:
            logger.warning("TTS not initialized, attempting to initialize...")
            if not self.initialize_model():
                return None
        
        try:
            # Get emotion modifiers
            emotion_config = self.emotion_modifiers.get(emotion, self.emotion_modifiers['neutral'])
            
            # Apply intensity scaling
            pitch_mod = 1.0 + (emotion_config['pitch_mod'] - 1.0) * intensity
            speed_mod = 1.0 + (emotion_config['speed_mod'] - 1.0) * intensity
            volume_mod = 1.0 + (emotion_config['volume_mod'] - 1.0) * intensity
            
            # Create emotional speech metadata
            speech_data = {
                'text': text,
                'emotion': emotion,
                'intensity': intensity,
                'modifiers': {
                    'pitch': pitch_mod,
                    'speed': speed_mod,
                    'volume': volume_mod
                },
                'timestamp': time.time(),
                'type': 'lightweight_emotional'
            }
            
            # Encode as base64 JSON for compatibility with audio data format
            import json
            speech_json = json.dumps(speech_data)
            speech_b64 = base64.b64encode(speech_json.encode('utf-8')).decode('utf-8')
            
            logger.info(f"🎭 Generated emotional speech: {emotion} ({intensity:.2f}) for '{text[:50]}...'")
            return speech_b64
            
        except Exception as e:
            logger.error(f"Error in emotional synthesis: {e}")
            return None
    
    def synthesize(self, text: str, voice: str = 'default') -> Optional[str]:
        """Regular synthesis (fallback to neutral emotion)"""
        return self.synthesize_emotional(text, 'neutral', 0.5)
    
    def get_available_emotions(self) -> list:
        """Get list of available emotions"""
        return list(self.emotion_modifiers.keys())
    
    def get_emotion_config(self, emotion: str) -> Dict[str, float]:
        """Get configuration for a specific emotion"""
        return self.emotion_modifiers.get(emotion, self.emotion_modifiers['neutral'])
