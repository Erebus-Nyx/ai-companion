"""
Enhanced Memory System for AI Companion
Provides intelligent memory storage, retrieval, and context management
Now includes RAG (Retrieval-Augmented Generation) capabilities for semantic search
"""

import json
import hashlib
import logging
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import re

# Add the src directory to Python path for absolute imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from databases.database_manager import DatabaseManager as DBManager

# Import RAG system if available
try:
    from models.rag_system import RAGEnhancedMemorySystem
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    RAGEnhancedMemorySystem = None


@dataclass
class MemoryItem:
    """Represents a single memory item with metadata"""
    id: Optional[int]
    memory_type: str
    key_topic: str
    value_content: str
    importance_score: float
    created_at: datetime
    last_accessed: datetime
    access_count: int


@dataclass
class ConversationSummary:
    """Represents a conversation summary"""
    date_range: str
    summary_text: str
    key_topics: List[str]
    emotional_tone: str


class MemorySystem:
    """
    Advanced memory system for the AI live2d chat
    Handles memory storage, retrieval, clustering, and context generation
    Now includes optional RAG capabilities for enhanced semantic search
    """
    
    def __init__(self, db_manager: DBManager, config: Optional[Dict[str, Any]] = None):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize RAG system if enabled and available
        self.rag_system = None
        if RAG_AVAILABLE and self.config.get('rag', {}).get('enabled', False):
            try:
                # Pass the full config to RAG system instead of modifying it
                self.rag_system = RAGEnhancedMemorySystem(self.config)
                self.logger.info("RAG system enabled and initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize RAG system: {e}")
                self.rag_system = None
        else:
            self.logger.info("RAG system disabled or not available")
        
        # Memory importance thresholds
        self.importance_thresholds = {
            'critical': 0.9,    # Life-changing events, deep personal info
            'high': 0.7,        # Important preferences, significant events
            'medium': 0.5,      # Regular conversations, minor preferences
            'low': 0.3,         # Small talk, trivial information
            'minimal': 0.1      # Background context
        }
        
        # Context window settings
        self.max_context_memories = 15
        self.max_context_length = 2000
        
    def add_memory(self, user_id: str, memory_type: str, content: str, 
                   topic: Optional[str] = None, importance: str = "medium", 
                   model_id: str = "default") -> int:
        """
        Add a new memory with automatic importance scoring and topic extraction
        Now supports model isolation.
        """
        # Extract topic if not provided
        if not topic:
            topic = self._extract_topic(content)
        
        # Calculate importance score
        importance_score = self.importance_thresholds.get(importance, 0.5)
        
        # Adjust importance based on content analysis
        importance_score = self._analyze_importance(content, importance_score)
        
        # Store memory with model isolation
        with self.db_manager.get_conversations_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (user_id, model_id, memory_type, key_topic, value_content, importance_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, model_id, memory_type, topic, content, importance_score))
            conn.commit()
            memory_id = cursor.lastrowid
        
        self.logger.info(f"Added memory for model {model_id}: {topic} (importance: {importance_score:.2f})")
        return memory_id
    
    def get_relevant_memories(self, user_id: str, query: str, limit: int = 10, 
                            model_id: str = "default") -> List[MemoryItem]:
        """
        Retrieve memories relevant to a query using keyword matching and importance
        Now supports model isolation.
        """
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        
        with self.db_manager.get_conversations_connection() as conn:
            cursor = conn.cursor()
            
            # Build keyword search with model isolation
            keyword_conditions = []
            params = [user_id, model_id]
            
            for keyword in keywords[:5]:  # Limit to top 5 keywords
                keyword_conditions.append("(key_topic LIKE ? OR value_content LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            if keyword_conditions:
                where_clause = f"WHERE user_id = ? AND model_id = ? AND ({' OR '.join(keyword_conditions)})"
            else:
                where_clause = "WHERE user_id = ? AND model_id = ?"
            
            query_sql = f"""
                SELECT id, memory_type, key_topic, value_content, importance_score, 
                       created_at, last_accessed, access_count
                FROM memories 
                {where_clause}
                ORDER BY importance_score DESC, last_accessed DESC
                LIMIT ?
            """
            params.append(limit)
            
            cursor.execute(query_sql, params)
            
            memories = []
            for row in cursor.fetchall():
                memory = MemoryItem(
                    id=row[0],
                    memory_type=row[1],
                    key_topic=row[2],
                    value_content=row[3],
                    importance_score=row[4],
                    created_at=row[5],
                    last_accessed=row[6],
                    access_count=row[7]
                )
                memories.append(memory)
                
                # Update access tracking
                cursor.execute("""
                    UPDATE memories 
                    SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                    WHERE id = ?
                """, (row[0],))
            
            conn.commit()
        
        return memories
        
        memories = []
        
        # Search for memories containing keywords
        for keyword in keywords:
            found_memories = self.db_manager.get_memories_by_topic(user_id, keyword)
            memories.extend(found_memories)
        
        # Get high-importance memories as context
        important_memories = self.db_manager.get_important_memories(user_id, limit=5)
        memories.extend(important_memories)
        
        # Remove duplicates and sort by relevance
        unique_memories = {m['id']: m for m in memories}.values()
        sorted_memories = sorted(unique_memories, 
                               key=lambda x: (x['importance_score'], x['access_count']), 
                               reverse=True)
        
        # Convert to MemoryItem objects
        memory_items = []
        for mem in sorted_memories[:limit]:
            memory_items.append(MemoryItem(
                id=mem['id'],
                memory_type=mem['memory_type'],
                key_topic=mem['key_topic'],
                value_content=mem['value_content'],
                importance_score=mem['importance_score'],
                created_at=datetime.fromisoformat(mem['created_at']),
                last_accessed=datetime.fromisoformat(mem['last_accessed']),
                access_count=mem['access_count']
            ))
        
        return memory_items
    
    def build_context_for_llm(self, user_id: str, current_query: str, 
                             model_id: str = "default") -> str:
        """
        Build contextualized memory string for LLM prompting
        Now supports model isolation.
        """
        # Get relevant memories for this model
        relevant_memories = self.get_relevant_memories(user_id, current_query, 
                                                     limit=self.max_context_memories, 
                                                     model_id=model_id)
        
        if not relevant_memories:
            return "No previous conversations or memories stored yet."
        
        # Group memories by type for better organization
        memory_groups = {
            'fact': [],
            'preference': [],
            'interest': [],
            'emotional_state': [],
            'experience': [],
            'other': []
        }
        
        for memory in relevant_memories:
            memory_type = memory.memory_type
            if memory_type not in memory_groups:
                memory_type = 'other'
            memory_groups[memory_type].append(memory)
        
        # Build context string
        context_parts = []
        
        # Add facts first (most important)
        if memory_groups['fact']:
            facts = [f"- {mem.value_content}" for mem in memory_groups['fact'][:3]]
            context_parts.append(f"Facts about the user:\n" + "\n".join(facts))
        
        # Add preferences
        if memory_groups['preference']:
            prefs = [f"- {mem.value_content}" for mem in memory_groups['preference'][:3]]
            context_parts.append(f"User preferences:\n" + "\n".join(prefs))
        
        # Add interests
        if memory_groups['interest']:
            interests = [f"- {mem.value_content}" for mem in memory_groups['interest'][:3]]
            context_parts.append(f"User interests:\n" + "\n".join(interests))
        
        # Add recent emotional states
        if memory_groups['emotional_state']:
            emotions = [f"- {mem.value_content}" for mem in memory_groups['emotional_state'][:2]]
            context_parts.append(f"Recent emotional states:\n" + "\n".join(emotions))
        
        context_string = "\n\n".join(context_parts)
        
        # Ensure context doesn't exceed max length
        if len(context_string) > self.max_context_length:
            context_string = context_string[:self.max_context_length] + "..."
        
        return context_string
    
    def create_conversation_summary(self, user_id: str, messages: List[Dict[str, str]]) -> ConversationSummary:
        """
        Create a summary of recent conversations
        """
        if not messages:
            return ConversationSummary("", "No conversation to summarize", [], "neutral")
        
        # Extract key information from messages
        user_messages = [msg['content'] for msg in messages if msg['role'] == 'user']
        assistant_messages = [msg['content'] for msg in messages if msg['role'] == 'assistant']
        
        # Generate summary
        summary_text = self._generate_summary(user_messages, assistant_messages)
        
        # Extract key topics
        all_text = " ".join(user_messages + assistant_messages)
        key_topics = self._extract_topics(all_text)
        
        # Analyze emotional tone
        emotional_tone = self._analyze_emotional_tone(all_text)
        
        # Create date range
        date_range = datetime.now().strftime("%Y-%m-%d")
        
        # Store summary in database
        self.db_manager.add_conversation_summary(
            user_id=user_id,
            date_range=date_range,
            summary_text=summary_text,
            key_topics=key_topics,
            emotional_tone=emotional_tone
        )
        
        return ConversationSummary(date_range, summary_text, key_topics, emotional_tone)
    
    def update_memory_importance(self, memory_id: int, new_importance: float) -> None:
        """Update the importance score of a memory"""
        self.db_manager.cursor.execute("""
            UPDATE user_memories 
            SET importance_score = ?, last_accessed = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_importance, memory_id))
        self.db_manager.connection.commit()
    
    def cleanup_old_memories(self, user_id: str, days_old: int = 90, min_importance: float = 0.3) -> int:
        """
        Clean up old, low-importance memories to keep database size manageable
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        self.db_manager.cursor.execute("""
            DELETE FROM user_memories 
            WHERE user_id = ? AND importance_score < ? AND created_at < ?
        """, (user_id, min_importance, cutoff_date.isoformat()))
        
        deleted_count = self.db_manager.cursor.rowcount
        self.db_manager.connection.commit()
        
        self.logger.info(f"Cleaned up {deleted_count} old memories for user {user_id}")
        return deleted_count
    
    # Private helper methods
    def _extract_topic(self, content: str) -> str:
        """Extract main topic from content"""
        # Simple topic extraction - could be enhanced with NLP
        words = re.findall(r'\b\w+\b', content.lower())
        
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        if meaningful_words:
            return meaningful_words[0]  # Return first meaningful word
        
        return "general"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for memory search"""
        words = re.findall(r'\b\w+\b', text.lower())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords[:5]  # Return top 5 keywords
    
    def _analyze_importance(self, content: str, base_score: float) -> float:
        """Analyze content to adjust importance score"""
        # Keywords that increase importance
        high_importance_words = ['love', 'hate', 'important', 'secret', 'personal', 'family', 'work', 'passion', 'dream', 'goal']
        
        # Keywords that decrease importance
        low_importance_words = ['maybe', 'perhaps', 'casual', 'random', 'whatever', 'small talk']
        
        content_lower = content.lower()
        
        # Adjust score based on keywords
        for word in high_importance_words:
            if word in content_lower:
                base_score = min(1.0, base_score + 0.1)
        
        for word in low_importance_words:
            if word in content_lower:
                base_score = max(0.1, base_score - 0.1)
        
        # Adjust based on length (longer content might be more important)
        if len(content) > 100:
            base_score = min(1.0, base_score + 0.05)
        
        return base_score
    
    def get_semantic_context(self, user_id: str, query: str, max_length: int = 2000, 
                           model_id: str = "default") -> str:
        """
        Get contextually relevant information using RAG if available, fallback to keyword search
        """
        if self.rag_system:
            try:
                # Use RAG system for semantic search
                context = self.rag_system.get_relevant_context_for_query(query, user_id)
                if context and len(context.strip()) > 0:
                    self.logger.debug(f"Retrieved RAG context for query: {query[:50]}...")
                    return context[:max_length]
            except Exception as e:
                self.logger.error(f"Error getting RAG context: {e}")
        
        # Fallback to traditional keyword-based search
        memories = self.get_relevant_memories(user_id, query, limit=5, model_id=model_id)
        
        if not memories:
            return ""
        
        context_parts = ["=== Relevant Context ===\n"]
        current_length = len(context_parts[0])
        
        for memory in memories:
            memory_text = f"Memory ({memory.importance_score:.2f}): {memory.value_content}\n\n"
            if current_length + len(memory_text) > max_length:
                break
            context_parts.append(memory_text)
            current_length += len(memory_text)
        
        context_parts.append("=== End Context ===\n")
        return "".join(context_parts)
    
    def add_conversation_memory(self, user_id: str, user_message: str, assistant_response: str,
                              model_id: str = "default", importance: str = "medium") -> int:
        """
        Add conversation to both traditional memory and RAG system if available
        """
        # Add to traditional memory system
        memory_id = self.add_memory(
            user_id=user_id,
            memory_type="conversation",
            content=f"User: {user_message}\nAssistant: {assistant_response}",
            topic=self._extract_topic(user_message),
            importance=importance,
            model_id=model_id
        )
        
        # Add to RAG system if available
        if self.rag_system:
            try:
                self.rag_system.add_conversation(
                    user_message=user_message,
                    assistant_response=assistant_response,
                    user_id=user_id,
                    metadata={"model_id": model_id, "memory_id": memory_id}
                )
                self.logger.debug(f"Added conversation to RAG system: memory_id={memory_id}")
            except Exception as e:
                self.logger.error(f"Error adding conversation to RAG system: {e}")
        
        return memory_id
    
    def store_conversation(self, user_message: str, assistant_response: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Wrapper method for backward compatibility with store_conversation calls.
        Extracts user_id from metadata and delegates to add_conversation_memory.
        """
        if not metadata or 'user_id' not in metadata:
            self.logger.error("store_conversation called without user_id in metadata")
            return -1
        
        user_id = metadata['user_id']
        model_id = metadata.get('avatar_id', 'default')
        importance = metadata.get('importance', 'medium')
        
        return self.add_conversation_memory(
            user_id=user_id,
            user_message=user_message,
            assistant_response=assistant_response,
            model_id=model_id,
            importance=importance
        )
    
    def search_conversation_history(self, user_id: str, query: str, limit: int = 5,
                                  model_id: str = "default") -> List[Dict[str, Any]]:
        """
        Search conversation history using RAG if available, fallback to traditional search
        """
        if self.rag_system:
            try:
                results = self.rag_system.search_conversations(query, user_id, limit)
                return [
                    {
                        'similarity_score': result['similarity_score'],
                        'user_message': result['metadata'].get('user_message', ''),
                        'assistant_message': result['metadata'].get('assistant_message', ''),
                        'conversation_id': result['metadata'].get('conversation_id'),
                        'timestamp': result['metadata'].get('timestamp')
                    }
                    for result in results
                ]
            except Exception as e:
                self.logger.error(f"Error searching with RAG system: {e}")
        
        # Fallback to traditional memory search
        memories = self.get_relevant_memories(user_id, query, limit, model_id)
        
        conversation_results = []
        for memory in memories:
            if memory.memory_type == "conversation":
                # Parse conversation content
                lines = memory.value_content.split('\n')
                user_msg = next((line[6:] for line in lines if line.startswith('User: ')), '')
                assistant_msg = next((line[11:] for line in lines if line.startswith('Assistant: ')), '')
                
                conversation_results.append({
                    'similarity_score': memory.importance_score,
                    'user_message': user_msg,
                    'assistant_message': assistant_msg,
                    'conversation_id': memory.id,
                    'timestamp': memory.created_at
                })
        
        return conversation_results
    
    def get_rag_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG system"""
        if self.rag_system:
            try:
                return self.rag_system.rag_system.get_collection_stats()
            except Exception as e:
                self.logger.error(f"Error getting RAG stats: {e}")
                return {"error": str(e)}
        return {"rag_enabled": False}
    
    def sync_rag_system(self) -> int:
        """Sync existing conversations with RAG system"""
        if self.rag_system:
            try:
                return self.rag_system.rag_system.sync_with_conversation_db()
            except Exception as e:
                self.logger.error(f"Error syncing RAG system: {e}")
                return 0
        return 0
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract multiple topics from text"""
        # Simple topic extraction
        words = re.findall(r'\b\w+\b', text.lower())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
        
        # Count word frequency
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top frequent words as topics
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:5]]
    
    def _analyze_emotional_tone(self, text: str) -> str:
        """Analyze emotional tone of text"""
        positive_words = ['happy', 'good', 'great', 'excellent', 'love', 'like', 'wonderful', 'amazing', 'fantastic']
        negative_words = ['sad', 'bad', 'terrible', 'hate', 'dislike', 'awful', 'horrible', 'disappointing']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _generate_summary(self, user_messages: List[str], assistant_messages: List[str]) -> str:
        """Generate a simple conversation summary"""
        if not user_messages:
            return "No user input to summarize"
        
        # Simple summary generation
        total_messages = len(user_messages) + len(assistant_messages)
        main_topics = self._extract_topics(" ".join(user_messages))
        
        summary = f"Conversation with {total_messages} messages. "
        if main_topics:
            summary += f"Main topics discussed: {', '.join(main_topics[:3])}."
        
        return summary
