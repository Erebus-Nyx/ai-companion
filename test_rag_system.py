#!/usr/bin/env python3
"""
Test script for RAG system implementation
Tests basic functionality of the enhanced memory system with RAG capabilities
"""

import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from models.rag_system import RAGSystem, RAGEnhancedMemorySystem
from models.memory_system import MemorySystem
from databases.database_manager import DatabaseManager
from config.config_manager import ConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rag_system():
    """Test the RAG system functionality"""
    
    print("🔍 Testing RAG System Implementation")
    print("=" * 50)
    
    try:
        # Initialize config manager
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Check if RAG is enabled
        rag_config = config.get('rag', {})
        if not rag_config.get('enabled', False):
            print("⚠️ RAG is disabled in configuration. Enabling for test...")
            rag_config['enabled'] = True
        
        print(f"✅ RAG Configuration:")
        print(f"   - Enabled: {rag_config.get('enabled', False)}")
        print(f"   - Embedding Model: {rag_config.get('embedding_model', 'all-MiniLM-L6-v2')}")
        print(f"   - Collection: {rag_config.get('collection_name', 'ai_companion_memory')}")
        print()
        
        # Initialize database manager
        print("📊 Initializing Database Manager...")
        db_manager = DatabaseManager()
        
        # Initialize enhanced memory system with RAG
        print("🧠 Initializing Enhanced Memory System with RAG...")
        memory_system = MemorySystem(db_manager, config)
        
        # Check if RAG system is available
        if memory_system.rag_system:
            print("✅ RAG system initialized successfully!")
            
            # Get RAG statistics
            stats = memory_system.get_rag_stats()
            print(f"📈 RAG Statistics:")
            for key, value in stats.items():
                print(f"   - {key}: {value}")
            print()
            
            # Test adding a conversation
            print("💬 Testing conversation addition...")
            memory_id = memory_system.add_conversation_memory(
                user_id="test_user",
                user_message="Hello, how are you today?",
                assistant_response="I'm doing well, thank you for asking! How can I help you today?",
                model_id="test_model",
                importance="medium"
            )
            print(f"✅ Added conversation with memory_id: {memory_id}")
            
            # Test semantic search
            print("🔍 Testing semantic search...")
            search_results = memory_system.search_conversation_history(
                user_id="test_user",
                query="greeting hello",
                limit=3
            )
            print(f"✅ Found {len(search_results)} relevant conversations")
            for i, result in enumerate(search_results):
                print(f"   {i+1}. Similarity: {result.get('similarity_score', 0):.3f}")
                print(f"      User: {result.get('user_message', '')[:50]}...")
                print(f"      Assistant: {result.get('assistant_message', '')[:50]}...")
            print()
            
            # Test context retrieval
            print("📝 Testing context retrieval...")
            context = memory_system.get_semantic_context(
                user_id="test_user",
                query="conversation about greetings",
                max_length=500
            )
            print(f"✅ Retrieved context ({len(context)} characters):")
            print(context[:200] + "..." if len(context) > 200 else context)
            print()
            
            # Test syncing
            print("🔄 Testing RAG sync...")
            synced_count = memory_system.sync_rag_system()
            print(f"✅ Synced {synced_count} conversations with RAG system")
            
            # Get updated statistics
            stats = memory_system.get_rag_stats()
            print(f"📈 Updated RAG Statistics:")
            for key, value in stats.items():
                print(f"   - {key}: {value}")
            
        else:
            print("❌ RAG system not available (likely missing dependencies)")
            print("   Make sure chromadb and sentence-transformers are installed")
            
        print()
        print("✅ RAG System Test Complete!")
        
    except Exception as e:
        logger.error(f"❌ RAG System Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_basic_rag_functionality():
    """Test basic RAG functionality without full integration"""
    
    print("🔧 Testing Basic RAG Functionality")
    print("=" * 50)
    
    try:
        # Test RAG configuration with proper structure matching config.yaml
        rag_config = {
            'rag': {
                'enabled': True,
                'vector_database': {
                    'type': 'chroma',
                    'path': 'databases/vector_db_test',
                    'collection_name': 'test_collection'
                },
                'embedding': {
                    'model_name': 'all-MiniLM-L6-v2',
                    'embedding_dim': 384,
                    'batch_size': 32
                }
            },
            'database': {
                'paths': {
                    'conversations': '~/.local/share/ai2d_chat/databases/conversations.db'
                }
            }
        }
        
        print("🚀 Initializing standalone RAG system...")
        rag_system = RAGSystem(rag_config)
        
        print("✅ RAG system initialized!")
        
        # Test adding a conversation
        print("💬 Testing conversation addition...")
        success = rag_system.add_conversation_to_vector_db(
            conversation_id=1,
            user_message="What is artificial intelligence?",
            assistant_message="Artificial intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans.",
            metadata={"user_id": "test_user", "model_id": "test_model"}
        )
        print(f"✅ Conversation added: {success}")
        
        # Test semantic search
        print("🔍 Testing semantic search...")
        results = rag_system.semantic_search("machine learning AI", n_results=3)
        print(f"✅ Found {len(results)} results")
        for i, result in enumerate(results):
            print(f"   {i+1}. Similarity: {result.get('similarity_score', 0):.3f}")
            print(f"      Document: {result.get('document', '')[:100]}...")
        
        # Test context retrieval
        print("📝 Testing context retrieval...")
        context = rag_system.get_relevant_context("artificial intelligence")
        print(f"✅ Retrieved context ({len(context)} characters)")
        print(context[:200] + "..." if len(context) > 200 else context)
        
        # Get collection stats
        print("📊 Getting collection statistics...")
        stats = rag_system.get_collection_stats()
        print(f"✅ Collection stats:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        
        print()
        print("✅ Basic RAG Functionality Test Complete!")
        
    except Exception as e:
        logger.error(f"❌ Basic RAG Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 RAG System Test Suite")
    print("=" * 60)
    print()
    
    # Test basic functionality first
    basic_success = test_basic_rag_functionality()
    print()
    
    # Test integrated functionality
    if basic_success:
        integrated_success = test_rag_system()
    else:
        print("⚠️ Skipping integrated test due to basic test failure")
        integrated_success = False
    
    print()
    print("📋 Test Summary:")
    print(f"   - Basic RAG Test: {'✅ PASSED' if basic_success else '❌ FAILED'}")
    print(f"   - Integrated RAG Test: {'✅ PASSED' if integrated_success else '❌ FAILED'}")
    
    if basic_success and integrated_success:
        print()
        print("🎉 All RAG tests passed! The system is ready for use.")
    else:
        print()
        print("⚠️ Some tests failed. Check the logs for details.")
        sys.exit(1)
