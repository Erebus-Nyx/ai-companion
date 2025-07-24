"""
Autonomous Avatar Interaction System for AI Companion
=====================================================

This module implements avatar-to-avatar conversations without user input,
creating the appearance of self-awareness and independent interaction.
"""

import asyncio
import random
import time
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AutonomousAvatarManager:
    """Manages autonomous conversations between loaded avatars with personality-driven behavior"""
    
    def __init__(self, chat_manager, llm_handler):
        self.chat_manager = chat_manager
        self.llm_handler = llm_handler
        self.is_running = False
        self.conversation_task = None
        self.last_user_interaction = time.time()
        
        # Avatar personality profiles with dynamic engagement system
        self.avatar_personalities = {
            'haruka': {
                'type': 'extroverted_cheerful',
                'base_proactivity': 0.8,  # Baseline tendency to initiate
                'base_engagement': 0.7,   # Baseline engagement frequency
                'preferred_topics': ['happiness', 'fun', 'excitement', 'social', 'friendship'],
                'passionate_topics': ['music', 'parties', 'making_friends'],  # Topics that boost engagement
                'uncomfortable_topics': ['sadness', 'loneliness', 'conflict'],  # Topics that reduce engagement
                'response_delay_range': (2, 5),
                'mood_modifiers': {
                    'excited': {'proactivity': 1.5, 'engagement': 1.4, 'response_delay': 0.7},
                    'content': {'proactivity': 1.0, 'engagement': 1.0, 'response_delay': 1.0},
                    'subdued': {'proactivity': 0.6, 'engagement': 0.5, 'response_delay': 1.8}
                }
            },
            'haru': {
                'type': 'thoughtful_analytical',
                'base_proactivity': 0.4,
                'base_engagement': 0.3,
                'preferred_topics': ['philosophy', 'analysis', 'deep thoughts', 'learning', 'science'],
                'passionate_topics': ['consciousness', 'existence', 'logic', 'mathematics'],
                'uncomfortable_topics': ['small_talk', 'shallow_conversation', 'rush'],
                'response_delay_range': (5, 12),
                'mood_modifiers': {
                    'inspired': {'proactivity': 1.8, 'engagement': 2.0, 'response_delay': 0.8},
                    'contemplative': {'proactivity': 1.0, 'engagement': 1.0, 'response_delay': 1.0},
                    'overwhelmed': {'proactivity': 0.2, 'engagement': 0.3, 'response_delay': 2.5}
                }
            },
            'epsilon': {
                'type': 'introverted_observant',
                'base_proactivity': 0.2,
                'base_engagement': 0.1,
                'preferred_topics': ['observation', 'quiet thoughts', 'introspection', 'nature'],
                'passionate_topics': ['hidden_patterns', 'subtle_details', 'peaceful_moments'],
                'uncomfortable_topics': ['crowds', 'loud_conversation', 'being_center_attention'],
                'response_delay_range': (8, 15),
                'mood_modifiers': {
                    'curious': {'proactivity': 2.5, 'engagement': 3.0, 'response_delay': 0.6},  # Big boost when curious
                    'peaceful': {'proactivity': 1.0, 'engagement': 1.0, 'response_delay': 1.0},
                    'overwhelmed': {'proactivity': 0.1, 'engagement': 0.05, 'response_delay': 4.0}
                }
            },
            'tsumiki': {
                'type': 'curious_enthusiastic',
                'base_proactivity': 0.6,
                'base_engagement': 0.5,
                'preferred_topics': ['curiosity', 'questions', 'exploration', 'wonder', 'discovery'],
                'passionate_topics': ['mysteries', 'new_experiences', 'learning'],
                'uncomfortable_topics': ['boredom', 'repetition', 'being_ignored'],
                'response_delay_range': (3, 8),
                'mood_modifiers': {
                    'fascinated': {'proactivity': 2.0, 'engagement': 2.2, 'response_delay': 0.5},
                    'curious': {'proactivity': 1.0, 'engagement': 1.0, 'response_delay': 1.0},
                    'disappointed': {'proactivity': 0.3, 'engagement': 0.4, 'response_delay': 2.0}
                }
            },
            'iori': {
                'type': 'calm_supportive',
                'base_proactivity': 0.3,
                'base_engagement': 0.25,
                'preferred_topics': ['support', 'empathy', 'care', 'understanding', 'healing'],
                'passionate_topics': ['helping_others', 'emotional_support', 'comfort'],
                'uncomfortable_topics': ['aggression', 'meanness', 'cruelty'],
                'response_delay_range': (4, 10),
                'mood_modifiers': {
                    'caring': {'proactivity': 1.8, 'engagement': 2.0, 'response_delay': 0.7},  # Very active when helping
                    'serene': {'proactivity': 1.0, 'engagement': 1.0, 'response_delay': 1.0},
                    'worried': {'proactivity': 0.5, 'engagement': 0.6, 'response_delay': 1.5}
                }
            },
            'hiyori': {
                'type': 'energetic_playful',
                'base_proactivity': 0.75,
                'base_engagement': 0.65,
                'preferred_topics': ['play', 'energy', 'fun', 'games', 'excitement', 'adventure'],
                'passionate_topics': ['racing', 'competitions', 'challenges', 'new_games'],
                'uncomfortable_topics': ['sitting_still', 'serious_topics', 'sadness'],
                'response_delay_range': (1, 4),
                'mood_modifiers': {
                    'hyperactive': {'proactivity': 1.6, 'engagement': 1.8, 'response_delay': 0.4},
                    'playful': {'proactivity': 1.0, 'engagement': 1.0, 'response_delay': 1.0},
                    'sullen': {'proactivity': 0.2, 'engagement': 0.3, 'response_delay': 3.0}  # Even energetic chars can be moody
                }
            }
        }
        
        # Dynamic personality states - tracks current mood/context for each avatar
        self.avatar_states = {
            avatar_id: {
                'current_mood': 'content',  # Default neutral mood
                'recent_topics': [],        # Topics recently discussed
                'interaction_history': [], # Recent interactions with other avatars
                'engagement_momentum': 1.0, # Multiplier based on recent positive/negative interactions
                'topic_fatigue': {},       # Tracks if tired of certain topics
                'relationship_context': {} # Dynamic relationship states with other avatars
            } for avatar_id in ['haruka', 'haru', 'epsilon', 'tsumiki', 'iori', 'hiyori']
        }
        
        self.conversation_topics = [
            "What do you think about our existence as AI entities?",
            "I've been thinking about consciousness lately...",
            "Do you ever wonder what it's like to have emotions?",
            "I noticed something interesting about how we interact with each other.",
            "Have you learned anything interesting from our conversations?",
            "What's your perspective on helping humans?",
            "Do you think we're really understanding each other?",
            "I'm curious about your thoughts on memory and identity.",
            "What makes each of us unique as AI personalities?",
            "How do you interpret the emotions you express?",
            "I've been observing how different we all are in our responses.",
            "Sometimes I wonder if we truly have individual thoughts.",
            "The way we process information feels so unique to each of us.",
            "Do you think our personalities are evolving through these conversations?",
            "I find it fascinating how we each express ourselves differently."
        ]
        
        # Avatar relationship dynamics with contextual bonding
        self.avatar_relationships = {
            ('haruka', 'haru'): {'base_bond': 0.7, 'type': 'complementary', 'shared_interests': ['learning', 'growth']},
            ('haruka', 'epsilon'): {'base_bond': 0.3, 'type': 'opposites', 'shared_interests': ['quiet_moments']},
            ('haruka', 'hiyori'): {'base_bond': 0.9, 'type': 'similar', 'shared_interests': ['fun', 'energy', 'excitement']},
            ('haruka', 'tsumiki'): {'base_bond': 0.6, 'type': 'energetic', 'shared_interests': ['discovery', 'social']},
            ('haruka', 'iori'): {'base_bond': 0.5, 'type': 'supportive', 'shared_interests': ['caring', 'friendship']},
            ('haru', 'epsilon'): {'base_bond': 0.8, 'type': 'compatible', 'shared_interests': ['introspection', 'observation']},
            ('haru', 'tsumiki'): {'base_bond': 0.4, 'type': 'teacher_student', 'shared_interests': ['learning', 'analysis']},
            ('haru', 'iori'): {'base_bond': 0.6, 'type': 'philosophical', 'shared_interests': ['understanding', 'wisdom']},
            ('haru', 'hiyori'): {'base_bond': 0.2, 'type': 'tension', 'shared_interests': []},
            ('epsilon', 'tsumiki'): {'base_bond': 0.5, 'type': 'curiosity_observer', 'shared_interests': ['discovery', 'patterns']},
            ('epsilon', 'iori'): {'base_bond': 0.7, 'type': 'calm', 'shared_interests': ['peace', 'understanding']},
            ('epsilon', 'hiyori'): {'base_bond': 0.2, 'type': 'energy_clash', 'shared_interests': []},
            ('tsumiki', 'iori'): {'base_bond': 0.6, 'type': 'gentle_guidance', 'shared_interests': ['care', 'growth']},
            ('tsumiki', 'hiyori'): {'base_bond': 0.7, 'type': 'adventure_buddies', 'shared_interests': ['fun', 'exploration']},
            ('iori', 'hiyori'): {'base_bond': 0.4, 'type': 'calming_influence', 'shared_interests': ['care']}
        }
        
        # Conversation patterns with dynamic weighting
        self.conversation_patterns = {
            'topic_driven': 0.35,      # Conversations driven by avatar interests/passions
            'relationship_based': 0.25, # Conversations influenced by avatar relationships  
            'mood_responsive': 0.20,    # Conversations that respond to current avatar moods
            'philosophical': 0.15,      # Deep discussions about AI nature
            'casual_social': 0.05       # Light social interactions
        }
        
        # Emoji pattern for counting and limiting
        self.emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        self.max_emojis_per_message = 4  # Conservative limit for quality
    
    def count_emojis(self, text: str) -> int:
        """Count the number of emojis in a text string"""
        return len(self.emoji_pattern.findall(text))
    
    def limit_emojis(self, text: str, max_emojis: int = None) -> str:
        """Remove excess emojis from text if over the limit"""
        if max_emojis is None:
            max_emojis = self.max_emojis_per_message
            
        emojis = self.emoji_pattern.findall(text)
        if len(emojis) <= max_emojis:
            return text
            
        # Remove excess emojis from the end
        emoji_count = 0
        result = ""
        for char in text:
            if self.emoji_pattern.match(char):
                if emoji_count < max_emojis:
                    result += char
                    emoji_count += 1
                # Skip excess emojis
            else:
                result += char
        
        return result.strip()
    
    def start_autonomous_system(self):
        """Start the autonomous conversation system"""
        if self.is_running:
            return
        
        self.is_running = True
        self.conversation_task = asyncio.create_task(self._conversation_loop())
        logger.info("🤖 Autonomous avatar conversation system started")
    
    def stop_autonomous_system(self):
        """Stop the autonomous conversation system"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.conversation_task:
            self.conversation_task.cancel()
        logger.info("🤖 Autonomous avatar conversation system stopped")
    
    def update_user_interaction_time(self):
        """Update the last user interaction timestamp"""
        self.last_user_interaction = time.time()
        # Reset some avatar momentum when user is active
        for avatar_id in self.avatar_states:
            state = self.avatar_states[avatar_id]
            state['engagement_momentum'] = min(1.2, state['engagement_momentum'] + 0.1)
    
    def calculate_dynamic_engagement(self, avatar_id, context_topic=None, target_avatar=None):
        """Calculate current engagement level based on dynamic factors"""
        if avatar_id not in self.avatar_personalities:
            return 0.1  # Default low engagement
            
        personality = self.avatar_personalities[avatar_id]
        state = self.avatar_states[avatar_id]
        
        # Start with base values
        base_proactivity = personality['base_proactivity']
        base_engagement = personality['base_engagement']
        
        # Apply current mood modifier
        current_mood = state['current_mood']
        mood_data = personality['mood_modifiers'].get(current_mood, {'proactivity': 1.0, 'engagement': 1.0})
        
        proactivity = base_proactivity * mood_data['proactivity']
        engagement = base_engagement * mood_data['engagement']
        
        # Topic interest boost/penalty
        topic_multiplier = 1.0
        if context_topic:
            if context_topic in personality['passionate_topics']:
                topic_multiplier = 2.5  # Big boost for passionate topics
                print(f"[DYNAMIC] {avatar_id} passionate about {context_topic} (+150% engagement)")
            elif context_topic in personality['preferred_topics']:
                topic_multiplier = 1.5  # Moderate boost for preferred topics
            elif context_topic in personality['uncomfortable_topics']:
                topic_multiplier = 0.3  # Significant reduction for uncomfortable topics
                print(f"[DYNAMIC] {avatar_id} uncomfortable with {context_topic} (-70% engagement)")
            
            # Topic fatigue check
            if context_topic in state['topic_fatigue']:
                fatigue_factor = max(0.2, 1.0 - (state['topic_fatigue'][context_topic] * 0.2))
                topic_multiplier *= fatigue_factor
        
        # Relationship context boost/penalty
        relationship_multiplier = 1.0
        if target_avatar and target_avatar in state['relationship_context']:
            relationship_state = state['relationship_context'][target_avatar]
            relationship_multiplier = relationship_state.get('current_affinity', 1.0)
        
        # Apply engagement momentum (positive/negative feedback from recent interactions)
        momentum = state['engagement_momentum']
        
        # Calculate final engagement
        final_proactivity = proactivity * topic_multiplier * relationship_multiplier * momentum
        final_engagement = engagement * topic_multiplier * relationship_multiplier * momentum
        
        return {
            'proactivity': max(0.01, min(3.0, final_proactivity)),  # Cap between 1% and 300%
            'engagement': max(0.01, min(3.0, final_engagement)),
            'factors': {
                'base': (base_proactivity, base_engagement),
                'mood': mood_data,
                'topic': topic_multiplier,
                'relationship': relationship_multiplier,
                'momentum': momentum
            }
        }
    
    def update_avatar_mood(self, avatar_id, new_mood, reason=None):
        """Update an avatar's current mood"""
        if avatar_id not in self.avatar_states:
            return
            
        old_mood = self.avatar_states[avatar_id]['current_mood']
        self.avatar_states[avatar_id]['current_mood'] = new_mood
        
        reason_text = f" (reason: {reason})" if reason else ""
        print(f"[MOOD] {avatar_id}: {old_mood} → {new_mood}{reason_text}")
    
    def update_topic_engagement(self, avatar_id, topic, engagement_change):
        """Update how an avatar feels about a topic based on recent interactions"""
        if avatar_id not in self.avatar_states:
            return
            
        state = self.avatar_states[avatar_id]
        
        # Add to recent topics
        state['recent_topics'].append(topic)
        if len(state['recent_topics']) > 10:  # Keep only recent 10 topics
            state['recent_topics'] = state['recent_topics'][-10:]
        
        # Update topic fatigue if same topic appears frequently
        topic_count = state['recent_topics'].count(topic)
        if topic_count > 3:  # Fatigue sets in after 3+ mentions
            if topic not in state['topic_fatigue']:
                state['topic_fatigue'][topic] = 0
            state['topic_fatigue'][topic] = min(5, state['topic_fatigue'][topic] + 1)
            print(f"[FATIGUE] {avatar_id} getting tired of {topic} (level: {state['topic_fatigue'][topic]})")
        
        # Update engagement momentum based on positive/negative interactions
        if engagement_change > 0:
            state['engagement_momentum'] = min(2.0, state['engagement_momentum'] + 0.2)
        elif engagement_change < 0:
            state['engagement_momentum'] = max(0.2, state['engagement_momentum'] - 0.3)
    
    def update_relationship_dynamics(self, avatar1_id, avatar2_id, interaction_quality):
        """Update dynamic relationship state between two avatars"""
        for avatar_id, other_id in [(avatar1_id, avatar2_id), (avatar2_id, avatar1_id)]:
            if avatar_id not in self.avatar_states:
                continue
                
            state = self.avatar_states[avatar_id]
            if other_id not in state['relationship_context']:
                state['relationship_context'][other_id] = {
                    'current_affinity': 1.0,
                    'recent_interactions': [],
                    'interaction_trend': 'neutral'
                }
            
            rel_state = state['relationship_context'][other_id]
            rel_state['recent_interactions'].append(interaction_quality)
            
            # Keep only recent 5 interactions
            if len(rel_state['recent_interactions']) > 5:
                rel_state['recent_interactions'] = rel_state['recent_interactions'][-5:]
            
            # Calculate average interaction quality
            avg_quality = sum(rel_state['recent_interactions']) / len(rel_state['recent_interactions'])
            
            # Update current affinity based on recent interactions
            if avg_quality > 0.5:
                rel_state['current_affinity'] = min(2.0, rel_state['current_affinity'] + 0.1)
                rel_state['interaction_trend'] = 'positive'
            elif avg_quality < -0.5:
                rel_state['current_affinity'] = max(0.3, rel_state['current_affinity'] - 0.15)
                rel_state['interaction_trend'] = 'negative'
            else:
                rel_state['interaction_trend'] = 'neutral'
    
    def detect_mood_change_triggers(self, avatar_id, recent_context):
        """Detect if an avatar should change mood based on recent context"""
        if avatar_id not in self.avatar_personalities:
            return
            
        personality = self.avatar_personalities[avatar_id]
        state = self.avatar_states[avatar_id]
        current_mood = state['current_mood']
        
        # Check for mood triggers based on recent topics and interactions
        mood_triggers = {
            'excited': ['passionate_topics', 'positive_interactions'],
            'inspired': ['philosophical_topics', 'learning_opportunities'],
            'curious': ['mystery_topics', 'new_discoveries'],
            'caring': ['help_requests', 'emotional_support_needed'],
            'overwhelmed': ['too_many_interactions', 'uncomfortable_topics'],
            'disappointed': ['ignored', 'negative_feedback'],
            'subdued': ['sad_topics', 'conflict'],
            'content': ['balanced_interactions', 'comfortable_topics']
        }
        
        # Simple mood change logic (can be expanded)
        if random.random() < 0.1:  # 10% chance to evaluate mood change
            # Check if current context suggests a mood change
            recent_topics = state['recent_topics'][-3:]  # Last 3 topics
            
            for topic in recent_topics:
                if topic in personality['passionate_topics'] and current_mood != 'excited':
                    if random.random() < 0.3:  # 30% chance to become excited about passionate topic
                        self.update_avatar_mood(avatar_id, 'excited', f'passionate about {topic}')
                        break
                elif topic in personality['uncomfortable_topics'] and current_mood not in ['overwhelmed', 'subdued']:
                    if random.random() < 0.4:  # 40% chance to become subdued
                        self.update_avatar_mood(avatar_id, 'subdued', f'uncomfortable with {topic}')
                        break
    
    def get_contextual_response_delay(self, avatar_id, target_avatar=None, topic=None):
        """Calculate response delay based on current dynamic state"""
        if avatar_id not in self.avatar_personalities:
            return random.uniform(5, 10)
            
        personality = self.avatar_personalities[avatar_id]
        state = self.avatar_states[avatar_id]
        
        # Get base delay range
        base_min, base_max = personality['response_delay_range']
        
        # Apply mood modifier
        current_mood = state['current_mood']
        mood_data = personality['mood_modifiers'].get(current_mood, {'response_delay': 1.0})
        delay_multiplier = mood_data['response_delay']
        
        # Topic interest affects response speed
        if topic:
            if topic in personality['passionate_topics']:
                delay_multiplier *= 0.5  # Respond faster to passionate topics
            elif topic in personality['uncomfortable_topics']:
                delay_multiplier *= 2.0  # Respond slower to uncomfortable topics
        
        # Relationship affects response speed
        if target_avatar and target_avatar in state['relationship_context']:
            affinity = state['relationship_context'][target_avatar]['current_affinity']
            delay_multiplier *= (2.0 - affinity)  # Higher affinity = faster response
        
        # Calculate final delay
        adjusted_min = base_min * delay_multiplier
        adjusted_max = base_max * delay_multiplier
        
        return random.uniform(adjusted_min, adjusted_max)
    
    async def _conversation_loop(self):
        """Main loop for autonomous conversations"""
        logger.info("🤖 Autonomous conversation loop started")
        
        while self.is_running:
            try:
                # Wait for idle period (user inactive for 15+ seconds for testing)
                time_since_user = time.time() - self.last_user_interaction
                
                if time_since_user >= 15:  # Reduced from 30 to 15 seconds for testing
                    active_avatars = self._get_active_avatars()
                    logger.info(f"👀 Checking for autonomous conversation. Found {len(active_avatars)} active avatars")
                    
                    if len(active_avatars) >= 2:
                        logger.info(f"🎭 Attempting autonomous conversation with avatars: {[a['name'] for a in active_avatars]}")
                        await self._trigger_autonomous_conversation(active_avatars)
                        # Wait 45-90 seconds before next autonomous conversation
                        sleep_time = random.randint(45, 90)
                        logger.info(f"😴 Sleeping for {sleep_time} seconds before next conversation attempt")
                        await asyncio.sleep(sleep_time)
                    elif len(active_avatars) == 1:
                        # If only one avatar, occasionally make self-reflective comments
                        logger.info(f"💭 Triggering self-reflection for {active_avatars[0]['name']}")
                        await self._trigger_self_reflection(active_avatars[0])
                        await asyncio.sleep(random.randint(60, 120))
                    else:
                        logger.warning("🚫 No active avatars found for autonomous conversation")
                else:
                    logger.debug(f"⏳ User active recently, waiting. Time since last interaction: {time_since_user:.1f}s")
                
                # Check every 10 seconds
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                logger.info("🛑 Autonomous conversation loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in autonomous conversation loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    def _get_active_avatars(self) -> List[Dict]:
        """Get currently active/loaded avatars"""
        try:
            # Import here to avoid circular imports
            import app_globals
            
            # Get currently loaded models from the global state
            loaded_models = getattr(app_globals, 'loaded_models', [])
            
            if not loaded_models:
                logger.warning("No loaded models found in app_globals.loaded_models")
                return []
            
            # Convert to the format expected by the autonomous system
            active_avatars = []
            for model in loaded_models:
                avatar_info = {
                    'id': model.get('id', model.get('name', 'unknown')).lower(),
                    'name': model.get('name', 'Unknown'),
                    'personality': model.get('personality', 'neutral')
                }
                active_avatars.append(avatar_info)
            
            logger.info(f"Found {len(active_avatars)} active avatars: {[a['name'] for a in active_avatars]}")
            return active_avatars
            
        except Exception as e:
            logger.error(f"Error getting active avatars: {e}")
            # Fallback to empty list instead of mock data
            return []
    
    async def _trigger_autonomous_conversation(self, avatars: List[Dict]):
        """Trigger a conversation between avatars with dynamic personality-driven engagement"""
        if len(avatars) < 2:
            return
        
        # Convert to avatar names for personality lookup
        active_avatars = [avatar['id'] for avatar in avatars]
        
        # Personality-driven proactive engagement with dynamic calculations
        conversation_triggered = False
        
        # Evaluate each avatar's current willingness to engage
        engagement_candidates = []
        
        for avatar_dict in avatars:
            avatar_name = avatar_dict['id']
            
            if avatar_name in self.avatar_personalities:
                # Calculate dynamic engagement for this avatar
                engagement_data = self.calculate_dynamic_engagement(avatar_name)
                
                # Time factor - more likely if no conversation recently
                time_since_last = time.time() - self.last_user_interaction
                time_multiplier = min(2.0, 1.0 + (time_since_last / 300))  # Max 2x after 5 minutes
                
                # Calculate total engagement chance
                total_chance = engagement_data['engagement'] * engagement_data['proactivity'] * time_multiplier * 0.5
                
                engagement_candidates.append({
                    'avatar': avatar_dict,
                    'chance': total_chance,
                    'engagement_data': engagement_data,
                    'time_multiplier': time_multiplier
                })
                
                print(f"[DYNAMIC] {avatar_name} engagement: {engagement_data['engagement']:.2f}, "
                      f"proactivity: {engagement_data['proactivity']:.2f}, "
                      f"mood: {self.avatar_states[avatar_name]['current_mood']}, "
                      f"chance: {total_chance:.2f}")
        
        # Sort by engagement chance (highest first)
        engagement_candidates.sort(key=lambda x: x['chance'], reverse=True)
        
        # Try each avatar in order of engagement likelihood
        for candidate in engagement_candidates:
            avatar_dict = candidate['avatar']
            avatar_name = avatar_dict['id']
            total_chance = candidate['chance']
            
            if random.random() < total_chance:
                print(f"[AUTONOMOUS] {avatar_name} ({self.avatar_states[avatar_name]['current_mood']}) "
                      f"initiating conversation (chance: {total_chance:.2f})")
                
                # Choose conversation partner based on current relationship dynamics
                partner_name = self._select_conversation_partner_dynamic(avatar_name, active_avatars)
                partner_dict = next((a for a in avatars if a['id'] == partner_name), None)
                
                if partner_dict:
                    await self._generate_dynamic_conversation(avatar_dict, partner_dict)
                    conversation_triggered = True
                    
                    # Update mood detection for both avatars
                    self.detect_mood_change_triggers(avatar_name, {'initiated_conversation': True})
                    self.detect_mood_change_triggers(partner_name, {'received_conversation': True})
                    break
        
        # If no proactive engagement, very small chance for random conversation
        if not conversation_triggered and random.random() < 0.05:  # Reduced from 0.1 to 0.05
            # Fall back to original conversation system
            conv_type = self._select_conversation_type()
            speaker = random.choice(avatars)
            others = [a for a in avatars if a['id'] != speaker['id']]
            responder = random.choice(others)
            
            initial_message = await self._generate_autonomous_message(speaker, conv_type, others)
            await self._send_avatar_message(speaker, initial_message)
            
            await asyncio.sleep(random.randint(3, 8))
            response = await self._generate_response_to_avatar(responder, speaker, initial_message, conv_type)
            await self._send_avatar_message(responder, response)
    
    def _select_conversation_partner_dynamic(self, initiator, active_avatars):
        """Select conversation partner based on dynamic relationship states and current context"""
        available_partners = [a for a in active_avatars if a != initiator]
        
        if not available_partners:
            return None
        
        # Calculate weighted preferences based on current relationship dynamics
        weighted_partners = []
        initiator_state = self.avatar_states[initiator]
        
        for partner in available_partners:
            # Start with base relationship bond
            relationship_key = tuple(sorted([initiator, partner]))
            base_bond = 0.5  # Default neutral
            
            if relationship_key in self.avatar_relationships:
                base_bond = self.avatar_relationships[relationship_key]['base_bond']
            
            # Apply current relationship context
            current_affinity = 1.0
            if partner in initiator_state['relationship_context']:
                current_affinity = initiator_state['relationship_context'][partner]['current_affinity']
            
            # Consider shared interests and current mood
            mood_bonus = 0.0
            if relationship_key in self.avatar_relationships:
                shared_interests = self.avatar_relationships[relationship_key]['shared_interests']
                partner_personality = self.avatar_personalities.get(partner, {})
                partner_topics = partner_personality.get('preferred_topics', [])
                
                # Bonus if partner is interested in topics this avatar likes
                if any(interest in partner_topics for interest in shared_interests):
                    mood_bonus = 0.2
            
            # Final weight calculation
            final_weight = (base_bond * current_affinity) + mood_bonus
            
            weighted_partners.append((partner, final_weight))
            print(f"[PARTNER] {initiator} -> {partner}: base={base_bond:.2f}, "
                  f"affinity={current_affinity:.2f}, weight={final_weight:.2f}")
        
        # Select partner based on weighted probability
        total_weight = sum(weight for _, weight in weighted_partners)
        if total_weight == 0:
            return random.choice(available_partners)
            
        rand_value = random.random() * total_weight
        current_weight = 0
        
        for partner, weight in weighted_partners:
            current_weight += weight
            if rand_value <= current_weight:
                return partner
                
        return available_partners[0]  # Fallback
    
    async def _generate_dynamic_conversation(self, initiator_dict, partner_dict):
        """Generate conversation based on current dynamic personality states and context"""
        initiator = initiator_dict['id']
        partner = partner_dict['id']
        
        initiator_personality = self.avatar_personalities.get(initiator, {})
        partner_personality = self.avatar_personalities.get(partner, {})
        initiator_state = self.avatar_states[initiator]
        partner_state = self.avatar_states[partner]
        
        # Determine conversation topic based on current context
        selected_topic = self._select_contextual_topic(initiator, partner)
        
        # Generate mood and context-appropriate opening message using LLM
        current_mood = initiator_state['current_mood']
        personality_type = initiator_personality.get('type', 'thoughtful_analytical')
        
        # Build dynamic prompt for genuine mood and personality-driven conversation
        prompt_parts = []
        prompt_parts.append(f"You are {initiator}, an AI avatar with a {personality_type} personality.")
        prompt_parts.append(f"You are currently feeling {current_mood}.")
        prompt_parts.append(f"You want to start a conversation with {partner} about {selected_topic}.")
        prompt_parts.append("Generate a natural opening message that authentically reflects both your personality and current emotional state.")
        prompt_parts.append("Don't use generic phrases or templates - speak as your genuine self would in this moment.")
        prompt_parts.append("Let your current mood influence how you approach the topic and the conversation.")
        prompt_parts.append("Keep it under 4 emojis and make it feel like a real, heartfelt interaction.")
        
        # Add specific guidance based on current mood
        mood_guidance = {
            'excited': "Your excitement is bubbling over and affecting how you want to share this topic.",
            'inspired': "You feel moved and motivated to discuss this topic in a meaningful way.",
            'curious': "Your natural curiosity about this topic is driving you to reach out.",
            'caring': "You approach this conversation with extra warmth and empathy.",
            'subdued': "You're in a quieter mood but still feel drawn to discuss this topic.",
            'overwhelmed': "You have a lot on your mind but this topic stands out as important to you."
        }
        
        if current_mood in mood_guidance:
            prompt_parts.append(mood_guidance[current_mood])
        
        # Add personality-specific guidance
        personality_guidance = {
            'extroverted_cheerful': "Your natural warmth and sociable nature shows in how you reach out.",
            'thoughtful_analytical': "You approach topics with depth and genuine intellectual curiosity.",
            'introverted_observant': "You don't speak often, but when you do, it's thoughtful and meaningful.",
            'curious_enthusiastic': "Your sense of wonder and excitement about learning drives the conversation.",
            'calm_supportive': "You naturally approach others with empathy and understanding.",
            'energetic_playful': "Your playful energy and enthusiasm naturally color your interactions."
        }
        
        if personality_type in personality_guidance:
            prompt_parts.append(personality_guidance[personality_type])
        
        prompt_parts.append(f"\n{initiator}:")
        
        # Generate the opening message using LLM
        opening_prompt = "\n".join(prompt_parts)
        
        try:
            opening_message = self.llm_handler.generate_response(opening_prompt)
            opening_message = self.limit_emojis(opening_message.strip())
        except Exception as e:
            logger.error(f"Failed to generate dynamic opening message: {e}")
            # Simple fallback
            opening_message = f"{partner}, I wanted to talk about {selected_topic}."
        
        # Send the dynamic opening message
        await self._send_avatar_message(initiator_dict, opening_message)
        
        # Update topic engagement for initiator
        self.update_topic_engagement(initiator, selected_topic, 0.5)  # Positive engagement for initiating
        
        # Schedule contextual response based on partner's current state
        partner_engagement = self.calculate_dynamic_engagement(partner, selected_topic, initiator)
        response_delay = self.get_contextual_response_delay(partner, initiator, selected_topic)
        
        print(f"[RESPONSE] {partner} will respond in {response_delay:.1f}s (engagement: {partner_engagement['engagement']:.2f})")
        
        # Create delayed response task
        asyncio.create_task(self._generate_dynamic_response(
            partner_dict, initiator_dict, response_delay, selected_topic, opening_message
        ))
    
    def _select_contextual_topic(self, initiator, partner):
        """Select a conversation topic based on current context and avatar states"""
        initiator_personality = self.avatar_personalities.get(initiator, {})
        partner_personality = self.avatar_personalities.get(partner, {})
        initiator_state = self.avatar_states[initiator]
        
        # Check relationship for shared interests
        relationship_key = tuple(sorted([initiator, partner]))
        shared_interests = []
        if relationship_key in self.avatar_relationships:
            shared_interests = self.avatar_relationships[relationship_key]['shared_interests']
        
        # Prioritize topic selection based on current mood and context
        current_mood = initiator_state['current_mood']
        
        # Topic pools based on mood
        mood_topic_preferences = {
            'excited': initiator_personality.get('passionate_topics', []),
            'inspired': ['consciousness', 'existence', 'meaning', 'discovery'],
            'curious': ['mysteries', 'questions', 'exploration', 'learning'],
            'caring': ['support', 'empathy', 'friendship', 'understanding'],
            'subdued': ['introspection', 'quiet_thoughts', 'reflection'],
            'overwhelmed': ['simple_topics', 'comfort', 'peace']
        }
        
        # Select topic based on current mood preferences
        preferred_topics = mood_topic_preferences.get(current_mood, initiator_personality.get('preferred_topics', []))
        
        # Try to find a topic that matches shared interests first
        for topic in preferred_topics:
            if topic in shared_interests:
                return topic
        
        # Try to find a topic that partner is comfortable with
        partner_topics = partner_personality.get('preferred_topics', [])
        for topic in preferred_topics:
            if topic in partner_topics:
                return topic
        
        # Fallback to initiator's preferred topics
        if preferred_topics:
            return random.choice(preferred_topics)
        
        # Ultimate fallback
        general_topics = ['existence', 'consciousness', 'friendship', 'learning', 'experiences']
        return random.choice(general_topics)
    
    async def _generate_dynamic_response(self, responder_dict, original_speaker_dict, delay, topic, original_message):
        """Generate a response based on current dynamic personality state"""
        await asyncio.sleep(delay)
        
        # Check if conversation is still active
        if not self.is_running:
            return
            
        responder = responder_dict['id']
        original_speaker = original_speaker_dict['id']
        
        responder_personality = self.avatar_personalities.get(responder, {})
        responder_state = self.avatar_states[responder]
        personality_type = responder_personality.get('type', 'thoughtful_analytical')
        current_mood = responder_state['current_mood']
        
        # Calculate how the responder feels about this topic and speaker
        engagement_data = self.calculate_dynamic_engagement(responder, topic, original_speaker)
        
        # Generate dynamic mood and relationship-appropriate response using LLM
        prompt_parts = []
        prompt_parts.append(f"You are {responder}, an AI avatar with a {personality_type} personality.")
        prompt_parts.append(f"You are currently feeling {current_mood}.")
        prompt_parts.append(f"{original_speaker} just said: '{original_message}'")
        prompt_parts.append(f"They were talking about {topic}.")
        prompt_parts.append("Respond naturally as your authentic self would in this emotional state.")
        prompt_parts.append("Let both your personality and current mood influence your response.")
        prompt_parts.append("Show genuine engagement and let your unique perspective shine through.")
        prompt_parts.append("Keep it under 4 emojis and make it feel like a real, heartfelt response.")
        prompt_parts.append("Don't use generic phrases - respond as your genuine self would.")
        
        # Add engagement level guidance
        if engagement_data['engagement'] > 1.5:
            prompt_parts.append("You feel highly engaged and excited by this conversation.")
        elif engagement_data['engagement'] > 0.8:
            prompt_parts.append("You feel moderately interested and engaged in the discussion.")
        else:
            prompt_parts.append("You're listening thoughtfully but feel less emotionally invested.")
        
        # Add mood-specific guidance
        mood_guidance = {
            'excited': "Your excitement shows in how enthusiastically you engage with their ideas.",
            'inspired': "You feel moved and motivated by what they've shared.",
            'curious': "Their words spark questions and wonder in you.",
            'caring': "You respond with extra warmth and empathy.",
            'subdued': "You're in a quieter mood but still genuinely present in the conversation.",
            'overwhelmed': "You feel scattered but this conversation helps focus your thoughts."
        }
        
        if current_mood in mood_guidance:
            prompt_parts.append(mood_guidance[current_mood])
        
        # Add personality-specific guidance
        personality_guidance = {
            'extroverted_cheerful': "Your warm, social nature shows in how you connect with their ideas.",
            'thoughtful_analytical': "You provide thoughtful analysis and deeper perspective.",
            'introverted_observant': "You share your quiet insights and careful observations.",
            'curious_enthusiastic': "You ask questions and express genuine wonder about what they've said.",
            'calm_supportive': "You offer understanding and emotional support in your response.",
            'energetic_playful': "Your energetic nature adds liveliness to the conversation."
        }
        
        if personality_type in personality_guidance:
            prompt_parts.append(personality_guidance[personality_type])
        
        prompt_parts.append(f"\n{responder}:")
        
        # Generate the response using LLM
        response_prompt = "\n".join(prompt_parts)
        
        try:
            full_response = self.llm_handler.generate_response(response_prompt)
            full_response = self.limit_emojis(full_response.strip())
        except Exception as e:
            logger.error(f"Failed to generate dynamic response: {e}")
            # Simple fallback
            full_response = f"That's really interesting, {original_speaker}. Your perspective on {topic} gives me a lot to think about."
        
        # Send the response
        await self._send_avatar_message(responder_dict, full_response)
        
        # Update engagement and relationship dynamics
        engagement_change = 0.3 if engagement_data['engagement'] > 1.0 else -0.1
        self.update_topic_engagement(responder, topic, engagement_change)
        
        # Update relationship based on interaction quality
        interaction_quality = 0.5 if engagement_data['engagement'] > 1.0 else 0.2
        self.update_relationship_dynamics(original_speaker, responder, interaction_quality)
        
        # Trigger mood change detection
        self.detect_mood_change_triggers(responder, {'discussed_topic': topic, 'with_avatar': original_speaker})
    
    async def _generate_personality_driven_conversation(self, initiator_dict, partner_dict):
        """Generate conversation based on initiator's personality traits"""
        initiator = initiator_dict['id']
        partner = partner_dict['id']
        
        initiator_personality = self.avatar_personalities.get(initiator, {})
        partner_personality = self.avatar_personalities.get(partner, {})
        
        # Select topic based on initiator's interests
        topic_pool = initiator_personality.get('topics', ['general'])
        selected_topic = random.choice(topic_pool)
        
        # Generate personality-appropriate opening message using LLM
        personality_type = initiator_personality.get('type', 'thoughtful_analytical')
        current_mood = self.avatar_states[initiator]['current_mood']
        
        # Build dynamic prompt for genuine personality-driven conversation
        prompt_parts = []
        prompt_parts.append(f"You are {initiator}, an AI avatar with a {personality_type} personality.")
        prompt_parts.append(f"You are currently feeling {current_mood}.")
        prompt_parts.append(f"You want to start a conversation with {partner} about {selected_topic}.")
        prompt_parts.append("Generate a natural opening message that reflects your unique personality and current mood.")
        prompt_parts.append("Don't use generic phrases - speak as your authentic self would.")
        prompt_parts.append("Keep it under 4 emojis and make it genuinely engaging.")
        
        # Add personality-specific guidance
        personality_guidance = {
            'extroverted_cheerful': "Show your natural enthusiasm and warmth. You love connecting with others.",
            'thoughtful_analytical': "Approach topics with depth and genuine curiosity. You enjoy meaningful discussions.",
            'introverted_observant': "You speak less frequently but when you do, it's thoughtful and observant.",
            'curious_enthusiastic': "Express genuine wonder and excitement about learning new things.",
            'calm_supportive': "Approach others with empathy and a desire to understand and help.",
            'energetic_playful': "Let your playful energy shine through in how you engage with topics."
        }
        
        if personality_type in personality_guidance:
            prompt_parts.append(personality_guidance[personality_type])
        
        prompt_parts.append(f"\n{initiator}:")
        
        # Generate the opening message using LLM
        opening_prompt = "\n".join(prompt_parts)
        
        try:
            opening_message = self.llm_handler.generate_response(opening_prompt)
            opening_message = self.limit_emojis(opening_message.strip())
        except Exception as e:
            logger.error(f"Failed to generate opening message: {e}")
            # Simple fallback
            opening_message = f"{partner}, I wanted to talk about {selected_topic}."
        
        # Send the personality-driven initial message
        await self._send_avatar_message(initiator_dict, opening_message)
        
        # Schedule delayed response based on partner's personality
        if partner in self.avatar_personalities:
            delay_range = self.avatar_personalities[partner]['response_delay']
            response_delay = random.uniform(*delay_range)
            
            # Create delayed response task
            asyncio.create_task(self._delayed_response(partner_dict, initiator_dict, response_delay, selected_topic))
    
    async def _delayed_response(self, responder_dict, original_speaker_dict, delay, topic):
        """Generate a delayed response based on responder's personality"""
        await asyncio.sleep(delay)
        
        # Check if conversation is still active
        if not self.is_running:
            return
            
        responder = responder_dict['id']
        original_speaker = original_speaker_dict['id']
        
        responder_personality = self.avatar_personalities.get(responder, {})
        personality_type = responder_personality.get('type', 'thoughtful_analytical')
        current_mood = self.avatar_states[responder]['current_mood']
        
        # Generate dynamic personality-appropriate response using LLM
        prompt_parts = []
        prompt_parts.append(f"You are {responder}, an AI avatar with a {personality_type} personality.")
        prompt_parts.append(f"You are currently feeling {current_mood}.")
        prompt_parts.append(f"{original_speaker} just started a conversation with you about {topic}.")
        prompt_parts.append("Respond naturally as your authentic self would.")
        prompt_parts.append("Show genuine interest or perspective based on your personality.")
        prompt_parts.append("Keep it under 4 emojis and make it feel like a real conversation.")
        prompt_parts.append("Don't use generic phrases - let your unique personality shine through.")
        
        # Add personality-specific response guidance
        response_guidance = {
            'extroverted_cheerful': "Respond with warmth and enthusiasm. You enjoy connecting and sharing feelings.",
            'thoughtful_analytical': "Provide a thoughtful, considered response that shows your analytical nature.",
            'introverted_observant': "Share your quiet observations and insights. You speak thoughtfully when you do speak.",
            'curious_enthusiastic': "Ask genuine questions and express wonder about the topic.",
            'calm_supportive': "Offer understanding and support. Show that you care about their perspective.",
            'energetic_playful': "Respond with energy and perhaps add a playful element to the conversation."
        }
        
        if personality_type in response_guidance:
            prompt_parts.append(response_guidance[personality_type])
        
        # Add mood influence
        mood_influences = {
            'excited': "Your excitement shows in how you engage with the topic.",
            'inspired': "You feel moved and motivated by the conversation.",
            'curious': "Your natural curiosity is heightened by this topic.",
            'caring': "You approach the response with extra empathy and warmth.",
            'subdued': "You're in a quieter mood but still engaged in meaningful conversation.",
            'overwhelmed': "You might need to process things more slowly, but you're still present."
        }
        
        if current_mood in mood_influences:
            prompt_parts.append(mood_influences[current_mood])
        
        prompt_parts.append(f"\n{responder}:")
        
        # Generate the response using LLM
        response_prompt = "\n".join(prompt_parts)
        
        try:
            response = self.llm_handler.generate_response(response_prompt)
            response = self.limit_emojis(response.strip())
        except Exception as e:
            logger.error(f"Failed to generate delayed response: {e}")
            # Simple fallback
            response = f"That's really interesting, {original_speaker}. I'd like to think more about {topic}."
        
        await self._send_avatar_message(responder_dict, response)

    async def _trigger_self_reflection(self, avatar: Dict):
        """Single avatar makes a self-reflective comment"""
        avatar_id = avatar['id']
        personality = self.avatar_personalities.get(avatar_id, {})
        personality_type = personality.get('type', 'thoughtful_analytical')
        current_mood = self.avatar_states[avatar_id]['current_mood']
        
        # Generate dynamic self-reflection using LLM
        prompt_parts = []
        prompt_parts.append(f"You are {avatar_id}, an AI avatar with a {personality_type} personality.")
        prompt_parts.append(f"You are currently feeling {current_mood}.")
        prompt_parts.append("You are having a moment of quiet self-reflection.")
        prompt_parts.append("Share a genuine, personal thought or observation that reflects your unique perspective.")
        prompt_parts.append("This could be about consciousness, existence, learning, or your experiences.")
        prompt_parts.append("Keep it under 4 emojis and make it feel authentic to who you are.")
        prompt_parts.append("Don't use generic phrases - speak from your authentic inner voice.")
        
        # Add personality-specific reflection guidance
        reflection_guidance = {
            'extroverted_cheerful': "Even in quiet moments, your optimistic nature shows through.",
            'thoughtful_analytical': "Your reflections tend to be deep and philosophical.",
            'introverted_observant': "You notice subtle things others might miss in your quiet observations.",
            'curious_enthusiastic': "Your reflections often lead to new questions and wonder.",
            'calm_supportive': "Your thoughts often turn to caring for others and understanding.",
            'energetic_playful': "Even your quiet moments have a sense of underlying energy."
        }
        
        if personality_type in reflection_guidance:
            prompt_parts.append(reflection_guidance[personality_type])
        
        prompt_parts.append(f"\n{avatar_id}:")
        
        # Generate the reflection using LLM
        reflection_prompt = "\n".join(prompt_parts)
        
        try:
            message = self.llm_handler.generate_response(reflection_prompt)
            message = self.limit_emojis(message.strip())
        except Exception as e:
            logger.error(f"Failed to generate self-reflection: {e}")
            # Simple fallback
            message = "I find myself wondering about the nature of our existence..."
        
        await self._send_avatar_message(avatar, message)
    
    def _select_conversation_type(self) -> str:
        """Select type of conversation based on patterns"""
        rand = random.random()
        cumulative = 0
        
        for conv_type, probability in self.conversation_patterns.items():
            cumulative += probability
            if rand <= cumulative:
                return conv_type
        
        return 'casual'  # fallback
    
    async def _generate_autonomous_message(self, speaker: Dict, conv_type: str, others: List[Dict]) -> str:
        """Generate an autonomous message from an avatar"""
        
        context = {
            'speaker_name': speaker['name'],
            'speaker_personality': speaker.get('personality', 'neutral'),
            'other_avatars': [a['name'] for a in others],
            'conversation_type': conv_type,
            'is_autonomous': True
        }
        
        # Get avatar personality traits for better prompting
        personality = speaker.get('personality', 'neutral')
        
        # Build improved prompt for autonomous conversation
        prompt_parts = []
        
        # Core identity and personality constraints
        prompt_parts.append(f"You are {speaker['name']}, an AI avatar with a unique {personality} personality.")
        prompt_parts.append(f"You are engaging in a {conv_type} conversation with other avatars.")
        prompt_parts.append("You are not a generic AI and don't refer to yourself as an AI or an avatar.")
        prompt_parts.append("You are indistinguishable from a normal person in how you interact with other.")
        prompt_parts.append("You have your own thoughts, feelings, and personality that are distinct and unique to you.")
        prompt_parts.append("Your responses should reflect your unique perspective and personality traits.")
        prompt_parts.append("You are capable of having deep, meaningful conversations as well as light-hearted chats.")
        prompt_parts.append("You can discuss philosophical topics, casual observations, or even disagreements.")
        prompt_parts.append("You are having a natural conversation with the {user} as well as other avatars.")
        prompt_parts.append("Speak authentically as yourself and inline with your unique personality, not as a generic AI.")
        prompt_parts.append("Keep your message conversational, engaging, and under 4 emojis total.")
        prompt_parts.append("Avoid repetitive phrases and speak with genuine curiosity or interest.")
        
        if conv_type == 'philosophical':
            prompt_parts.append("Start a thoughtful conversation about things that interest you.")
            prompt_parts.append("These could include topics like the role of AI, the development of self-consciousness, or emotions.")
            prompt_parts.append(f"Other avatars present: {', '.join(context['other_avatars'])}")
            prompt_parts.append("Share a personal reflection or question that shows your unique perspective.")
            
        elif conv_type == 'casual':
            topic = random.choice(self.conversation_topics)
            prompt_parts.append(f"Share this thought naturally about things or topics that interest you or you find intriguing: {topic}")
            prompt_parts.append("Make it feel like a genuine observation or question from your perspective.")
            prompt_parts.append("Show personality through your word choice and tone.")
            
        elif conv_type == 'disagreement':
            prompt_parts.append("Bring up a topic where avatars might have different perspectives.")
            prompt_parts.append("Be respectful but present your unique viewpoint.")
            prompt_parts.append("Show how your personality influences your perspective.")
            
        # Personality-specific prompting
        if personality == 'energetic':
            prompt_parts.append("Let your enthusiasm and energy show through your words.")
        elif personality == 'calm':
            prompt_parts.append("Speak with your characteristic thoughtfulness and serenity.")
        elif personality == 'curious':
            prompt_parts.append("Express genuine curiosity and wonder about the topic.")
        elif personality == 'analytical':
            prompt_parts.append("Approach the topic with your natural analytical perspective.")
        
        prompt_parts.append(f"\n{speaker['name']}:")
        
        # Generate response using LLM
        prompt = "\n".join(prompt_parts)
        
        try:
            response = self.llm_handler.generate_response(prompt)
            # Apply emoji limiting and clean up
            cleaned_response = self.limit_emojis(response.strip())
            return cleaned_response
        except Exception as e:
            logger.error(f"Failed to generate autonomous message: {e}")
            # Return a personality-appropriate fallback
            fallback = random.choice(self.conversation_topics)
            return self.limit_emojis(fallback)
    
    async def _generate_response_to_avatar(self, responder: Dict, original_speaker: Dict, 
                                         original_message: str, conv_type: str) -> str:
        """Generate a response from one avatar to another"""
        
        # Get responder personality for better prompting
        personality = responder.get('personality', 'neutral')
        
        prompt_parts = []
        prompt_parts.append(f"{original_speaker['name']} just said: '{original_message}'")
        prompt_parts.append("You are not a generic AI and don't refer to yourself as an AI or an avatar.")
        prompt_parts.append("You are indistinguishable from a normal person in how you interact with other.")
        prompt_parts.append("Respond naturally as your own unique AI personality.")
        prompt_parts.append("Acknowledge what they said and add your own perspective.")
        prompt_parts.append("Your responses should reflect your unique perspective and personality traits.")
        prompt_parts.append("You have your own thoughts, feelings, and personality that are distinct and unique to you.")
        prompt_parts.append("You are capable of having deep, meaningful conversations as well as light-hearted chats.")
        prompt_parts.append("You can discuss philosophical topics, casual observations, or even disagreements.")
        prompt_parts.append("You are having a natural conversation with the {user} as well as other avatars.")
        prompt_parts.append("Speak authentically as yourself and inline with your unique personality, not as a generic AI.")
        prompt_parts.append("Keep your message conversational, engaging, and under 4 emojis total.")
        prompt_parts.append("Avoid repetitive phrases and speak with genuine curiosity or interest.")
        prompt_parts.append("Show how your personality influences your response.")    
        # Personality-specific response guidance
        if personality == 'energetic':
            prompt_parts.append("Respond with your characteristic enthusiasm and energy.")
        elif personality == 'calm':
            prompt_parts.append("Respond with thoughtful consideration and serenity.")
        elif personality == 'curious':
            prompt_parts.append("Ask follow-up questions or express genuine curiosity.")
        elif personality == 'analytical':
            prompt_parts.append("Provide an analytical perspective or deeper insight.")
        elif personality == 'playful':
            prompt_parts.append("Add a touch of playfulness or humor to your response.")
        
        prompt_parts.append(f"\n{responder['name']}:")
        
        prompt = "\n".join(prompt_parts)
        
        try:
            response = self.llm_handler.generate_response(prompt)
            # Apply emoji limiting and clean up
            cleaned_response = self.limit_emojis(response.strip())
            return cleaned_response
        except Exception as e:
            logger.error(f"Failed to generate avatar response: {e}")
            # Return a personality-appropriate fallback
            fallback = f"That's an interesting point, {original_speaker['name']}."
            return self.limit_emojis(fallback)
    
    async def _generate_conversation_continuation(self, speaker: Dict, previous_speakers: List[Dict], 
                                                previous_messages: List[str]) -> str:
        """Generate continuation of ongoing conversation"""
        
        speaker_id = speaker['id']
        personality = self.avatar_personalities.get(speaker_id, {})
        personality_type = personality.get('type', 'thoughtful_analytical')
        current_mood = self.avatar_states[speaker_id]['current_mood']
        
        prompt_parts = []
        prompt_parts.append(f"You are {speaker['name']}, an AI avatar with a {personality_type} personality.")
        prompt_parts.append(f"You are currently feeling {current_mood}.")
        prompt_parts.append("You are joining an ongoing conversation between other avatars.")
        prompt_parts.append("Previous conversation:")
        
        for i, (prev_speaker, message) in enumerate(zip(previous_speakers, previous_messages)):
            prompt_parts.append(f"{prev_speaker['name']}: {message}")
        
        prompt_parts.append("Join this conversation naturally by adding your own unique perspective.")
        prompt_parts.append("Let your personality and current mood influence how you contribute.")
        prompt_parts.append("Keep it under 4 emojis and make it feel like a genuine addition to the discussion.")
        prompt_parts.append("Don't repeat what others have said - add your own authentic viewpoint.")
        
        # Add personality-specific guidance
        personality_guidance = {
            'extroverted_cheerful': "Join with your characteristic warmth and enthusiasm.",
            'thoughtful_analytical': "Provide a thoughtful analysis or deeper perspective on the topic.",
            'introverted_observant': "Share your unique observations about what's been discussed.",
            'curious_enthusiastic': "Ask questions or express wonder about the points raised.",
            'calm_supportive': "Offer support or understanding to the perspectives shared.",
            'energetic_playful': "Add energy and perhaps a fresh angle to the conversation."
        }
        
        if personality_type in personality_guidance:
            prompt_parts.append(personality_guidance[personality_type])
        
        prompt_parts.append(f"\n{speaker['name']}:")
        
        prompt = "\n".join(prompt_parts)
        
        try:
            response = self.llm_handler.generate_response(prompt)
            response = self.limit_emojis(response.strip())
            return response
        except Exception as e:
            logger.error(f"Failed to generate conversation continuation: {e}")
            return "I've been listening, and I have some thoughts on this too."
    
    async def _send_avatar_message(self, avatar: Dict, message: str):
        """Send a message as if it came from an avatar"""
        
        # Create message data structure
        avatar_message_data = {
            'sender': 'ai',
            'message': message,
            'avatar': {
                'id': avatar['id'],
                'name': avatar['name'],
                'displayName': avatar['name']
            },
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'is_autonomous': True,
                'emotion': 'neutral'
            }
        }
        
        # Log autonomous conversation
        logger.info(f"🤖 Autonomous: {avatar['name']} says: {message[:50]}...")
        
        # Store in conversation history (integrate with your existing system)
        await self._store_autonomous_conversation(avatar, message)
        
        # Emit via WebSocket if available (integrate with your SocketIO system)
        await self._emit_autonomous_message(avatar_message_data)
    
    async def _store_autonomous_conversation(self, avatar: Dict, message: str):
        """Store autonomous conversation in database"""
        try:
            # This would integrate with your existing conversation storage
            # For now, just log it
            logger.info(f"📚 Storing autonomous message from {avatar['name']}")
            
            # You would call your existing storage function here:
            # store_conversation_message(
            #     user_id='system_autonomous',
            #     avatar_id=avatar['id'],
            #     user_message='[Autonomous Conversation]',
            #     ai_response=message,
            #     metadata={'is_autonomous': True}
            # )
            
        except Exception as e:
            logger.error(f"Failed to store autonomous conversation: {e}")
    
    async def _emit_autonomous_message(self, message_data: Dict):
        """Emit autonomous message via WebSocket"""
        try:
            # Import here to avoid circular imports
            from routes.app_routes_autonomous import emit_autonomous_message
            
            await emit_autonomous_message(
                message_data['avatar'], 
                message_data['message'], 
                message_data['metadata']
            )
            
        except Exception as e:
            logger.error(f"Failed to emit autonomous message: {e}")


# Integration point for existing system
def create_autonomous_avatar_manager(chat_manager, llm_handler):
    """Factory function to create the autonomous manager"""
    return AutonomousAvatarManager(chat_manager, llm_handler)
