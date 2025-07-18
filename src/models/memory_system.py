"""
Enhanced Memory System for AI Companion
Provides intelligent memory storage, retrieval, and context management
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
    Advanced memory system for the AI companion
    Handles memory storage, retrieval, clustering, and context generation
    """
    
    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
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
                   topic: Optional[str] = None, importance: str = "medium") -> int:
        """
        Add a new memory with automatic importance scoring and topic extraction
        """
        # Extract topic if not provided
        if not topic:
            topic = self._extract_topic(content)
        
        # Calculate importance score
        importance_score = self.importance_thresholds.get(importance, 0.5)
        
        # Adjust importance based on content analysis
        importance_score = self._analyze_importance(content, importance_score)
        
        # Store memory
        memory_id = self.db_manager.add_memory(
            user_id=user_id,
            memory_type=memory_type,
            key_topic=topic,
            value_content=content,
            importance_score=importance_score
        )
        
        self.logger.info(f"Added memory: {topic} (importance: {importance_score:.2f})")
        return memory_id
    
    def get_relevant_memories(self, user_id: str, query: str, limit: int = 10) -> List[MemoryItem]:
        """
        Retrieve memories relevant to a query using keyword matching and importance
        """
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        
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
    
    def build_context_for_llm(self, user_id: str, current_query: str = "") -> str:
        """
        Build formatted context string for LLM from relevant memories
        """
        # Get relevant memories
        memories = self.get_relevant_memories(user_id, current_query, self.max_context_memories)
        
        if not memories:
            return "No previous memories available."
        
        # Build context string
        context_parts = []
        
        # Group memories by type
        memory_groups = {}
        for memory in memories:
            if memory.memory_type not in memory_groups:
                memory_groups[memory.memory_type] = []
            memory_groups[memory.memory_type].append(memory)
        
        # Format each group
        for memory_type, mem_list in memory_groups.items():
            if memory_type == 'preference':
                context_parts.append("User Preferences:")
                for mem in mem_list[:5]:  # Limit preferences
                    context_parts.append(f"- {mem.key_topic}: {mem.value_content}")
            
            elif memory_type == 'fact':
                context_parts.append("Important Facts:")
                for mem in mem_list[:5]:
                    context_parts.append(f"- {mem.value_content}")
            
            elif memory_type == 'interest':
                context_parts.append("User Interests:")
                interests = [mem.value_content for mem in mem_list[:3]]
                context_parts.append(f"- {', '.join(interests)}")
            
            elif memory_type == 'relationship':
                context_parts.append("Relationship Context:")
                for mem in mem_list[:3]:
                    context_parts.append(f"- {mem.value_content}")
        
        # Join with newlines and trim if too long
        context = "\n".join(context_parts)
        
        if len(context) > self.max_context_length:
            context = context[:self.max_context_length] + "..."
        
        return context
    
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
