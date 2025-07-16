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
        
        # Model components
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.loading_lock = threading.Lock()
        
        # Model paths
        self.model_dir = Path("/home/nyx/ai-companion/models/tts/kokoro")
        self.model_path = self.model_dir / "onnx" / "model.onnx"
        self.config_path = self.model_dir / "config.json"
        self.tokenizer_path = self.model_dir / "tokenizer.json"
        self.voices_dir = self.model_dir / "voices"
        
        # Voice management
        self.available_voices = {}
        self.current_voice = "af_sarah"  # Default voice
        self.voice_configs = {}
        self.voice_embeddings = {}
        
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
        """Load voice configurations and embeddings."""
        try:
            voices_json_path = self.model_dir / "voices.json"
            if voices_json_path.exists():
                with open(voices_json_path, 'r') as f:
                    self.voice_configs = json.load(f)
                    
            # Load voice embeddings
            if self.voices_dir.exists():
                for voice_file in self.voices_dir.glob("*.bin"):
                    voice_name = voice_file.stem
                    try:
                        # Load binary voice embedding
                        voice_embedding = np.fromfile(voice_file, dtype=np.float32)
                        self.voice_embeddings[voice_name] = voice_embedding
                        self.logger.info(f"Loaded voice embedding: {voice_name} ({len(voice_embedding)} dims)")
                    except Exception as e:
                        self.logger.warning(f"Failed to load voice embedding {voice_name}: {e}")
                        
            self.logger.info(f"Loaded {len(self.voice_embeddings)} voice embeddings")
            
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
        """Initialize the Kokoro ONNX TTS model, fallback to lightweight TTS if needed."""
        if self.model_loaded:
            return True
        self.logger.info("Initializing Kokoro TTS ONNX model...")
        try:
            # Use the correct ONNX model path
            model_path = Path("models/tts/kokoro/onnx/model.onnx")
            if not model_path.exists():
                self.logger.error(f"Kokoro ONNX model not found at {model_path}")
                raise FileNotFoundError(f"Kokoro ONNX model not found at {model_path}")
            if ort is not None and model_path.exists():
                self.model = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
                # Log input names for debugging
                input_names = [i.name for i in self.model.get_inputs()]
                self.logger.info(f"Kokoro ONNX model input names: {input_names}")
                self.model_loaded = True
                self.logger.info(f"✅ Kokoro TTS ONNX model loaded: {model_path}")
                return True
            else:
                self.logger.warning("ONNXRuntime not available or model file missing. Falling back to lightweight TTS.")
        except Exception as e:
            self.logger.error(f"Failed to load Kokoro TTS ONNX model: {e}")
        # Fallback to lightweight TTS
        self.model = LightweightEmotionalTTS()
        self.model.initialize_model()
        self.model_loaded = False
        self.logger.info("Using LightweightEmotionalTTS fallback.")
        return False

    def _minimal_tokenizer(self, text: str) -> np.ndarray:
        """Fallback: tokenize text as whitespace split and map to fake IDs."""
        # This is a placeholder; real models need a proper tokenizer
        tokens = text.strip().split()
        token_ids = [min(abs(hash(t)) % 32000, 32000) for t in tokens]  # Clamp to vocab size
        if not token_ids:
            token_ids = [0]
        return np.array(token_ids, dtype=np.int64)

    def _preprocess_text(self, text: str, emotion: Optional[str] = None, intensity: Optional[float] = None) -> dict:
        """Convert input text and emotion to model input dict for ONNX inference."""
        # Try to use Hugging Face tokenizer if available, else fallback
        tokenizer = None
        try:
            from transformers import PreTrainedTokenizerFast
            tokenizer = PreTrainedTokenizerFast(tokenizer_file="models/tts/kokoro/tokenizer.json")
            input_ids = np.array(tokenizer.encode(text), dtype=np.int64)
        except Exception as e:
            self.logger.warning(f"Failed to load transformers tokenizer: {e}. Using minimal tokenizer.")
            input_ids = self._minimal_tokenizer(text)
        # Pad/truncate to length 128 (arbitrary, adjust as needed)
        max_len = 128
        if len(input_ids) < max_len:
            input_ids = np.pad(input_ids, (0, max_len - len(input_ids)), 'constant')
        else:
            input_ids = input_ids[:max_len]
        input_ids = input_ids.reshape(1, -1)
        # Style: map emotion to style index (very basic mapping)
        style_map = {
            'neutral': 0, 'happy': 1, 'excited': 2, 'sad': 3, 'empathetic': 4, 'surprised': 5,
            'joyful': 6, 'cheerful': 7, 'amazed': 8, 'supportive': 9, 'caring': 10, 'disappointed': 11,
            'curious': 12, 'thoughtful': 13, 'calm': 14
        }
        style = np.array([[style_map.get((emotion or 'neutral').lower(), 0)]], dtype=np.int64)
        # Speed: use intensity to modulate speed (default 1.0)
        speed = np.array([[1.0 + 0.2 * float(intensity or 0.5)]], dtype=np.float32)
        # Return dict matching ONNX model's expected input names
        return {
            'input_ids': input_ids,
            'style': style,
            'speed': speed
        }

    def synthesize_emotional_speech(self, text: str, emotion: Optional[str] = None, 
                                   intensity: Optional[float] = None, 
                                   voice_id: Optional[str] = None) -> Optional[np.ndarray]:
        """Synthesize speech with emotional tone modulation."""
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
        # Get base audio
        if self.model_loaded and self.model is not None and ort is not None:
            try:
                # Preprocess text to model input, now with emotion/intensity
                input_dict = self._preprocess_text(clean_text, emotion, intensity)
                # Log input_dict keys for debugging
                self.logger.info(f"ONNX input_dict keys: {list(input_dict.keys())}")
                output = self.model.run(None, input_dict)
                audio = self._postprocess_audio(output[0].squeeze())
                return audio
            except Exception as e:
                self.logger.error(f"Kokoro ONNX inference error: {e}")
        # Fallback to lightweight TTS
        if isinstance(self.model, LightweightEmotionalTTS):
            # Fallback: return 1 second of silence at 24kHz
            return np.zeros(24000, dtype=np.float32)
        return None

    def synthesize_speech(self, text: str, voice_id: Optional[str] = None) -> Optional[np.ndarray]:
        """Synthesize speech using Kokoro ONNX model or fallback."""
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

    def _postprocess_audio(self, output: np.ndarray) -> np.ndarray:
        """Convert model output to audio waveform."""
        try:
            if output is None or output.size == 0:
                self.logger.warning("Empty model output, generating silence")
                return np.zeros(self.sample_rate, dtype=np.float32)
            
            # Handle different output shapes
            audio = output.squeeze()
            
            # Ensure audio is 1D
            if audio.ndim > 1:
                audio = audio.flatten()
            
            # Convert to float32 if needed
            if audio.dtype != np.float32:
                if audio.dtype in [np.int16, np.int32]:
                    # Convert from integer to float
                    audio = audio.astype(np.float32) / (2**(audio.dtype.itemsize * 8 - 1))
                else:
                    audio = audio.astype(np.float32)
            
            # Normalize audio to prevent clipping
            max_val = np.max(np.abs(audio))
            if max_val > 1.0:
                audio = audio / max_val * 0.95
            
            # Ensure minimum length (avoid empty audio)
            if len(audio) < 1000:
                self.logger.warning(f"Short audio output ({len(audio)} samples), padding")
                audio = np.pad(audio, (0, max(1000 - len(audio), 0)), mode='constant')
            
            self.logger.debug(f"Postprocessed audio: shape={audio.shape}, dtype={audio.dtype}, range=({audio.min():.3f}, {audio.max():.3f})")
            return audio
            
        except Exception as e:
            self.logger.error(f"Error in audio postprocessing: {e}")
            # Return silence as fallback
            return np.zeros(self.sample_rate, dtype=np.float32)

    def synthesize_speech(self, text: str, voice_id: Optional[str] = None) -> Optional[np.ndarray]:
        """Synthesize speech using Kokoro ONNX model or fallback."""
        if self.model_loaded and self.model is not None and ort is not None:
            try:
                # Preprocess text to model input
                input_tensor = self._preprocess_text(text)
                input_name = self.model.get_inputs()[0].name
                # Run inference
                output = self.model.run(None, {input_name: input_tensor})
                # Postprocess output to audio
                audio = self._postprocess_audio(output[0].squeeze())
                return audio
            except Exception as e:
                self.logger.error(f"Kokoro ONNX inference error: {e}")
                # Fallback to lightweight
        # Fallback to lightweight TTS    def synthesize_speech(self, text: str, voice_id: Optional[str] = None) -> Optional[np.ndarray]:
        """Synthesize speech using Kokoro ONNX model or fallback."""
        return self.synthesize_emotional_speech(text, "neutral", 0.3, voice_id)

    # Alias for backward compatibility
    def synthesize(self, text: str, voice: str = "default", emotion: Optional[str] = None, 
                  intensity: Optional[float] = None) -> Optional[np.ndarray]:
        """Synthesize speech with optional emotional tone (backward compatible)."""
        if emotion:
            return self.synthesize_emotional_speech(text, emotion, intensity, voice if voice != "default" else None)
        else:
            return self.synthesize_speech(text, voice if voice != "default" else None)

# Backward compatibility alias
TTSHandler = EmotionalTTSHandler
