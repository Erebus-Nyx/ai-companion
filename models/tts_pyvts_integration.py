#!/usr/bin/env python3
"""
TTS Integration with PyVTS and Phoneme Detection
Coordinates TTS, lipsync, and emotion expression
"""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Optional, Any
import base64
import io

from .pyvts_integration import get_pyvts_controller, trigger_pyvts_emotion, trigger_pyvts_lipsync
from .phoneme_detection import extract_phonemes_from_tts

class TTSPyVTSIntegrator:
    """Integrates TTS with PyVTS for synchronized avatar animation"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.active_animations = {}  # Track active animations by avatar ID
    
    async def synthesize_with_lipsync(self, 
                                     text: str, 
                                     emotion: str = 'neutral',
                                     intensity: float = 0.5,
                                     avatar_id: str = 'default') -> Dict[str, Any]:
        """
        Synthesize TTS with synchronized PyVTS lipsync and emotion
        """
        try:
            self.logger.info(f"Starting TTS synthesis with PyVTS integration for: {text[:50]}...")
            
            # Get PyVTS controller
            pyvts_controller = await get_pyvts_controller()
            if not pyvts_controller:
                self.logger.warning("PyVTS not available, proceeding with TTS only")
                return await self._fallback_tts_only(text, emotion, intensity)
            
            # Import TTS handler
            try:
                from .tts_handler import EmotionalTTSHandler
                tts_handler = EmotionalTTSHandler()
                
                if not tts_handler.initialize_model():
                    raise Exception("TTS model initialization failed")
                
            except Exception as e:
                self.logger.error(f"TTS handler error: {e}")
                return {"error": "TTS system unavailable"}
            
            # 1. Trigger emotion expression first
            emotion_task = None
            if emotion and emotion != 'neutral':
                emotion_duration = max(3.0, len(text) * 0.1)  # Estimate duration
                emotion_task = asyncio.create_task(
                    trigger_pyvts_emotion(emotion, intensity, emotion_duration)
                )
            
            # 2. Synthesize TTS audio
            tts_result = tts_handler.synthesize_emotional_speech(text, emotion, intensity)
            
            if not tts_result or 'audio_data' not in tts_result:
                raise Exception("TTS synthesis failed")
            
            # 3. Extract phonemes from audio
            audio_data = tts_result['audio_data']
            
            # Convert audio data if needed
            if isinstance(audio_data, str):
                # Base64 encoded audio
                audio_bytes = base64.b64decode(audio_data.split(',')[-1])
                audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            elif isinstance(audio_data, (list, np.ndarray)):
                audio_array = np.array(audio_data, dtype=np.float32)
            else:
                raise Exception(f"Unsupported audio data type: {type(audio_data)}")
            
            # Extract phonemes and timing
            phonemes, timing_data, envelope = await extract_phonemes_from_tts(audio_array, 22050)
            
            # 4. Trigger lipsync animation
            lipsync_task = asyncio.create_task(
                trigger_pyvts_lipsync(phonemes, timing_data)
            )
            
            # 5. Wait for all animations to complete
            tasks = [lipsync_task]
            if emotion_task:
                tasks.append(emotion_task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # 6. Return enhanced TTS result
            enhanced_result = {
                **tts_result,
                'pyvts_integration': True,
                'phonemes': phonemes,
                'timing_data': timing_data,
                'envelope': envelope,
                'emotion_applied': emotion != 'neutral',
                'avatar_id': avatar_id
            }
            
            self.logger.info(f"TTS with PyVTS integration completed successfully")
            return enhanced_result
            
        except Exception as e:
            self.logger.error(f"TTS PyVTS integration error: {e}")
            return await self._fallback_tts_only(text, emotion, intensity)
    
    async def _fallback_tts_only(self, text: str, emotion: str, intensity: float) -> Dict[str, Any]:
        """Fallback to TTS-only synthesis"""
        try:
            from .tts_handler import EmotionalTTSHandler
            tts_handler = EmotionalTTSHandler()
            
            if tts_handler.initialize_model():
                result = tts_handler.synthesize_emotional_speech(text, emotion, intensity)
                if result:
                    result['pyvts_integration'] = False
                    result['fallback_mode'] = True
                    return result
            
            return {"error": "TTS synthesis failed"}
            
        except Exception as e:
            self.logger.error(f"Fallback TTS error: {e}")
            return {"error": "TTS system unavailable"}
    
    async def trigger_idle_state(self, avatar_id: str = 'default'):
        """Start idle animations for the avatar"""
        try:
            pyvts_controller = await get_pyvts_controller()
            if pyvts_controller:
                await pyvts_controller.start_idle_animations()
                self.logger.info(f"Started idle animations for avatar {avatar_id}")
            
        except Exception as e:
            self.logger.error(f"Error starting idle animations: {e}")
    
    async def stop_idle_state(self, avatar_id: str = 'default'):
        """Stop idle animations for the avatar"""
        try:
            pyvts_controller = await get_pyvts_controller()
            if pyvts_controller:
                await pyvts_controller.stop_idle_animations()
                self.logger.info(f"Stopped idle animations for avatar {avatar_id}")
            
        except Exception as e:
            self.logger.error(f"Error stopping idle animations: {e}")
    
    async def trigger_manual_emotion(self, 
                                   emotion: str, 
                                   intensity: float = 0.5, 
                                   duration: float = 2.0,
                                   avatar_id: str = 'default') -> bool:
        """Manually trigger emotion without TTS"""
        try:
            success = await trigger_pyvts_emotion(emotion, intensity, duration)
            if success:
                self.logger.info(f"Manual emotion {emotion} triggered for avatar {avatar_id}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error triggering manual emotion: {e}")
            return False
    
    async def get_avatar_status(self, avatar_id: str = 'default') -> Dict[str, Any]:
        """Get current avatar status and capabilities"""
        try:
            pyvts_controller = await get_pyvts_controller()
            if not pyvts_controller:
                return {
                    'connected': False,
                    'pyvts_available': False,
                    'avatar_id': avatar_id
                }
            
            model_info = await pyvts_controller.get_current_model_info()
            available_models = await pyvts_controller.get_available_models()
            
            return {
                'connected': pyvts_controller.connected,
                'pyvts_available': True,
                'current_model': model_info,
                'available_models': len(available_models),
                'idle_active': pyvts_controller.is_idle_active,
                'avatar_id': avatar_id,
                'parameters_loaded': len(pyvts_controller.available_parameters)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting avatar status: {e}")
            return {
                'connected': False,
                'pyvts_available': False,
                'error': str(e),
                'avatar_id': avatar_id
            }

# Global instance
tts_pyvts_integrator = None

def get_tts_pyvts_integrator():
    """Get or create TTS PyVTS integrator instance"""
    global tts_pyvts_integrator
    if tts_pyvts_integrator is None:
        tts_pyvts_integrator = TTSPyVTSIntegrator()
    return tts_pyvts_integrator

async def synthesize_with_pyvts(text: str, 
                               emotion: str = 'neutral',
                               intensity: float = 0.5,
                               avatar_id: str = 'default') -> Dict[str, Any]:
    """Helper function for TTS with PyVTS integration"""
    integrator = get_tts_pyvts_integrator()
    return await integrator.synthesize_with_lipsync(text, emotion, intensity, avatar_id)

async def trigger_avatar_emotion(emotion: str, 
                                intensity: float = 0.5, 
                                duration: float = 2.0,
                                avatar_id: str = 'default') -> bool:
    """Helper function to trigger avatar emotions"""
    integrator = get_tts_pyvts_integrator()
    return await integrator.trigger_manual_emotion(emotion, intensity, duration, avatar_id)

async def start_avatar_idle(avatar_id: str = 'default'):
    """Helper function to start avatar idle animations"""
    integrator = get_tts_pyvts_integrator()
    await integrator.trigger_idle_state(avatar_id)

async def stop_avatar_idle(avatar_id: str = 'default'):
    """Helper function to stop avatar idle animations"""
    integrator = get_tts_pyvts_integrator()
    await integrator.stop_idle_state(avatar_id)
