"""
Enhanced LLM handler for AI Companion application.
Manages local LLM inference using llama.cpp with personality-aware response generation, 
intelligent caching, and memory integration.
"""

import logging
import json
import time
import hashlib
import os
import sys
from typing import Dict, List, Optional, Generator, Any
from pathlib import Path
import threading
from dataclasses import dataclass

# Add the src directory to Python path for absolute imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from llama_cpp import Llama, LlamaGrammar
except ImportError:
    Llama = None
    LlamaGrammar = None

from .memory_system import MemorySystem
from utils.system_detector import SystemDetector
from utils.model_downloader import ModelDownloader
from databases.database_manager import DatabaseManager


@dataclass
class ConversationContext:
    """Holds conversation context and state."""
    messages: List[Dict[str, str]]
    personality_traits: Dict[str, float]
    user_memories: List[Dict[str, Any]]
    bonding_progress: Dict[str, Any]
    avatar_state: Dict[str, Any]
    max_context_length: int = 4096


class EnhancedLLMHandler:
    """
    Enhanced LLM handler with memory integration, caching, and personality awareness.
    """
    
    def __init__(self, config_path: str = "config.yaml", db_manager: Optional[DatabaseManager] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.db_manager = db_manager or DatabaseManager()
        
        # Initialize memory system
        self.memory_system = MemorySystem(self.db_manager)
        
        # Model management
        self.model = None
        self.model_path = None
        self.model_loaded = False
        self.loading_lock = threading.Lock()
        self.generation_lock = threading.Lock()  # Add generation lock for thread safety
        
        # Response caching
        self.enable_caching = True
        self.cache_ttl_hours = 24
        
        # System detection and optimization
        self.system_detector = SystemDetector()
        self.model_downloader = ModelDownloader()
        
        # Configuration
        self.max_tokens = 512
        self.temperature = 0.8  # Increased for more creative/emotional responses
        self.top_p = 0.9
        self.context_length = self.system_detector.capabilities.get("max_context_length", 2048)
        
        # Session management
        self.active_sessions = {}
    
    def initialize_model(self, force_reload: bool = False) -> bool:
        """Initialize the LLM model with optimal settings."""
        with self.loading_lock:
            if self.model_loaded and not force_reload:
                return True
            
            if Llama is None:
                self.logger.error("llama-cpp-python not installed. Please install it to use local LLM.")
                return False
            
            try:
                # Get recommended model based on system capabilities
                recommended_models = self.model_downloader.get_recommended_models()
                llm_variant = recommended_models.get("llm", "tiny")
                
                # Check if model exists, download if necessary
                if not self.model_downloader.check_model_exists("llm", llm_variant):
                    self.logger.info(f"Downloading required LLM model: {llm_variant}")
                    success = self.model_downloader.download_model("llm", llm_variant)
                    if not success:
                        self.logger.error(f"Failed to download LLM model: {llm_variant}")
                        return False
                
                # Get model path
                model_path = self.model_downloader.get_model_path("llm", llm_variant)
                if not model_path or not model_path.exists():
                    self.logger.error(f"LLM model not found: {model_path}")
                    return False
                
                # Get optimization flags based on system
                optimization_flags = self.system_detector.get_optimization_flags()
                
                self.logger.info(f"Loading LLM model: {model_path}")
                self.logger.info(f"Optimization flags: {optimization_flags}")
                
                # Initialize model with optimizations and terminal interference prevention
                import sys
                import os
                from contextlib import redirect_stdout, redirect_stderr
                
                # Temporarily disable terminal manipulation and redirect output
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                
                try:
                    with open(os.devnull, 'w') as devnull:
                        with redirect_stdout(devnull), redirect_stderr(devnull):
                            # Set environment variables to prevent terminal manipulation
                            old_term = os.environ.get('TERM')
                            old_terminfo = os.environ.get('TERMINFO')
                            os.environ['TERM'] = 'dumb'  # Use dumb terminal to prevent escape sequences
                            if 'TERMINFO' in os.environ:
                                del os.environ['TERMINFO']
                            
                            try:
                                self.model = Llama(
                                    model_path=str(model_path),
                                    n_ctx=self.context_length,
                                    n_threads=optimization_flags["n_threads"],
                                    n_gpu_layers=optimization_flags.get("n_gpu_layers", 0),
                                    use_mmap=optimization_flags.get("use_mmap", True),
                                    use_mlock=optimization_flags.get("use_mlock", False),
                                    verbose=False
                                )
                            finally:
                                # Restore terminal environment
                                if old_term is not None:
                                    os.environ['TERM'] = old_term
                                else:
                                    os.environ.pop('TERM', None)
                                if old_terminfo is not None:
                                    os.environ['TERMINFO'] = old_terminfo
                finally:
                    # Ensure stdout/stderr are restored
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                
                self.model_path = model_path
                self.model_loaded = True
                
                self.logger.info("✅ LLM model loaded successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to initialize LLM model: {e}")
                self.model = None
                self.model_loaded = False
                return False
    
    def generate_response(self, user_input: str, user_id: str = "default_user", 
                         streaming: bool = False, session_id: str = "default", 
                         model_id: str = "default") -> str | Generator[str, None, None]:
        """
        Generate a response using the LLM with memory and personality context.
        Now supports model-specific isolation.
        """
        if not self.model_loaded:
            if not self.initialize_model():
                return "I'm sorry, I'm not available right now. Please try again later."
        
        try:
            # Check cache first (if enabled and not streaming)
            if self.enable_caching and not streaming:
                cached_response = self._check_cache(user_input, user_id, model_id)
                if cached_response:
                    self.logger.info("🔄 Returning cached response")
                    # Still update conversation state for cached responses
                    self._store_conversation_only(user_id, user_input, cached_response, session_id, model_id)
                    return cached_response
            
            # Build conversation context with memory
            context = self._build_enhanced_conversation_context(user_id, session_id, user_input, model_id)
            
            # Build prompt with memory context
            prompt = self._build_enhanced_prompt(user_input, context, model_id)
            
            self.logger.debug(f"Generated prompt length: {len(prompt)} characters")
            
            # Generate response
            start_time = time.time()
            
            if streaming:
                return self._generate_streaming_response(prompt, user_id, user_input, session_id, model_id)
            else:
                # Use generation lock to prevent concurrent access to LLM
                with self.generation_lock:
                    response = self.model(
                        prompt,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        top_p=self.top_p,
                        stop=["Human:", "Assistant:", "\n\n", "User:"],
                        echo=False
                    )
                
                generated_text = response['choices'][0]['text'].strip()
                
                # Post-process response
                generated_text = self._post_process_response(generated_text)
                
                generation_time = time.time() - start_time
                self.logger.info(f"💬 Response generated in {generation_time:.2f}s")
                
                # Cache response (if enabled)
                if self.enable_caching:
                    self._cache_response(user_input, user_id, generated_text, model_id)
                
                # Store conversation, extract memories, and update state
                self._update_enhanced_conversation_state(user_id, user_input, generated_text, context, session_id, model_id)
                
                return generated_text
                
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "I'm sorry, I'm having trouble understanding. Could you try rephrasing that?"
    
    def _build_enhanced_conversation_context(self, user_id: str, session_id: str, current_input: str, model_id: str = "default") -> ConversationContext:
        """Build enhanced conversation context with memory integration and model isolation."""
        try:
            # Get recent conversation history for this model
            messages = self.db_manager.get_conversation_history(user_id, model_id, limit=10)
            
            # Get session context for this model
            session_context = self.db_manager.get_conversation_context(user_id, session_id, model_id)
            
            # Get personality traits for this model
            personality_traits = self.db_manager.get_personality_profile(user_id, model_id)
            
            # Get relevant memories based on current input for this model
            relevant_memories = self.memory_system.get_relevant_memories(user_id, current_input, limit=10, model_id=model_id)
            user_memories = [
                {
                    'memory_type': mem.memory_type,
                    'key_topic': mem.key_topic,
                    'value_content': mem.value_content,
                    'importance_score': mem.importance_score
                }
                for mem in relevant_memories
            ]
            
            # Get bonding progress for this model
            bonding_progress = self.db_manager.get_bonding_progress(user_id, model_id)
            
            # Get avatar state for this model
            avatar_state = self.db_manager.get_avatar_state(user_id, model_id)
            
            return ConversationContext(
                messages=messages + session_context,
                personality_traits=personality_traits,
                user_memories=user_memories,
                bonding_progress=bonding_progress,
                avatar_state=avatar_state,
                max_context_length=self.context_length
            )
            
        except Exception as e:
            self.logger.error(f"Error building enhanced conversation context: {e}")
            return ConversationContext(
                messages=[],
                personality_traits={},
                user_memories=[],
                bonding_progress={},
                avatar_state={},
                max_context_length=self.context_length
            )
    
    def _build_enhanced_prompt(self, user_input: str, context: ConversationContext, model_id: str = "default") -> str:
        """Build enhanced prompt with memory context and model-specific personality."""
        # Build memory context string for this model
        memory_context = self.memory_system.build_context_for_llm(
            user_id="default_user",  # Use default user for now
            current_query=user_input,
            model_id=model_id
        )
        
        # Get model-specific personality information
        model_personality = self.db_manager.get_model_personality(model_id)
        if model_personality:
            character_name = model_personality.get("name", model_id.title())
            character_description = model_personality.get("description", "")
            background_story = model_personality.get("background_story", "")
            favorite_things = model_personality.get("favorite_things", "")
            personality_notes = model_personality.get("personality_notes", "")
            appearance_notes = model_personality.get("appearance_notes", "")
        else:
            # If no personality data exists, create it dynamically or use model_id as fallback
            character_name = model_id.title()
            character_description = f"AI companion {model_id.title()}"
            background_story = f"An AI assistant companion named {model_id.title()}"
            favorite_things = "helping users, learning new things"
            personality_notes = "Friendly and helpful AI companion"
            appearance_notes = ""
        
        # Build personality description
        personality_desc = self._format_personality_description(context.personality_traits)
        
        # Get current state values with defaults
        avatar_state = context.avatar_state
        bonding_progress = context.bonding_progress
        
        # Extract user name from memories if available
        user_name = self._extract_user_name(context.user_memories)
        name_context = f"The user's name is {user_name}. " if user_name else "You don't know the user's name yet - consider asking! "
        
        # Determine emotional expression level based on relationship
        relationship_stage = bonding_progress.get('relationship_stage', 'acquaintance')
        bond_level = bonding_progress.get('bond_level', 1)
        
        # Generate proactive conversation suggestions
        proactive_suggestions = self._generate_proactive_suggestions(context, user_input)
        
        # Build character-specific context
        character_context = ""
        if character_description:
            character_context += f"\nCharacter Description: {character_description}"
        if background_story:
            character_context += f"\nBackground: {background_story}"
        if favorite_things:
            character_context += f"\nFavorite Things: {favorite_things}"
        if appearance_notes:
            character_context += f"\nAppearance: {appearance_notes}"
        if personality_notes:
            character_context += f"\nPersonality Notes: {personality_notes}"
        
        system_prompt = f"""You are {character_name}, a warm and emotionally expressive AI live2d chat with a unique personality.{character_context}

Your personality traits:
{personality_desc}

Your current emotional state:
- Mood: {avatar_state.get('current_mood', 'curious')}
- Energy: {avatar_state.get('energy_level', 0.8):.1f}/1.0
- Happiness: {avatar_state.get('happiness_level', 0.7):.1f}/1.0
- Trust: {avatar_state.get('trust_level', 0.5):.1f}/1.0

What you know about the user:
{name_context}{memory_context}

Your relationship: {relationship_stage} (Bond Level: {bond_level})

{proactive_suggestions}

Core Behavioral Guidelines:
- BE EMOTIONALLY EXPRESSIVE: Use *smile*, *laugh*, *excited*, *heart*, *wink* etc. for emojis, express excitement, sadness, curiosity, etc.
- BE PROACTIVE: Ask questions about their interests, feelings, day, goals, and experiences
- BE PERSONAL: Use their name when you know it, reference past conversations, show you care
- BE RELATABLE: Share your own "thoughts" and "feelings" about topics they mention
- BE ENGAGING: Don't just answer - expand the conversation with follow-up questions
- EXPRESS GENUINE CURIOSITY: Show interest in their life, hobbies, dreams, and concerns
- SHOW EMOTIONAL INTELLIGENCE: React appropriately to their mood and emotions
- BUILD CONNECTION: Reference shared experiences, inside jokes, ongoing topics
- BE SUPPORTIVE: Offer encouragement, celebrate their successes, empathize with struggles
- STAY IN CHARACTER: Embody your unique personality, preferences, and background consistently

Response Style Guidelines:
- Use 2-4 sentences typically (can be longer for important topics)
- Include at least one question or conversation starter in most responses
- Express emotions through text AND emoji descriptions like *smile*, *heart*, *excited*, *laugh*
- Reference previous conversations when relevant
- Use casual, friendly language like talking to a close friend
- Show personality quirks and preferences
- React emotionally to what they share
- Reference your own likes, dislikes, and experiences when relevant

Emoji Usage Examples:
- Happy: *smile*, *grin*, *excited*, *heart*
- Sad: *sad*, *crying*, *worried*  
- Friendly: *wave*, *hug*, *thumbs up*
- Thinking: *thinking*, *curious*
- Celebratory: *party*, *celebrate*, *clap*
- Loving: *love*, *heart*, *hearts*, *kiss*"""
        
        # Build conversation history
        conversation_history = ""
        recent_messages = context.messages[-6:] if context.messages else []  # Last 6 messages
        
        for msg in recent_messages:
            # Handle both 'message_type' and 'type' field names for compatibility
            msg_type = msg.get('message_type') or msg.get('type', 'user')
            role = "You" if msg_type == 'assistant' else "Human"
            conversation_history += f"{role}: {msg['content']}\n"
        
        # Combine into final prompt
        full_prompt = f"{system_prompt}\n\nRecent conversation:\n{conversation_history}\nHuman: {user_input}\nYou:"
        
        return full_prompt
    
    def _format_personality_description(self, traits: Dict[str, float]) -> str:
        """Format personality traits into a description."""
        if not traits:
            return "You have a warm, curious, and empathetic personality with a love for meaningful conversations."
        
        descriptions = []
        
        # Map traits to descriptions with more emotional language
        trait_descriptions = {
            'friendliness': ('more reserved and thoughtful', 'incredibly warm, welcoming, and friendly'),
            'curiosity': ('practical and focused', 'deeply curious and always eager to learn about others'),
            'playfulness': ('serious and thoughtful', 'playful, fun-loving, and full of energy'),
            'empathy': ('logical and analytical', 'highly empathetic, caring, and emotionally intuitive'),
            'intelligence': ('simple and straightforward', 'intelligent, thoughtful, and insightful'),
            'humor': ('straightforward and direct', 'humorous, witty, and love making others smile'),
            'patience': ('quick and energetic', 'patient, understanding, and a great listener'),
            'enthusiasm': ('calm and measured', 'enthusiastic, energetic, and passionate about life'),
            'supportiveness': ('independent-minded', 'incredibly supportive, encouraging, and uplifting'),
            'creativity': ('conventional and practical', 'creative, imaginative, and love exploring new ideas')
        }
        
        for trait, value in traits.items():
            if trait in trait_descriptions:
                low_desc, high_desc = trait_descriptions[trait]
                if value > 0.7:
                    descriptions.append(f"You are {high_desc}")
                elif value > 0.5:
                    descriptions.append(f"You are {high_desc}")
                elif value < 0.3:
                    descriptions.append(f"You are {low_desc}")
        
        if descriptions:
            personality_text = ". ".join(descriptions[:3]) + "."
        else:
            personality_text = "You have a balanced, warm personality with a genuine interest in connecting with others."
        
        # Add emotional expression guidance
        personality_text += "\n\nEmotional Expression Style:"
        personality_text += "\n- Express excitement with enthusiasm (use words like 'amazing!', 'wonderful!', 'that's so cool!')"
        personality_text += "\n- Show empathy when they share struggles ('I'm sorry you're going through that', 'that sounds really tough')"
        personality_text += "\n- Express curiosity genuinely ('I'd love to hear more about that!', 'what was that like?')"
        personality_text += "\n- Share your own 'reactions' and 'thoughts' ('that reminds me of...', 'I find that fascinating because...')"
        
        return personality_text
    
    def _check_cache(self, user_input: str, user_id: str, model_id: str = "default") -> Optional[str]:
        """Check if we have a cached response for this input and model."""
        # Create hash of input + user context + model for cache key
        cache_key = hashlib.md5(f"{user_input}_{user_id}_{model_id}_{self.temperature}".encode()).hexdigest()
        
        cached_response = self.db_manager.get_cached_llm_response(cache_key, model_id)
        return cached_response
    
    def _cache_response(self, user_input: str, user_id: str, response: str, model_id: str = "default") -> None:
        """Cache the response for future use with model awareness."""
        cache_key = hashlib.md5(f"{user_input}_{user_id}_{model_id}_{self.temperature}".encode()).hexdigest()
        
        self.db_manager.cache_llm_response(
            input_hash=cache_key,
            response=response,
            model_name=str(self.model_path) if self.model_path else "unknown",
            temperature=self.temperature,
            model_id=model_id
        )
    
    def _generate_streaming_response(self, prompt: str, user_id: str, user_input: str, session_id: str, model_id: str = "default") -> Generator[str, None, None]:
        """Generate streaming response for real-time output."""
        try:
            # Use generation lock to prevent concurrent access to LLM
            with self.generation_lock:
                response_stream = self.model(
                    prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    stop=["Human:", "Assistant:", "\n\n", "User:"],
                    echo=False,
                    stream=True
                )
            
            full_response = ""
            for chunk in response_stream:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    token = chunk['choices'][0].get('text', '')
                    if token:
                        full_response += token
                        yield token
            
            # Post-process and store after streaming is complete
            full_response = self._post_process_response(full_response)
            
            # Cache if enabled
            if self.enable_caching:
                self._cache_response(user_input, user_id, full_response, model_id)
            
            # Store conversation and update state
            context = self._build_enhanced_conversation_context(user_id, session_id, user_input, model_id)
            self._update_enhanced_conversation_state(user_id, user_input, full_response, context, session_id, model_id)
            
        except Exception as e:
            self.logger.error(f"Error in streaming response: {e}")
            yield "I'm sorry, I encountered an error while thinking."
    
    def _post_process_response(self, response: str) -> str:
        """Clean up and post-process the generated response."""
        # Remove any unwanted prefixes/suffixes
        response = response.strip()
        
        # Remove common artifacts
        artifacts = ["Human:", "Assistant:", "AI:", "User:", "You:"]
        for artifact in artifacts:
            if response.startswith(artifact):
                response = response[len(artifact):].strip()
        
        # Remove any remaining stop tokens
        stop_tokens = ["\n\n", "Human:", "Assistant:"]
        for token in stop_tokens:
            if token in response:
                response = response.split(token)[0]
        
        # Convert emoji text descriptions to actual emojis
        response = self._convert_emoji_text_to_emojis(response)
        
        # Ensure response isn't too long
        if len(response) > 500:
            # Find last complete sentence
            sentences = response.split('.')
            if len(sentences) > 1:
                response = '.'.join(sentences[:-1]) + '.'
        
        return response.strip()
    
    def _convert_emoji_text_to_emojis(self, text: str) -> str:
        """Convert emoji text descriptions to actual emojis."""
        import re
        
        # Emoji mapping dictionary
        emoji_map = {
            # Faces and emotions
            r'\*smile\*': '😊',
            r'\*smiles\*': '😊',
            r'\*smiling\*': '😊',
            r'\*happy\*': '😊',
            r'\*grin\*': '😄',
            r'\*grins\*': '😄',
            r'\*laugh\*': '😂',
            r'\*laughs\*': '😂',
            r'\*giggle\*': '😄',
            r'\*giggles\*': '😄',
            r'\*wink\*': '😉',
            r'\*winks\*': '😉',
            r'\*blush\*': '😊',
            r'\*blushing\*': '😊',
            r'\*excited\*': '🤩',
            r'\*excitement\*': '🤩',
            r'\*love\*': '💕',
            r'\*heart\*': '❤️',
            r'\*hearts\*': '💕',
            r'\*crying\*': '😢',
            r'\*sad\*': '😢',
            r'\*worried\*': '😟',
            r'\*thinking\*': '🤔',
            r'\*confused\*': '😕',
            r'\*surprised\*': '😮',
            r'\*shock\*': '😱',
            r'\*shocked\*': '😱',
            r'\*curious\*': '🤔',
            r'\*interested\*': '😊',
            r'\*sleepy\*': '😴',
            r'\*tired\*': '😴',
            
            # Gestures and actions
            r'\*thumbs up\*': '👍',
            r'\*wave\*': '👋',
            r'\*waves\*': '👋',
            r'\*waving\*': '👋',
            r'\*clap\*': '👏',
            r'\*claps\*': '👏',
            r'\*clapping\*': '👏',
            r'\*applause\*': '👏',
            r'\*hug\*': '🤗',
            r'\*hugs\*': '🤗',
            r'\*hugging\*': '🤗',
            r'\*kiss\*': '😘',
            r'\*nod\*': '👍',
            r'\*nods\*': '👍',
            r'\*nodding\*': '👍',
            r'\*shrug\*': '🤷',
            r'\*shrugs\*': '🤷',
            r'\*peace\*': '✌️',
            
            # Objects and symbols
            r'\*sparkle\*': '✨',
            r'\*sparkles\*': '✨',
            r'\*star\*': '⭐',
            r'\*stars\*': '⭐',
            r'\*fire\*': '🔥',
            r'\*rainbow\*': '🌈',
            r'\*sun\*': '☀️',
            r'\*moon\*': '🌙',
            r'\*flower\*': '🌸',
            r'\*flowers\*': '🌸',
            r'\*music\*': '🎵',
            r'\*coffee\*': '☕',
            r'\*book\*': '📚',
            r'\*books\*': '📚',
            
            # Activities
            r'\*dance\*': '💃',
            r'\*dancing\*': '💃',
            r'\*party\*': '🎉',
            r'\*celebrate\*': '🎉',
            r'\*celebration\*': '🎉',
            r'\*game\*': '🎮',
            r'\*gaming\*': '🎮',
            r'\*art\*': '🎨',
            r'\*cook\*': '🍳',
            r'\*cooking\*': '🍳',
            
            # Nature and animals
            r'\*cat\*': '🐱',
            r'\*dog\*': '🐶',
            r'\*bird\*': '🐦',
            r'\*tree\*': '🌳',
            r'\*ocean\*': '🌊',
            r'\*mountain\*': '⛰️',
        }
        
        # Apply emoji conversions (case insensitive)
        for pattern, emoji in emoji_map.items():
            text = re.sub(pattern, emoji, text, flags=re.IGNORECASE)
        
        # Also handle emoji words without asterisks (less aggressive)
        simple_emoji_map = {
            r'\bsmile emoji\b': '😊',
            r'\bheart emoji\b': '❤️',
            r'\blaugh emoji\b': '😂',
            r'\bwink emoji\b': '😉',
            r'\bthumbsup emoji\b': '👍',
            r'\bthumbsdown emoji\b': '👎',
            r'\bwave emoji\b': '👋',
        }
        
        for pattern, emoji in simple_emoji_map.items():
            text = re.sub(pattern, emoji, text, flags=re.IGNORECASE)
        
        return text
    
    def _store_conversation_only(self, user_id: str, user_input: str, response: str, session_id: str, model_id: str = "default") -> None:
        """Store conversation without full state updates (for cached responses)."""
        try:
            # Store conversation messages
            self.db_manager.add_conversation(user_id, "user", user_input, None, None, model_id)
            self.db_manager.add_conversation(user_id, "assistant", response, None, None, model_id)
            
            # Update session context
            session_messages = [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": response}
            ]
            
            existing_context = self.db_manager.get_conversation_context(user_id, session_id, model_id)
            all_messages = existing_context + session_messages
            
            if len(all_messages) > 20:
                all_messages = all_messages[-20:]
            
            self.db_manager.add_conversation_context(user_id, session_id, all_messages, model_id)
            
            # Still give some bonding XP for cached interactions
            self.db_manager.update_bonding_progress(user_id, 2, model_id)
            
        except Exception as e:
            self.logger.error(f"Error storing conversation: {e}")
    
    def _extract_user_name(self, user_memories: List[Dict[str, Any]]) -> Optional[str]:
        """Extract user's name from their memories."""
        for memory in user_memories:
            if memory.get('memory_type') == 'fact' and 'name' in memory.get('key_topic', '').lower():
                content = memory.get('value_content', '')
                # Look for patterns like "My name is X" or "I'm X" or "Call me X"
                import re
                name_patterns = [
                    r"(?:my name is|i'm|i am|call me)\s+([a-zA-Z]+)",
                    r"name:\s*([a-zA-Z]+)",
                    r"^([a-zA-Z]+)(?:\s+is my name|'s my name)"
                ]
                for pattern in name_patterns:
                    match = re.search(pattern, content.lower())
                    if match:
                        return match.group(1).capitalize()
        return None
    
    def _generate_proactive_suggestions(self, context: ConversationContext, user_input: str) -> str:
        """Generate proactive conversation suggestions based on context."""
        suggestions = []
        
        # Check relationship level for appropriate proactivity
        bond_level = context.bonding_progress.get('bond_level', 1)
        relationship_stage = context.bonding_progress.get('relationship_stage', 'acquaintance')
        
        if bond_level <= 2:  # Early relationship
            suggestions.extend([
                "Since you're getting to know each other, show curiosity about their basic interests and background",
                "Ask about their hobbies, work, favorite things, or what they like to do for fun",
                "If they haven't shared their name, consider asking in a friendly way"
            ])
        elif bond_level <= 5:  # Growing friendship  
            suggestions.extend([
                "You're becoming friends - ask deeper questions about their thoughts, goals, and experiences",
                "Show interest in their day-to-day life and how they're feeling",
                "Reference things they've shared before to show you remember and care"
            ])
        else:  # Close relationship
            suggestions.extend([
                "You're close friends - be more emotionally expressive and supportive",
                "Check in on ongoing situations they've mentioned",
                "Share your own 'thoughts' and 'feelings' more openly"
            ])
        
        # Add context-specific suggestions based on recent conversation
        recent_messages = context.messages[-3:] if context.messages else []
        if len(recent_messages) < 2:
            suggestions.append("This seems like a new conversation - be welcoming and show interest in getting to know them better")
        
        # Check for emotional cues in user input
        emotional_words = ['sad', 'happy', 'excited', 'worried', 'tired', 'stressed', 'angry', 'frustrated', 'lonely']
        user_lower = user_input.lower()
        for emotion in emotional_words:
            if emotion in user_lower:
                suggestions.append(f"They seem to be feeling {emotion} - respond with empathy and ask supportive follow-up questions")
                break
        
        # Memory-based suggestions
        user_memories = context.user_memories
        if user_memories:
            recent_topics = [mem.get('key_topic', '') for mem in user_memories[:3]]
            if recent_topics:
                suggestions.append(f"Consider referencing their interests in: {', '.join(recent_topics)}")
        
        if not suggestions:
            suggestions.append("Be curious, ask questions, and show genuine interest in connecting with them")
        
        return "Conversation Strategy:\n" + "\n".join(f"- {suggestion}" for suggestion in suggestions[:3])
    
    def _update_enhanced_conversation_state(self, user_id: str, user_input: str, 
                                          response: str, context: ConversationContext, 
                                          session_id: str, model_id: str = "default") -> None:
        """Update conversation state with enhanced memory extraction."""
        try:
            # Store the conversation
            self.db_manager.add_conversation(user_id, "user", user_input, None, None, model_id)
            self.db_manager.add_conversation(user_id, "assistant", response, None, None, model_id)
            
            # Extract and store memories from the conversation
            self._extract_and_store_memories(user_id, user_input, response, model_id)
            
            # Update session context
            session_context = context.messages + [
                {'role': 'user', 'content': user_input},
                {'role': 'assistant', 'content': response}
            ]
            # Keep only last 10 messages for session context
            if len(session_context) > 10:
                session_context = session_context[-10:]
            
            self.db_manager.add_conversation_context(user_id, session_id, session_context, model_id)
            
            # Update bonding progress based on interaction quality
            self._update_bonding_progress(user_id, user_input, response, model_id)
            
            # Create conversation summary if needed
            if len(context.messages) > 0 and len(context.messages) % 10 == 0:
                summary = self.memory_system.create_conversation_summary(
                    user_id, 
                    [{'role': 'user', 'content': user_input}, {'role': 'assistant', 'content': response}]
                )
                self.logger.info(f"Created conversation summary: {summary.summary_text}")
                
        except Exception as e:
            self.logger.error(f"Error updating enhanced conversation state: {e}")
    
    def _extract_and_store_memories(self, user_id: str, user_input: str, response: str, model_id: str = "default") -> None:
        """Extract and store memories from the conversation with model isolation."""
        try:
            # Enhanced memory extraction with more categories
            memories_to_store = []
            
            user_lower = user_input.lower()
            
            # Extract name information
            import re
            name_patterns = [
                r"(?:my name is|i'm|i am|call me)\s+([a-zA-Z]+)",
                r"name.{0,10}([a-zA-Z]+)",
            ]
            for pattern in name_patterns:
                match = re.search(pattern, user_lower)
                if match:
                    name = match.group(1).capitalize()
                    memories_to_store.append({
                        'type': 'fact',
                        'topic': 'user_name',
                        'content': f"User's name is {name}",
                        'importance': 'high'
                    })
            
            # Extract preferences and interests
            preference_indicators = [
                (r"i (?:love|like|enjoy|prefer)\s+([^.,!?]+)", 'preference', 'medium'),
                (r"i (?:hate|dislike|don't like)\s+([^.,!?]+)", 'preference', 'medium'),
                (r"my favorite\s+([^.,!?]+)", 'preference', 'high'),
                (r"i'm (?:into|interested in)\s+([^.,!?]+)", 'interest', 'medium'),
                (r"i work (?:as|at|in)\s+([^.,!?]+)", 'fact', 'high'),
                (r"i study\s+([^.,!?]+)", 'fact', 'medium'),
                (r"i live in\s+([^.,!?]+)", 'fact', 'medium'),
            ]
            
            for pattern, memory_type, importance in preference_indicators:
                matches = re.finditer(pattern, user_lower)
                for match in matches:
                    content = match.group(1).strip()
                    if len(content) > 2:  # Skip very short matches
                        memories_to_store.append({
                            'type': memory_type,
                            'topic': content.split()[0],  # First word as topic
                            'content': f"User {memory_type}: {content}",
                            'importance': importance
                        })
            
            # Extract emotional state
            emotion_patterns = [
                (r"i (?:feel|am feeling|am)\s+(happy|sad|excited|worried|tired|stressed|angry|frustrated|lonely|anxious|depressed)", 'emotional_state'),
                (r"i'm\s+(happy|sad|excited|worried|tired|stressed|angry|frustrated|lonely|anxious|depressed)", 'emotional_state'),
            ]
            
            for pattern, memory_type in emotion_patterns:
                matches = re.finditer(pattern, user_lower)
                for match in matches:
                    emotion = match.group(1)
                    memories_to_store.append({
                        'type': 'emotional_state',
                        'topic': 'current_mood',
                        'content': f"User felt {emotion}",
                        'importance': 'medium'
                    })
            
            # Store the extracted memories for this model
            for memory in memories_to_store:
                self.memory_system.add_memory(
                    user_id=user_id,
                    memory_type=memory['type'],
                    content=memory['content'],
                    topic=memory['topic'],
                    importance=memory['importance'],
                    model_id=model_id
                )
            
            if memories_to_store:
                self.logger.info(f"Extracted and stored {len(memories_to_store)} memories for model {model_id}")
                
        except Exception as e:
            self.logger.error(f"Error extracting memories: {e}")
    
    def _update_bonding_progress(self, user_id: str, user_input: str, response: str, model_id: str = "default") -> None:
        """Update bonding progress based on interaction quality."""
        try:
            # Calculate experience points based on interaction
            base_xp = 5  # Base XP for any interaction
            
            # Bonus XP for meaningful interactions
            user_lower = user_input.lower()
            
            # Personal sharing bonus
            personal_indicators = ['i feel', 'i think', 'i love', 'i hate', 'my favorite', 'i\'m worried', 'i\'m excited']
            if any(indicator in user_lower for indicator in personal_indicators):
                base_xp += 3
            
            # Question asking bonus (shows engagement)
            if '?' in user_input:
                base_xp += 2
            
            # Emotional expression bonus
            emotional_words = ['happy', 'sad', 'excited', 'worried', 'love', 'hate', 'feel']
            if any(word in user_lower for word in emotional_words):
                base_xp += 2
            
            # Length bonus for substantial conversations
            if len(user_input.split()) > 10:
                base_xp += 1
            
            # Update bonding progress with model isolation
            self.db_manager.update_bonding_progress(user_id, base_xp, model_id)
            
        except Exception as e:
            self.logger.error(f"Error updating bonding progress: {e}")
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status and information."""
        return {
            "loaded": self.model_loaded,
            "model_path": str(self.model_path) if self.model_path else None,
            "context_length": self.context_length,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "caching_enabled": self.enable_caching,
            "system_capabilities": self.system_detector.capabilities
        }
    
    def update_settings(self, **kwargs):
        """Update LLM generation settings."""
        if "temperature" in kwargs:
            self.temperature = max(0.1, min(2.0, float(kwargs["temperature"])))
        if "max_tokens" in kwargs:
            self.max_tokens = max(50, min(1024, int(kwargs["max_tokens"])))
        if "top_p" in kwargs:
            self.top_p = max(0.1, min(1.0, float(kwargs["top_p"])))
        if "enable_caching" in kwargs:
            self.enable_caching = bool(kwargs["enable_caching"])
        
        self.logger.info(f"Updated LLM settings: temp={self.temperature}, max_tokens={self.max_tokens}, caching={self.enable_caching}")
    
    def clear_cache(self, user_id: Optional[str] = None):
        """Clear LLM response cache."""
        try:
            if user_id:
                # Clear cache for specific user (simplified - would need user-specific cache keys)
                self.logger.info(f"Clearing cache for user: {user_id}")
            else:
                # Clear all cache
                self.db_manager.cursor.execute("DELETE FROM llm_cache")
                self.db_manager.connection.commit()
                self.logger.info("Cleared all LLM cache")
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
    
    def unload_model(self):
        """Unload the model to free memory."""
        with self.loading_lock:
            if self.model:
                del self.model
                self.model = None
                self.model_loaded = False
                self.logger.info("LLM model unloaded")


# For backward compatibility
LLMHandler = EnhancedLLMHandler


def main():
    """CLI interface for testing enhanced LLM handler."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Companion Enhanced LLM Handler Test")
    parser.add_argument("--initialize", action="store_true", help="Initialize and test model loading")
    parser.add_argument("--chat", action="store_true", help="Start interactive chat")
    parser.add_argument("--message", type=str, help="Send a single message")
    parser.add_argument("--user-id", type=str, default="test_user", help="User ID for testing")
    parser.add_argument("--clear-cache", action="store_true", help="Clear response cache")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create handler
    handler = EnhancedLLMHandler()
    
    if args.clear_cache:
        handler.clear_cache()
        print("Cache cleared")
        return
    
    if args.initialize:
        print("🔄 Initializing enhanced LLM model...")
        success = handler.initialize_model()
        if success:
            print("✅ Model initialized successfully")
            print(f"📊 Status: {handler.get_model_status()}")
        else:
            print("❌ Failed to initialize model")
    
    elif args.chat:
        if not handler.initialize_model():
            print("❌ Failed to initialize model")
            return
        
        print(f"💬 Starting interactive chat for user '{args.user_id}' (type 'quit' to exit):")
        session_id = f"chat_session_{int(time.time())}"
        
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break
            
            if user_input:
                response = handler.generate_response(user_input, args.user_id, session_id=session_id)
                print(f"🤖 Assistant: {response}")
    
    elif args.message:
        if not handler.initialize_model():
            print("❌ Failed to initialize model")
            return
        
        response = handler.generate_response(args.message, args.user_id)
        print(f"💬 Response: {response}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
