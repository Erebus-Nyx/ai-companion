#!/usr/bin/env python3
"""
PyVTS Integration for Live2D Avatar Control
Alternative to motion files for models without built-in motions
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
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
        
    def _create_emotion_mappings(self) -> Dict[str, Dict[str, float]]:
        """Create emotion to parameter mappings for VTube Studio"""
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
    
    async def trigger_lipsync(self, phonemes: List[str], timing: List[float]) -> bool:
        """Trigger lipsync based on phoneme data"""
        if not self.connected or not self.current_model:
            return False
        
        try:
            # Map phonemes to mouth shapes
            phoneme_to_mouth = {
                'A': {'MouthOpenY': 0.8, 'MouthForm': 0.0},
                'I': {'MouthOpenY': 0.2, 'MouthForm': 0.8},
                'U': {'MouthOpenY': 0.3, 'MouthForm': -0.5},
                'E': {'MouthOpenY': 0.5, 'MouthForm': 0.3},
                'O': {'MouthOpenY': 0.6, 'MouthForm': -0.3},
                'M': {'MouthOpenY': 0.0, 'MouthForm': 0.0},
                'B': {'MouthOpenY': 0.0, 'MouthForm': 0.0},
                'P': {'MouthOpenY': 0.0, 'MouthForm': 0.0},
                'silent': {'MouthOpenY': 0.0, 'MouthForm': 0.0}
            }
            
            # Schedule phoneme changes
            current_time = 0.0
            for i, phoneme in enumerate(phonemes):
                if phoneme in phoneme_to_mouth:
                    mouth_params = phoneme_to_mouth[phoneme]
                    
                    # Schedule parameter change
                    async def set_mouth_delayed(delay, params):
                        await asyncio.sleep(delay)
                        await self._set_parameters(params)
                    
                    asyncio.create_task(set_mouth_delayed(current_time, mouth_params))
                
                if i < len(timing):
                    current_time += timing[i]
            
            # Return mouth to neutral after all phonemes
            async def reset_mouth_delayed(delay):
                await asyncio.sleep(delay)
                await self._set_parameters({'MouthOpenY': 0.0, 'MouthForm': 0.0})
            
            asyncio.create_task(reset_mouth_delayed(current_time + 0.5))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to trigger lipsync: {e}")
            return False
    
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
                await self.vts.close()
                self.connected = False
                self.logger.info("PyVTS connection closed")
            except Exception as e:
                self.logger.error(f"Error closing PyVTS: {e}")

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

async def trigger_pyvts_lipsync(phonemes: List[str], timing: List[float]) -> bool:
    """Helper function to trigger lipsync via PyVTS"""
    controller = await get_pyvts_controller()
    if controller:
        return await controller.trigger_lipsync(phonemes, timing)
    return False
