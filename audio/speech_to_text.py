import logging
import asyncio
import threading
import queue
import time
from typing import Optional, Callable, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum
import json

# Speech recognition backends
import speech_recognition as sr
import whisper
import torch
import numpy as np

logger = logging.getLogger(__name__)

class STTEngine(Enum):
    """Available speech-to-text engines"""
    GOOGLE = "google"
    WHISPER_ONLINE = "whisper_api"
    WHISPER_LOCAL = "whisper_local"
    SPHINX = "sphinx"
    AZURE = "azure"
    AWS = "aws"

@dataclass
class STTConfig:
    """Speech-to-text configuration"""
    engine: STTEngine = STTEngine.GOOGLE
    language: str = "en-US"
    timeout: float = 10.0
    phrase_timeout: float = 5.0
    
    # Whisper-specific settings
    whisper_model: str = "base"
    whisper_device: str = "auto"
    
    # API credentials
    google_api_key: Optional[str] = None
    azure_key: Optional[str] = None
    azure_region: Optional[str] = None
    aws_key_id: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_region: Optional[str] = None

@dataclass
class STTResult:
    """Speech-to-text result"""
    text: str
    confidence: float
    engine: STTEngine
    processing_time: float
    language: Optional[str] = None
    alternatives: Optional[List[str]] = None
    error: Optional[str] = None

class WhisperSTT:
    """Local Whisper speech-to-text engine"""
    
    def __init__(self, model_name: str = "base", device: str = "auto"):
        self.model_name = model_name
        self.device = self._get_device(device)
        self.model = None
        self._load_model()
        
    def _get_device(self, device: str) -> str:
        """Determine the best device for Whisper"""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return device
        
    def _load_model(self):
        """Load Whisper model"""
        try:
            logger.info(f"Loading Whisper model '{self.model_name}' on {self.device}")
            self.model = whisper.load_model(self.model_name, device=self.device)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
            
    def transcribe(self, audio_data: bytes, language: str = "en") -> STTResult:
        """Transcribe audio using Whisper"""
        start_time = time.time()
        
        try:
            # Convert audio bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe with Whisper
            result = self.model.transcribe(
                audio_array,
                language=language if language != "auto" else None,
                fp16=self.device != "cpu"
            )
            
            processing_time = time.time() - start_time
            
            return STTResult(
                text=result["text"].strip(),
                confidence=1.0,  # Whisper doesn't provide confidence scores
                engine=STTEngine.WHISPER_LOCAL,
                processing_time=processing_time,
                language=result.get("language"),
                alternatives=None
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Whisper transcription error: {e}")
            
            return STTResult(
                text="",
                confidence=0.0,
                engine=STTEngine.WHISPER_LOCAL,
                processing_time=processing_time,
                error=str(e)
            )

class SpeechToTextEngine:
    """Main speech-to-text engine with multiple backend support"""
    
    def __init__(self, config: STTConfig):
        self.config = config
        self.recognizer = sr.Recognizer()
        self.whisper_engine = None
        
        # Initialize Whisper if needed
        if config.engine == STTEngine.WHISPER_LOCAL:
            self._init_whisper()
            
        # Configure recognizer
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
    def _init_whisper(self):
        """Initialize local Whisper engine"""
        try:
            self.whisper_engine = WhisperSTT(
                model_name=self.config.whisper_model,
                device=self.config.whisper_device
            )
        except Exception as e:
            logger.error(f"Failed to initialize Whisper: {e}")
            # Fallback to Google
            self.config.engine = STTEngine.GOOGLE
            
    def transcribe(self, audio_data: bytes) -> STTResult:
        """Transcribe audio data to text"""
        start_time = time.time()
        
        try:
            # Convert to AudioData object for speech_recognition
            audio = sr.AudioData(audio_data, 16000, 2)
            
            # Route to appropriate engine
            if self.config.engine == STTEngine.GOOGLE:
                return self._transcribe_google(audio, start_time)
            elif self.config.engine == STTEngine.WHISPER_LOCAL:
                return self._transcribe_whisper_local(audio_data, start_time)
            elif self.config.engine == STTEngine.WHISPER_ONLINE:
                return self._transcribe_whisper_api(audio, start_time)
            elif self.config.engine == STTEngine.SPHINX:
                return self._transcribe_sphinx(audio, start_time)
            elif self.config.engine == STTEngine.AZURE:
                return self._transcribe_azure(audio, start_time)
            elif self.config.engine == STTEngine.AWS:
                return self._transcribe_aws(audio, start_time)
            else:
                raise ValueError(f"Unsupported STT engine: {self.config.engine}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Transcription error: {e}")
            
            return STTResult(
                text="",
                confidence=0.0,
                engine=self.config.engine,
                processing_time=processing_time,
                error=str(e)
            )
            
    def _transcribe_google(self, audio: sr.AudioData, start_time: float) -> STTResult:
        """Transcribe using Google Speech Recognition"""
        try:
            text = self.recognizer.recognize_google(
                audio, 
                language=self.config.language,
                key=self.config.google_api_key
            )
            
            processing_time = time.time() - start_time
            
            return STTResult(
                text=text,
                confidence=0.95,  # Google doesn't provide confidence
                engine=STTEngine.GOOGLE,
                processing_time=processing_time,
                language=self.config.language
            )
            
        except sr.UnknownValueError:
            processing_time = time.time() - start_time
            return STTResult(
                text="",
                confidence=0.0,
                engine=STTEngine.GOOGLE,
                processing_time=processing_time,
                error="Could not understand audio"
            )
        except sr.RequestError as e:
            processing_time = time.time() - start_time
            return STTResult(
                text="",
                confidence=0.0,
                engine=STTEngine.GOOGLE,
                processing_time=processing_time,
                error=f"Google API error: {e}"
            )
            
    def _transcribe_whisper_local(self, audio_data: bytes, start_time: float) -> STTResult:
        """Transcribe using local Whisper"""
        if not self.whisper_engine:
            processing_time = time.time() - start_time
            return STTResult(
                text="",
                confidence=0.0,
                engine=STTEngine.WHISPER_LOCAL,
                processing_time=processing_time,
                error="Whisper engine not initialized"
            )
            
        return self.whisper_engine.transcribe(audio_data, self.config.language)
        
    def _transcribe_whisper_api(self, audio: sr.AudioData, start_time: float) -> STTResult:
        """Transcribe using OpenAI Whisper API"""
        try:
            text = self.recognizer.recognize_whisper_api(
                audio,
                api_key=self.config.google_api_key  # Reuse for Whisper API key
            )
            
            processing_time = time.time() - start_time
            
            return STTResult(
                text=text,
                confidence=0.95,
                engine=STTEngine.WHISPER_ONLINE,
                processing_time=processing_time,
                language=self.config.language
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return STTResult(
                text="",
                confidence=0.0,
                engine=STTEngine.WHISPER_ONLINE,
                processing_time=processing_time,
                error=f"Whisper API error: {e}"
            )
            
    def _transcribe_sphinx(self, audio: sr.AudioData, start_time: float) -> STTResult:
        """Transcribe using CMU Sphinx (offline)"""
        try:
            text = self.recognizer.recognize_sphinx(audio)
            
            processing_time = time.time() - start_time
            
            return STTResult(
                text=text,
                confidence=0.8,  # Sphinx has lower accuracy
                engine=STTEngine.SPHINX,
                processing_time=processing_time,
                language=self.config.language
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return STTResult(
                text="",
                confidence=0.0,
                engine=STTEngine.SPHINX,
                processing_time=processing_time,
                error=f"Sphinx error: {e}"
            )
            
    def _transcribe_azure(self, audio: sr.AudioData, start_time: float) -> STTResult:
        """Transcribe using Azure Speech Services"""
        try:
            text = self.recognizer.recognize_azure(
                audio,
                key=self.config.azure_key,
                location=self.config.azure_region,
                language=self.config.language
            )
            
            processing_time = time.time() - start_time
            
            return STTResult(
                text=text,
                confidence=0.95,
                engine=STTEngine.AZURE,
                processing_time=processing_time,
                language=self.config.language
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return STTResult(
                text="",
                confidence=0.0,
                engine=STTEngine.AZURE,
                processing_time=processing_time,
                error=f"Azure error: {e}"
            )
            
    def _transcribe_aws(self, audio: sr.AudioData, start_time: float) -> STTResult:
        """Transcribe using AWS Transcribe"""
        try:
            text = self.recognizer.recognize_amazon(
                audio,
                credentials=(self.config.aws_key_id, self.config.aws_secret_key),
                region=self.config.aws_region,
                language=self.config.language
            )
            
            processing_time = time.time() - start_time
            
            return STTResult(
                text=text,
                confidence=0.95,
                engine=STTEngine.AWS,
                processing_time=processing_time,
                language=self.config.language
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return STTResult(
                text="",
                confidence=0.0,
                engine=STTEngine.AWS,
                processing_time=processing_time,
                error=f"AWS error: {e}"
            )

class SpeechToText:
    """High-level speech-to-text service with async support"""
    
    def __init__(self, config: Optional[STTConfig] = None):
        self.config = config or STTConfig()
        self.engine = SpeechToTextEngine(self.config)
        
        # Async processing
        self.processing_queue = queue.Queue()
        self.result_callbacks: List[Callable[[STTResult], None]] = []
        self.is_processing = False
        self.processing_thread = None
        
    def add_result_callback(self, callback: Callable[[STTResult], None]):
        """Add callback for transcription results"""
        self.result_callbacks.append(callback)
        
    def remove_result_callback(self, callback: Callable[[STTResult], None]):
        """Remove result callback"""
        if callback in self.result_callbacks:
            self.result_callbacks.remove(callback)
            
    def start_async_processing(self):
        """Start async processing thread"""
        if self.is_processing:
            return
            
        self.is_processing = True
        self.processing_thread = threading.Thread(target=self._async_processing_loop, daemon=True)
        self.processing_thread.start()
        logger.info("Started async STT processing")
        
    def stop_async_processing(self):
        """Stop async processing thread"""
        self.is_processing = False
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
        logger.info("Stopped async STT processing")
        
    def _async_processing_loop(self):
        """Async processing loop"""
        while self.is_processing:
            try:
                audio_data = self.processing_queue.get(timeout=0.1)
                result = self.engine.transcribe(audio_data)
                
                # Call all result callbacks
                for callback in self.result_callbacks:
                    try:
                        callback(result)
                    except Exception as e:
                        logger.error(f"Error in STT result callback: {e}")
                        
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in async STT processing: {e}")
                
    def transcribe_sync(self, audio_data: bytes) -> STTResult:
        """Synchronous transcription"""
        return self.engine.transcribe(audio_data)
        
    def transcribe_async(self, audio_data: bytes):
        """Asynchronous transcription"""
        if not self.is_processing:
            self.start_async_processing()
            
        self.processing_queue.put(audio_data)
        
    def change_engine(self, engine: STTEngine):
        """Change STT engine"""
        self.config.engine = engine
        self.engine = SpeechToTextEngine(self.config)
        logger.info(f"Changed STT engine to {engine.value}")
        
    def change_language(self, language: str):
        """Change recognition language"""
        self.config.language = language
        logger.info(f"Changed STT language to {language}")
        
    def get_supported_languages(self) -> List[str]:
        """Get supported languages for current engine"""
        # Common languages supported by most engines
        common_languages = [
            "en-US", "en-GB", "en-AU", "en-CA",
            "es-ES", "es-MX", "fr-FR", "fr-CA",
            "de-DE", "it-IT", "pt-BR", "pt-PT",
            "ja-JP", "ko-KR", "zh-CN", "zh-TW",
            "ru-RU", "ar-SA", "hi-IN", "nl-NL"
        ]
        
        if self.config.engine == STTEngine.WHISPER_LOCAL:
            # Whisper supports many more languages
            whisper_languages = [
                "af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs", "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu", "fa", "fi", "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht", "hu", "hy", "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko", "la", "lb", "ln", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru", "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw", "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur", "uz", "vi", "yi", "yo", "zh"
            ]
            return whisper_languages
            
        return common_languages
        
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            'engine': self.config.engine.value,
            'language': self.config.language,
            'is_processing': self.is_processing,
            'queue_size': self.processing_queue.qsize(),
            'num_callbacks': len(self.result_callbacks)
        }
