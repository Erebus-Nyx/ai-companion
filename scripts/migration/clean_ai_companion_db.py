#!/usr/bin/env python3
"""
Script to clean phantom models from ai2d_chat.db
"""

import os
import sqlite3
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_ai2d_chat_db():
    """Clean phantom models from ai2d_chat.db"""
    
    user_data_dir = os.path.expanduser("~/.local/share/ai2d_chat")
    db_path = os.path.join(user_data_dir, "databases", "ai2d_chat.db")
    
    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return False
        
    logger.info(f"Cleaning phantom models from: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='live2d_models'")
        if not cursor.fetchone():
            logger.info("No live2d_models table found")
            conn.close()
            return True
        
        # Get all models
        cursor.execute("SELECT id, model_name, model_path FROM live2d_models")
        models = cursor.fetchall()
        
        logger.info(f"Found {len(models)} models in database")
        
        removed_count = 0
        for model_id, model_name, model_path in models:
            logger.info(f"Checking model: {model_name} -> {model_path}")
            
            # Check if model path contains old static/assets path
            if model_path and ('static/assets' in model_path or '/src/web/static/assets' in model_path):
                # Remove model and its motions
                cursor.execute("DELETE FROM live2d_motions WHERE model_id = ?", (model_id,))
                motions_deleted = cursor.rowcount
                
                cursor.execute("DELETE FROM live2d_models WHERE id = ?", (model_id,))
                
                logger.info(f"❌ Removed phantom model '{model_name}' (and {motions_deleted} motions)")
                removed_count += 1
            else:
                logger.info(f"✅ Keeping model '{model_name}' (valid path)")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Cleaned {removed_count} phantom models from ai2d_chat.db")
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning ai2d_chat.db: {e}")
        return False

if __name__ == "__main__":
    clean_ai2d_chat_db()
