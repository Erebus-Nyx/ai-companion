# Enhanced VAD Integration for AI Companion

This document describes the enhanced Voice Activity Detection (VAD) and Speaker Diarization integration for the AI Companion project, incorporating advanced ML-based audio processing using **faster-whisper** and **pyannote.audio**.

## Overview

The enhanced VAD system provides significant improvements over the basic WebRTC VAD implementation:

### Key Benefits

1. **4-10x Faster Performance**: Using faster-whisper for optimized speech-to-text
2. **Better Noise Handling**: ML-based VAD with pyannote.audio handles background noise more effectively
3. **Reduced False Wake-Words**: Advanced audio segmentation reduces false positives
4. **Voice Authentication**: Optional speaker analysis for user identification
5. **Flexible Configuration**: Multiple performance modes (lightweight, balanced, high-accuracy)
6. **Graceful Fallback**: Automatic fallback to basic VAD if enhanced system fails

## Architecture

The enhanced VAD system consists of several components:

```
Enhanced Audio Pipeline
├── PyannoteVAD (ML-based voice activity detection)
├── FasterWhisperSTT (Optimized speech-to-text)
├── EnhancedAudioPipeline (Core processing)
├── EnhancedAudioPipelineWrapper (Integration layer)
└── Configuration Management
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The enhanced VAD dependencies include:
- `faster-whisper>=0.10.0`
- `pyannote.audio>=3.1.0`
- `pyannote.core>=5.0.0`
- `pyannote.database>=5.0.0`
- `pyannote.metrics>=3.2.0`

### 2. Configuration

The enhanced VAD is configured through `config.yaml`:

```yaml
voice_detection:
  cue_words:
    - "hello"
    - "help"
    - "avatar"
  
  enhanced_vad:
    enabled: true
    mode: "lightweight"  # lightweight, balanced, high_accuracy
    fallback_to_basic: true
    
    # VAD Settings
    vad_model: "pyannote/segmentation-3.0"
    vad_onset_threshold: 0.5
    vad_offset_threshold: 0.5
    vad_min_duration_on: 0.1
    vad_min_duration_off: 0.1
    
    # STT Settings  
    stt_model: "small"  # tiny, base, small, medium, large
    stt_language: "en"
    stt_device: "auto"  # auto, cpu, cuda
    stt_compute_type: "float16"  # float16, int8, float32
    
    # Audio Processing
    chunk_duration: 1.0
    min_speech_duration: 0.5
    max_speech_duration: 30.0
    silence_threshold: 0.01
    
    # Speaker Analysis (optional)
    speaker_analysis_enabled: false
    min_speakers: 1
    max_speakers: 2
```

## Usage

### Basic Integration

```python
from src.audio import create_audio_pipeline_from_config

# Create pipeline from configuration
pipeline = create_audio_pipeline_from_config("config.yaml")

# Setup event callbacks
pipeline.add_event_callback('wake_word_detected', on_wake_word)
pipeline.add_event_callback('transcription_ready', on_transcription)

# Start processing
pipeline.start()
```

### Advanced Usage

```python
from src.audio import create_enhanced_audio_pipeline

# Create enhanced pipeline with specific mode
pipeline = create_enhanced_audio_pipeline(
    wake_words=["hello", "help", "avatar"],
    enhanced_mode="balanced",  # lightweight, balanced, high_accuracy
    use_enhanced_vad=True,
    fallback_to_basic=True
)

# Process audio chunks directly
transcription = pipeline.process_audio_chunk(audio_data)
```

### Integration with AI Companion

See `enhanced_vad_example.py` for a complete integration example:

```python
class EnhancedAICompanion:
    def __init__(self):
        # Initialize enhanced audio pipeline
        self.audio_pipeline = create_audio_pipeline_from_config()
        self._setup_audio_callbacks()
    
    def _on_transcription(self, event):
        result = event.data.get('result')
        text = result.text
        confidence = result.confidence
        
        # Process with your AI logic
        response = self.process_user_input(text)
        self.speak_response(response)
```

## Performance Modes

### Lightweight Mode
- **Use Case**: Resource-constrained environments, real-time processing
- **Models**: tiny/base faster-whisper, basic VAD settings
- **Performance**: Fastest, lowest memory usage
- **Accuracy**: Good for clear speech

### Balanced Mode (Default)
- **Use Case**: General purpose, good balance of speed and accuracy
- **Models**: small faster-whisper, optimized VAD settings
- **Performance**: Good speed with better accuracy
- **Accuracy**: Handles moderate background noise

### High Accuracy Mode
- **Use Case**: High-quality transcription, challenging audio conditions
- **Models**: medium/large faster-whisper, sensitive VAD settings
- **Performance**: Slower but more accurate
- **Accuracy**: Best for noisy environments, accented speech

## API Reference

### EnhancedAudioPipelineWrapper

Main class for enhanced audio processing.

```python
class EnhancedAudioPipelineWrapper:
    def __init__(self, wake_words: List[str], config: EnhancedAudioConfig)
    def start(self) -> None
    def stop(self) -> None
    def process_audio_chunk(self, audio_data: bytes) -> Optional[str]
    def get_performance_stats(self) -> Dict[str, Any]
    def switch_to_enhanced(self, mode: Optional[str] = None) -> bool
    def switch_to_basic(self) -> None
```

### Event Callbacks

Available events:
- `wake_word_detected`: Wake word found in audio
- `speech_started`: Speech recording began
- `speech_ended`: Speech recording finished
- `transcription_ready`: Speech-to-text result available
- `pipeline_switched`: VAD pipeline changed (enhanced ↔ basic)
- `enhanced_vad_ready`: Enhanced VAD system initialized
- `error`: Error occurred in processing

### Configuration Classes

```python
@dataclass
class EnhancedVADConfig:
    vad_model: str = "pyannote/segmentation-3.0"
    stt_model: str = "small"
    stt_language: str = "en"
    chunk_duration: float = 1.0
    # ... other settings

@dataclass 
class EnhancedAudioConfig:
    basic_config: AudioConfig
    enhanced_vad_config: EnhancedVADConfig
    use_enhanced_vad: bool = True
    enhanced_mode: str = "lightweight"
    fallback_to_basic: bool = True
```

## Testing

### Configuration Test
```bash
python3 test_config_only.py
```

### Full Integration Test (requires dependencies)
```bash
python3 test_enhanced_vad.py
```

### Example Demo
```bash
python3 enhanced_vad_example.py
```

## Performance Optimization

### Hardware Requirements

**Minimum**:
- CPU: Multi-core processor
- RAM: 4GB available
- Storage: 2GB for models

**Recommended**:
- CPU: 8+ cores or GPU with CUDA
- RAM: 8GB available
- GPU: NVIDIA GPU with 4GB+ VRAM (optional)

### Model Selection

| Model Size | Speed | Accuracy | Memory | Use Case |
|------------|-------|----------|---------|----------|
| tiny       | Fastest | Basic | 39MB | Real-time, low-resource |
| base       | Fast | Good | 74MB | Balanced performance |
| small      | Medium | Better | 244MB | General purpose |
| medium     | Slow | High | 769MB | High accuracy needed |
| large      | Slowest | Highest | 1550MB | Maximum accuracy |

### Performance Tuning

```python
# Optimize for speed
config = EnhancedVADConfig(
    stt_model="tiny",
    stt_compute_type="int8",
    chunk_duration=0.5,
    vad_onset_threshold=0.3
)

# Optimize for accuracy  
config = EnhancedVADConfig(
    stt_model="large",
    stt_compute_type="float16",
    chunk_duration=2.0,
    vad_onset_threshold=0.7
)
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'faster_whisper'**
   ```bash
   pip install faster-whisper
   ```

2. **CUDA not available**
   - Enhanced VAD will automatically fall back to CPU
   - Install CUDA-compatible PyTorch for GPU acceleration

3. **Model download fails**
   - Check internet connection
   - Models are downloaded automatically on first use
   - Manually download: `huggingface-hub download pyannote/segmentation-3.0`

4. **High memory usage**
   - Use smaller models (tiny/base)
   - Reduce chunk_duration
   - Use int8 compute_type

5. **Poor transcription accuracy**
   - Increase model size (small → medium → large)
   - Adjust VAD thresholds
   - Check audio quality and background noise

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger('src.audio').setLevel(logging.DEBUG)
```

## Integration with Existing Systems

### WebRTC VAD Replacement

The enhanced VAD can be used as a drop-in replacement for WebRTC VAD:

```python
# Before (WebRTC VAD)
from src.audio import AudioPipeline, AudioConfig

pipeline = AudioPipeline(
    wake_words=["hello"], 
    audio_config=AudioConfig()
)

# After (Enhanced VAD)
from src.audio import create_enhanced_audio_pipeline

pipeline = create_enhanced_audio_pipeline(
    wake_words=["hello"],
    enhanced_mode="lightweight"
)
```

### Gradual Migration

1. **Phase 1**: Install enhanced VAD alongside existing system
2. **Phase 2**: Enable enhanced VAD with fallback to basic
3. **Phase 3**: Monitor performance and adjust configuration
4. **Phase 4**: Disable basic VAD once enhanced system is stable

## Comparison with Intv_App Reference

Based on the analysis of your Intv_App implementation, this enhanced VAD integration provides:

### Similar Features
- ✅ PyAnnote VAD with segmentation-3.0
- ✅ Faster-whisper STT integration
- ✅ 5-step audio pipeline (Audio → VAD → Diarization → ASR → Processing)
- ✅ Hardware-optimized model selection
- ✅ LiveSpeechProcessor equivalent functionality

### Additional Improvements
- ✅ Seamless fallback to basic VAD
- ✅ Configuration-driven setup
- ✅ Multiple performance modes
- ✅ Comprehensive event system
- ✅ Integration with existing AI live2d chat architecture
- ✅ Performance monitoring and statistics

### Key Differences
- **Intv_App**: Standalone audio processing for interview applications
- **AI Companion**: Integrated with conversational AI system
- **Intv_App**: Focus on accuracy and detailed transcription
- **AI Companion**: Focus on real-time interaction and responsiveness

## Future Enhancements

1. **Real-time Streaming**: Implement streaming transcription for lower latency
2. **Custom Models**: Support for fine-tuned VAD/STT models
3. **Multi-language**: Dynamic language detection and switching
4. **Speaker Identification**: Enhanced speaker diarization for multi-user scenarios
5. **Emotion Detection**: Integration with emotion recognition models
6. **Noise Reduction**: Advanced audio preprocessing for better quality

## License and Credits

This enhanced VAD integration uses:
- **faster-whisper**: MIT License
- **pyannote.audio**: MIT License
- **PyTorch**: BSD License

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test scripts and examples
3. Enable debug logging for detailed information
4. Check the GitHub issues for similar problems
