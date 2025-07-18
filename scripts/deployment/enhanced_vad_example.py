#!/usr/bin/env python3
"""
Enhanced VAD Integration Example
Shows how to integrate enhanced VAD with your AI companion
"""

import asyncio
import logging
import time
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedAICompanion:
    """
    AI Companion with Enhanced VAD Integration
    
    This example shows how to integrate the enhanced VAD pipeline
    with your existing AI companion system.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.audio_pipeline = None
        self.is_running = False
        
        # Initialize audio pipeline
        self._initialize_audio_pipeline()
    
    def _initialize_audio_pipeline(self):
        """Initialize audio pipeline based on configuration"""
        try:
            # Import here to avoid dependency issues during testing
            from src.audio import create_audio_pipeline_from_config
            
            logger.info("Initializing enhanced audio pipeline...")
            self.audio_pipeline = create_audio_pipeline_from_config(self.config_path)
            
            # Setup event callbacks
            self._setup_audio_callbacks()
            
            logger.info("✓ Enhanced audio pipeline initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Enhanced audio pipeline not available: {e}")
            logger.info("Using mock audio pipeline for demonstration")
            self.audio_pipeline = MockAudioPipeline()
            self._setup_audio_callbacks()
            
        except Exception as e:
            logger.error(f"Failed to initialize audio pipeline: {e}")
            raise
    
    def _setup_audio_callbacks(self):
        """Setup audio event callbacks"""
        if not self.audio_pipeline:
            return
        
        # Add event callbacks
        self.audio_pipeline.add_event_callback('wake_word_detected', self._on_wake_word)
        self.audio_pipeline.add_event_callback('speech_started', self._on_speech_start)
        self.audio_pipeline.add_event_callback('speech_ended', self._on_speech_end)
        self.audio_pipeline.add_event_callback('transcription_ready', self._on_transcription)
        self.audio_pipeline.add_event_callback('error', self._on_audio_error)
        
        # Enhanced VAD specific callbacks
        if hasattr(self.audio_pipeline, 'using_enhanced'):
            self.audio_pipeline.add_event_callback('pipeline_switched', self._on_pipeline_switch)
            self.audio_pipeline.add_event_callback('enhanced_vad_ready', self._on_enhanced_vad_ready)
    
    def _on_wake_word(self, event):
        """Handle wake word detection"""
        wake_word = event.data.get('wake_word', 'unknown')
        logger.info(f"👂 Wake word detected: '{wake_word}'")
        
        # Your AI companion logic here
        # For example: activate conversation mode, play acknowledgment sound, etc.
    
    def _on_speech_start(self, event):
        """Handle speech start"""
        logger.info("🎤 Speech recording started")
        
        # Your AI companion logic here
        # For example: show listening indicator, pause other audio, etc.
    
    def _on_speech_end(self, event):
        """Handle speech end"""
        logger.info("⏹️  Speech recording ended")
        
        # Your AI companion logic here
        # For example: show processing indicator
    
    def _on_transcription(self, event):
        """Handle speech transcription"""
        result = event.data.get('result')
        if result:
            text = result.text
            confidence = result.confidence
            logger.info(f"📝 Transcription: '{text}' (confidence: {confidence:.2f})")
            
            # Process the transcribed text with your AI companion
            self._process_user_input(text, confidence)
    
    def _on_audio_error(self, event):
        """Handle audio errors"""
        error = event.data
        logger.error(f"❌ Audio error: {error}")
        
        # Your error handling logic here
    
    def _on_pipeline_switch(self, event):
        """Handle pipeline switching (enhanced VAD specific)"""
        switch_info = event.data
        from_pipeline = switch_info.get('from', 'unknown')
        to_pipeline = switch_info.get('to', 'unknown')
        reason = switch_info.get('reason', 'not specified')
        
        logger.info(f"🔄 Audio pipeline switched: {from_pipeline} → {to_pipeline}")
        if reason:
            logger.info(f"   Reason: {reason}")
    
    def _on_enhanced_vad_ready(self, event):
        """Handle enhanced VAD ready event"""
        vad_info = event.data
        mode = vad_info.get('mode', 'unknown')
        logger.info(f"🚀 Enhanced VAD ready in {mode} mode")
    
    def _process_user_input(self, text: str, confidence: float):
        """Process user input with AI companion logic"""
        logger.info(f"🤖 Processing user input: '{text}'")
        
        # Your AI companion processing logic here
        # For example:
        # - Intent recognition
        # - Conversation context
        # - Generate response
        # - TTS output
        
        # Mock response for demonstration
        response = self._generate_mock_response(text)
        logger.info(f"🗣️  AI Response: '{response}'")
    
    def _generate_mock_response(self, user_input: str) -> str:
        """Generate a mock response (replace with your AI logic)"""
        responses = {
            "hello": "Hello! How can I help you today?",
            "help": "I'm here to assist you. What do you need help with?",
            "avatar": "I'm your AI companion avatar. What would you like to know?",
        }
        
        # Simple keyword matching for demonstration
        for keyword, response in responses.items():
            if keyword.lower() in user_input.lower():
                return response
        
        return "That's interesting! Tell me more about that."
    
    async def start(self):
        """Start the AI companion"""
        if self.is_running:
            return
        
        logger.info("🚀 Starting Enhanced AI Companion...")
        
        try:
            # Start audio pipeline
            self.audio_pipeline.start()
            self.is_running = True
            
            logger.info("✅ Enhanced AI Companion started successfully!")
            logger.info("Listening for wake words: hello, help, avatar")
            
            # Show performance stats if using enhanced VAD
            if hasattr(self.audio_pipeline, 'get_performance_stats'):
                stats = self.audio_pipeline.get_performance_stats()
                logger.info(f"Pipeline type: {stats.get('pipeline_type', 'unknown')}")
                if stats.get('using_enhanced'):
                    logger.info(f"Enhanced mode: {stats.get('enhanced_mode', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to start AI companion: {e}")
            raise
    
    async def stop(self):
        """Stop the AI companion"""
        if not self.is_running:
            return
        
        logger.info("🛑 Stopping Enhanced AI Companion...")
        
        try:
            if self.audio_pipeline:
                self.audio_pipeline.stop()
            
            self.is_running = False
            logger.info("✅ Enhanced AI Companion stopped")
            
        except Exception as e:
            logger.error(f"Error stopping AI companion: {e}")
    
    def get_status(self) -> dict:
        """Get current status"""
        status = {
            'running': self.is_running,
            'audio_pipeline': type(self.audio_pipeline).__name__ if self.audio_pipeline else None
        }
        
        # Add enhanced VAD stats if available
        if hasattr(self.audio_pipeline, 'get_performance_stats'):
            status['performance'] = self.audio_pipeline.get_performance_stats()
        
        return status

class MockAudioPipeline:
    """Mock audio pipeline for testing when dependencies aren't available"""
    
    def __init__(self):
        self.callbacks = {}
        self.is_running = False
    
    def add_event_callback(self, event_type: str, callback):
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
    
    def start(self):
        logger.info("📢 Mock audio pipeline started (no real audio processing)")
        self.is_running = True
    
    def stop(self):
        logger.info("📢 Mock audio pipeline stopped")  
        self.is_running = False

async def main():
    """Main demonstration function"""
    logger.info("=" * 60)
    logger.info("Enhanced VAD AI Companion Integration Demo")  
    logger.info("=" * 60)
    
    # Create AI companion
    companion = EnhancedAICompanion()
    
    try:
        # Start the companion
        await companion.start()
        
        # Show status
        status = companion.get_status()
        logger.info(f"Status: {status}")
        
        # Run for a short demo period
        logger.info("Running demo for 10 seconds...")
        await asyncio.sleep(10)
        
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo error: {e}")
    finally:
        # Stop the companion
        await companion.stop()
        
    logger.info("=" * 60)
    logger.info("Demo complete!")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
