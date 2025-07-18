"""
Enhanced Voice Activity Detection using Pyannote and faster-whisper.

This module provides advanced VAD capabilities for better audio processing
in single-speaker AI companion environments.
"""

import logging
import numpy as np
import torch
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import time
import io
import wave
from pathlib import Path
from tqdm import tqdm
import sys
import os
import json

try:
    from pyannote.audio import Pipeline
    from pyannote.audio.pipelines.utils.hook import ProgressHook
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    logging.warning("Pyannote not available. Install with: pip install pyannote.audio")

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logging.warning("faster-whisper not available. Install with: pip install faster-whisper")

try:
    from silero_vad import load_silero_vad, get_speech_timestamps
    SILERO_AVAILABLE = True
except ImportError:
    SILERO_AVAILABLE = False
    logging.warning("Silero VAD not available. Install with: pip install silero-vad torch torchaudio")

from .voice_detection import AudioConfig, VoiceActivity
from .model_registry import model_registry

logger = logging.getLogger(__name__)

class ModelCacheManager:
    """Manages caching of downloaded models to avoid re-downloading"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            # Use user data directory
            from pathlib import Path
            cache_dir = str(Path.home() / ".local" / "share" / "ai-companion" / "models")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_info_file = self.cache_dir / "model_cache.json"
        self.cache_info = self._load_cache_info()
    
    def _load_cache_info(self) -> Dict[str, Any]:
        """Load cache information from file"""
        if self.cache_info_file.exists():
            try:
                with open(self.cache_info_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache info: {e}")
        return {}
    
    def _save_cache_info(self):
        """Save cache information to file"""
        try:
            with open(self.cache_info_file, 'w') as f:
                json.dump(self.cache_info, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache info: {e}")
    
    def is_model_cached(self, model_name: str) -> bool:
        """Check if a model is already cached"""
        if model_name in self.cache_info:
            cache_entry = self.cache_info[model_name]
            model_path = self.cache_dir / cache_entry.get("path", "")
            return model_path.exists()
        return False
    
    def get_cached_model_path(self, model_name: str) -> Optional[Path]:
        """Get the path to a cached model"""
        if self.is_model_cached(model_name):
            cache_entry = self.cache_info[model_name]
            return self.cache_dir / cache_entry["path"]
        return None
    
    def add_to_cache(self, model_name: str, model_path: Path, metadata: Dict[str, Any] = None):
        """Add a model to the cache registry"""
        rel_path = model_path.relative_to(self.cache_dir) if model_path.is_relative_to(self.cache_dir) else model_path
        self.cache_info[model_name] = {
            "path": str(rel_path),
            "cached_at": time.time(),
            "metadata": metadata or {}
        }
        self._save_cache_info()
    
    def get_model_cache_dir(self, model_name: str) -> Path:
        """Get the cache directory for a specific model"""
        # Create subdirectory for each model
        model_dir = self.cache_dir / model_name.replace("/", "_").replace(":", "_")
        model_dir.mkdir(parents=True, exist_ok=True)
        return model_dir

@dataclass
class EnhancedVADConfig:
    """Configuration for enhanced VAD system"""
    # VAD Engine Selection
    vad_engine: str = "pyannote"  # "pyannote", "silero", "hybrid"
    
    # Pyannote VAD settings
    vad_model: str = "pyannote/segmentation-3.0"
    vad_onset_threshold: float = 0.5
    vad_offset_threshold: float = 0.5
    vad_min_duration_on: float = 0.1  # seconds
    vad_min_duration_off: float = 0.1  # seconds
    
    # Silero VAD settings
    silero_threshold: float = 0.5
    silero_min_speech_duration_ms: int = 250
    silero_max_speech_duration_s: int = 30
    silero_min_silence_duration_ms: int = 100
    silero_window_size_samples: int = 1536  # 96ms at 16kHz
    
    # Diarization settings (for speaker verification)
    enable_diarization: bool = True
    diarization_model: str = "pyannote/speaker-diarization-3.1"
    min_speakers: int = 1
    max_speakers: int = 2  # User + possible background speaker
    speaker_verification_enabled: bool = True
    
    # faster-whisper settings
    stt_model: str = "small"
    stt_language: str = "en"
    stt_device: str = "auto"
    stt_compute_type: str = "float16"  # int8, int16, float16, float32
    stt_cpu_threads: int = 0  # 0 = auto
    
    # Audio processing
    sample_rate: int = 16000
    chunk_duration: float = 1.0  # seconds per chunk for processing
    min_speech_duration: float = 0.5  # minimum speech duration to process
    max_speech_duration: float = 30.0  # maximum speech duration
    silence_threshold: float = 0.01

class PyannoteVAD:
    """Enhanced VAD using Pyannote Audio"""
    
    def __init__(self, config: EnhancedVADConfig):
        self.config = config
        self.vad_pipeline = None
        self.diarization_pipeline = None
        self.device = self._get_device()
        self.cache_manager = ModelCacheManager()
        
        if PYANNOTE_AVAILABLE:
            self._load_models()
        else:
            raise RuntimeError("Pyannote not available. Cannot use enhanced VAD.")
    
    def _get_device(self) -> str:
        """Determine best device for processing"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _load_models(self):
        """Load Pyannote models with progress tracking and caching"""
        try:
            # Check if VAD model is cached
            vad_model_name = self.config.vad_model
            if self.cache_manager.is_model_cached(vad_model_name):
                print(f"✅ Found cached VAD model: {vad_model_name}")
                # For Pyannote, we still need to download but the HuggingFace cache should handle it
                vad_loaded = False  # Still try to load normally, cache will be used automatically
            else:
                vad_loaded = False
            
            if not vad_loaded:
                print(f"\n🔄 Downloading Pyannote VAD model: {vad_model_name}")
                
                # Try different authentication methods
                auth_methods = [
                    None,  # No auth
                    True,  # Use saved token
                    "hf_token_none",  # Placeholder
                ]
                
                with tqdm(total=len(auth_methods), desc="🔍 Trying authentication methods", leave=False) as auth_pbar:
                    for i, auth_method in enumerate(auth_methods):
                        try:
                            auth_pbar.set_description(f"🔑 Auth method {i+1}/{len(auth_methods)}")
                            
                            # Create progress hook for model loading
                            if PYANNOTE_AVAILABLE and hasattr(Pipeline, 'from_pretrained'):
                                print(f"   📥 Downloading VAD model (method {i+1})...")
                                
                                # Download to cache directory
                                cache_dir = self.cache_manager.get_model_cache_dir(vad_model_name)
                                
                                self.vad_pipeline = Pipeline.from_pretrained(
                                    vad_model_name,
                                    use_auth_token=auth_method,
                                    cache_dir=str(cache_dir)
                                )
                                vad_loaded = True
                                print(f"   ✅ Pyannote VAD model downloaded and cached!")
                                
                                # Add to cache registry
                                self.cache_manager.add_to_cache(
                                    vad_model_name, 
                                    cache_dir,
                                    {"model_type": "vad", "auth_method": str(auth_method)}
                                )
                                
                                auth_pbar.update(len(auth_methods) - i)  # Complete the progress bar
                                break
                        except Exception as e:
                            logger.debug(f"Auth method {auth_method} failed: {e}")
                            auth_pbar.update(1)
                            continue
            
            if not vad_loaded:
                print("   ⚠️  Could not load Pyannote VAD model, creating mock pipeline for testing")
                self.vad_pipeline = self._create_mock_vad_pipeline()
            
            # Handle diarization model
            if self.config.enable_diarization:
                diarization_model_name = self.config.diarization_model
                
                # Check if diarization model is cached
                if self.cache_manager.is_model_cached(diarization_model_name):
                    print(f"✅ Found cached diarization model: {diarization_model_name}")
                    # For Pyannote, we still need to download but the HuggingFace cache should handle it
                    diarization_loaded = False  # Still try to load normally, cache will be used automatically
                else:
                    diarization_loaded = False
                
                if not diarization_loaded:
                    print(f"\n🔄 Downloading Pyannote diarization model: {diarization_model_name}")
                    
                    auth_methods = [None, True, "hf_token_none"]
                    with tqdm(total=len(auth_methods), desc="🔍 Trying diarization auth", leave=False) as dia_pbar:
                        for i, auth_method in enumerate(auth_methods):
                            try:
                                dia_pbar.set_description(f"🔑 Auth method {i+1}/{len(auth_methods)}")
                                
                                print(f"   📥 Downloading diarization model (method {i+1})...")
                                
                                # Download to cache directory
                                cache_dir = self.cache_manager.get_model_cache_dir(diarization_model_name)
                                
                                self.diarization_pipeline = Pipeline.from_pretrained(
                                    diarization_model_name,
                                    use_auth_token=auth_method,
                                    cache_dir=str(cache_dir)
                                )
                                diarization_loaded = True
                                print(f"   ✅ Pyannote diarization model downloaded and cached!")
                                
                                # Add to cache registry
                                self.cache_manager.add_to_cache(
                                    diarization_model_name, 
                                    cache_dir,
                                    {"model_type": "diarization", "auth_method": str(auth_method)}
                                )
                                
                                dia_pbar.update(len(auth_methods) - i)  # Complete the progress bar
                                break
                            except Exception as e:
                                logger.debug(f"Diarization auth method {auth_method} failed: {e}")
                                dia_pbar.update(1)
                                continue
                
                if not diarization_loaded:
                    print("   ⚠️  Could not load Pyannote diarization model, creating mock pipeline for testing")
                    self.diarization_pipeline = self._create_mock_diarization_pipeline()
                
            print("✅ Pyannote models loading completed!")
            
        except Exception as e:
            logger.error(f"Failed to load Pyannote models: {e}")
            # Create mock pipelines for testing
            print("⚠️  Creating mock pipelines for testing purposes")
            self.vad_pipeline = self._create_mock_vad_pipeline()
            if self.config.enable_diarization:
                self.diarization_pipeline = self._create_mock_diarization_pipeline()
    
    def detect_voice_activity(self, audio_data: bytes) -> List[VoiceActivity]:
        """Detect voice activity in audio data"""
        if not self.vad_pipeline:
            return []
        
        try:
            # Convert audio to temporary file for Pyannote
            audio_file = self._bytes_to_audio_file(audio_data)
            
            # Run VAD
            vad_result = self.vad_pipeline(audio_file)
            
            # Convert to VoiceActivity objects
            activities = []
            for segment in vad_result.get_timeline():
                activities.append(VoiceActivity(
                    is_speech=True,
                    confidence=1.0,  # Pyannote doesn't provide segment-level confidence
                    audio_data=self._extract_segment_audio(audio_data, segment.start, segment.end),
                    timestamp=segment.start
                ))
            
            return activities
            
        except Exception as e:
            logger.error(f"VAD detection error: {e}")
            return []
    
    def analyze_speakers(self, audio_data: bytes) -> Dict[str, Any]:
        """Analyze speakers in audio (for single-speaker verification)"""
        if not self.diarization_pipeline:
            return {"speaker_count": 1, "primary_speaker": "SPEAKER_00"}
        
        try:
            audio_file = self._bytes_to_audio_file(audio_data)
            
            # Run diarization
            diarization = self.diarization_pipeline(audio_file)
            
            # Analyze results
            speakers = set()
            speaker_durations = {}
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speakers.add(speaker)
                duration = turn.end - turn.start
                speaker_durations[speaker] = speaker_durations.get(speaker, 0) + duration
            
            # Find primary speaker (longest duration)
            primary_speaker = max(speaker_durations.items(), key=lambda x: x[1])[0] if speaker_durations else "SPEAKER_00"
            
            return {
                "speaker_count": len(speakers),
                "primary_speaker": primary_speaker,
                "speaker_durations": speaker_durations,
                "total_duration": sum(speaker_durations.values())
            }
        except Exception as e:
            logger.error(f"Speaker analysis error: {e}")
            return {"speaker_count": 1, "primary_speaker": "SPEAKER_00"}
    
    def _bytes_to_audio_file(self, audio_data: bytes) -> Dict[str, Any]:
        """Convert audio bytes to format suitable for Pyannote"""
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # For mock pipelines, just return a simple dict
        # For real Pyannote pipelines, return proper format
        return {
            "waveform": torch.from_numpy(audio_array).unsqueeze(0),
            "sample_rate": self.config.sample_rate,
            "duration": len(audio_array) / self.config.sample_rate
        }
    
    def _extract_segment_audio(self, audio_data: bytes, start: float, end: float) -> bytes:
        """Extract audio segment between start and end times"""
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        start_sample = int(start * self.config.sample_rate)
        end_sample = int(end * self.config.sample_rate)
        segment = audio_array[start_sample:end_sample]
        return segment.tobytes()

    def _create_mock_vad_pipeline(self):
        """Create a mock VAD pipeline for testing when real models can't be loaded"""
        class MockVADPipeline:
            def __call__(self, audio_file):
                # Create a mock timeline with some voice activity
                class MockSegment:
                    def __init__(self, start, end):
                        self.start = start
                        self.end = end
                
                class MockTimeline:
                    def __init__(self):
                        # Create some mock voice activity segments
                        self.segments = [
                            MockSegment(0.5, 1.5),  # Voice from 0.5s to 1.5s
                            MockSegment(2.0, 3.0),  # Voice from 2.0s to 3.0s
                        ]
                    
                    def get_timeline(self):
                        return self.segments
                
                return MockTimeline()
        
        return MockVADPipeline()
    
    def _create_mock_diarization_pipeline(self):
        """Create a mock diarization pipeline for testing"""
        class MockDiarizationPipeline:
            def __call__(self, audio_file):
                # Create mock diarization result
                class MockTurn:
                    def __init__(self, start, end):
                        self.start = start
                        self.end = end
                
                class MockDiarization:
                    def __init__(self):
                        self.turns = [
                            (MockTurn(0.0, 2.0), None, "SPEAKER_00"),
                            (MockTurn(2.0, 4.0), None, "SPEAKER_00"),
                        ]
                    
                    def itertracks(self, yield_label=False):
                        for turn, _, speaker in self.turns:
                            if yield_label:
                                yield turn, None, speaker
                            else:
                                yield turn, None
                
                return MockDiarization()
        
        return MockDiarizationPipeline()

class SileroVAD:
    """Fast VAD using Silero VAD"""
    
    def __init__(self, config: EnhancedVADConfig):
        self.config = config
        self.model = None
        self.device = self._get_device()
        self.cache_manager = ModelCacheManager()
        
        if SILERO_AVAILABLE:
            self._load_model()
        else:
            raise RuntimeError("Silero VAD not available. Cannot use Silero VAD.")
    
    def _get_device(self) -> str:
        """Determine best device for processing"""
        if torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"
    
    def _load_model(self):
        """Load Silero VAD model with progress tracking and caching"""
        try:
            model_name = f"silero_vad_{self.device}"
            
            # Check if model is already loaded in global registry
            if model_registry.has_model(model_name):
                print(f"✅ Using cached Silero VAD model from memory")
                self.model = model_registry.get_model(model_name)
                return
            
            # Check if this is first load for this session
            if self.cache_manager.is_model_cached("silero_vad"):
                print(f"✅ Found cached Silero VAD model (loading into memory)")
            else:
                print(f"\n🔄 Loading Silero VAD model (first time)")
            
            with tqdm(total=100, desc="📥 Loading Silero model", unit="%") as pbar:
                pbar.update(30)  # Model selection
                
                logger.info("Loading Silero VAD model")
                self.model = load_silero_vad()
                pbar.update(50)  # Model loaded
                
                self.model.to(self.device)
                pbar.update(20)  # Model moved to device
                
                # Store in global registry
                model_registry.set_model(model_name, self.model)
                
                # Mark as cached if not already
                if not self.cache_manager.is_model_cached("silero_vad"):
                    cache_dir = self.cache_manager.get_model_cache_dir("silero_vad")
                    self.cache_manager.add_to_cache(
                        "silero_vad",
                        cache_dir,
                        {"model_type": "silero_vad", "device": self.device}
                    )
                
            print(f"   ✅ Silero VAD model loaded successfully on {self.device}")
            logger.info("Silero VAD model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD model: {e}")
            raise
    
    def detect_voice_activity(self, audio_data: bytes) -> List[VoiceActivity]:
        """Detect voice activity using Silero VAD"""
        if not self.model:
            return []
        
        try:
            # Convert audio bytes to tensor
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            audio_tensor = torch.from_numpy(audio_array).to(self.device)
            
            # Get speech timestamps
            speech_timestamps = get_speech_timestamps(
                audio_tensor,
                self.model,
                threshold=self.config.silero_threshold,
                min_speech_duration_ms=self.config.silero_min_speech_duration_ms,
                max_speech_duration_s=self.config.silero_max_speech_duration_s,
                min_silence_duration_ms=self.config.silero_min_silence_duration_ms,
                window_size_samples=self.config.silero_window_size_samples,
                speech_pad_ms=30
            )
            
            # Convert to VoiceActivity objects
            activities = []
            for timestamp in speech_timestamps:
                start_time = timestamp['start'] / self.config.sample_rate
                end_time = timestamp['end'] / self.config.sample_rate
                
                # Extract audio segment
                segment_audio = self._extract_segment_audio(audio_data, start_time, end_time)
                
                activities.append(VoiceActivity(
                    is_speech=True,
                    confidence=0.8,  # Silero doesn't provide confidence scores
                    audio_data=segment_audio,
                    timestamp=start_time
                ))
            
            return activities
            
        except Exception as e:
            logger.error(f"Silero VAD detection error: {e}")
            return []
    
    def analyze_speakers(self, audio_data: bytes) -> Dict[str, Any]:
        """Analyze speakers (Silero doesn't support diarization, return single speaker)"""
        return {"speaker_count": 1, "primary_speaker": "SPEAKER_00"}
    
    def _extract_segment_audio(self, audio_data: bytes, start: float, end: float) -> bytes:
        """Extract audio segment between start and end times"""
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        start_sample = int(start * self.config.sample_rate)
        end_sample = int(end * self.config.sample_rate)
        
        segment = audio_array[start_sample:end_sample]
        return segment.tobytes()

class HybridVAD:
    """Hybrid VAD combining Silero (fast) and Pyannote (accurate)"""
    
    def __init__(self, config: EnhancedVADConfig):
        self.config = config
        self.silero_vad = None
        self.pyannote_vad = None
        
        # Initialize available VAD engines
        if SILERO_AVAILABLE:
            try:
                self.silero_vad = SileroVAD(config)
                logger.info("Silero VAD initialized for hybrid mode")
            except Exception as e:
                logger.warning(f"Failed to initialize Silero VAD: {e}")
        
        if PYANNOTE_AVAILABLE:
            try:
                self.pyannote_vad = PyannoteVAD(config)
                logger.info("Pyannote VAD initialized for hybrid mode")
            except Exception as e:
                logger.warning(f"Failed to initialize Pyannote VAD: {e}")
    
    def detect_voice_activity(self, audio_data: bytes) -> List[VoiceActivity]:
        """Detect voice activity using hybrid approach"""
        # Strategy: Use Silero for fast initial detection, then Pyannote for refinement
        
        if not self.silero_vad and not self.pyannote_vad:
            logger.error("No VAD engines available")
            return []
        
        # Step 1: Fast detection with Silero
        if self.silero_vad:
            silero_activities = self.silero_vad.detect_voice_activity(audio_data)
            
            # If no speech detected by Silero, return empty
            if not silero_activities:
                return []
            
            # Step 2: Refine with Pyannote if available
            if self.pyannote_vad and len(audio_data) < 1024 * 1024:  # Only for smaller audio chunks
                pyannote_activities = self.pyannote_vad.detect_voice_activity(audio_data)
                
                # Combine results (prefer Pyannote for accuracy)
                return self._merge_vad_results(silero_activities, pyannote_activities)
            
            return silero_activities
        
        # Fallback to Pyannote only
        elif self.pyannote_vad:
            return self.pyannote_vad.detect_voice_activity(audio_data)
        
        return []
    
    def analyze_speakers(self, audio_data: bytes) -> Dict[str, Any]:
        """Analyze speakers using best available method"""
        if self.pyannote_vad:
            return self.pyannote_vad.analyze_speakers(audio_data)
        elif self.silero_vad:
            return self.silero_vad.analyze_speakers(audio_data)
        else:
            return {"speaker_count": 1, "primary_speaker": "SPEAKER_00"}
    
    def _merge_vad_results(self, silero_results: List[VoiceActivity], pyannote_results: List[VoiceActivity]) -> List[VoiceActivity]:
        """Merge VAD results from both engines"""
        if not pyannote_results:
            return silero_results
        
        if not silero_results:
            return pyannote_results
        
        # Use Pyannote results as they're more accurate
        # But ensure we don't miss segments detected by Silero
        merged = list(pyannote_results)
        
        for silero_activity in silero_results:
            # Check if this segment overlaps with any Pyannote segment
            overlaps = any(
                abs(silero_activity.timestamp - pyannote_activity.timestamp) < 0.5
                for pyannote_activity in pyannote_results
            )
            
            if not overlaps:
                merged.append(silero_activity)
        
        # Sort by timestamp
        merged.sort(key=lambda x: x.timestamp)
        return merged

class FasterWhisperSTT:
    """Enhanced STT using faster-whisper"""
    
    def __init__(self, config: EnhancedVADConfig):
        self.config = config
        self.model = None
        self.device = self._get_device()
        self.cache_manager = ModelCacheManager()
        
        if FASTER_WHISPER_AVAILABLE:
            self._load_model()
        else:
            raise RuntimeError("faster-whisper not available. Cannot use enhanced STT.")
    
    def _get_device(self) -> str:
        """Determine best device for Whisper"""
        if self.config.stt_device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        return self.config.stt_device
    
    def _load_model(self):
        """Load faster-whisper model with progress tracking and caching"""
        try:
            model_name = f"faster_whisper_{self.config.stt_model}_{self.device}_{self.config.stt_compute_type}"
            
            # Check if model is already loaded in global registry
            if model_registry.has_model(model_name):
                print(f"✅ Using cached faster-whisper model: {self.config.stt_model} from memory")
                self.model = model_registry.get_model(model_name)
                return
            
            # Check if this is first load for this session
            cache_key = f"faster_whisper_{self.config.stt_model}"
            if self.cache_manager.is_model_cached(cache_key):
                print(f"✅ Found cached faster-whisper model: {self.config.stt_model} (loading into memory)")
            else:
                print(f"\n🔄 Loading faster-whisper model: {self.config.stt_model} (first time)")
            
            with tqdm(total=100, desc="📥 Loading Whisper model", unit="%") as pbar:
                pbar.update(20)  # Model selection
                
                self.model = WhisperModel(
                    self.config.stt_model,
                    device=self.device,
                    compute_type=self.config.stt_compute_type,
                    cpu_threads=self.config.stt_cpu_threads if self.device == "cpu" else 0
                )
                
                pbar.update(80)  # Model loading complete
                
                # Store in global registry
                model_registry.set_model(model_name, self.model)
                
                # Mark as cached if not already
                if not self.cache_manager.is_model_cached(cache_key):
                    cache_dir = self.cache_manager.get_model_cache_dir(cache_key)
                    self.cache_manager.add_to_cache(
                        cache_key,
                        cache_dir,
                        {
                            "model_type": "faster_whisper",
                            "model_size": self.config.stt_model,
                            "device": self.device,
                            "compute_type": self.config.stt_compute_type
                        }
                    )
                
            print(f"   ✅ faster-whisper model loaded on {self.device}")
            logger.info(f"faster-whisper model loaded on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load faster-whisper model: {e}")
            raise
    
    def transcribe(self, audio_data: bytes, language: str = "en") -> Dict[str, Any]:
        """Transcribe audio using faster-whisper"""
        if not self.model:
            return {"text": "", "confidence": 0.0, "error": "Model not loaded"}
        
        start_time = time.time()
        
        try:
            # Convert audio bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe
            segments, info = self.model.transcribe(
                audio_array,
                language=language if language != "auto" else None,
                vad_filter=True,  # Use built-in VAD
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    max_speech_duration_s=30
                )
            )
            
            # Combine segments
            text_segments = []
            total_confidence = 0.0
            segment_count = 0
            
            for segment in segments:
                text_segments.append(segment.text.strip())
                # faster-whisper provides average log probability
                if hasattr(segment, 'avg_logprob'):
                    # Convert log probability to confidence (approximate)
                    confidence = min(1.0, max(0.0, (segment.avg_logprob + 1.0)))
                    total_confidence += confidence
                    segment_count += 1
            
            full_text = " ".join(text_segments).strip()
            avg_confidence = total_confidence / segment_count if segment_count > 0 else 0.0
            processing_time = time.time() - start_time
            
            return {
                "text": full_text,
                "confidence": avg_confidence,
                "language": info.language,
                "language_probability": info.language_probability,
                "processing_time": processing_time,
                "segments": len(text_segments)
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"faster-whisper transcription error: {e}")
            
            return {
                "text": "",
                "confidence": 0.0,
                "error": str(e),
                "processing_time": processing_time
            }

class EnhancedAudioPipeline:
    """Enhanced audio pipeline with Pyannote VAD and faster-whisper"""
    
    def __init__(self, config: Optional[EnhancedVADConfig] = None):
        self.config = config or EnhancedVADConfig()
        
        # Initialize components
        self.vad = None
        self.stt = None
        self.user_speaker_profile = None  # For speaker verification
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize VAD and STT components"""
        try:
            # Initialize VAD based on engine selection
            if self.config.vad_engine == "pyannote" and PYANNOTE_AVAILABLE:
                self.vad = PyannoteVAD(self.config)
                logger.info("Pyannote VAD initialized")
            elif self.config.vad_engine == "silero" and SILERO_AVAILABLE:
                self.vad = SileroVAD(self.config)
                logger.info("Silero VAD initialized")
            elif self.config.vad_engine == "hybrid":
                self.vad = HybridVAD(self.config)
                logger.info("Hybrid VAD initialized")
            else:
                # Fallback to available engines
                if PYANNOTE_AVAILABLE:
                    self.vad = PyannoteVAD(self.config)
                    logger.info("Fallback to Pyannote VAD")
                elif SILERO_AVAILABLE:
                    self.vad = SileroVAD(self.config)
                    logger.info("Fallback to Silero VAD")
                else:
                    logger.warning("No enhanced VAD engines available")
            
            if FASTER_WHISPER_AVAILABLE:
                self.stt = FasterWhisperSTT(self.config)
                logger.info("Enhanced STT initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize enhanced pipeline: {e}")
            raise
    
    def process_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """Process audio through enhanced pipeline"""
        result = {
            "vad_activities": [],
            "speaker_analysis": {},
            "transcription": {},
            "is_user_speaking": False,
            "processing_time": 0
        }
        
        start_time = time.time()
        
        try:
            # Step 1: Voice Activity Detection
            if self.vad:
                activities = self.vad.detect_voice_activity(audio_data)
                result["vad_activities"] = activities
                
                # Step 2: Speaker Analysis (if speech detected)
                if activities:
                    speaker_analysis = self.vad.analyze_speakers(audio_data)
                    result["speaker_analysis"] = speaker_analysis
                    
                    # Determine if user is speaking (single speaker assumption)
                    result["is_user_speaking"] = (
                        speaker_analysis.get("speaker_count", 0) <= 1 and
                        speaker_analysis.get("total_duration", 0) > 0.5
                    )
            
            # Step 3: Transcription (if user is speaking)
            if result["is_user_speaking"] and self.stt:
                transcription = self.stt.transcribe(audio_data)
                result["transcription"] = transcription
            
            result["processing_time"] = time.time() - start_time
            
        except Exception as e:
            result["error"] = str(e)
            result["processing_time"] = time.time() - start_time
            logger.error(f"Enhanced pipeline processing error: {e}")
        
        return result
    
    def calibrate_user_voice(self, audio_samples: List[bytes]) -> bool:
        """Calibrate system to user's voice for better detection"""
        try:
            if not self.vad:
                return False
            
            # Analyze multiple samples to create user profile
            speaker_profiles = []
            for sample in audio_samples:
                analysis = self.vad.analyze_speakers(sample)                
                if analysis.get("speaker_count") == 1:
                    speaker_profiles.append(analysis)
            
            if speaker_profiles:
                # Store primary speaker as user profile
                self.user_speaker_profile = speaker_profiles[0]["primary_speaker"]
                logger.info(f"User voice profile calibrated: {self.user_speaker_profile}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Voice calibration error: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status"""
        return {
            "vad_available": self.vad is not None,
            "vad_engine": self.config.vad_engine,
            "stt_available": self.stt is not None,
            "user_calibrated": self.user_speaker_profile is not None,
            "pyannote_available": PYANNOTE_AVAILABLE,
            "silero_available": SILERO_AVAILABLE,
            "faster_whisper_available": FASTER_WHISPER_AVAILABLE,
            "config": {
                "vad_engine": self.config.vad_engine,
                "vad_model": self.config.vad_model,
                "stt_model": self.config.stt_model,
                "stt_device": self.config.stt_device
            }
        }

# Factory functions for different use cases
def create_enhanced_pipeline(
    enable_diarization: bool = True,
    stt_model: str = "base",
    device: str = "auto",
    vad_engine: str = "hybrid"
) -> EnhancedAudioPipeline:
    """Create enhanced pipeline with specified settings"""
    
    config = EnhancedVADConfig(
        vad_engine=vad_engine,
        enable_diarization=enable_diarization,
        stt_model=stt_model,
        stt_device=device
    )
    
    return EnhancedAudioPipeline(config)

def create_lightweight_pipeline() -> EnhancedAudioPipeline:
    """Create lightweight pipeline for resource-constrained devices"""
    
    config = EnhancedVADConfig(
        vad_engine="silero",  # Faster than pyannote
        enable_diarization=False,  # Disable for performance
        stt_model="tiny",
        stt_device="cpu",
        stt_compute_type="int8"
    )
    
    return EnhancedAudioPipeline(config)

def create_balanced_pipeline() -> EnhancedAudioPipeline:
    """Create balanced pipeline with good performance and accuracy trade-off"""
    
    config = EnhancedVADConfig(
        vad_engine="pyannote",  # Good accuracy
        enable_diarization=True,
        stt_model="base",
        stt_device="auto",
        stt_compute_type="float16"
    )
    
    return EnhancedAudioPipeline(config)

def create_high_accuracy_pipeline() -> EnhancedAudioPipeline:
    """Create high-accuracy pipeline for powerful systems"""
    
    config = EnhancedVADConfig(
        vad_engine="hybrid",  # Best of both worlds
        enable_diarization=True,
        stt_model="base",  # or "small" for better accuracy
        stt_device="auto",
        stt_compute_type="float16"
    )
    
    return EnhancedAudioPipeline(config)

# Alias for backward compatibility
def create_lightweight_enhanced_pipeline() -> EnhancedAudioPipeline:
    """Alias for create_lightweight_pipeline for backward compatibility"""
    return create_lightweight_pipeline()
