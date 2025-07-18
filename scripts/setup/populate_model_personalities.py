#!/usr/bin/env python3
"""
Populate model personalities from config.yaml into the database.
"""

import sys
import os
import yaml
import json
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from databases.database_manager import DatabaseManager, init_databases

def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def populate_model_personalities():
    """Populate model personalities from config into database"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize databases
    logger.info("Initializing databases...")
    init_databases()
    
    # Load config
    logger.info("Loading configuration...")
    config = load_config()
    
    db_manager = DatabaseManager()
    
    # Extract Live2D models from config
    live2d_models = config.get('live2d_models', {})
    avatar_settings = config.get('avatar_settings', {})
    personality_traits = avatar_settings.get('personality', {}).get('traits', {})
    
    for model_name, model_config in live2d_models.items():
        if not model_config.get('active', False):
            continue
            
        logger.info(f"Processing model: {model_name}")
        
        # Extract model traits
        model_traits = model_config.get('traits', [])
        
        # Build base traits from config
        base_traits = {}
        current_traits = {}
        
        # Map trait categories to values
        for trait_category in model_traits:
            if trait_category in personality_traits:
                for trait in personality_traits[trait_category]:
                    # Default values - these can be customized per model
                    base_traits[trait] = 0.7
                    current_traits[trait] = 0.7
        
        # Extract appearance information
        appearance = model_config.get('appearance', {})
        appearance_notes = []
        
        if 'hair' in appearance:
            hair = appearance['hair']
            hair_desc = f"Hair: {hair.get('color', 'unknown')} color"
            if 'style' in hair:
                hair_desc += f", {', '.join(hair['style'])}"
            appearance_notes.append(hair_desc)
        
        if 'eye_color' in appearance:
            appearance_notes.append(f"Eyes: {appearance['eye_color']}")
        
        if 'clothing' in appearance:
            appearance_notes.append(f"Clothing: {', '.join(appearance['clothing'])}")
        
        if 'accessories' in appearance:
            acc = appearance['accessories']
            if 'hair' in acc and acc['hair']:
                appearance_notes.append(f"Hair accessories: {', '.join(acc['hair'])}")
        
        # Create model personality entry
        model_id = model_name.lower()
        
        with db_manager.get_personality_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO model_personalities 
                (model_id, name, base_traits, current_traits, description, 
                 appearance_notes, config_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                model_id,
                model_config.get('avatar_name', model_name),
                json.dumps(base_traits),
                json.dumps(current_traits),
                f"AI companion model {model_name}",
                "; ".join(appearance_notes),
                "config.yaml"
            ))
            conn.commit()
        
        logger.info(f"✅ Created personality for {model_name} ({model_id})")
        logger.info(f"   Traits: {list(base_traits.keys())}")
        logger.info(f"   Appearance: {'; '.join(appearance_notes)}")
    
    logger.info("🎉 Model personalities populated successfully!")

if __name__ == "__main__":
    populate_model_personalities()
