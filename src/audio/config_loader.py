"""
Configuration loader for enhanced audio pipeline
Loads and validates enhanced VAD settings from config.yaml
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .enhanced_vad import EnhancedVADConfig
from .voice_detection import AudioConfig
from .enhanced_audio_pipeline import EnhancedAudioConfig

logger = logging.getLogger(__name__)

@dataclass
class AudioConfigLoader:
    """Loads and manages audio configuration from YAML files"""
    
    config_path: str = "config.yaml"
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return {}
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return {}
    
    def create_enhanced_audio_config(self, 
                                   wake_words: Optional[list] = None) -> EnhancedAudioConfig:
        """
        Create enhanced audio configuration from loaded config
        
        Args:
            wake_words: Override wake words from config
            
        Returns:
            Configured EnhancedAudioConfig instance
        """
        config = self.load_config()
        
        # Extract voice detection settings
        voice_config = config.get('voice_detection', {})
        enhanced_vad_config = voice_config.get('enhanced_vad', {})
        
        # Get wake words
        if wake_words is None:
            wake_words = voice_config.get('cue_words', ['hello', 'help', 'avatar'])
        
        # Basic audio config
        basic_config = AudioConfig(
            sample_rate=16000,
            channels=1,
            chunk_size=1024,
            vad_aggressiveness=2
        )
        
        # Enhanced VAD config
        enhanced_vad = EnhancedVADConfig(
            # VAD settings
            vad_model=enhanced_vad_config.get('vad_model', 'pyannote/segmentation-3.0'),
            vad_onset_threshold=enhanced_vad_config.get('vad_onset_threshold', 0.5),
            vad_offset_threshold=enhanced_vad_config.get('vad_offset_threshold', 0.5),
            vad_min_duration_on=enhanced_vad_config.get('vad_min_duration_on', 0.1),
            vad_min_duration_off=enhanced_vad_config.get('vad_min_duration_off', 0.1),
            
            # STT settings
            stt_model=enhanced_vad_config.get('stt_model', 'small'),
            stt_language=enhanced_vad_config.get('stt_language', 'en'),
            stt_device=enhanced_vad_config.get('stt_device', 'auto'),
            stt_compute_type=enhanced_vad_config.get('stt_compute_type', 'float16'),
            
            # Audio processing
            chunk_duration=enhanced_vad_config.get('chunk_duration', 1.0),
            min_speech_duration=enhanced_vad_config.get('min_speech_duration', 0.5),
            max_speech_duration=enhanced_vad_config.get('max_speech_duration', 30.0),
            silence_threshold=enhanced_vad_config.get('silence_threshold', 0.01),
            
            # Speaker analysis
            speaker_analysis_enabled=enhanced_vad_config.get('speaker_analysis_enabled', False),
            min_speakers=enhanced_vad_config.get('min_speakers', 1),
            max_speakers=enhanced_vad_config.get('max_speakers', 2)
        )
        
        # Enhanced audio config
        enhanced_config = EnhancedAudioConfig(
            basic_config=basic_config,
            enhanced_vad_config=enhanced_vad,
            use_enhanced_vad=enhanced_vad_config.get('enabled', True),
            enhanced_mode=enhanced_vad_config.get('mode', 'lightweight'),
            fallback_to_basic=enhanced_vad_config.get('fallback_to_basic', True)
        )
        
        logger.info(f"Created enhanced audio config (mode: {enhanced_config.enhanced_mode}, "
                   f"enhanced VAD: {enhanced_config.use_enhanced_vad})")
        
        return enhanced_config
    
    def get_wake_words(self) -> list:
        """Get wake words from config"""
        config = self.load_config()
        voice_config = config.get('voice_detection', {})
        return voice_config.get('cue_words', ['hello', 'help', 'avatar'])
    
    def is_enhanced_vad_enabled(self) -> bool:
        """Check if enhanced VAD is enabled in config"""
        config = self.load_config()
        voice_config = config.get('voice_detection', {})
        enhanced_vad_config = voice_config.get('enhanced_vad', {})
        return enhanced_vad_config.get('enabled', True)
    
    def get_enhanced_vad_mode(self) -> str:
        """Get enhanced VAD mode from config"""
        config = self.load_config()
        voice_config = config.get('voice_detection', {})
        enhanced_vad_config = voice_config.get('enhanced_vad', {})
        return enhanced_vad_config.get('mode', 'lightweight')

def load_enhanced_audio_config(config_path: str = "config.yaml", 
                             wake_words: Optional[list] = None) -> EnhancedAudioConfig:
    """
    Convenience function to load enhanced audio configuration
    
    Args:
        config_path: Path to configuration file
        wake_words: Override wake words from config
        
    Returns:
        Configured EnhancedAudioConfig instance
    """
    loader = AudioConfigLoader(config_path)
    return loader.create_enhanced_audio_config(wake_words)

def create_audio_pipeline_from_config(config_path: str = "config.yaml"):
    """
    Create audio pipeline from configuration file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configured audio pipeline (enhanced or basic)
    """
    from .enhanced_audio_pipeline import create_enhanced_audio_pipeline
    from .audio_pipeline import AudioPipeline
    
    loader = AudioConfigLoader(config_path)
    wake_words = loader.get_wake_words()
    
    if loader.is_enhanced_vad_enabled():
        logger.info("Creating enhanced audio pipeline from config")
        config = loader.create_enhanced_audio_config(wake_words)
        
        return create_enhanced_audio_pipeline(
            wake_words=wake_words,
            enhanced_mode=config.enhanced_mode,
            use_enhanced_vad=config.use_enhanced_vad,
            fallback_to_basic=config.fallback_to_basic
        )
    else:
        logger.info("Creating basic audio pipeline from config")
        config = loader.create_enhanced_audio_config(wake_words)
        
        return AudioPipeline(
            wake_words=wake_words,
            audio_config=config.basic_config
        )
