"""
RAG (Retrieval-Augmented Generation) System for AI Companion
Integrates with existing memory system and provides semantic search capabilities.
"""

import os
import json
import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class RAGSystem:
    """
    RAG system that enhances the AI companion's memory and retrieval capabilities.
    Integrates with existing conversation database and provides semantic search.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Extract config values with proper fallbacks
        rag_config = config.get('rag', {})
        vector_db_config = rag_config.get('vector_database', {})
        embedding_config = rag_config.get('embedding', {})
        
        self.embedding_model_name = embedding_config.get('model_name', 'sentence-transformers/all-MiniLM-L6-v2')
        if self.embedding_model_name.startswith('sentence-transformers/'):
            self.embedding_model_name = self.embedding_model_name.replace('sentence-transformers/', '')
        
        self.collection_name = vector_db_config.get('collection_name', 'ai2d_chat_knowledge')
        self.persist_directory = vector_db_config.get('path', 'databases/vector_db')
        
        # Expand user path if needed
        if self.persist_directory.startswith('~'):
            self.persist_directory = os.path.expanduser(self.persist_directory)
        
        # Ensure vector database directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Initialize Chroma client
        self.chroma_client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(name=self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "AI Companion conversation memory and knowledge base"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
        
        # Connect to existing conversation database
        # Use proper database path from config structure
        database_config = config.get('database', {})
        database_paths = database_config.get('paths', {})
        self.db_path = database_paths.get('conversations', '~/.local/share/ai2d_chat/databases/conversations.db')
        if self.db_path.startswith('~'):
            self.db_path = os.path.expanduser(self.db_path)
        
        logger.info("RAG System initialized successfully")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for given text"""
        try:
            embedding = self.embedding_model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
    
    def add_conversation_to_vector_db(self, conversation_id: int, user_message: str, 
                                    assistant_message: str, metadata: Dict[str, Any] = None):
        """Add conversation pair to vector database for semantic search"""
        try:
            # Create unique ID for this conversation pair
            doc_id = f"conv_{conversation_id}_{hashlib.md5(user_message.encode()).hexdigest()[:8]}"
            
            # Combine user and assistant messages for better context
            combined_text = f"User: {user_message}\nAssistant: {assistant_message}"
            
            # Generate embedding
            embedding = self.generate_embedding(combined_text)
            if not embedding:
                logger.warning(f"Failed to generate embedding for conversation {conversation_id}")
                return False
            
            # Prepare metadata
            doc_metadata = {
                "conversation_id": conversation_id,
                "user_message": user_message,
                "assistant_message": assistant_message,
                "timestamp": datetime.now().isoformat(),
                "type": "conversation",
                **(metadata or {})
            }
            
            # Add to collection
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[combined_text],
                metadatas=[doc_metadata]
            )
            
            logger.debug(f"Added conversation {conversation_id} to vector database")
            return True
            
        except Exception as e:
            logger.error(f"Error adding conversation to vector database: {e}")
            return False
    
    def add_knowledge_snippet(self, text: str, source: str, metadata: Dict[str, Any] = None):
        """Add knowledge snippet to vector database"""
        try:
            # Create unique ID for this knowledge snippet
            doc_id = f"knowledge_{hashlib.md5(text.encode()).hexdigest()}"
            
            # Generate embedding
            embedding = self.generate_embedding(text)
            if not embedding:
                logger.warning(f"Failed to generate embedding for knowledge snippet")
                return False
            
            # Prepare metadata
            doc_metadata = {
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "type": "knowledge",
                **(metadata or {})
            }
            
            # Add to collection
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[doc_metadata]
            )
            
            logger.debug(f"Added knowledge snippet from {source} to vector database")
            return True
            
        except Exception as e:
            logger.error(f"Error adding knowledge snippet to vector database: {e}")
            return False
    
    def semantic_search(self, query: str, n_results: int = 5, 
                       filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Perform semantic search on the vector database"""
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                logger.warning("Failed to generate embedding for search query")
                return []
            
            # Perform search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'distance': results['distances'][0][i]
                })
            
            logger.debug(f"Semantic search for '{query}' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            return []
    
    def get_relevant_context(self, query: str, max_context_length: int = 2000) -> str:
        """Get relevant context for a query, formatted for LLM consumption"""
        try:
            # Search for relevant information
            results = self.semantic_search(query, n_results=5)
            
            if not results:
                return ""
            
            # Build context string
            context_parts = []
            current_length = 0
            
            context_parts.append("=== Relevant Context ===\n")
            
            for result in results:
                metadata = result['metadata']
                similarity = result['similarity_score']
                
                # Skip low-similarity results
                if similarity < 0.3:
                    continue
                
                # Format context based on type
                if metadata.get('type') == 'conversation':
                    context_text = f"Previous conversation (similarity: {similarity:.2f}):\n"
                    context_text += f"User: {metadata.get('user_message', '')}\n"
                    context_text += f"Assistant: {metadata.get('assistant_message', '')}\n\n"
                elif metadata.get('type') == 'knowledge':
                    context_text = f"Knowledge from {metadata.get('source', 'unknown')} (similarity: {similarity:.2f}):\n"
                    context_text += f"{result['document']}\n\n"
                else:
                    context_text = f"Information (similarity: {similarity:.2f}):\n{result['document']}\n\n"
                
                # Check if adding this would exceed max length
                if current_length + len(context_text) > max_context_length:
                    break
                
                context_parts.append(context_text)
                current_length += len(context_text)
            
            context_parts.append("=== End Context ===\n")
            
            return "".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return ""
    
    def sync_with_conversation_db(self):
        """Sync conversation database with vector database"""
        try:
            # Connect to conversation database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get conversations that aren't in vector database yet
            cursor.execute("""
                SELECT id, user_message, assistant_response, timestamp, user_id 
                FROM conversations 
                WHERE user_message IS NOT NULL AND assistant_response IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT 100
            """)
            
            conversations = cursor.fetchall()
            
            # Get existing document IDs to avoid duplicates
            existing_ids = set()
            try:
                existing_data = self.collection.get()
                existing_ids = set(existing_data['ids'])
            except Exception as e:
                logger.warning(f"Could not fetch existing IDs: {e}")
            
            synced_count = 0
            for conv_id, user_msg, assistant_msg, timestamp, user_id in conversations:
                # Generate expected document ID
                expected_id = f"conv_{conv_id}_{hashlib.md5(user_msg.encode()).hexdigest()[:8]}"
                
                # Skip if already exists
                if expected_id in existing_ids:
                    continue
                
                # Add to vector database
                metadata = {
                    'user_id': user_id,
                    'original_timestamp': timestamp
                }
                
                if self.add_conversation_to_vector_db(conv_id, user_msg, assistant_msg, metadata):
                    synced_count += 1
            
            conn.close()
            
            logger.info(f"Synced {synced_count} conversations with vector database")
            return synced_count
            
        except Exception as e:
            logger.error(f"Error syncing with conversation database: {e}")
            return 0
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database collection"""
        try:
            data = self.collection.get()
            total_documents = len(data['ids'])
            
            # Count by type
            type_counts = {}
            for metadata in data.get('metadatas', []):
                doc_type = metadata.get('type', 'unknown')
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            return {
                'total_documents': total_documents,
                'type_counts': type_counts,
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model_name
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def clear_collection(self):
        """Clear all documents from the collection (use with caution)"""
        try:
            # Delete the existing collection
            self.chroma_client.delete_collection(name=self.collection_name)
            
            # Create a new empty collection
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "AI Companion conversation memory and knowledge base"}
            )
            
            logger.info(f"Cleared collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False


class RAGEnhancedMemorySystem:
    """
    Enhanced memory system that integrates RAG capabilities with existing memory system
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rag_system = RAGSystem(config)
        
        # Auto-sync on initialization
        self.rag_system.sync_with_conversation_db()
        
        logger.info("RAG Enhanced Memory System initialized")
    
    def add_conversation(self, user_message: str, assistant_response: str, 
                        user_id: str = None, metadata: Dict[str, Any] = None):
        """Add conversation to both traditional and vector databases"""
        try:
            # Add to traditional database (existing functionality)
            # This would integrate with your existing memory system
            
            # Add to vector database for semantic search
            conversation_id = self._get_next_conversation_id()
            
            rag_metadata = {
                'user_id': user_id,
                **(metadata or {})
            }
            
            self.rag_system.add_conversation_to_vector_db(
                conversation_id, user_message, assistant_response, rag_metadata
            )
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error adding conversation to enhanced memory: {e}")
            return None
    
    def get_relevant_context_for_query(self, query: str, user_id: str = None) -> str:
        """Get relevant context for a user query using semantic search"""
        try:
            # Filter by user if specified
            filter_metadata = None
            if user_id:
                filter_metadata = {"user_id": user_id}
            
            # Get context using RAG system
            context = self.rag_system.get_relevant_context(query)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return ""
    
    def search_conversations(self, query: str, user_id: str = None, 
                           limit: int = 5) -> List[Dict[str, Any]]:
        """Search conversations using semantic similarity"""
        try:
            filter_metadata = {"type": "conversation"}
            if user_id:
                filter_metadata["user_id"] = user_id
            
            results = self.rag_system.semantic_search(
                query, n_results=limit, filter_metadata=filter_metadata
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            return []
    
    def _get_next_conversation_id(self) -> int:
        """Get next conversation ID from database"""
        try:
            conn = sqlite3.connect(self.rag_system.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM conversations")
            result = cursor.fetchone()
            conn.close()
            
            return (result[0] or 0) + 1
            
        except Exception as e:
            logger.error(f"Error getting next conversation ID: {e}")
            return 1
