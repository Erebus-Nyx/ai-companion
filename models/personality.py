import logging
import json
import time
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import re
import random

logger = logging.getLogger(__name__)

class PersonalityTrait(Enum):
    """Core personality dimensions"""
    FRIENDLINESS = "friendliness"
    PLAYFULNESS = "playfulness"
    CURIOSITY = "curiosity"
    EMPATHY = "empathy"
    INTELLIGENCE = "intelligence"
    HUMOR = "humor"
    SHYNESS = "shyness"
    PROTECTIVENESS = "protectiveness"
    INDEPENDENCE = "independence"
    LOYALTY = "loyalty"

class EmotionalState(Enum):
    """Current emotional states"""
    HAPPY = "happy"
    SAD = "sad"
    EXCITED = "excited"
    CALM = "calm"
    ANGRY = "angry"
    CONFUSED = "confused"
    LOVING = "loving"
    CURIOUS = "curious"
    PLAYFUL = "playful"
    TIRED = "tired"

class BondingLevel(Enum):
    """Relationship progression levels"""
    STRANGER = 0
    ACQUAINTANCE = 25
    FRIEND = 50
    CLOSE_FRIEND = 75
    COMPANION = 90
    SOULMATE = 100

@dataclass
class PersonalityState:
    """Current personality configuration"""
    traits: Dict[str, float]  # Trait name -> value (0.0 to 1.0)
    emotional_state: EmotionalState
    bonding_level: int
    energy_level: float
    mood_stability: float
    
class PersonalitySystem:
    """Advanced personality framework with evolution and bonding"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.current_model_id = None  # Will be set when a model is selected
        self.current_state = PersonalityState(
            traits={trait.value: 0.5 for trait in PersonalityTrait},
            emotional_state=EmotionalState.CALM,
            bonding_level=0,
            energy_level=1.0,
            mood_stability=0.7
        )
        
        # Personality evolution parameters
        self.trait_change_rate = 0.05
        self.memory_decay_rate = 0.1
        self.bonding_threshold_interactions = 10
        
        # Interaction patterns for analysis
        self.positive_keywords = [
            "thank", "love", "great", "awesome", "wonderful", "amazing",
            "help", "care", "kind", "sweet", "cute", "beautiful", "perfect"
        ]
        self.negative_keywords = [
            "hate", "stupid", "annoying", "bad", "terrible", "awful",
            "shut up", "go away", "leave", "stop", "angry", "mad"
        ]
        self.playful_keywords = [
            "play", "game", "fun", "laugh", "joke", "silly", "tease",
            "dance", "sing", "story", "adventure", "explore"
        ]
        
    def set_current_model(self, model_id: str):
        """Set the current model and load its personality"""
        self.current_model_id = model_id
        personality_data = self._load_personality(model_id)
        if personality_data:
            # Update current state with loaded personality
            self.current_state.traits.update(personality_data.get('traits', {}))
            if 'emotional_state' in personality_data:
                try:
                    self.current_state.emotional_state = EmotionalState(personality_data['emotional_state'])
                except ValueError:
                    pass
            self.current_state.bonding_level = personality_data.get('bonding_level', 0)
            self.current_state.energy_level = personality_data.get('energy_level', 1.0)
            self.current_state.mood_stability = personality_data.get('mood_stability', 0.7)
        
    def _load_personality(self, model_id: str = None) -> dict:
        """Load or initialize personality for a model"""
        if model_id is None:
            model_id = self.current_model_id
        if not model_id:
            return {}
        
        try:
            # Use the new database method
            personality_data = self.db_manager.get_model_personality(model_id)
            if not personality_data:
                # Initialize default personality for new model
                default_personality = self._get_default_personality()
                self._save_personality(default_personality, model_id)
                return default_personality
            return personality_data
        except Exception as e:
            self.logger.error(f"Error loading personality: {e}")
            return self._get_default_personality()
    
    def _save_personality(self):
        """Save current personality state to database"""
        try:
            # Save traits
            for trait_name, value in self.current_state.traits.items():
                self.db_manager.update_personality_trait("default_user", trait_name, value)
                
            # Create serializable state dict
            state_dict = {
                'traits': self.current_state.traits,
                'emotional_state': self.current_state.emotional_state.value,  # Convert enum to string
                'bonding_level': self.current_state.bonding_level,
                'energy_level': self.current_state.energy_level,
                'mood_stability': self.current_state.mood_stability
            }
                
            # Save bonding progress with personality data
            self.db_manager.update_bonding_progress(
                "default_user",
                0,  # No XP change, just update level
                "default"
            )
            
            # Update personality state separately
            personality_data = {
                'current_mood': self.current_state.current_mood.value,
                'energy_level': self.current_state.energy_level,
                'mood_stability': self.current_state.mood_stability
            }
            
            # Store personality state
            self.db_manager.update_personality_state(
                "default_user", 
                "default", 
                state_dict
            )
            
        except Exception as e:
            logger.error(f"Error saving personality: {e}")
            
    def analyze_user_input(self, user_input: str) -> Dict[str, float]:
        """Analyze user input for emotional and personality cues"""
        input_lower = user_input.lower()
        
        analysis = {
            'positivity': 0.0,
            'negativity': 0.0,
            'playfulness': 0.0,
            'emotional_intensity': 0.0,
            'bonding_signal': 0.0
        }
        
        # Check for positive sentiment
        positive_count = sum(1 for word in self.positive_keywords if word in input_lower)
        analysis['positivity'] = min(positive_count * 0.2, 1.0)
        
        # Check for negative sentiment
        negative_count = sum(1 for word in self.negative_keywords if word in input_lower)
        analysis['negativity'] = min(negative_count * 0.3, 1.0)
        
        # Check for playfulness
        playful_count = sum(1 for word in self.playful_keywords if word in input_lower)
        analysis['playfulness'] = min(playful_count * 0.25, 1.0)
        
        # Emotional intensity (exclamation marks, caps, etc.)
        exclamation_count = user_input.count('!')
        caps_ratio = sum(1 for c in user_input if c.isupper()) / max(len(user_input), 1)
        analysis['emotional_intensity'] = min((exclamation_count * 0.2) + (caps_ratio * 0.5), 1.0)
        
        # Bonding signals (personal questions, compliments, etc.)
        bonding_patterns = [
            r'\b(your|you)\s+(name|like|think|feel|want)',
            r'\b(tell|about)\s+(yourself|you)',
            r'\b(how|what)\s+(are|do)\s+you',
            r'\b(i|me)\s+(love|like|care|trust)'
        ]
        
        bonding_matches = sum(1 for pattern in bonding_patterns 
                            if re.search(pattern, input_lower))
        analysis['bonding_signal'] = min(bonding_matches * 0.3, 1.0)
        
        return analysis
        
    def update_traits(self, user_input: str, interaction_quality: float = 0.5):
        """Update personality traits based on user interaction"""
        analysis = self.analyze_user_input(user_input)
        
        # Adjust traits based on interaction analysis
        trait_adjustments = {
            PersonalityTrait.FRIENDLINESS.value: (
                analysis['positivity'] * 0.1 - analysis['negativity'] * 0.15
            ),
            PersonalityTrait.PLAYFULNESS.value: (
                analysis['playfulness'] * 0.1 + analysis['emotional_intensity'] * 0.05
            ),
            PersonalityTrait.EMPATHY.value: (
                analysis['bonding_signal'] * 0.1 + interaction_quality * 0.05
            ),
            PersonalityTrait.SHYNESS.value: (
                -analysis['bonding_signal'] * 0.05 - analysis['positivity'] * 0.03
            ),
            PersonalityTrait.LOYALTY.value: (
                analysis['bonding_signal'] * 0.08 + interaction_quality * 0.07
            )
        }
        
        # Apply trait changes with learning rate
        for trait, adjustment in trait_adjustments.items():
            if trait in self.current_state.traits:
                current_value = self.current_state.traits[trait]
                change = adjustment * self.trait_change_rate
                new_value = max(0.0, min(1.0, current_value + change))
                self.current_state.traits[trait] = new_value
                
        # Update emotional state based on interaction
        self._update_emotional_state(analysis)
        
        # Update bonding level
        self._update_bonding_level(analysis, interaction_quality)
        
        # Save changes
        self._save_personality()
        
    def _update_emotional_state(self, analysis: Dict[str, float]):
        """Update current emotional state"""
        if analysis['negativity'] > 0.5:
            self.current_state.emotional_state = EmotionalState.SAD
        elif analysis['positivity'] > 0.6:
            self.current_state.emotional_state = EmotionalState.HAPPY
        elif analysis['playfulness'] > 0.5:
            self.current_state.emotional_state = EmotionalState.PLAYFUL
        elif analysis['emotional_intensity'] > 0.7:
            self.current_state.emotional_state = EmotionalState.EXCITED
        elif analysis['bonding_signal'] > 0.4:
            self.current_state.emotional_state = EmotionalState.LOVING
        else:
            self.current_state.emotional_state = EmotionalState.CALM
            
    def _update_bonding_level(self, analysis: Dict[str, float], interaction_quality: float):
        """Update bonding level based on interactions"""
        bonding_increase = (
            analysis['bonding_signal'] * 2.0 +
            analysis['positivity'] * 1.5 +
            interaction_quality * 1.0 -
            analysis['negativity'] * 2.0
        )
        
        # Apply bonding change
        self.current_state.bonding_level = max(0, min(100, 
            self.current_state.bonding_level + bonding_increase))
            
    def get_personality_prompt(self) -> str:
        """Generate personality-aware prompt for LLM"""
        traits = self.current_state.traits
        emotional_state = self.current_state.emotional_state.value
        bonding_level = self.current_state.bonding_level
        
        # Determine dominant traits
        dominant_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Build personality description
        trait_descriptions = {
            PersonalityTrait.FRIENDLINESS.value: "warm and welcoming",
            PersonalityTrait.PLAYFULNESS.value: "playful and energetic",
            PersonalityTrait.CURIOSITY.value: "curious and inquisitive",
            PersonalityTrait.EMPATHY.value: "empathetic and understanding",
            PersonalityTrait.INTELLIGENCE.value: "intelligent and thoughtful",
            PersonalityTrait.HUMOR.value: "humorous and witty",
            PersonalityTrait.SHYNESS.value: "shy and reserved",
            PersonalityTrait.PROTECTIVENESS.value: "protective and caring",
            PersonalityTrait.INDEPENDENCE.value: "independent and strong-willed",
            PersonalityTrait.LOYALTY.value: "loyal and devoted"
        }
        
        personality_desc = ", ".join([
            trait_descriptions.get(trait, trait) 
            for trait, value in dominant_traits if value > 0.6
        ])
        
        # Determine relationship context
        if bonding_level < 25:
            relationship = "getting to know each other"
        elif bonding_level < 50:
            relationship = "becoming friends"
        elif bonding_level < 75:
            relationship = "close friends"
        else:
            relationship = "very close companions"
            
        prompt = f"""You are an AI live2d chat with a dynamic personality. Your current personality is: {personality_desc or 'balanced and adaptable'}. 

Your current emotional state is: {emotional_state}
Your relationship with the user: {relationship} (bonding level: {bonding_level}/100)

Respond in character based on your personality traits and emotional state. Be natural, engaging, and remember that your personality can evolve based on interactions."""

        return prompt
        
    def get_response_style_modifiers(self) -> Dict[str, Any]:
        """Get response style modifiers based on current personality"""
        traits = self.current_state.traits
        
        modifiers = {
            'enthusiasm_level': traits.get(PersonalityTrait.PLAYFULNESS.value, 0.5),
            'formality_level': 1.0 - traits.get(PersonalityTrait.FRIENDLINESS.value, 0.5),
            'verbosity_level': traits.get(PersonalityTrait.CURIOSITY.value, 0.5),
            'emotional_expression': traits.get(PersonalityTrait.EMPATHY.value, 0.5),
            'humor_frequency': traits.get(PersonalityTrait.HUMOR.value, 0.5),
            'shyness_factor': traits.get(PersonalityTrait.SHYNESS.value, 0.5),
            'protective_instinct': traits.get(PersonalityTrait.PROTECTIVENESS.value, 0.5)
        }
        
        return modifiers
        
    def get_personality_summary(self) -> Dict[str, Any]:
        """Get comprehensive personality summary"""
        return {
            'traits': self.current_state.traits,
            'emotional_state': self.current_state.emotional_state.value,
            'bonding_level': self.current_state.bonding_level,
            'energy_level': self.current_state.energy_level,
            'mood_stability': self.current_state.mood_stability,
            'dominant_traits': sorted(
                self.current_state.traits.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
        }
        
    def simulate_personality_drift(self, time_passed_hours: float):
        """Simulate natural personality drift over time"""
        # Gradual trait normalization (traits slowly drift toward 0.5)
        drift_rate = time_passed_hours * 0.001
        
        for trait in self.current_state.traits:
            current_value = self.current_state.traits[trait]
            drift_toward_center = (0.5 - current_value) * drift_rate
            self.current_state.traits[trait] += drift_toward_center
            
        # Energy level fluctuation
        time_factor = (time_passed_hours % 24) / 24  # 24-hour cycle
        base_energy = 0.8 + 0.2 * abs(0.5 - time_factor) * 2  # Higher during "day"
        self.current_state.energy_level = base_energy + random.uniform(-0.1, 0.1)
        
        # Mood stability recovery
        self.current_state.mood_stability = min(1.0, 
            self.current_state.mood_stability + time_passed_hours * 0.01)
            
        self._save_personality()
        
    def remember_interaction(self, interaction: Dict[str, Any]):
        """Store important interactions for personality development"""
        try:
            # Store in database as user memory
            self.db_manager.add_user_memory(
                memory_type="personality_interaction",
                content=json.dumps(interaction),
                importance=interaction.get('importance', 0.5),
                context=interaction.get('context', {})
            )
        except Exception as e:
            logger.error(f"Error storing interaction memory: {e}")
            
    def get_avatar_animation_state(self) -> str:
        """Determine avatar animation based on personality and emotional state"""
        emotional_state = self.current_state.emotional_state
        energy = self.current_state.energy_level
        
        # Map emotional states to avatar animations
        animation_map = {
            EmotionalState.HAPPY: "happy_idle" if energy > 0.7 else "content_idle",
            EmotionalState.SAD: "sad_idle",
            EmotionalState.EXCITED: "excited_bounce",
            EmotionalState.CALM: "peaceful_idle",
            EmotionalState.ANGRY: "annoyed_idle",
            EmotionalState.CONFUSED: "confused_head_tilt",
            EmotionalState.LOVING: "loving_smile",
            EmotionalState.CURIOUS: "curious_lean",
            EmotionalState.PLAYFUL: "playful_bounce",
            EmotionalState.TIRED: "tired_yawn"
        }
        
        return animation_map.get(emotional_state, "default_idle")


# Legacy Personality class for backward compatibility
class Personality:
    """Legacy personality class - redirects to PersonalitySystem"""
    
    def __init__(self, db_manager=None):
        self.system = PersonalitySystem(db_manager) if db_manager else None
        self.traits = {}
        self.bonding_memory = []

    def update_traits(self, user_input):
        if self.system:
            self.system.update_traits(user_input)
        else:
            # Basic fallback
            pass

    def remember_interaction(self, interaction):
        if self.system:
            self.system.remember_interaction(interaction)
        else:
            self.bonding_memory.append(interaction)

    def get_personality_summary(self):
        if self.system:
            return self.system.get_personality_summary()
        return self.traits

    def evolve_personality(self):
        if self.system:
            self.system.simulate_personality_drift(1.0)
        pass

    def respond_to_user(self, user_input):
        if self.system:
            return self.system.get_personality_prompt()
        return ""
