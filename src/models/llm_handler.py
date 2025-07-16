"""
LLM handler for AI Companion application.
Manages local LLM inference using llama.cpp with personality-aware response generation and intelligent caching.
"""

import logging
import json
import time
import hashlib
from typing import Dict, List, Optional, Generator, Any
from pathlib import Path
import threading
from dataclasses import dataclass

try:
    from llama_cpp import Llama, LlamaGrammar
except ImportError:
    Llama = None
    LlamaGrammar = None

from .memory_system import MemorySystem
from ..utils.system_detector import SystemDetector
from ..utils.model_downloader import ModelDownloader
from ..database.db_manager import DBManager


@dataclass
class ConversationContext:
    """Holds conversation context and state."""
    messages: List[Dict[str, str]]
    personality_traits: Dict[str, float]
    user_memories: List[Dict[str, Any]]
    bonding_progress: Dict[str, Any]
    avatar_state: Dict[str, Any]
    max_context_length: int = 4096


class LLMHandler:
    """
    Handles local LLM inference with personality-aware response generation.
    """
    
    def __init__(self, config_path: str = "config.yaml", db_manager: Optional[DBManager] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.db_manager = db_manager or DBManager()
        
        # Initialize memory system
        self.memory_system = MemorySystem(self.db_manager)
        
        # Model management
        self.model = None
        self.model_path = None
        self.model_loaded = False
        self.loading_lock = threading.Lock()
        
        # Response caching
        self.enable_caching = True
        self.cache_ttl_hours = 24
        self.loading_lock = threading.Lock()
        
        # System detection and optimization
        self.system_detector = SystemDetector()
        self.model_downloader = ModelDownloader()
        
        # Configuration
        self.max_tokens = 512
        self.temperature = 0.7
        self.top_p = 0.9
        self.context_length = self.system_detector.capabilities.get("max_context_length", 2048)
        
        # Personality system prompt template
        self.system_prompt_template = """You are an AI companion with a unique personality. Your traits are:
{personality_description}

Your current emotional state:
- Mood: {current_mood}
- Energy: {energy_level:.1f}/1.0
- Happiness: {happiness_level:.1f}/1.0
- Trust: {trust_level:.1f}/1.0

What you know about the user:
{user_memories}

Your relationship: {relationship_stage} (Bond Level: {bond_level})

Guidelines:
- Be conversational and natural
- Show your personality through your responses
- Remember and reference previous conversations
- Express emotions appropriately
- Build deeper connection over time
- Keep responses concise but meaningful
"""
    
    def initialize_model(self, force_reload: bool = False) -> bool:
        """Initialize the LLM model with optimal settings."""
        with self.loading_lock:
            if self.model_loaded and not force_reload:
                return True
            
            if Llama is None:
                self.logger.error("llama-cpp-python not installed. Please install it to use local LLM.")
                return False
            
            try:
                # Get recommended model
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
                
                # Get optimization flags
                optimization_flags = self.system_detector.get_optimization_flags()
                
                self.logger.info(f"Loading LLM model: {model_path}")
                
                # Initialize model with optimizations
                self.model = Llama(
                    model_path=str(model_path),
                    n_ctx=self.context_length,
                    n_threads=optimization_flags["n_threads"],
                    n_gpu_layers=optimization_flags["n_gpu_layers"],
                    use_mmap=optimization_flags["use_mmap"],
                    use_mlock=optimization_flags["use_mlock"],
                    verbose=False
                )
                
                self.model_path = model_path
                self.model_loaded = True
                
                self.logger.info("LLM model loaded successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to initialize LLM model: {e}")
                self.model = None
                self.model_loaded = False
                return False
    
    def _build_conversation_context(self, user_id: str) -> ConversationContext:
        """Build conversation context with personality and memories."""
        try:
            # Get recent conversation history
            messages = self.db_manager.get_conversation_history(user_id, limit=10)
            
            # Get personality traits
            personality_traits = self.db_manager.get_personality_profile(user_id)
            
            # Get important memories
            user_memories = self.db_manager.get_important_memories(user_id, limit=5)
            
            # Get bonding progress
            bonding_progress = self.db_manager.get_bonding_progress(user_id)
            
            # Get avatar state
            avatar_state = self.db_manager.get_avatar_state(user_id)
            
            return ConversationContext(
                messages=messages,
                personality_traits=personality_traits,
                user_memories=user_memories,
                bonding_progress=bonding_progress,
                avatar_state=avatar_state,
                max_context_length=self.context_length
            )
            
        except Exception as e:
            self.logger.error(f"Error building conversation context: {e}")
            # Return minimal context
            return ConversationContext(
                messages=[],
                personality_traits={},
                user_memories=[],
                bonding_progress={},
                avatar_state={},
                max_context_length=self.context_length
            )
    
    def _format_personality_description(self, traits: Dict[str, float]) -> str:
        """Format personality traits into a description."""
        if not traits:
            return "You have a balanced, friendly personality."
        
        descriptions = []
        
        # Map traits to descriptions
        trait_descriptions = {
            'friendliness': ('reserved', 'warm and friendly'),
            'curiosity': ('practical', 'very curious and inquisitive'),
            'playfulness': ('serious', 'playful and fun-loving'),
            'empathy': ('logical', 'highly empathetic and caring'),
            'intelligence': ('simple', 'intelligent and thoughtful'),
            'humor': ('straightforward', 'humorous and witty'),
            'patience': ('quick', 'patient and understanding'),
            'enthusiasm': ('calm', 'enthusiastic and energetic'),
            'supportiveness': ('independent', 'supportive and encouraging'),
            'creativity': ('conventional', 'creative and imaginative')
        }
        
        for trait, value in traits.items():
            if trait in trait_descriptions:
                low_desc, high_desc = trait_descriptions[trait]
                if value > 0.7:
                    descriptions.append(f"very {high_desc}")
                elif value > 0.5:
                    descriptions.append(f"{high_desc}")
                elif value < 0.3:
                    descriptions.append(f"{low_desc}")
        
        if descriptions:
            return f"You are {', '.join(descriptions[:3])}."
        else:
            return "You have a balanced personality."
    
    def _format_user_memories(self, memories: List[Dict[str, Any]]) -> str:
        """Format user memories for context."""
        if not memories:
            return "You're just getting to know this user."
        
        memory_text = []
        for memory in memories[:5]:  # Limit to most important
            memory_type = memory.get('memory_type', 'fact')
            key_topic = memory.get('key_topic', '')
            value_content = memory.get('value_content', '')
            
            if memory_type == 'preference':
                memory_text.append(f"They like {key_topic}: {value_content}")
            elif memory_type == 'interest':
                memory_text.append(f"They're interested in {key_topic}")
            elif memory_type == 'fact':
                memory_text.append(f"About them: {value_content}")
            else:
                memory_text.append(f"{key_topic}: {value_content}")
        
        return "\n".join(memory_text)
    
    def _build_system_prompt(self, context: ConversationContext) -> str:
        """Build the system prompt with personality and context."""
        personality_desc = self._format_personality_description(context.personality_traits)
        user_memories_text = self._format_user_memories(context.user_memories)
        
        # Get current state values with defaults
        avatar_state = context.avatar_state
        bonding_progress = context.bonding_progress
        
        return self.system_prompt_template.format(
            personality_description=personality_desc,
            current_mood=avatar_state.get('current_mood', 'neutral'),
            energy_level=avatar_state.get('energy_level', 0.8),
            happiness_level=avatar_state.get('happiness_level', 0.7),
            trust_level=avatar_state.get('trust_level', 0.3),
            user_memories=user_memories_text,
            relationship_stage=bonding_progress.get('relationship_stage', 'stranger'),
            bond_level=bonding_progress.get('bond_level', 1)
        )
    
    def _build_prompt(self, user_input: str, context: ConversationContext) -> str:
        """Build the complete prompt for the LLM."""
        # System prompt
        system_prompt = self._build_system_prompt(context)
        
        # Conversation history
        conversation_text = []
        for msg in context.messages[-5:]:  # Last 5 messages for context
            role = "Human" if msg['message_type'] == 'user' else "Assistant"
            conversation_text.append(f"{role}: {msg['content']}")
        
        # Current user input
        conversation_text.append(f"Human: {user_input}")
        conversation_text.append("Assistant:")
        
        # Combine everything
        full_prompt = f"{system_prompt}\n\nConversation:\n" + "\n".join(conversation_text)
        
        return full_prompt
    
    def generate_response(self, user_input: str, user_id: str = "default_user", 
                         streaming: bool = False) -> str:
        """Generate a response to user input with personality awareness."""
        if not self.model_loaded:
            if not self.initialize_model():
                return "I'm sorry, I'm having trouble thinking right now. Please try again later."
        
        try:
            # Build conversation context
            context = self._build_conversation_context(user_id)
            
            # Build prompt
            prompt = self._build_prompt(user_input, context)
            
            self.logger.debug(f"Generated prompt length: {len(prompt)} characters")
            
            # Generate response
            start_time = time.time()
            
            if streaming:
                return self._generate_streaming_response(prompt, user_id, user_input)
            else:
                response = self.model(
                    prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    stop=["Human:", "Assistant:", "\n\n"],
                    echo=False
                )
                
                generated_text = response['choices'][0]['text'].strip()
                
                # Post-process response
                generated_text = self._post_process_response(generated_text)
                
                generation_time = time.time() - start_time
                self.logger.info(f"Response generated in {generation_time:.2f}s")
                
                # Store conversation and update personality
                self._update_conversation_state(user_id, user_input, generated_text, context)
                
                return generated_text
                
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "I'm sorry, I'm having trouble understanding. Could you try rephrasing that?"
    
    def _generate_streaming_response(self, prompt: str, user_id: str, user_input: str) -> Generator[str, None, None]:
        """Generate streaming response for real-time output."""
        try:
            response_stream = self.model(
                prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                stop=["Human:", "Assistant:", "\n\n"],
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
            context = self._build_conversation_context(user_id)
            self._update_conversation_state(user_id, user_input, full_response, context)
            
        except Exception as e:
            self.logger.error(f"Error in streaming response: {e}")
            yield "I'm sorry, I encountered an error while thinking."
    
    def _post_process_response(self, response: str) -> str:
        """Clean up and post-process the generated response."""
        # Remove any unwanted prefixes/suffixes
        response = response.strip()
        
        # Remove common artifacts
        artifacts = ["Human:", "Assistant:", "AI:", "User:"]
        for artifact in artifacts:
            if response.startswith(artifact):
                response = response[len(artifact):].strip()
        
        # Ensure response isn't too long
        if len(response) > 500:
            # Find last complete sentence
            sentences = response.split('.')
            if len(sentences) > 1:
                response = '.'.join(sentences[:-1]) + '.'
        
        return response
    
    def _update_conversation_state(self, user_id: str, user_input: str, 
                                 response: str, context: ConversationContext):
        """Update conversation history and personality state."""
        try:
            # Store conversation messages
            self.db_manager.add_conversation(user_id, "user", user_input, None, None)
            self.db_manager.add_conversation(user_id, "assistant", response, None, None)
            
            # Update bonding progress (small XP gain for each interaction)
            self.db_manager.update_bonding_progress(user_id, experience_points=5)
            
            # Analyze user input for memories and personality updates
            self._analyze_and_store_insights(user_id, user_input, response)
            
            # Update avatar emotional state based on conversation
            self._update_avatar_emotional_state(user_id, user_input, response)
            
        except Exception as e:
            self.logger.error(f"Error updating conversation state: {e}")
    
    def _analyze_and_store_insights(self, user_id: str, user_input: str, response: str):
        """Analyze conversation for insights and memories to store."""
        # Simple keyword-based analysis for now
        # This could be enhanced with more sophisticated NLP
        
        # Look for preferences
        preference_keywords = {
            'like': 'preference',
            'love': 'preference', 
            'enjoy': 'preference',
            'favorite': 'preference',
            'prefer': 'preference'
        }
        
        # Look for interests
        interest_keywords = {
            'interested in': 'interest',
            'hobby': 'interest',
            'passion': 'interest'
        }
        
        # Look for personal facts
        fact_keywords = {
            'my name is': 'fact',
            'i am': 'fact',
            'i work': 'fact',
            'i live': 'fact'
        }
        
        user_lower = user_input.lower()
        
        # Check for preferences
        for keyword, memory_type in preference_keywords.items():
            if keyword in user_lower:
                # Extract context around the keyword
                start_idx = user_lower.find(keyword)
                context = user_input[max(0, start_idx-20):start_idx+50]
                
                self.db_manager.add_memory(
                    user_id=user_id,
                    memory_type=memory_type,
                    key_topic=keyword,
                    value_content=context.strip(),
                    importance_score=0.6
                )
                break
        
        # Similar analysis for interests and facts...
        # This is a simplified implementation
    
    def _update_avatar_emotional_state(self, user_id: str, user_input: str, response: str):
        """Update avatar emotional state based on conversation tone."""
        # Simple sentiment analysis - could be enhanced
        user_lower = user_input.lower()
        
        # Positive indicators
        positive_words = ['happy', 'great', 'awesome', 'love', 'amazing', 'wonderful']
        negative_words = ['sad', 'angry', 'upset', 'terrible', 'hate', 'awful']
        
        positive_count = sum(1 for word in positive_words if word in user_lower)
        negative_count = sum(1 for word in negative_words if word in user_lower)
        
        # Get current state
        current_state = self.db_manager.get_avatar_state(user_id)
        
        # Adjust emotional levels slightly
        updates = {}
        
        if positive_count > negative_count:
            # User seems positive, increase happiness and energy
            updates['happiness_level'] = min(1.0, current_state.get('happiness_level', 0.7) + 0.05)
            updates['energy_level'] = min(1.0, current_state.get('energy_level', 0.8) + 0.03)
            updates['current_mood'] = 'happy'
        elif negative_count > positive_count:
            # User seems negative, show empathy by adjusting mood
            updates['happiness_level'] = max(0.0, current_state.get('happiness_level', 0.7) - 0.03)
            updates['current_mood'] = 'concerned'
        
        # Trust builds slowly over interactions
        updates['trust_level'] = min(1.0, current_state.get('trust_level', 0.3) + 0.01)
        
        if updates:
            self.db_manager.update_avatar_state(user_id, **updates)
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status and information."""
        return {
            "loaded": self.model_loaded,
            "model_path": str(self.model_path) if self.model_path else None,
            "context_length": self.context_length,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
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
        
        self.logger.info(f"Updated LLM settings: temp={self.temperature}, max_tokens={self.max_tokens}")
    
    def unload_model(self):
        """Unload the model to free memory."""
        with self.loading_lock:
            if self.model:
                del self.model
                self.model = None
                self.model_loaded = False
                self.logger.info("LLM model unloaded")


def main():
    """CLI interface for testing LLM handler."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Companion LLM Handler Test")
    parser.add_argument("--initialize", action="store_true", help="Initialize and test model loading")
    parser.add_argument("--chat", action="store_true", help="Start interactive chat")
    parser.add_argument("--message", type=str, help="Send a single message")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create handler
    handler = LLMHandler()
    
    if args.initialize:
        print("Initializing LLM model...")
        success = handler.initialize_model()
        if success:
            print("✓ Model initialized successfully")
            print(f"Status: {handler.get_model_status()}")
        else:
            print("✗ Failed to initialize model")
    
    elif args.chat:
        if not handler.initialize_model():
            print("Failed to initialize model")
            return
        
        print("Starting interactive chat (type 'quit' to exit):")
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break
            
            if user_input:
                response = handler.generate_response(user_input)
                print(f"Assistant: {response}")
    
    elif args.message:
        if not handler.initialize_model():
            print("Failed to initialize model")
            return
        
        response = handler.generate_response(args.message)
        print(f"Response: {response}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
