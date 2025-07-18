#!/usr/bin/env python3
"""
AI Companion Configuration Manager

Handles configuration, secrets, and runtime data paths for both development
and production (pipx) installations.

For pipx installations, creates user-local directories:
- ~/.config/ai-companion/       (configuration files)
- ~/.local/share/ai-companion/   (databases, models, cache)
- ~/.cache/ai-companion/         (temporary cache files)
"""

import os
import sys
import shutil
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import tempfile
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration and data paths for AI Companion."""
    
    def __init__(self):
        self.is_dev_mode = self._detect_dev_mode()
        self.setup_paths()
        self.ensure_directories()
        
    @classmethod
    def setup_fresh_installation(cls, clean_databases: bool = True) -> 'ConfigManager':
        """Set up a fresh AI Companion installation with clean configuration."""
        manager = cls()
        manager.install_configuration_files(clean_databases=clean_databases)
        return manager
        
    def _detect_dev_mode(self) -> bool:
        """Detect if we're running in development mode (editable install)."""
        # Check if we're running from source directory
        current_file = Path(__file__).resolve()
        src_dir = current_file.parent
        
        # Look for development indicators
        repo_indicators = ['.git', 'setup.py', 'pyproject.toml']
        parent_dir = src_dir.parent
        
        for indicator in repo_indicators:
            if (parent_dir / indicator).exists():
                logger.info("Development mode detected (repository structure found)")
                return True
                
        # Check if installed with pip -e
        try:
            import pkg_resources
            dist = pkg_resources.get_distribution('ai-companion')
            if dist.location and 'site-packages' not in dist.location:
                logger.info("Development mode detected (editable install)")
                return True
        except:
            pass
            
        logger.info("Production mode detected (pipx install)")
        return False
        
    def setup_paths(self):
        """Setup paths based on installation mode."""
        if self.is_dev_mode:
            # Development mode: use repository directories
            repo_root = Path(__file__).parent.parent.resolve()
            self.config_dir = repo_root
            self.data_dir = repo_root
            self.cache_dir = repo_root / 'cache'
            self.database_dir = repo_root / 'src' / 'databases'
            self.models_dir = repo_root / 'src' / 'models'
            self.live2d_models_dir = repo_root / 'src' / 'live2d_models'
            
        else:
            # Production mode: use XDG user directories
            home = Path.home()
            
            # Configuration directory
            self.config_dir = home / '.config' / 'ai-companion'
            
            # Data directory  
            self.data_dir = home / '.local' / 'share' / 'ai-companion'
            
            # Cache directory
            self.cache_dir = home / '.cache' / 'ai-companion'
            
            # Specific data subdirectories
            self.database_dir = self.data_dir / 'databases'
            self.models_dir = self.data_dir / 'models'
            self.live2d_models_dir = self.data_dir / 'live2d_models'
            
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.config_dir,
            self.data_dir,
            self.cache_dir,
            self.database_dir,
            self.models_dir,
            self.live2d_models_dir,
            # Additional subdirectories for specific components
            self.cache_dir / 'logs',
            self.cache_dir / 'audio_output',
            self.cache_dir / 'audio_input',
            self.models_dir / 'llm',
            self.models_dir / 'tts' / 'kokoro',
            self.models_dir / 'tts' / 'voices',
            self.models_dir / 'embeddings',
            self.models_dir / 'faster-whisper',
            self.models_dir / 'silero_vad',
            self.models_dir / 'pyannote' / 'segmentation-3.0',
            self.models_dir / 'pyannote' / 'speaker-diarization-3.1',
            self.database_dir / 'vector_db',
            # User management directories
            self.get_sessions_path(),
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
            
    def get_config_path(self, filename: str = 'config.yaml') -> Path:
        """Get path to configuration file."""
        config_path = self.config_dir / filename
        
        # For production, install configuration if it doesn't exist
        if not self.is_dev_mode and not config_path.exists():
            self.install_configuration_files(clean_databases=True)
            
        return config_path
        
    def get_secrets_path(self, filename: str = '.secrets') -> Path:
        """Get path to secrets file."""
        secrets_path = self.config_dir / filename
        
        # For production, install configuration if secrets don't exist
        if not self.is_dev_mode and not secrets_path.exists():
            self.install_configuration_files(clean_databases=False)  # Don't clean DBs twice
            
        return secrets_path
        
    def get_sessions_path(self) -> Path:
        """Get path to sessions directory."""
        return self.cache_dir / 'sessions'
        
    def get_database_path(self, db_name: str) -> Path:
        """Get path to database file."""
        return self.database_dir / db_name
        
    def get_models_path(self, model_type: str = '') -> Path:
        """Get path to models directory or specific model type."""
        if model_type:
            return self.models_dir / model_type
        return self.models_dir
        
    def get_live2d_models_path(self, model_name: str = '') -> Path:
        """Get path to Live2D models directory or specific model."""
        if model_name:
            return self.live2d_models_dir / model_name
        return self.live2d_models_dir
        
    def get_cache_path(self, cache_type: str = '') -> Path:
        """Get path to cache directory or specific cache type."""
        if cache_type:
            return self.cache_dir / cache_type
        return self.cache_dir
        
    def _copy_default_config(self, config_path: Path):
        """Copy default configuration from package resources."""
        try:
            # Try to find config template in package
            import pkg_resources
            template_content = pkg_resources.resource_string(
                'ai_companion', 'config_template.yaml'
            ).decode('utf-8')
            
            with open(config_path, 'w') as f:
                f.write(template_content)
                
            logger.info(f"Created default config at: {config_path}")
            
        except Exception as e:
            logger.warning(f"Could not copy default config: {e}")
            # Create minimal config
            self._create_minimal_config(config_path)
            
    def _copy_default_secrets(self, secrets_path: Path):
        """Copy default secrets template."""
        try:
            import pkg_resources
            template_content = pkg_resources.resource_string(
                'ai_companion', '.secrets.template'
            ).decode('utf-8')
            
            with open(secrets_path, 'w') as f:
                f.write(template_content)
                
            logger.info(f"Created default secrets template at: {secrets_path}")
            logger.warning("Please edit the secrets file with your actual credentials!")
            
        except Exception as e:
            logger.warning(f"Could not copy default secrets: {e}")
            self._create_minimal_secrets(secrets_path)
            
    def _create_functional_default_config(self, config_path: Path):
        """Create functional default configuration with appropriate model settings."""
        # Import system detector to determine appropriate model sizes
        try:
            from .utils.system_detector import SystemDetector
            system_detector = SystemDetector()
            memory_gb = system_detector.system_info.get("total_memory_gb", 4)
            
            # Select appropriate models based on system capabilities
            if memory_gb >= 16:
                llm_model = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"  # Start with tiny for reliability
                stt_model = "large-v3"  # High quality for good systems
            elif memory_gb >= 8:
                llm_model = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
                stt_model = "medium"
            elif memory_gb >= 4:
                llm_model = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
                stt_model = "small"
            else:
                llm_model = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
                stt_model = "base"
        except:
            # Fallback if system detection fails
            llm_model = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
            stt_model = "base"
        
        # Create functional default configuration based on current config.yaml structure
        default_config = {
            'config_version': '1.0',
            'general': {
                'app_name': 'AI Companion',
                'app_version': '0.4.0',
                'debug_mode': False,
                'developer_mode': False,
                'logging_level': 'INFO',
                'logging_file': '~/.local/share/ai-companion/.cache/logs/app.log',
                'secrets_file': '~/.config/ai-companion/.secrets'
            },
            'server': {
                'host': '0.0.0.0',
                'port': 19447,
                'enable_ssl': False,
                'ssl_cert': '',
                'ssl_key': '',
                'cors_origins': ['*'],
                'max_request_size': '100MB',
                'timeout': 30,
                'proxy': {
                    'enabled': False,
                    'trust_x_forwarded_for': False,
                    'trust_x_forwarded_proto': False,
                    'behind_reverse_proxy': False,
                    'proxy_headers': ['X-Forwarded-For', 'X-Forwarded-Proto', 'X-Real-IP']
                }
            },
            'authentication': {
                'enabled': False,
                'session_timeout': 3600,
                'password_policy': {
                    'min_length': 8,
                    'require_uppercase': True,
                    'require_lowercase': True,
                    'require_numbers': True,
                    'require_special_chars': False
                },
                'user_database': {
                    'path': '~/.local/share/ai-companion/databases/users.db'
                },
                'session_storage': {
                    'type': 'file',
                    'path': '~/.local/share/ai-companion/.cache/sessions/'
                },
                'registration': {
                    'enabled': True,
                    'require_admin_approval': False,
                    'default_permissions': ['chat', 'voice', 'model_switch']
                }
            },
            'user_profiles': {
                'enabled': False,
                'allow_custom_avatars': True,
                'conversation_isolation': True,
                'profile_data': {
                    'collect_name': True,
                    'collect_age': False,
                    'collect_preferences': True,
                    'collect_avatar_settings': True
                },
                'data_retention': {
                    'conversation_history_days': 365,
                    'inactive_user_cleanup_days': 90,
                    'user_data_export': True
                }
            },
            'database': {
                'default_settings': {
                    'type': 'sqlite',
                    'pool_size': 5,
                    'timeout': 30
                },
                'paths': {
                    'ai_companion': str(self.database_dir / 'ai_companion.db'),
                    'conversations': str(self.database_dir / 'conversations.db'),
                    'live2d_models': str(self.database_dir / 'live2d.db'),
                    'personality': str(self.database_dir / 'personality.db'),
                    'system': str(self.database_dir / 'system.db'),
                    'users': str(self.database_dir / 'users.db'),
                    'user_profiles': str(self.database_dir / 'user_profiles.db'),
                    'user_sessions': str(self.database_dir / 'user_sessions.db')
                }
            },
            'integrated_models': {
                'llm': {
                    'model_name': llm_model,
                    'model_path': str(self.models_dir / 'llm' / 'TinyLlama-1.1B-Chat-v1.0-GGUF'),
                    'model_format': 'gguf',
                    'max_tokens': 4096,
                    'temperature': 0.7,
                    'top_p': 1.0
                },
                'tts': {
                    'model_name': 'onnx-community/Kokoro-82M-ONNX',
                    'model_path': str(self.models_dir / 'tts' / 'kokoro'),
                    'voice_path': str(self.models_dir / 'tts' / 'voices'),
                    'voice': 'af_heart',
                    'language': 'en-US'
                },
                'stt': {
                    'model_name': 'faster-whisper',
                    'model_path': str(self.models_dir / 'faster-whisper'),
                    'stt_model': stt_model,
                    'stt_language': 'en',
                    'stt_device': 'auto',
                    'stt_compute_type': 'float16',
                    'stt_cpu_threads': 0
                },
                'vad': {
                    'model_name': 'silero_vad',
                    'model_path': str(self.models_dir / 'silero_vad'),
                    'threshold': 0.5,
                    'silero_threshold': 0.5,
                    'silero_min_speech_duration_ms': 250,
                    'silero_max_speech_duration_s': 30,
                    'silero_min_silence_duration_ms': 100,
                    'silero_window_size_samples': 1536
                },
                'enhanced_vad': {
                    'enabled': True,
                    'vad_engine': 'hybrid',
                    'mode': 'lightweight',
                    'fallback_to_basic': True
                }
            },
            'audio_processing': {
                'sample_rate': 16000,
                'chunk_size': 1024,
                'min_speech_duration': 0.5,
                'max_speech_duration': 30.0,
                'audio_format': 'wav',
                'audio_output_path': str(self.cache_dir / 'audio_output/'),
                'audio_input_path': str(self.cache_dir / 'audio_input/'),
                'voice_detection': {
                    'cue_words': ['hello', 'help', 'avatar', 'ai']
                },
                'detection_threshold': 0.5,
                'detection_timeout': 5.0
            },
            'logging': {
                'enable_file_logging': True,
                'file_log_path': str(self.cache_dir / 'logs/app.log'),
                'file_log_level': 'DEBUG',
                'enable_console_logging': True,
                'console_log_level': 'INFO',
                'log_rotation': {
                    'enabled': True,
                    'max_size': '100MB',
                    'backup_count': 5
                },
                'structured_logging': True
            },
            'rag': {
                'enabled': False,
                'vector_database': {
                    'type': 'chroma',
                    'path': str(self.database_dir / 'vector_db'),
                    'collection_name': 'ai_companion_knowledge'
                },
                'embedding': {
                    'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
                    'model_path': str(self.models_dir / 'embeddings/all-MiniLM-L6-v2'),
                    'embedding_dim': 384,
                    'batch_size': 32
                }
            },
            'cross_avatar': {
                'enabled': False
            },
            'service': {
                'deployment_mode': 'pipx',
                'auto_start': False,
                'restart_policy': 'on-failure',
                'working_directory': str(self.data_dir),
                'environment_vars': {
                    'PYTHONPATH': str(self.data_dir),
                    'AI_COMPANION_CONFIG': str(self.config_dir / 'config.yaml')
                }
            },
            'avatar_settings': {
                'personality': {
                    'default': 'SFW',
                    'traits': {
                        'SFW': ['friendly', 'curious', 'playful', 'thoughtful', 'empathetic', 'creative', 'humorous']
                    }
                },
                'animation_speed': 1.0,
                'idle_animation': True,
                'idle_animation_interval': 5.0
            },
            'live2d_models': {
                'Epsilon': {
                    'active': True,
                    'nsfw': False,
                    'model_info': {
                        'path': str(self.live2d_models_dir / 'epsilon'),
                        'model_version': '4.0',
                        'model_type': 'Cubism',
                        'expression_method': 'seperated',
                        'motions': True,
                        'idle_animation': True
                    },
                    'avatar_name': 'Epsilon',
                    'traits': ['SFW', 'light', 'neutral']
                }
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2, width=120)
            
        logger.info(f"Created functional default config at: {config_path} with LLM: {llm_model}, STT: {stt_model}")
        
    def _create_functional_default_secrets(self, secrets_path: Path):
        """Create functional default secrets file with secure random values."""
        import secrets
        import string
        
        # Generate secure random keys
        secret_key = secrets.token_hex(32)
        jwt_secret = secrets.token_hex(32)
        db_encryption_key = secrets.token_hex(32)
        
        # Generate random admin password
        admin_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        functional_secrets = f"""# AI Companion Secrets Configuration
# This file contains sensitive tokens and credentials
# Do not commit this file to version control!

# =============================================================================
# API Keys and Tokens
# =============================================================================

# HuggingFace Token for accessing pyannote models
# Get your token from: https://huggingface.co/settings/tokens
# Required for pyannote/speaker-diarization-3.1 and pyannote/segmentation-3.0
HF_TOKEN=your_huggingface_token_here
HUGGINGFACE_TOKEN=your_huggingface_token_here

# OpenAI API Key (optional, for enhanced LLM capabilities)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Claude API Key (optional)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google Cloud API Key (optional, for TTS/STT services)
GOOGLE_CLOUD_API_KEY=your_google_cloud_api_key_here

# =============================================================================
# Security and Authentication (AUTO-GENERATED)
# =============================================================================

# Secret key for session encryption and JWT tokens (AUTO-GENERATED)
SECRET_KEY={secret_key}

# JWT Secret for user authentication tokens (AUTO-GENERATED)
JWT_SECRET={jwt_secret}

# Database encryption key (for sensitive user data) (AUTO-GENERATED)
DATABASE_ENCRYPTION_KEY={db_encryption_key}

# Admin user credentials (AUTO-GENERATED - CHANGE THESE!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD={admin_password}
ADMIN_EMAIL=admin@localhost

# =============================================================================
# External Services (Optional)
# =============================================================================

# Redis connection (if using Redis for session storage)
REDIS_URL=redis://localhost:6379/0

# PostgreSQL connection (if using PostgreSQL instead of SQLite)
DATABASE_URL=postgresql://user:password@localhost/ai_companion

# Email service configuration (for user notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
SMTP_USE_TLS=true

# =============================================================================
# Model and API Configurations
# =============================================================================

# Custom model API endpoints
CUSTOM_LLM_API_URL=http://localhost:8000/v1
CUSTOM_LLM_API_KEY=your_custom_api_key_here

# Voice cloning service API (if using external TTS)
VOICE_CLONING_API_KEY=your_voice_cloning_api_key_here

# =============================================================================
# IMPORTANT SECURITY NOTES
# =============================================================================

# 1. CHANGE THE AUTO-GENERATED ADMIN PASSWORD IMMEDIATELY!
# 2. Replace placeholder API keys with actual credentials as needed
# 3. For HuggingFace: Visit https://huggingface.co/settings/tokens
# 4. Keep this file secure and never commit it to version control
# 5. Set proper file permissions: chmod 600 ~/.config/ai-companion/.secrets
"""
        
        with open(secrets_path, 'w') as f:
            f.write(functional_secrets)
            
        # Set secure file permissions (readable only by owner)
        try:
            import stat
            secrets_path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600 permissions
        except:
            pass  # Ignore if chmod fails on Windows
            
        logger.info(f"Created functional default secrets at: {secrets_path}")
        logger.warning(f"AUTO-GENERATED ADMIN PASSWORD: {admin_password} - CHANGE THIS IMMEDIATELY!")
        
    def clean_install_databases(self):
        """Clean database installation - remove any existing databases for fresh start."""
        if not self.database_dir.exists():
            return
            
        # List of database files to clean
        db_files = [
            'ai_companion.db',
            'conversations.db', 
            'live2d.db',
            'personality.db',
            'system.db',
            'users.db',
            'user_profiles.db',
            'user_sessions.db'
        ]
        
        # Remove existing database files
        removed_files = []
        for db_file in db_files:
            db_path = self.database_dir / db_file
            if db_path.exists():
                try:
                    db_path.unlink()
                    removed_files.append(db_file)
                except Exception as e:
                    logger.warning(f"Could not remove {db_file}: {e}")
                    
        # Remove vector database directory
        vector_db_path = self.database_dir / 'vector_db'
        if vector_db_path.exists():
            try:
                import shutil
                shutil.rmtree(vector_db_path)
                removed_files.append('vector_db/')
            except Exception as e:
                logger.warning(f"Could not remove vector database: {e}")
                
        if removed_files:
            logger.info(f"Cleaned databases for fresh installation: {', '.join(removed_files)}")
        else:
            logger.info("No existing databases found - clean installation")
            
    def install_configuration_files(self, clean_databases: bool = True):
        """Install configuration files, optionally with clean database setup."""
        logger.info("Installing AI Companion configuration...")
        
        # Ensure directories exist
        self.ensure_directories()
        
        # Clean databases if requested
        if clean_databases:
            self.clean_install_databases()
            
        config_path = self.config_dir / 'config.yaml'
        secrets_path = self.config_dir / '.secrets'
        
        # Check if configuration files already exist
        config_exists = config_path.exists()
        secrets_exists = secrets_path.exists()
        
        if config_exists and secrets_exists:
            logger.info("Configuration files already exist - skipping installation")
            return True
            
        # Try to copy from repository first (if in development mode)
        if self.is_dev_mode:
            repo_config = Path(__file__).parent.parent / 'config.yaml'
            repo_secrets = Path(__file__).parent.parent / '.secrets.template'
            
            if not config_exists and repo_config.exists():
                try:
                    import shutil
                    shutil.copy2(repo_config, config_path)
                    logger.info(f"Copied development config to: {config_path}")
                except Exception as e:
                    logger.warning(f"Could not copy repo config: {e}")
                    config_exists = False
                    
            if not secrets_exists and repo_secrets.exists():
                try:
                    import shutil
                    shutil.copy2(repo_secrets, secrets_path)
                    logger.info(f"Copied development secrets template to: {secrets_path}")
                except Exception as e:
                    logger.warning(f"Could not copy repo secrets: {e}")
                    secrets_exists = False
        
        # Create functional defaults if copying failed or not in dev mode
        if not config_exists:
            self._create_functional_default_config(config_path)
            
        if not secrets_exists:
            self._create_functional_default_secrets(secrets_path)
            
        logger.info("AI Companion configuration installation complete!")
        return True
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        config_path = self.get_config_path()
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Update paths in config to use proper directories
            if not self.is_dev_mode:
                self._update_config_paths(config)
                
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            return self._get_default_config()
            
    def _update_config_paths(self, config: Dict[str, Any]):
        """Update configuration paths for production mode."""
        # Update integrated models paths
        if 'integrated_models' in config:
            if 'llm' in config['integrated_models']:
                config['integrated_models']['llm']['model_path'] = str(self.models_dir / 'llm')
            if 'tts' in config['integrated_models']:
                config['integrated_models']['tts']['model_path'] = str(self.models_dir / 'tts' / 'kokoro')
                config['integrated_models']['tts']['voice_path'] = str(self.models_dir / 'tts' / 'voices')
            if 'stt' in config['integrated_models']:
                config['integrated_models']['stt']['model_path'] = str(self.models_dir / 'faster-whisper')
            if 'vad' in config['integrated_models']:
                config['integrated_models']['vad']['model_path'] = str(self.models_dir / 'silero_vad')
            if 'pyannote_segmentation' in config['integrated_models']:
                config['integrated_models']['pyannote_segmentation']['model_path'] = str(self.models_dir / 'pyannote' / 'segmentation-3.0')
            if 'pyannote_diarization' in config['integrated_models']:
                config['integrated_models']['pyannote_diarization']['model_path'] = str(self.models_dir / 'pyannote' / 'speaker-diarization-3.1')
                
        # Update database paths
        if 'database' in config and 'paths' in config['database']:
            for db_name in config['database']['paths']:
                config['database']['paths'][db_name] = str(self.database_dir / f'{db_name}.db')
                
        # Update Live2D models paths
        if 'live2d_models' in config:
            for model_name, model_config in config['live2d_models'].items():
                if isinstance(model_config, dict) and 'model_info' in model_config and 'path' in model_config['model_info']:
                    model_config['model_info']['path'] = str(self.live2d_models_dir / model_name.lower())
                    
        # Update RAG paths
        if 'rag' in config:
            if 'vector_database' in config['rag'] and 'path' in config['rag']['vector_database']:
                config['rag']['vector_database']['path'] = str(self.database_dir / 'vector_db')
            if 'embedding' in config['rag'] and 'model_path' in config['rag']['embedding']:
                config['rag']['embedding']['model_path'] = str(self.models_dir / 'embeddings')
                
        # Update audio processing paths
        if 'audio_processing' in config:
            if 'audio_output_path' in config['audio_processing']:
                config['audio_processing']['audio_output_path'] = str(self.cache_dir / 'audio_output')
            if 'audio_input_path' in config['audio_processing']:
                config['audio_processing']['audio_input_path'] = str(self.cache_dir / 'audio_input')
                
        # Update logging paths
        if 'logging' in config:
            if 'file_log_path' in config['logging']:
                config['logging']['file_log_path'] = str(self.cache_dir / 'logs' / 'app.log')
        if 'general' in config and 'logging_file' in config['general']:
            config['general']['logging_file'] = str(self.cache_dir / 'logs' / 'app.log')
            
        # Update service configuration
        if 'service' in config:
            if 'working_directory' in config['service']:
                config['service']['working_directory'] = str(self.data_dir)
            if 'environment_vars' in config['service']:
                if 'AI_COMPANION_CONFIG' in config['service']['environment_vars']:
                    config['service']['environment_vars']['AI_COMPANION_CONFIG'] = str(self.config_dir / 'config.yaml')
                    
        # Update authentication paths
        if 'authentication' in config:
            if 'user_database' in config['authentication'] and 'path' in config['authentication']['user_database']:
                config['authentication']['user_database']['path'] = str(self.database_dir / 'users.db')
            if 'session_storage' in config['authentication'] and 'path' in config['authentication']['session_storage']:
                config['authentication']['session_storage']['path'] = str(self.get_sessions_path())
                
        # Update general settings
        if 'general' in config and 'secrets_file' in config['general']:
            config['general']['secrets_file'] = str(self.get_secrets_path())
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'server': {
                'host': '0.0.0.0',
                'port': 19443,
                'debug': False
            },
            'live2d': {
                'models_path': str(self.live2d_models_dir),
                'default_model': 'Hiyori'
            },
            'ai': {
                'models_path': str(self.models_dir),
                'cache_path': str(self.cache_dir)
            },
            'database': {
                'path': str(self.database_dir)
            }
        }
        
    def load_secrets(self) -> Dict[str, str]:
        """Load secrets from file."""
        secrets_path = self.get_secrets_path()
        secrets = {}
        
        try:
            with open(secrets_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        secrets[key.strip()] = value.strip()
                        
            return secrets
            
        except Exception as e:
            logger.warning(f"Failed to load secrets from {secrets_path}: {e}")
            return {}
            
    def get_info(self) -> Dict[str, Any]:
        """Get configuration manager info."""
        return {
            'mode': 'development' if self.is_dev_mode else 'production',
            'config_dir': str(self.config_dir),
            'data_dir': str(self.data_dir),
            'cache_dir': str(self.cache_dir),
            'database_dir': str(self.database_dir),
            'models_dir': str(self.models_dir),
            'live2d_models_dir': str(self.live2d_models_dir),
        }


# Global instance
config_manager = ConfigManager()

# Convenience functions
def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    return config_manager

def get_config() -> Dict[str, Any]:
    """Get the application configuration."""
    return config_manager.load_config()

def get_secrets() -> Dict[str, str]:
    """Get the application secrets."""
    return config_manager.load_secrets()

def get_database_path(db_name: str) -> Path:
    """Get path to a database file."""
    return config_manager.get_database_path(db_name)

def get_models_path(model_type: str = '') -> Path:
    """Get path to models directory."""
    return config_manager.get_models_path(model_type)

def get_live2d_models_path(model_name: str = '') -> Path:
    """Get path to Live2D models directory."""
    return config_manager.get_live2d_models_path(model_name)

def get_cache_path(cache_type: str = '') -> Path:
    """Get path to cache directory."""
    return config_manager.get_cache_path(cache_type)

def get_rag_config() -> Dict[str, Any]:
    """Get RAG configuration."""
    config = config_manager.load_config()
    return config.get('rag', {})

def get_cross_avatar_config() -> Dict[str, Any]:
    """Get cross-avatar interaction configuration."""
    config = config_manager.load_config()
    return config.get('cross_avatar', {})

def get_service_config() -> Dict[str, Any]:
    """Get service configuration."""
    config = config_manager.load_config()
    return config.get('service', {})

def is_rag_enabled() -> bool:
    """Check if RAG is enabled."""
    rag_config = get_rag_config()
    return rag_config.get('enabled', False)

def is_cross_avatar_enabled() -> bool:
    """Check if cross-avatar interactions are enabled."""
    cross_avatar_config = get_cross_avatar_config()
    return cross_avatar_config.get('enabled', False)

def get_authentication_config() -> Dict[str, Any]:
    """Get authentication configuration."""
    config = config_manager.load_config()
    return config.get('authentication', {})

def get_user_profiles_config() -> Dict[str, Any]:
    """Get user profiles configuration."""
    config = config_manager.load_config()
    return config.get('user_profiles', {})

def get_server_config() -> Dict[str, Any]:
    """Get server configuration including network settings."""
    config = config_manager.load_config()
    return config.get('server', {})

def is_authentication_enabled() -> bool:
    """Check if user authentication is enabled."""
    auth_config = get_authentication_config()
    return auth_config.get('enabled', False)

def is_user_profiles_enabled() -> bool:
    """Check if user profiles are enabled."""
    profiles_config = get_user_profiles_config()
    return profiles_config.get('enabled', False)

def get_sessions_path() -> Path:
    """Get path to sessions directory."""
    return config_manager.get_sessions_path()
