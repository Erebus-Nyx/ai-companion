#!/usr/bin/env python3
"""
PyVTS Integration for Live2D Avatar Control
Alternative to motion files for models without built-in motions
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
import time

try:
    import pyvts
except ImportError:
    pyvts = None
    logging.warning("PyVTS not installed. Install with: pip install pyvts")

class PyVTSController:
    """Controls Live2D avatars via VTube Studio API using PyVTS"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.vts = None
        self.connected = False
        self.available_models = []
        self.current_model = None
        self.available_parameters = {}
        self.emotion_mappings = self._create_emotion_mappings()
        self.idle_task = None
        self.breathing_task = None
        self.is_idle_active = False
        
    def _create_emotion_mappings(self) -> Dict[str, Dict[str, float]]:
        """Create emotion to parameter mappings for VTube Studio with body posturing"""
        return {
            'happy': {
                'FaceAngleY': 0.0,
                'FaceAngleX': 0.0,
                'FaceAngleZ': 0.0,
                'MouthOpenY': 0.3,
                'MouthForm': 0.5,
                'EyeOpenLeft': 1.0,
                'EyeOpenRight': 1.0,
                'BrowLeftY': 0.2,
                'BrowRightY': 0.2,
                # Body posturing for happiness
                'BodyAngleX': 0.1,  # Slight forward lean
                'BodyAngleY': 0.0,
                'ArmLeftX': 0.2,    # Relaxed arm position
                'ArmRightX': -0.2,
                'HandLeftY': 0.1,   # Slightly raised hands
                'HandRightY': 0.1,
            },
            'excited': {
                'FaceAngleY': 0.1,
                'FaceAngleX': -0.1,
                'FaceAngleZ': 0.05,
                'MouthOpenY': 0.6,
                'MouthForm': 0.8,
                'EyeOpenLeft': 1.2,
                'EyeOpenRight': 1.2,
                'BrowLeftY': 0.4,
                'BrowRightY': 0.4,
                # Body posturing for excitement
                'BodyAngleX': -0.1,  # Leaning back slightly
                'BodyAngleY': 0.1,   # Slight turn
                'ArmLeftX': 0.4,     # More animated arm positions
                'ArmRightX': -0.4,
                'HandLeftY': 0.3,    # Raised hands
                'HandRightY': 0.3,
                'BodyPositionY': 0.1, # Slight bounce
            },
            'sad': {
                'FaceAngleY': 0.0,
                'FaceAngleX': 0.2,
                'FaceAngleZ': 0.0,
                'MouthOpenY': -0.2,
                'MouthForm': -0.3,
                'EyeOpenLeft': 0.6,
                'EyeOpenRight': 0.6,
                'BrowLeftY': -0.3,
                'BrowRightY': -0.3,
                # Body posturing for sadness
                'BodyAngleX': 0.3,   # Slumped forward
                'BodyAngleY': -0.1,  # Slight turn away
                'ArmLeftX': -0.1,    # Arms closer to body
                'ArmRightX': 0.1,
                'HandLeftY': -0.2,   # Drooping hands
                'HandRightY': -0.2,
                'BodyPositionY': -0.1, # Slightly lower position
            },
            'surprised': {
                'FaceAngleY': 0.0,
                'FaceAngleX': -0.2,
                'FaceAngleZ': 0.0,
                'MouthOpenY': 0.8,
                'MouthForm': 0.2,
                'EyeOpenLeft': 1.5,
                'EyeOpenRight': 1.5,
                'BrowLeftY': 0.6,
                'BrowRightY': 0.6,
                # Body posturing for surprise
                'BodyAngleX': -0.2,  # Leaning back
                'BodyAngleY': 0.0,
                'ArmLeftX': 0.3,     # Arms out in surprise
                'ArmRightX': -0.3,
                'HandLeftY': 0.4,    # Hands raised
                'HandRightY': 0.4,
            },
            'angry': {
                'FaceAngleY': 0.0,
                'FaceAngleX': -0.1,
                'FaceAngleZ': 0.0,
                'MouthOpenY': 0.2,
                'MouthForm': -0.5,
                'EyeOpenLeft': 0.8,
                'EyeOpenRight': 0.8,
                'BrowLeftY': -0.5,
                'BrowRightY': -0.5,
                # Body posturing for anger
                'BodyAngleX': -0.1,  # Chest out, assertive
                'BodyAngleY': 0.0,
                'ArmLeftX': -0.4,    # Arms crossed or hands on hips
                'ArmRightX': 0.4,
                'HandLeftY': 0.0,    # Firm hand positions
                'HandRightY': 0.0,
                'BodyPositionY': 0.05, # Slightly elevated stance
            },
            'seductive': {
                'FaceAngleY': 0.1,
                'FaceAngleX': 0.1,
                'FaceAngleZ': -0.05,
                'MouthOpenY': 0.4,
                'MouthForm': 0.6,
                'EyeOpenLeft': 0.7,
                'EyeOpenRight': 0.7,
                'BrowLeftY': 0.1,
                'BrowRightY': 0.1,
                # Body posturing for seductive
                'BodyAngleX': 0.1,   # Slight forward lean
                'BodyAngleY': 0.2,   # Turn to show profile
                'ArmLeftX': 0.1,     # Graceful arm positions
                'ArmRightX': -0.3,
                'HandLeftY': 0.2,    # Elegant hand positions
                'HandRightY': 0.1,
            },
            'shy': {
                'FaceAngleY': -0.2,
                'FaceAngleX': 0.1,
                'FaceAngleZ': 0.1,
                'MouthOpenY': 0.1,
                'MouthForm': 0.2,
                'EyeOpenLeft': 0.8,
                'EyeOpenRight': 0.8,
                'BrowLeftY': -0.1,
                'BrowRightY': -0.1,
                # Body posturing for shyness
                'BodyAngleX': 0.2,   # Hunched shoulders
                'BodyAngleY': -0.3,  # Turning away
                'ArmLeftX': -0.2,    # Arms behind back or close to body
                'ArmRightX': -0.1,
                'HandLeftY': -0.1,   # Fidgeting hands
                'HandRightY': -0.1,
                'FootLeftX': 0.1,    # Shuffling feet
                'FootRightX': -0.1,
            },
            'curious': {
                'FaceAngleY': 0.1,
                'FaceAngleX': -0.1,
                'FaceAngleZ': 0.02,
                'MouthOpenY': 0.2,
                'MouthForm': 0.3,
                'EyeOpenLeft': 1.1,
                'EyeOpenRight': 1.1,
                'BrowLeftY': 0.3,
                'BrowRightY': 0.3,
                # Body posturing for curiosity
                'BodyAngleX': -0.1,  # Leaning forward with interest
                'BodyAngleY': 0.1,   # Slight head tilt
                'ArmLeftX': 0.2,     # Open, questioning posture
                'ArmRightX': -0.1,
                'HandLeftY': 0.1,    # Gesturing hands
                'HandRightY': 0.2,
            },
            'neutral': {
                'FaceAngleY': 0.0,
                'FaceAngleX': 0.0,
                'FaceAngleZ': 0.0,
                'MouthOpenY': 0.0,
                'MouthForm': 0.0,
                'EyeOpenLeft': 1.0,
                'EyeOpenRight': 1.0,
                'BrowLeftY': 0.0,
                'BrowRightY': 0.0,
                # Neutral body posturing
                'BodyAngleX': 0.0,
                'BodyAngleY': 0.0,
                'ArmLeftX': 0.0,
                'ArmRightX': 0.0,
                'HandLeftY': 0.0,
                'HandRightY': 0.0,
                'BodyPositionY': 0.0,
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize PyVTS connection"""
        if not pyvts:
            self.logger.error("PyVTS not available")
            return False
        
        try:
            self.vts = pyvts.vts()
            await self.vts.connect()
            self.connected = True
            
            # Get available models
            await self._load_available_models()
            
            # Get current model info
            await self._update_current_model()
            
            self.logger.info("PyVTS initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PyVTS: {e}")
            return False
    
    async def _load_available_models(self):
        """Load list of available models"""
        try:
            models_response = await self.vts.request(
                pyvts.vts_request.RequestType.AvailableModelsRequest
            )
            self.available_models = models_response['data']['availableModels']
            self.logger.info(f"Found {len(self.available_models)} available models")
            
        except Exception as e:
            self.logger.error(f"Failed to load available models: {e}")
    
    async def _update_current_model(self):
        """Update current model information"""
        try:
            model_response = await self.vts.request(
                pyvts.vts_request.RequestType.CurrentModelRequest
            )
            self.current_model = model_response['data']
            
            # Load parameters for current model
            await self._load_model_parameters()
            
            self.logger.info(f"Current model: {self.current_model.get('modelName', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Failed to get current model: {e}")
    
    async def _load_model_parameters(self):
        """Load available parameters for current model"""
        try:
            params_response = await self.vts.request(
                pyvts.vts_request.RequestType.ParameterListRequest
            )
            
            self.available_parameters = {}
            for param in params_response['data']['parameters']:
                self.available_parameters[param['name']] = {
                    'min': param['min'],
                    'max': param['max'],
                    'default': param['defaultValue']
                }
            
            self.logger.info(f"Loaded {len(self.available_parameters)} parameters")
            
        except Exception as e:
            self.logger.error(f"Failed to load model parameters: {e}")
    
    async def trigger_emotion(self, emotion: str, intensity: float = 0.5, duration: float = 2.0) -> bool:
        """Trigger emotion expression via parameter manipulation"""
        if not self.connected or not self.current_model:
            self.logger.warning("PyVTS not connected or no model loaded")
            return False
        
        emotion = emotion.lower()
        if emotion not in self.emotion_mappings:
            self.logger.warning(f"Unknown emotion: {emotion}")
            return False
        
        try:
            # Get parameter values for emotion
            emotion_params = self.emotion_mappings[emotion]
            
            # Apply intensity scaling
            scaled_params = {}
            for param_name, value in emotion_params.items():
                if param_name in self.available_parameters:
                    scaled_value = value * intensity
                    # Clamp to parameter limits
                    param_info = self.available_parameters[param_name]
                    scaled_value = max(param_info['min'], min(param_info['max'], scaled_value))
                    scaled_params[param_name] = scaled_value
            
            # Apply parameters
            await self._set_parameters(scaled_params)
            
            # Schedule return to neutral after duration
            asyncio.create_task(self._return_to_neutral_after_delay(duration))
            
            self.logger.info(f"Applied emotion {emotion} with intensity {intensity}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to trigger emotion {emotion}: {e}")
            return False
    
    async def _set_parameters(self, parameters: Dict[str, float]):
        """Set multiple parameters at once"""
        parameter_list = []
        for name, value in parameters.items():
            parameter_list.append({
                'id': name,
                'value': value
            })
        
        request = pyvts.vts_request.ParameterValueRequest(parameter_list)
        await self.vts.request(request)
    
    async def _return_to_neutral_after_delay(self, delay: float):
        """Return to neutral expression after delay"""
        await asyncio.sleep(delay)
        await self.trigger_emotion('neutral', 1.0, 0.0)
    
    async def trigger_lipsync(self, phonemes: List[Tuple[str, float, float]], timing_data: List[Dict]) -> bool:
        """Enhanced lipsync based on phoneme data with timing and envelope"""
        if not self.connected or not self.current_model:
            return False
        
        try:
            # Enhanced phoneme to mouth shape mapping
            phoneme_to_mouth = {
                'A': {'MouthOpenY': 0.9, 'MouthForm': 0.0, 'MouthSmile': 0.0},
                'E': {'MouthOpenY': 0.6, 'MouthForm': 0.4, 'MouthSmile': 0.2},
                'I': {'MouthOpenY': 0.3, 'MouthForm': 0.8, 'MouthSmile': 0.6},
                'O': {'MouthOpenY': 0.7, 'MouthForm': -0.4, 'MouthSmile': 0.0},
                'U': {'MouthOpenY': 0.4, 'MouthForm': -0.7, 'MouthSmile': 0.0},
                'M': {'MouthOpenY': 0.0, 'MouthForm': 0.0, 'MouthSmile': 0.0},
                'B': {'MouthOpenY': 0.0, 'MouthForm': 0.0, 'MouthSmile': 0.0},
                'P': {'MouthOpenY': 0.0, 'MouthForm': 0.0, 'MouthSmile': 0.0},
                'F': {'MouthOpenY': 0.2, 'MouthForm': 0.3, 'MouthSmile': 0.0},
                'V': {'MouthOpenY': 0.2, 'MouthForm': 0.3, 'MouthSmile': 0.0},
                'T': {'MouthOpenY': 0.3, 'MouthForm': 0.2, 'MouthSmile': 0.0},
                'D': {'MouthOpenY': 0.3, 'MouthForm': 0.2, 'MouthSmile': 0.0},
                'L': {'MouthOpenY': 0.4, 'MouthForm': 0.1, 'MouthSmile': 0.1},
                'N': {'MouthOpenY': 0.2, 'MouthForm': 0.1, 'MouthSmile': 0.0},
                'S': {'MouthOpenY': 0.2, 'MouthForm': 0.5, 'MouthSmile': 0.3},
                'Z': {'MouthOpenY': 0.2, 'MouthForm': 0.5, 'MouthSmile': 0.3},
                'silent': {'MouthOpenY': 0.0, 'MouthForm': 0.0, 'MouthSmile': 0.0}
            }
            
            # Create lipsync tasks for each phoneme
            lipsync_tasks = []
            
            for timing_info in timing_data:
                phoneme = timing_info.get('phoneme', 'silent')
                viseme = timing_info.get('viseme', phoneme)
                start_time = timing_info.get('start', 0.0)
                duration = timing_info.get('duration', 0.1)
                
                # Use viseme for mouth shape if available, otherwise phoneme
                mouth_key = viseme if viseme in phoneme_to_mouth else phoneme
                if mouth_key not in phoneme_to_mouth:
                    mouth_key = 'silent'
                
                mouth_params = phoneme_to_mouth[mouth_key].copy()
                
                # Create lipsync task
                task = asyncio.create_task(
                    self._perform_phoneme_lipsync(start_time, duration, mouth_params)
                )
                lipsync_tasks.append(task)
            
            # Wait for all lipsync tasks to complete
            await asyncio.gather(*lipsync_tasks, return_exceptions=True)
            
            # Return mouth to neutral
            await self._set_parameters({
                'MouthOpenY': 0.0, 
                'MouthForm': 0.0, 
                'MouthSmile': 0.0
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to trigger enhanced lipsync: {e}")
            return False
    
    async def _perform_phoneme_lipsync(self, start_time: float, duration: float, mouth_params: Dict[str, float]):
        """Perform individual phoneme lipsync with timing"""
        try:
            # Wait for start time
            await asyncio.sleep(start_time)
            
            # Set mouth shape
            await self._set_parameters(mouth_params)
            
            # Hold for duration
            await asyncio.sleep(duration)
            
        except Exception as e:
            self.logger.error(f"Error in phoneme lipsync: {e}")
    
    async def load_model(self, model_name: str) -> bool:
        """Load a specific model"""
        if not self.connected:
            return False
        
        try:
            # Find model by name
            target_model = None
            for model in self.available_models:
                if model['modelName'] == model_name:
                    target_model = model
                    break
            
            if not target_model:
                self.logger.warning(f"Model not found: {model_name}")
                return False
            
            # Load model
            request = pyvts.vts_request.ModelLoadRequest(target_model['modelID'])
            await self.vts.request(request)
            
            # Update current model info
            await self._update_current_model()
            
            self.logger.info(f"Loaded model: {model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {e}")
            return False
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        return self.available_models
    
    async def get_current_model_info(self) -> Optional[Dict[str, Any]]:
        """Get current model information"""
        return self.current_model
    
    async def close(self):
        """Close PyVTS connection"""
        if self.vts and self.connected:
            try:
                # Stop idle animations
                await self.stop_idle_animations()
                
                await self.vts.close()
                self.connected = False
                self.logger.info("PyVTS connection closed")
            except Exception as e:
                self.logger.error(f"Error closing PyVTS: {e}")
    
    async def start_idle_animations(self):
        """Start background idle animations"""
        if self.is_idle_active:
            return
        
        self.is_idle_active = True
        self.idle_task = asyncio.create_task(self._idle_animation_loop())
        self.breathing_task = asyncio.create_task(self._breathing_animation_loop())
        self.logger.info("Started idle animations")
    
    async def stop_idle_animations(self):
        """Stop background idle animations"""
        self.is_idle_active = False
        
        if self.idle_task:
            self.idle_task.cancel()
            self.idle_task = None
        
        if self.breathing_task:
            self.breathing_task.cancel()
            self.breathing_task = None
        
        self.logger.info("Stopped idle animations")
    
    async def _idle_animation_loop(self):
        """Background loop for idle animations"""
        import random
        
        while self.is_idle_active and self.connected:
            try:
                await asyncio.sleep(random.uniform(3.0, 8.0))  # Random interval
                
                if not self.is_idle_active:
                    break
                
                # Random idle movements
                idle_movements = [
                    'blink',
                    'head_tilt',
                    'look_around',
                    'subtle_movement',
                    'hand_movement',
                    'foot_shuffle'
                ]
                
                movement = random.choice(idle_movements)
                await self._perform_idle_movement(movement)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in idle animation loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _breathing_animation_loop(self):
        """Background breathing animation"""
        import math
        
        while self.is_idle_active and self.connected:
            try:
                # Breathing cycle: 4 seconds in, 4 seconds out
                for phase in range(80):  # 8 seconds total, 0.1s steps
                    if not self.is_idle_active:
                        break
                    
                    # Create breathing motion
                    breath_cycle = math.sin(phase * math.pi / 40)  # Complete cycle
                    breath_intensity = 0.05 * breath_cycle  # Subtle movement
                    
                    await self._set_parameters({
                        'BodyPositionY': breath_intensity,
                        'BreathY': breath_intensity * 2
                    })
                    
                    await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in breathing animation: {e}")
                await asyncio.sleep(1.0)
    
    async def _perform_idle_movement(self, movement_type: str):
        """Perform a specific idle movement"""
        import random
        
        try:
            if movement_type == 'blink':
                # Enhanced blinking
                await self._set_parameters({
                    'EyeOpenLeft': 0.0,
                    'EyeOpenRight': 0.0
                })
                await asyncio.sleep(0.15)
                await self._set_parameters({
                    'EyeOpenLeft': 1.0,
                    'EyeOpenRight': 1.0
                })
            
            elif movement_type == 'head_tilt':
                # Subtle head tilt
                tilt = random.uniform(-0.1, 0.1)
                await self._set_parameters({'FaceAngleZ': tilt})
                await asyncio.sleep(2.0)
                await self._set_parameters({'FaceAngleZ': 0.0})
            
            elif movement_type == 'look_around':
                # Looking left/right
                direction = random.uniform(-0.2, 0.2)
                await self._set_parameters({'FaceAngleY': direction})
                await asyncio.sleep(1.5)
                await self._set_parameters({'FaceAngleY': 0.0})
            
            elif movement_type == 'subtle_movement':
                # Random subtle body movement
                await self._set_parameters({
                    'BodyAngleY': random.uniform(-0.05, 0.05),
                    'BodyPositionX': random.uniform(-0.02, 0.02)
                })
                await asyncio.sleep(2.0)
                await self._set_parameters({
                    'BodyAngleY': 0.0,
                    'BodyPositionX': 0.0
                })
            
            elif movement_type == 'hand_movement':
                # Subtle hand gestures
                await self._set_parameters({
                    'HandLeftY': random.uniform(-0.1, 0.1),
                    'HandRightY': random.uniform(-0.1, 0.1)
                })
                await asyncio.sleep(1.0)
                await self._set_parameters({
                    'HandLeftY': 0.0,
                    'HandRightY': 0.0
                })
            
            elif movement_type == 'foot_shuffle':
                # Foot shuffling
                await self._set_parameters({
                    'FootLeftX': random.uniform(-0.05, 0.05),
                    'FootRightX': random.uniform(-0.05, 0.05)
                })
                await asyncio.sleep(0.5)
                await self._set_parameters({
                    'FootLeftX': 0.0,
                    'FootRightX': 0.0
                })
        
        except Exception as e:
            self.logger.error(f"Error performing idle movement {movement_type}: {e}")

# Global instance
pyvts_controller = None

async def get_pyvts_controller():
    """Get or create PyVTS controller instance"""
    global pyvts_controller
    if pyvts_controller is None:
        pyvts_controller = PyVTSController()
        if not await pyvts_controller.initialize():
            pyvts_controller = None
    return pyvts_controller

async def trigger_pyvts_emotion(emotion: str, intensity: float = 0.5, duration: float = 2.0) -> bool:
    """Helper function to trigger emotions via PyVTS"""
    controller = await get_pyvts_controller()
    if controller:
        return await controller.trigger_emotion(emotion, intensity, duration)
    return False

async def trigger_pyvts_lipsync(phonemes: List[Tuple[str, float, float]], timing_data: List[Dict]) -> bool:
    """Helper function to trigger enhanced lipsync via PyVTS"""
    controller = await get_pyvts_controller()
    if controller:
        return await controller.trigger_lipsync(phonemes, timing_data)
    return False
