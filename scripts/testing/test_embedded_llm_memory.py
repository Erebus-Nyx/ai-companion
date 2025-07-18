#!/usr/bin/env python3
"""
Comprehensive test for the embedded llama.cpp and SQLite memory system integration.
Tests the enhanced LLM handler, memory system, and database functionality.
"""

import sys
import os
import logging
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.db_manager import DBManager
from models.enhanced_llm_handler import EnhancedLLMHandler
from models.memory_system import MemorySystem

def setup_logging():
    """Setup logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_database_setup():
    """Test database initialization and schema creation"""
    logger = logging.getLogger(__name__)
    logger.info("🗄️ Testing database setup...")
    
    try:
        # Initialize database
        db_manager = DBManager("test_ai_companion.db")
        
        # Test basic functionality
        user_id = "test_user"
        
        # Test personality traits
        traits = db_manager.get_personality_profile(user_id)
        logger.info(f"✅ Retrieved personality traits: {list(traits.keys())}")
        
        # Test adding conversation
        conversation_id = db_manager.add_conversation(user_id, "user", "Hello, this is a test message")
        logger.info(f"✅ Added conversation with ID: {conversation_id}")
        
        # Test bonding progress
        bonding = db_manager.get_bonding_progress(user_id)
        logger.info(f"✅ Retrieved bonding progress: {bonding}")
        
        # Test avatar state
        avatar_state = db_manager.get_avatar_state(user_id)
        logger.info(f"✅ Retrieved avatar state: {avatar_state}")
        
        db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

def test_memory_system():
    """Test memory system functionality"""
    logger = logging.getLogger(__name__)
    logger.info("🧠 Testing memory system...")
    
    try:
        # Initialize database and memory system
        db_manager = DBManager("test_ai_companion.db")
        memory_system = MemorySystem(db_manager)
        
        user_id = "test_user"
        
        # Test adding memories
        memory_id1 = memory_system.add_memory(
            user_id=user_id,
            memory_type="preference",
            content="I love pizza with pepperoni",
            topic="food",
            importance="medium"
        )
        logger.info(f"✅ Added preference memory: {memory_id1}")
        
        memory_id2 = memory_system.add_memory(
            user_id=user_id,
            memory_type="fact",
            content="I work as a software engineer",
            importance="high"
        )
        logger.info(f"✅ Added fact memory: {memory_id2}")
        
        memory_id3 = memory_system.add_memory(
            user_id=user_id,
            memory_type="interest",
            content="I enjoy playing video games and reading sci-fi books",
            importance="medium"
        )
        logger.info(f"✅ Added interest memory: {memory_id3}")
        
        # Test memory retrieval
        relevant_memories = memory_system.get_relevant_memories(user_id, "food and cooking", limit=5)
        logger.info(f"✅ Retrieved {len(relevant_memories)} relevant memories about food")
        
        # Test context building
        context = memory_system.build_context_for_llm(user_id, "What do you know about me?")
        logger.info(f"✅ Built LLM context: {len(context)} characters")
        
        # Test conversation summary
        messages = [
            {"role": "user", "content": "I love pizza"},
            {"role": "assistant", "content": "That's great! What's your favorite topping?"},
            {"role": "user", "content": "Pepperoni for sure"},
            {"role": "assistant", "content": "Pepperoni is a classic choice!"}
        ]
        summary = memory_system.create_conversation_summary(user_id, messages)
        logger.info(f"✅ Created conversation summary: {summary.summary_text}")
        
        db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory system test failed: {e}")
        return False

def test_enhanced_llm_handler():
    """Test enhanced LLM handler functionality"""
    logger = logging.getLogger(__name__)
    logger.info("🤖 Testing Enhanced LLM Handler...")
    
    try:
        # Initialize components
        db_manager = DBManager("test_ai_companion.db")
        llm_handler = EnhancedLLMHandler(db_manager=db_manager)
        
        # Test model status (without initializing the actual model for speed)
        status = llm_handler.get_model_status()
        logger.info(f"✅ LLM status retrieved: {status}")
        
        # Test settings update
        llm_handler.update_settings(temperature=0.8, max_tokens=256)
        logger.info("✅ LLM settings updated")
        
        # Test caching functions
        llm_handler._cache_response("test input", "test_user", "test response")
        cached = llm_handler._check_cache("test input", "test_user")
        assert cached == "test response", "Cache test failed"
        logger.info("✅ LLM caching system working")
        
        # Test context building
        context = llm_handler._build_enhanced_conversation_context("test_user", "test_session", "Hello")
        logger.info(f"✅ Built conversation context with {len(context.messages)} messages")
        
        db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced LLM handler test failed: {e}")
        return False

def test_model_initialization():
    """Test actual model initialization (optional, requires model download)"""
    logger = logging.getLogger(__name__)
    logger.info("🔄 Testing model initialization (this may take time)...")
    
    try:
        # Initialize components
        db_manager = DBManager("test_ai_companion.db")
        llm_handler = EnhancedLLMHandler(db_manager=db_manager)
        
        # Test model initialization
        logger.info("Attempting to initialize LLM model...")
        success = llm_handler.initialize_model()
        
        if success:
            logger.info("✅ LLM model initialized successfully")
            
            # Test actual response generation
            test_input = "Hello, how are you?"
            response = llm_handler.generate_response(test_input, user_id="test_user")
            logger.info(f"✅ Generated response: {response}")
            
            return True
        else:
            logger.warning("⚠️ Model initialization failed (may be expected if no model available)")
            return False
        
    except Exception as e:
        logger.error(f"❌ Model initialization test failed: {e}")
        return False

def test_integration():
    """Test full integration between components"""
    logger = logging.getLogger(__name__)
    logger.info("🔗 Testing full system integration...")
    
    try:
        # Initialize all components
        db_manager = DBManager("test_ai_companion.db")
        memory_system = MemorySystem(db_manager)
        llm_handler = EnhancedLLMHandler(db_manager=db_manager)
        
        user_id = "integration_test_user"
        session_id = "test_session_1"
        
        # Simulate a conversation flow
        
        # 1. User introduces themselves
        user_input1 = "Hi, my name is Alice and I'm a teacher"
        
        # Extract memories from input
        llm_handler._extract_and_store_memories(user_id, user_input1)
        logger.info("✅ Extracted and stored memories from user introduction")
        
        # 2. Build context for response
        context = llm_handler._build_enhanced_conversation_context(user_id, session_id, user_input1)
        logger.info(f"✅ Built context with {len(context.user_memories)} memories")
        
        # 3. Test conversation state updates
        llm_handler._update_enhanced_conversation_state(
            user_id, user_input1, "Nice to meet you, Alice!", context, session_id
        )
        logger.info("✅ Updated conversation state")
        
        # 4. Test memory retrieval for next interaction
        user_input2 = "What do you remember about me?"
        relevant_memories = memory_system.get_relevant_memories(user_id, user_input2, limit=5)
        logger.info(f"✅ Retrieved {len(relevant_memories)} relevant memories")
        
        # 5. Test bonding progress
        bonding = db_manager.get_bonding_progress(user_id)
        logger.info(f"✅ Bonding progress: Level {bonding.get('bond_level', 1)}, {bonding.get('experience_points', 0)} XP")
        
        # 6. Test avatar state
        avatar_state = db_manager.get_avatar_state(user_id)
        logger.info(f"✅ Avatar state: {avatar_state.get('current_mood', 'neutral')} mood, {avatar_state.get('happiness_level', 0.7):.1f} happiness")
        
        db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False

def cleanup_test_files():
    """Clean up test database files"""
    test_files = ["test_ai_companion.db"]
    for file in test_files:
        if Path(file).exists():
            os.remove(file)
            print(f"🗑️ Cleaned up {file}")

def main():
    """Run all tests"""
    logger = setup_logging()
    
    print("🚀 Starting Embedded LLaMA.cpp and SQLite Memory System Tests")
    print("=" * 70)
    
    tests = [
        ("Database Setup", test_database_setup),
        ("Memory System", test_memory_system),
        ("Enhanced LLM Handler", test_enhanced_llm_handler),
        ("Full Integration", test_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        start_time = time.time()
        
        try:
            success = test_func()
            duration = time.time() - start_time
            results[test_name] = {"success": success, "duration": duration}
            
            if success:
                print(f"✅ {test_name} test PASSED ({duration:.2f}s)")
            else:
                print(f"❌ {test_name} test FAILED ({duration:.2f}s)")
                
        except Exception as e:
            duration = time.time() - start_time
            results[test_name] = {"success": False, "duration": duration}
            print(f"💥 {test_name} test CRASHED: {e} ({duration:.2f}s)")
    
    # Optional model initialization test
    print(f"\n🔄 Optional: Model Initialization Test")
    print("This test will attempt to download and initialize an actual LLM model.")
    response = input("Run model initialization test? (y/N): ").strip().lower()
    
    if response == 'y':
        start_time = time.time()
        try:
            success = test_model_initialization()
            duration = time.time() - start_time
            results["Model Initialization"] = {"success": success, "duration": duration}
            
            if success:
                print(f"✅ Model Initialization test PASSED ({duration:.2f}s)")
            else:
                print(f"⚠️ Model Initialization test INCOMPLETE ({duration:.2f}s)")
        except Exception as e:
            duration = time.time() - start_time
            results["Model Initialization"] = {"success": False, "duration": duration}
            print(f"💥 Model Initialization test CRASHED: {e} ({duration:.2f}s)")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results.values() if r["success"])
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{test_name:<25} {status:>10} ({result['duration']:.2f}s)")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The embedded LLaMA.cpp and SQLite memory system is ready!")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    # Cleanup
    cleanup_response = input("\nClean up test database files? (Y/n): ").strip().lower()
    if cleanup_response != 'n':
        cleanup_test_files()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
