"""
Enhanced TTS handler for AI Companion application.
Manages text-to-speech synthesis using Kokoro TTS with multiple voice options and emotional tone synthesis.
Includes lightweight fallback for when full models are unavailable.
"""

import logging
import json
import io
import threading
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, BinaryIO, Tuple
import numpy as np

try:
    from kokoro_onnx import Kokoro
except ImportError:
    Kokoro = None
    
try:
    import torch
    import torchaudio
    import onnxruntime as ort
    from transformers import AutoTokenizer
except ImportError:
    torch = None
    torchaudio = None
    ort = None
    AutoTokenizer = None

try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    sd = None
    sf = None

from utils.system_detector import SystemDetector
from utils.model_downloader import ModelDownloader
from models.lightweight_emotional_tts import LightweightEmotionalTTS


class EmotionalTTSHandler:
    """
    Enhanced TTS handler with emotional tone synthesis capabilities.
    Supports emotion-based voice modulation and personality-aware speech generation.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        
        # Model components - using Kokoro library
        self.kokoro_model = None
        self.model_loaded = False
        self.loading_lock = threading.Lock()
        
        # Model paths - use user data directory
        from pathlib import Path
        import os
        user_data_dir = Path.home() / ".local" / "share" / "ai2d_chat"
        self.model_dir = user_data_dir / "models" / "tts" / "kokoro"
        
        # Kokoro model files (following official Kokoro TTS structure)
        self.onnx_model_path = self.model_dir / "kokoro-v1.0.onnx"
        self.voices_bin_path = self.model_dir / "voices-v1.0.bin"
        self.voices_json_path = self.model_dir / "voices-v1.0.json"
        
        # Voice management
        self.available_voices = {}
        self.current_voice = "af_sarah"  # Default voice
        self.voice_configs = {}
        self.voice_embeddings = {}  # Initialize voice embeddings dict
        
        # Load voice configurations
        self._load_voice_configs()
        
        # Emotional synthesis settings
        self.emotion_mappings = self._initialize_emotion_mappings()
        self.current_emotion = "neutral"
        self.emotion_intensity = 0.5
        
        # Audio settings
        self.sample_rate = 24000
        self.audio_device = None
        
        # System detection and optimization
        self.system_detector = SystemDetector()
        self.model_downloader = ModelDownloader()
        
        # Performance settings
        self.enable_streaming = True
        self.chunk_size = 1024
        
        # Audio queue for playback
        self.audio_queue = []
        self.is_playing = False
        self.playback_thread = None
    
    def _initialize_emotion_mappings(self) -> Dict[str, Dict[str, float]]:
        """Initialize emotion-to-voice parameter mappings."""
        return {
            # Positive emotions
            'excited': {
                'pitch_shift': 0.2,      # Higher pitch
                'speed_factor': 1.1,     # Slightly faster
                'volume_gain': 0.1,      # Slightly louder
                'expression_boost': 0.3   # More expressive
            },
            'happy': {
                'pitch_shift': 0.1,
                'speed_factor': 1.05,
                'volume_gain': 0.05,
                'expression_boost': 0.2
            },
            'joyful': {
                'pitch_shift': 0.15,
                'speed_factor': 1.08,
                'volume_gain': 0.08,
                'expression_boost': 0.25
            },
            'cheerful': {
                'pitch_shift': 0.08,
                'speed_factor': 1.03,
                'volume_gain': 0.03,
                'expression_boost': 0.15
            },
            
            # Surprise/wonder emotions
            'surprised': {
                'pitch_shift': 0.25,
                'speed_factor': 0.9,     # Slower for emphasis
                'volume_gain': 0.15,
                'expression_boost': 0.4
            },
            'amazed': {
                'pitch_shift': 0.2,
                'speed_factor': 0.95,
                'volume_gain': 0.1,
                'expression_boost': 0.3
            },
            
            # Empathetic/caring emotions
            'empathetic': {
                'pitch_shift': -0.1,     # Lower, warmer pitch
                'speed_factor': 0.9,     # Slower, more caring
                'volume_gain': -0.05,    # Softer
                'expression_boost': 0.2
            },
            'supportive': {
                'pitch_shift': -0.05,
                'speed_factor': 0.92,
                'volume_gain': -0.02,
                'expression_boost': 0.15
            },
            'caring': {
                'pitch_shift': -0.08,
                'speed_factor': 0.88,
                'volume_gain': -0.03,
                'expression_boost': 0.18
            },
            
            # Sad/melancholy emotions
            'sad': {
                'pitch_shift': -0.15,
                'speed_factor': 0.85,
                'volume_gain': -0.1,
                'expression_boost': 0.1
            },
            'disappointed': {
                'pitch_shift': -0.12,
                'speed_factor': 0.87,
                'volume_gain': -0.08,
                'expression_boost': 0.12
            },
            
            # Curious/thoughtful emotions
            'curious': {
                'pitch_shift': 0.05,
                'speed_factor': 0.98,
                'volume_gain': 0.02,
                'expression_boost': 0.1
            },
            'thoughtful': {
                'pitch_shift': -0.03,
                'speed_factor': 0.95,
                'volume_gain': -0.01,
                'expression_boost': 0.08
            },
            
            # Neutral/default
            'neutral': {
                'pitch_shift': 0.0,
                'speed_factor': 1.0,
                'volume_gain': 0.0,
                'expression_boost': 0.0
            },
            'calm': {
                'pitch_shift': -0.02,
                'speed_factor': 0.98,
                'volume_gain': -0.01,
                'expression_boost': 0.05
            }
        }
    
    def _load_voice_configs(self) -> None:
        """Load voice configurations (not needed with official kokoro_onnx library)."""
        # With the official kokoro_onnx library, voice embeddings are handled internally
        # The voices-v1.0.bin file contains all voice embeddings and is loaded by the Kokoro class
        try:
            # Optional: Load custom voice metadata if available
            voices_json_path = self.model_dir / "voices.json"
            if voices_json_path.exists():
                with open(voices_json_path, 'r') as f:
                    self.voice_configs = json.load(f)
                    self.logger.info(f"Loaded voice configurations from {voices_json_path}")
            else:
                self.logger.info("No custom voice config found - using defaults")
                    
        except Exception as e:
            self.logger.error(f"Failed to load voice configurations: {e}")
    
    def set_emotion(self, emotion: str, intensity: float = 0.5) -> bool:
        """Set the current emotion for TTS synthesis."""
        if emotion not in self.emotion_mappings:
            self.logger.warning(f"Unknown emotion: {emotion}, using neutral")
            emotion = "neutral"
        
        self.current_emotion = emotion
        self.emotion_intensity = max(0.0, min(1.0, intensity))
        
        self.logger.info(f"TTS emotion set to: {emotion} (intensity: {self.emotion_intensity:.2f})")
        return True
    
    def get_current_emotion(self) -> Dict[str, Union[str, float]]:
        """Get current emotion settings."""
        return {
            'emotion': self.current_emotion,
            'intensity': self.emotion_intensity,
            'parameters': self.emotion_mappings.get(self.current_emotion, {})
        }
    
    def extract_emotion_from_text(self, text: str) -> Tuple[str, float]:
        """Extract emotion tags from text and determine primary emotion."""
        # Extract emotion tags (e.g., *excited*, *empathetic*)
        emotion_pattern = r'\*([^*]+)\*'
        emotions = re.findall(emotion_pattern, text)
        
        if not emotions:
            return "neutral", 0.3
        
        # Priority mapping for emotions
        emotion_priority = {
            'excited': 10, 'happy': 9, 'joyful': 9, 'cheerful': 8,
            'surprised': 7, 'amazed': 7,
            'empathetic': 8, 'supportive': 7, 'caring': 7,
            'sad': 6, 'disappointed': 5,
            'curious': 4, 'thoughtful': 3,
            'neutral': 2, 'calm': 2
        }
        
        # Find highest priority emotion
        primary_emotion = max(emotions, key=lambda e: emotion_priority.get(e.lower(), 0))
        
        # Calculate intensity based on number of emotion tags and context
        base_intensity = len(emotions) * 0.2
        
        # Boost intensity for high-energy emotions
        high_energy_emotions = ['excited', 'amazed', 'surprised', 'joyful']
        if primary_emotion.lower() in high_energy_emotions:
            base_intensity += 0.3
        
        # Check for intensity indicators in text
        if any(word in text.lower() for word in ['!', 'amazing', 'wonderful', 'fantastic']):
            base_intensity += 0.2
        
        intensity = min(base_intensity, 1.0)
        
        return primary_emotion.lower(), intensity

    def initialize_model(self) -> bool:
        """Initialize the Kokoro TTS model using the official kokoro_onnx library."""
        if self.model_loaded:
            return True
            
        with self.loading_lock:
            if self.model_loaded:  # Double-check after acquiring lock
                return True
                
            self.logger.info("Initializing Kokoro TTS model...")
            
            try:
                # Check if Kokoro library is available
                if Kokoro is None:
                    self.logger.error("kokoro_onnx library not available. Install with: pip install kokoro-onnx")
                    raise ImportError("kokoro_onnx library not available")
                
                # Ensure model files exist
                if not self.onnx_model_path.exists():
                    self.logger.error(f"Kokoro ONNX model not found at {self.onnx_model_path}")
                    self.logger.info("Download the model with:")
                    self.logger.info("wget https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx")
                    raise FileNotFoundError(f"Kokoro ONNX model not found at {self.onnx_model_path}")
                
                # Check for voice files (prefer .bin over .json)
                voice_file = None
                if self.voices_bin_path.exists():
                    voice_file = str(self.voices_bin_path)
                    self.logger.info(f"Using voice file: {voice_file}")
                elif self.voices_json_path.exists():
                    voice_file = str(self.voices_json_path)
                    self.logger.info(f"Using voice file: {voice_file}")
                else:
                    self.logger.error(f"No voice files found. Expected at {self.voices_bin_path} or {self.voices_json_path}")
                    self.logger.info("Download voices with:")
                    self.logger.info("wget https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin")
                    raise FileNotFoundError("Voice files not found")
                
                # Initialize Kokoro model
                self.kokoro_model = Kokoro(str(self.onnx_model_path), voice_file)
                
                # Verify model is working by getting available voices
                self.available_voices = list(self.kokoro_model.get_voices())
                self.logger.info(f"✅ Kokoro TTS model loaded successfully with {len(self.available_voices)} voices")
                self.logger.info(f"Available voices: {', '.join(self.available_voices[:5])}{'...' if len(self.available_voices) > 5 else ''}")
                
                # Verify current voice is available
                if self.current_voice not in self.available_voices:
                    self.current_voice = self.available_voices[0] if self.available_voices else "af_sarah"
                    self.logger.info(f"Set voice to: {self.current_voice}")
                
                self.model_loaded = True
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to load Kokoro TTS model: {e}")
                self.logger.info("Falling back to lightweight TTS...")
                
                # Fallback to lightweight TTS
                try:
                    self.kokoro_model = LightweightEmotionalTTS()
                    self.kokoro_model.initialize_model()
                    self.model_loaded = True  # Mark as successfully loaded (fallback mode)
                    self.logger.info("✅ Using LightweightEmotionalTTS fallback")
                    return True  # Return True for successful fallback
                except Exception as fallback_error:
                    self.logger.error(f"Failed to initialize fallback TTS: {fallback_error}")
                    return False

    def _get_emotional_params(self, emotion: Optional[str], intensity: Optional[float]) -> dict:
        """Get emotional parameters for TTS synthesis."""
        params = {
            'speed': 1.0,
            'language': 'en-us',
            'voice_blend': None
        }
        
        if not emotion or emotion == 'neutral':
            return params
        
        # Get emotion mapping
        emotion_config = self.emotion_mappings.get(emotion, {})
        intensity = intensity or 0.5
        
        # Calculate speed based on emotion
        base_speed = emotion_config.get('speed_factor', 1.0)
        speed_adjustment = (base_speed - 1.0) * intensity
        params['speed'] = 1.0 + speed_adjustment
        
        # Clamp speed to reasonable range
        params['speed'] = max(0.5, min(2.0, params['speed']))
        
        return params

    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for TTS by removing emojis, symbols, and unpronounceable elements."""
        import re
        
        # Remove emojis (Unicode emoji ranges)
        emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F]|'  # Emoticons
            r'[\U0001F300-\U0001F5FF]|'  # Symbols & pictographs
            r'[\U0001F680-\U0001F6FF]|'  # Transport & map symbols
            r'[\U0001F1E0-\U0001F1FF]|'  # Flags (iOS)
            r'[\U00002702-\U000027B0]|'  # Dingbats
            r'[\U000024C2-\U0001F251]'   # Enclosed characters
        )
        
        # Remove emojis
        text = emoji_pattern.sub('', text)
        
        # Remove common chat expressions and symbols
        unwanted_patterns = [
            r'\bmmmm+\b',           # mmmmm, mmmmmm, etc.
            r'\blol\b',             # lol
            r'\bhaha+\b',           # haha, hahaha, etc.
            r'\bahh+\b',            # ahh, ahhh, etc.
            r'\buh+m*\b',           # uhm, uhhm, etc.
            r'\boh+\b',             # oh, ohh, ohhh, etc.
            r'\bmhm+\b',            # mhm, mhmm, etc.
            r'\bhmm+\b',            # hmm, hmmm, etc.
            r'\bngh+\b',            # ngh, nghhh, etc.
            r'\bungh+\b',           # ungh, unghhh, etc.
            r'~+',                  # tildes
            r'-{2,}',               # multiple dashes
            r'\*{2,}',              # multiple asterisks
            r'_{2,}',               # multiple underscores
            r'\.{3,}',              # ellipsis with more than 3 dots
            r'!{2,}',               # multiple exclamations
            r'\?{2,}',              # multiple questions
            r'[^\w\s\.\!\?\,\'\;\:\-]', # Non-standard punctuation (keep hyphens)
            r'\b[a-zA-Z]{1}\1{3,}\b',   # Repeated single letters (aaaa, bbbbb, etc.)
        ]
        
        for pattern in unwanted_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove empty emotion tags
        text = re.sub(r'\*\s*\*', '', text)
        
        # Ensure we have actual pronounceable content
        if not re.search(r'[a-zA-Z]', text):
            return "Hello"  # Fallback if no pronounceable text remains
        
        return text

    def synthesize_emotional_speech(self, text: str, emotion: Optional[str] = None, 
                                   intensity: Optional[float] = None, 
                                   voice_id: Optional[str] = None) -> Optional[np.ndarray]:
        """Synthesize speech with emotional tone modulation using Kokoro TTS."""
        if not self.model_loaded:
            if not self.initialize_model():
                self.logger.error("TTS model not initialized")
                return None
        
        # Auto-detect emotion from text if not provided
        if emotion is None:
            detected_emotion, detected_intensity = self.extract_emotion_from_text(text)
            emotion = detected_emotion
            if intensity is None:
                intensity = detected_intensity
        
        # Set emotion for synthesis
        if emotion:
            self.set_emotion(emotion, intensity or self.emotion_intensity)
        
        # Clean text of emotion tags for synthesis
        clean_text = re.sub(r'\*([^*]+)\*', '', text).strip()
        
        # Apply comprehensive text cleaning for TTS
        clean_text = self._clean_text_for_tts(clean_text)
        
        if not clean_text or len(clean_text.strip()) == 0:
            self.logger.warning("No valid text remaining after cleaning for TTS")
            return None
        
        # Get voice to use
        voice = voice_id or self.current_voice
        
        # Calculate emotional parameters
        emotion_params = self._get_emotional_params(emotion, intensity)
        
        try:
            # Use Kokoro TTS model if available (check for the create method)
            if self.model_loaded and self.kokoro_model and hasattr(self.kokoro_model, 'create'):
                self.logger.info(f"🎵 Generating TTS with Kokoro: voice={voice}, emotion={emotion}, intensity={intensity}")
                
                # Generate audio using Kokoro
                samples, sample_rate = self.kokoro_model.create(
                    clean_text, 
                    voice=voice, 
                    speed=emotion_params.get('speed', 1.0),
                    lang=emotion_params.get('language', 'en-us')
                )
                
                # Convert to numpy array if needed
                if not isinstance(samples, np.ndarray):
                    samples = np.array(samples, dtype=np.float32)
                
                # Apply additional emotional modulation
                if emotion and emotion != 'neutral':
                    samples = self._apply_emotion_modulation(samples, emotion, intensity or 0.5)
                
                self.logger.info(f"✅ Generated {len(samples)} samples at {sample_rate}Hz")
                return samples
                
            # Use lightweight TTS fallback (check for synthesize_emotional_speech method)
            elif self.model_loaded and self.kokoro_model and hasattr(self.kokoro_model, 'synthesize_emotional_speech'):
                self.logger.info(f"🎵 Generating TTS with lightweight fallback: emotion={emotion}, intensity={intensity}")
                
                samples = self.kokoro_model.synthesize_emotional_speech(clean_text, emotion, intensity)
                
                if samples is not None:
                    self.logger.info(f"✅ Generated {len(samples)} samples with lightweight TTS")
                    return samples
                else:
                    self.logger.warning("Lightweight TTS returned None")
                    return None
                
            else:
                self.logger.warning("No TTS method available")
                # Generate silence as last resort
                return self._fallback_synthesis(clean_text, emotion, intensity)
                
        except Exception as e:
            self.logger.error(f"TTS synthesis error: {e}")
            # Use fallback method
            return self._fallback_synthesis(clean_text, emotion, intensity)
    
    def _fallback_synthesis(self, text: str, emotion: Optional[str], intensity: Optional[float]) -> Optional[np.ndarray]:
        """Fallback synthesis method when Kokoro is not available."""
        try:
            if hasattr(self.kokoro_model, 'synthesize_emotional_speech'):
                # Use lightweight TTS fallback
                return self.kokoro_model.synthesize_emotional_speech(text, emotion, intensity)
            else:
                # Generate silence as last resort
                self.logger.warning("No TTS method available, generating silence")
                return np.zeros(int(self.sample_rate * 2), dtype=np.float32)  # 2 seconds of silence
        except Exception as e:
            self.logger.error(f"Fallback synthesis failed: {e}")
            return np.zeros(int(self.sample_rate * 2), dtype=np.float32)

    def synthesize_speech(self, text: str, voice_id: Optional[str] = None) -> Optional[np.ndarray]:
        """Synthesize speech using Kokoro TTS model or fallback."""
        return self.synthesize_emotional_speech(text, "neutral", 0.3, voice_id)

    def _apply_emotion_modulation(self, audio: np.ndarray, emotion: str, intensity: float) -> np.ndarray:
        """Apply emotional modulation to audio signal."""
        if emotion not in self.emotion_mappings:
            return audio
        
        emotion_params = self.emotion_mappings[emotion]
        modulated_audio = audio.copy()
        
        try:
            # Apply pitch shifting
            pitch_shift = emotion_params.get('pitch_shift', 0.0) * intensity
            if abs(pitch_shift) > 0.01:
                modulated_audio = self._pitch_shift_audio(modulated_audio, pitch_shift)
            
            # Apply speed/tempo changes
            speed_factor = 1.0 + (emotion_params.get('speed_factor', 1.0) - 1.0) * intensity
            if abs(speed_factor - 1.0) > 0.01:
                modulated_audio = self._time_stretch_audio(modulated_audio, speed_factor)
            
            # Apply volume gain
            volume_gain = emotion_params.get('volume_gain', 0.0) * intensity
            if abs(volume_gain) > 0.01:
                modulated_audio = modulated_audio * (1.0 + volume_gain)
            
            # Apply expression boost (add subtle vibrato/tremolo)
            expression_boost = emotion_params.get('expression_boost', 0.0) * intensity
            if expression_boost > 0.01:
                modulated_audio = self._add_expression(modulated_audio, expression_boost)
            
            # Normalize to prevent clipping
            max_val = np.max(np.abs(modulated_audio))
            if max_val > 0.95:
                modulated_audio = modulated_audio * (0.95 / max_val)
            
            return modulated_audio
            
        except Exception as e:
            self.logger.error(f"Error applying emotion modulation: {e}")
            return audio
    
    def _pitch_shift_audio(self, audio: np.ndarray, pitch_shift: float) -> np.ndarray:
        """Apply pitch shifting to audio (simplified implementation)."""
        try:
            # Simple pitch shifting using resampling
            # This is a basic implementation - production code would use librosa or similar
            if abs(pitch_shift) < 0.01:
                return audio
            
            # Calculate new sample rate for pitch shift
            new_rate = self.sample_rate * (1.0 + pitch_shift)
            
            # Resample audio
            if len(audio) > 0:
                # Simple linear interpolation resampling
                old_indices = np.arange(len(audio))
                new_indices = np.linspace(0, len(audio) - 1, int(len(audio) * self.sample_rate / new_rate))
                shifted_audio = np.interp(new_indices, old_indices, audio)
                
                # Pad or truncate to original length
                if len(shifted_audio) > len(audio):
                    return shifted_audio[:len(audio)]
                else:
                    padded = np.zeros(len(audio))
                    padded[:len(shifted_audio)] = shifted_audio
                    return padded
            
            return audio
            
        except Exception as e:
            self.logger.error(f"Error in pitch shifting: {e}")
            return audio
    
    def _time_stretch_audio(self, audio: np.ndarray, speed_factor: float) -> np.ndarray:
        """Apply time stretching to audio (simplified implementation)."""
        try:
            if abs(speed_factor - 1.0) < 0.01:
                return audio
            
            # Simple time stretching using resampling
            new_length = int(len(audio) / speed_factor)
            
            if new_length > 0:
                # Resample to new length
                old_indices = np.arange(len(audio))
                new_indices = np.linspace(0, len(audio) - 1, new_length)
                stretched_audio = np.interp(new_indices, old_indices, audio)
                
                # Pad or truncate to original length
                if len(stretched_audio) > len(audio):
                    return stretched_audio[:len(audio)]
                else:
                    padded = np.zeros(len(audio))
                    padded[:len(stretched_audio)] = stretched_audio
                    return padded
            
            return audio
            
        except Exception as e:
            self.logger.error(f"Error in time stretching: {e}")
            return audio
    
    def _add_expression(self, audio: np.ndarray, expression_amount: float) -> np.ndarray:
        """Add expression (vibrato/tremolo) to audio."""
        try:
            if expression_amount < 0.01:
                return audio
            
            # Add subtle vibrato (pitch modulation)
            t = np.arange(len(audio)) / self.sample_rate
            vibrato_freq = 4.0 + expression_amount * 2.0  # 4-6 Hz vibrato
            vibrato_depth = expression_amount * 0.02  # Subtle depth
            
            vibrato = np.sin(2 * np.pi * vibrato_freq * t) * vibrato_depth
            
            # Apply vibrato by modulating the audio
            for i in range(1, len(audio)):
                phase_shift = vibrato[i] * 0.1
                if i - int(phase_shift) >= 0 and i - int(phase_shift) < len(audio):
                    audio[i] = audio[i] * (1.0 + phase_shift)
            
            # Add subtle tremolo (amplitude modulation)
            tremolo_freq = 3.0 + expression_amount * 1.5  # 3-4.5 Hz tremolo
            tremolo_depth = expression_amount * 0.05
            
            tremolo = np.sin(2 * np.pi * tremolo_freq * t) * tremolo_depth
            audio = audio * (1.0 + tremolo)
            
            return audio
            
        except Exception as e:
            self.logger.error(f"Error adding expression: {e}")
            return audio

    # Backward compatibility alias
    def synthesize(self, text: str, voice: str = "default", emotion: Optional[str] = None, 
                  intensity: Optional[float] = None) -> Optional[np.ndarray]:
        """Synthesize speech with optional emotional tone (backward compatible)."""
        if emotion:
            return self.synthesize_emotional_speech(text, emotion, intensity, voice if voice != "default" else None)
        else:
            return self.synthesize_speech(text, voice if voice != "default" else None)


# Backward compatibility alias
TTSHandler = EmotionalTTSHandler
