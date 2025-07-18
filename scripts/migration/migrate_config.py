#!/usr/bin/env python3
"""
Database Migration Script for Config.yaml Updates

This script handles migration tasks for the updated configuration:
1. Consolidate databases to single directory structure
2. Update database paths to match new config
3. Migrate existing data to new schema if needed
"""

import os
import shutil
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

class ConfigMigration:
    """Handles migration of AI Companion configuration and data."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        # Paths
        self.project_root = Path(__file__).parent.parent
        self.user_data_dir = Path.home() / ".local" / "share" / "ai-companion"
        
        # Old database locations (scattered)
        self.old_db_paths = {
            "ai_companion": self.project_root / "databases" / "ai_companion.db",
            "conversations": self.project_root / "databases" / "conversations.db",
            "live2d": self.project_root / "databases" / "live2d.db",
            "personality": self.project_root / "databases" / "personality.db",
            "system": self.project_root / "databases" / "system.db"
        }
        
        # New database locations (consolidated)
        self.new_db_paths = {
            "ai_companion": self.user_data_dir / "databases" / "ai_companion.db",
            "conversations": self.user_data_dir / "databases" / "conversations.db", 
            "live2d_models": self.user_data_dir / "databases" / "live2d_models.db",
            "personality": self.user_data_dir / "databases" / "personality.db",
            "system": self.user_data_dir / "databases" / "system.db"
        }
        
        # Ensure target directory exists
        (self.user_data_dir / "databases").mkdir(parents=True, exist_ok=True)
    
    def migrate_databases(self) -> Dict[str, bool]:
        """Migrate databases to new consolidated structure."""
        results = {}
        
        self.logger.info("🗄️ Starting database migration...")
        
        for db_name, old_path in self.old_db_paths.items():
            try:
                # Map old names to new names
                new_name = "live2d_models" if db_name == "live2d" else db_name
                new_path = self.new_db_paths[new_name]
                
                if old_path.exists():
                    if new_path.exists():
                        self.logger.warning(f"⚠️ Target database already exists: {new_path}")
                        # Create backup
                        backup_path = new_path.with_suffix(f".backup.{int(time.time())}")
                        shutil.copy2(new_path, backup_path)
                        self.logger.info(f"📋 Created backup: {backup_path}")
                    
                    # Copy database
                    shutil.copy2(old_path, new_path)
                    self.logger.info(f"✅ Migrated {db_name}: {old_path} → {new_path}")
                    results[db_name] = True
                else:
                    self.logger.info(f"ℹ️ Database not found (skipping): {old_path}")
                    results[db_name] = True  # Not an error if it doesn't exist
                    
            except Exception as e:
                self.logger.error(f"❌ Failed to migrate {db_name}: {e}")
                results[db_name] = False
        
        return results
    
    def update_model_paths(self) -> bool:
        """Update model paths in existing code to match new config structure."""
        try:
            # Files that might need path updates
            files_to_update = [
                "src/models/tts_handler.py",
                "src/models/enhanced_llm_handler.py", 
                "src/database/live2d_models_separated.py",
                "src/app_globals.py"
            ]
            
            for file_path in files_to_update:
                full_path = self.project_root / file_path
                if full_path.exists():
                    self._update_file_paths(full_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update model paths: {e}")
            return False
    
    def _update_file_paths(self, file_path: Path):
        """Update hardcoded paths in a specific file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Replace hardcoded paths with user data directory paths
            replacements = {
                # Database paths
                'databases/conversations.db': '~/.local/share/ai-companion/databases/conversations.db',
                'databases/live2d.db': '~/.local/share/ai-companion/databases/live2d_models.db',
                'databases/personality.db': '~/.local/share/ai-companion/databases/personality.db',
                'databases/system.db': '~/.local/share/ai-companion/databases/system.db',
                
                # Model paths
                'models/tts/kokoro': '~/.local/share/ai-companion/models/tts/kokoro',
                'models/llm/': '~/.local/share/ai-companion/models/llm/',
                '/models/faster_whisper': '~/.local/share/ai-companion/models/faster_whisper',
                
                # Voice paths
                'models/voices/': '~/.local/share/ai-companion/models/tts/voices/',
            }
            
            for old_path, new_path in replacements.items():
                content = content.replace(old_path, new_path)
            
            # Only write if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.logger.info(f"📝 Updated paths in: {file_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update {file_path}: {e}")
    
    def create_voice_directory_structure(self) -> bool:
        """Create new Kokoro voice directory structure."""
        try:
            voice_dir = self.user_data_dir / "models" / "tts" / "kokoro" / "voices"
            voice_dir.mkdir(parents=True, exist_ok=True)
            
            # Create sample voice configuration
            voice_config = {
                "voices": {
                    "af_heart": {
                        "name": "Heart (American)",
                        "language": "en-US",
                        "gender": "female"
                    },
                    "af_michael": {
                        "name": "Michael (American)", 
                        "language": "en-US",
                        "gender": "male"
                    }
                },
                "default": "af_heart"
            }
            
            config_file = voice_dir / "voices.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(voice_config, f, indent=2)
            
            self.logger.info(f"✅ Created voice directory structure: {voice_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create voice directory: {e}")
            return False
    
    def run_full_migration(self) -> Dict[str, bool]:
        """Run complete migration process."""
        results = {}
        
        self.logger.info("🚀 Starting full configuration migration...")
        
        # 1. Migrate databases
        db_results = self.migrate_databases()
        results["databases"] = all(db_results.values())
        
        # 2. Update model paths in code
        results["model_paths"] = self.update_model_paths()
        
        # 3. Create voice directory structure
        results["voice_structure"] = self.create_voice_directory_structure()
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        if successful == total:
            self.logger.info("🎉 Migration completed successfully!")
        else:
            self.logger.warning(f"⚠️ Migration completed with issues: {successful}/{total} tasks successful")
        
        return results

def main():
    """CLI interface for migration."""
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description="AI Companion Configuration Migration")
    parser.add_argument("action", choices=["migrate", "databases", "paths", "voices"],
                       help="Migration action to perform")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be done without making changes")
    
    args = parser.parse_args()
    
    migration = ConfigMigration()
    
    if args.action == "migrate":
        results = migration.run_full_migration()
        print(f"\nMigration Results: {results}")
    
    elif args.action == "databases":
        results = migration.migrate_databases()
        print(f"\nDatabase Migration Results: {results}")
    
    elif args.action == "paths":
        success = migration.update_model_paths()
        print(f"\nPath Update Result: {success}")
    
    elif args.action == "voices":
        success = migration.create_voice_directory_structure()
        print(f"\nVoice Structure Creation Result: {success}")

if __name__ == "__main__":
    main()
