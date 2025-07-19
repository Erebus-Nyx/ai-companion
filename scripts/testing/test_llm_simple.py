#!/usr/bin/env python3
"""Simple test for LLM handler"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.db_manager import DBManager
from models.enhanced_llm_handler import EnhancedLLMHandler

def test_llm():
    print("Testing LLM handler...")
    
    # Initialize database
    print("Initializing database...")
    db_manager = DBManager()
    db_manager.initialize_database()
    print("Database initialized")
    
    # Initialize LLM handler
    print("Initializing LLM handler...")
    llm_handler = EnhancedLLMHandler(db_manager=db_manager)
    
    # Try to initialize the model
    print("Loading LLM model...")
    success = llm_handler.initialize_model()
    
    if success:
        print("LLM model loaded successfully!")
        
        # Test a simple query
        print("Testing LLM response...")
        response = llm_handler.generate_response("Hello, how are you?", user_id="test_user")
        print(f"LLM Response: {response}")
        
    else:
        print("Failed to load LLM model")
        
        # Check what models are available
        print("Available model files:")
        model_dir = "/home/nyx/ai2d_chat/models/llm"
        if os.path.exists(model_dir):
            for file in os.listdir(model_dir):
                print(f"  - {file}")
        else:
            print("  No model directory found")

if __name__ == "__main__":
    test_llm()
