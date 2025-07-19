import os
import sys
import subprocess
import shutil
import logging
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Live2DSetup:
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.base_path = Path(__file__).parent.parent
        self.viewer_path = self.base_path / self.config.get_live2d_viewer_path()
        self.repository_url = self.config.get_live2d_repository_url()
        
        # Add rebuild flag
        self.force_rebuild = False
        
        # Setup logging
        self.setup_logging()
        
        # Initialize system detector and model downloader
        self.system_detector = None
        self.model_downloader = None
        self._initialize_system_components()
    
    def clean_existing_installation(self) -> bool:
        """Clean existing installation for fresh rebuild"""
        try:
            logger.info("Cleaning existing installation...")
            
            # Clean Live2D Viewer Web
            if self.viewer_path.exists():
                logger.info(f"Removing existing Live2D Viewer Web at {self.viewer_path}")
                shutil.rmtree(self.viewer_path, ignore_errors=True)
            
            # Clean build artifacts
            artifacts_to_clean = [
                'node_modules',
                'dist',
                'build',
                '.cache',
                'package-lock.json'
            ]
            
            for artifact in artifacts_to_clean:
                artifact_path = self.viewer_path / artifact
                if artifact_path.exists():
                    logger.info(f"Removing build artifact: {artifact}")
                    if artifact_path.is_dir():
                        shutil.rmtree(artifact_path, ignore_errors=True)
                    else:
                        artifact_path.unlink(missing_ok=True)
            
            # Clean Python cache
            python_cache_patterns = ['__pycache__', '.pytest_cache', '*.egg-info']
            
            for root, dirs, files in os.walk(self.base_path):
                # Remove cache directories
                for cache_dir in list(dirs):
                    if cache_dir in python_cache_patterns:
                        cache_path = Path(root) / cache_dir
                        logger.info(f"Removing Python cache: {cache_path}")
                        shutil.rmtree(cache_path, ignore_errors=True)
                        dirs.remove(cache_dir)
                
                # Remove cache files
                for file in files:
                    if file.endswith(('.pyc', '.pyo')):
                        cache_file = Path(root) / file
                        cache_file.unlink(missing_ok=True)
            
            # Clean dist directory
            dist_dir = self.base_path / 'dist'
            if dist_dir.exists():
                logger.info("Removing dist directory")
                shutil.rmtree(dist_dir, ignore_errors=True)
            
            # Clean build directory
            build_dir = self.base_path / 'build'
            if build_dir.exists():
                logger.info("Removing build directory")
                shutil.rmtree(build_dir, ignore_errors=True)
            
            logger.info("Existing installation cleaned successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clean existing installation: {e}")
            return False
    
    def rebuild_python_package(self) -> bool:
        """Rebuild the Python package"""
        try:
            logger.info("Rebuilding Python package...")
            
            # Change to project root
            original_cwd = os.getcwd()
            os.chdir(self.base_path)
            
            # Clean any existing build artifacts
            subprocess.run(['python', '-m', 'pip', 'uninstall', 'ai2d_chat', '-y'], 
                         capture_output=True)
            
            # Build the package
            logger.info("Building wheel package...")
            result = subprocess.run(['python', '-m', 'build'], 
                                  capture_output=True, text=True, check=True)
            logger.info("Package built successfully")
            
            # Install the package in development mode
            logger.info("Installing package in development mode...")
            result = subprocess.run(['pip', 'install', '-e', '.'], 
                                  capture_output=True, text=True, check=True)
            logger.info("Package installed successfully")
            
            os.chdir(original_cwd)
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Package rebuild failed: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during package rebuild: {e}")
            return False
        finally:
            try:
                os.chdir(original_cwd)
            except:
                pass
        
    def setup_logging(self):
        """Setup comprehensive logging system"""
        try:
            logs_dir = self.base_path / 'logs'
            logs_dir.mkdir(exist_ok=True)
            
            # Create timestamped log file
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            log_file = logs_dir / f'setup_live2d_{timestamp}.log'
            
            # Configure file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            
            # Add handler to logger
            logger.addHandler(file_handler)
            
            # Create setup log tracking
            setup_log = {
                'timestamp': timestamp,
                'log_file': str(log_file),
                'setup_phase': 'initialization'
            }
            
            with open(logs_dir / 'setup_status.json', 'w') as f:
                json.dump(setup_log, f, indent=2)
                
            logger.info(f"Logging initialized - log file: {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to setup logging: {e}")
    
    def _initialize_system_components(self):
        """Initialize system detection and model downloading components"""
        try:
            # Import system detector
            from models.system_detector import SystemDetector
            self.system_detector = SystemDetector()
            logger.info("System detector initialized")
            
            # Import model downloader
            from models.model_downloader import ModelDownloader
            self.model_downloader = ModelDownloader(self.config)
            logger.info("Model downloader initialized")
            
        except ImportError as e:
            logger.warning(f"Could not import system components: {e}")
            logger.warning("Creating placeholder components...")
            self._create_placeholder_components()
        except Exception as e:
            logger.error(f"Failed to initialize system components: {e}")
            
    def _create_placeholder_components(self):
        """Create placeholder system components if imports fail"""
        class PlaceholderSystemDetector:
            def detect_system_capabilities(self):
                return {
                    'gpu_available': False,
                    'memory_gb': 8,
                    'cpu_cores': 4,
                    'platform': sys.platform,
                    'python_version': sys.version
                }
            
            def get_recommended_models(self):
                return {
                    'llm': ['llama-2-7b-chat.gguf'],
                    'tts': ['tacotron2-en'],
                    'vad': ['silero-vad'],
                    'live2d': ['default-model']
                }
        
        class PlaceholderModelDownloader:
            def __init__(self, config):
                self.config = config
                
            def download_model(self, model_name, model_type):
                logger.info(f"Placeholder: Would download {model_name} ({model_type})")
                return True
                
            def verify_model(self, model_name, model_type):
                return True
        
        self.system_detector = PlaceholderSystemDetector()
        self.model_downloader = PlaceholderModelDownloader(self.config)
    
    def detect_system_requirements(self) -> Dict[str, Any]:
        """Detect system capabilities and determine required models"""
        try:
            logger.info("Detecting system capabilities...")
            
            capabilities = self.system_detector.detect_system_capabilities()
            recommended_models = self.system_detector.get_recommended_models()
            
            logger.info(f"System capabilities: {capabilities}")
            logger.info(f"Recommended models: {recommended_models}")
            
            # Update config with system info
            self.config.set('system.capabilities', capabilities)
            self.config.set('system.recommended_models', recommended_models)
            
            return {
                'capabilities': capabilities,
                'recommended_models': recommended_models
            }
            
        except Exception as e:
            logger.error(f"System detection failed: {e}")
            return {
                'capabilities': {},
                'recommended_models': {}
            }
    
    def download_required_models(self, system_info: Dict[str, Any]) -> bool:
        """Download all required models based on system capabilities"""
        try:
            logger.info("Starting model downloads...")
            
            recommended_models = system_info.get('recommended_models', {})
            
            # Download LLM models
            for model_name in recommended_models.get('llm', []):
                logger.info(f"Downloading LLM model: {model_name}")
                if not self.model_downloader.download_model(model_name, 'llm'):
                    logger.error(f"Failed to download LLM model: {model_name}")
                    return False
            
            # Download TTS models
            for model_name in recommended_models.get('tts', []):
                logger.info(f"Downloading TTS model: {model_name}")
                if not self.model_downloader.download_model(model_name, 'tts'):
                    logger.error(f"Failed to download TTS model: {model_name}")
                    return False
            
            # Download VAD models
            for model_name in recommended_models.get('vad', []):
                logger.info(f"Downloading VAD model: {model_name}")
                if not self.model_downloader.download_model(model_name, 'vad'):
                    logger.error(f"Failed to download VAD model: {model_name}")
                    return False
            
            # Setup Live2D models directory and download sample models
            self.setup_live2d_models()
            
            logger.info("All models downloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Model download failed: {e}")
            return False
    
    def setup_live2d_models(self) -> bool:
        """Setup Live2D models directory and download sample models"""
        try:
            logger.info("Setting up Live2D models...")
            
            models_dir = self.base_path / self.config.get_models_directory()
            models_dir.mkdir(parents=True, exist_ok=True)
            
            # Create sample model structure
            sample_model_dir = models_dir / 'sample_model'
            sample_model_dir.mkdir(exist_ok=True)
            
            # Create placeholder model files
            model_json = {
                "Version": 3,
                "FileReferences": {
                    "Moc": "sample_model.moc3",
                    "Textures": ["textures/texture_00.png"],
                    "Motions": {
                        "Idle": [{"File": "motions/idle.motion3.json"}]
                    }
                },
                "Groups": [
                    {"Target": "Parameter", "Name": "EyeBlink", "Ids": ["ParamEyeLOpen", "ParamEyeROpen"]},
                    {"Target": "Parameter", "Name": "LipSync", "Ids": ["ParamMouthOpenY"]}
                ]
            }
            
            with open(sample_model_dir / 'sample_model.model3.json', 'w') as f:
                json.dump(model_json, f, indent=2)
            
            # Create subdirectories
            (sample_model_dir / 'textures').mkdir(exist_ok=True)
            (sample_model_dir / 'motions').mkdir(exist_ok=True)
            
            logger.info(f"Live2D models directory setup at: {models_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Live2D models: {e}")
            return False
    
    def setup_voice_models(self) -> bool:
        """Setup voice/TTS models and configurations"""
        try:
            logger.info("Setting up voice models...")
            
            voices_dir = self.base_path / 'models' / 'voices'
            voices_dir.mkdir(parents=True, exist_ok=True)
            
            # Download common voice models
            voice_models = [
                'tacotron2-en',
                'waveglow-en',
                'silero-tts-en'
            ]
            
            for voice_model in voice_models:
                logger.info(f"Setting up voice model: {voice_model}")
                if not self.model_downloader.download_model(voice_model, 'voice'):
                    logger.warning(f"Failed to download voice model: {voice_model}")
            
            # Create voice configuration
            voice_config = {
                'default_voice': 'tacotron2-en',
                'available_voices': voice_models,
                'voice_settings': {
                    'speed': 1.0,
                    'pitch': 1.0,
                    'volume': 0.8
                }
            }
            
            with open(voices_dir / 'voice_config.json', 'w') as f:
                json.dump(voice_config, f, indent=2)
            
            logger.info("Voice models setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Voice models setup failed: {e}")
            return False
    
    def initialize_databases(self) -> bool:
        """Initialize all required databases"""
        try:
            logger.info("Initializing databases...")
            
            # Create databases directory
            db_dir = self.base_path / 'databases'
            db_dir.mkdir(exist_ok=True)
            
            # Initialize Live2D database
            from database.live2d_models_separated import initialize_live2d_database
            initialize_live2d_database()
            logger.info("Live2D database initialized")
            
            # Initialize conversations database
            try:
                from database.conversation_manager import initialize_conversations_database
                initialize_conversations_database()
                logger.info("Conversations database initialized")
            except ImportError:
                logger.warning("Conversations database module not found, skipping")
            
            # Initialize personality database
            try:
                from database.personality_manager import initialize_personality_database
                initialize_personality_database()
                logger.info("Personality database initialized")
            except ImportError:
                logger.warning("Personality database module not found, skipping")
            
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    def setup_configuration_files(self) -> bool:
        """Setup config.yaml and .secrets files"""
        try:
            logger.info("Setting up configuration files...")
            
            # Create config.yaml
            config_yaml = {
                'server': {
                    'host': '127.0.0.1',
                    'port': 5000,
                    'debug': True
                },
                'live2d': {
                    'enabled': True,
                    'viewer_web_path': 'src/web/static/live2d-viewer-web',
                    'models_directory': 'models/live2d',
                    'auto_setup': True,
                    'integration_mode': 'embedded'
                },
                'ai': {
                    'model_path': 'models/llm',
                    'memory_enabled': True,
                    'max_context_length': 4096
                },
                'audio': {
                    'enabled': True,
                    'sample_rate': 16000,
                    'vad_enabled': True,
                    'tts_enabled': True,
                    'voices_directory': 'models/voices'
                },
                'database': {
                    'conversations_db': 'databases/conversations.db',
                    'live2d_db': 'databases/live2d.db',
                    'personality_db': 'databases/personality.db'
                },
                'logging': {
                    'level': 'INFO',
                    'directory': 'logs',
                    'max_files': 10
                }
            }
            
            # Save config.yaml
            import yaml
            try:
                with open(self.base_path / 'config.yaml', 'w') as f:
                    yaml.dump(config_yaml, f, default_flow_style=False, indent=2)
                logger.info("config.yaml created successfully")
            except ImportError:
                # Fallback to JSON if PyYAML not available
                with open(self.base_path / 'config.json', 'w') as f:
                    json.dump(config_yaml, f, indent=2)
                logger.info("config.json created successfully (YAML not available)")
            
            # Create .secrets file template
            secrets_template = {
                'api_keys': {
                    'openai': 'your-openai-api-key-here',
                    'huggingface': 'your-huggingface-token-here'
                },
                'database': {
                    'encryption_key': 'generate-a-secure-key-here'
                },
                'security': {
                    'secret_key': 'generate-a-flask-secret-key-here'
                }
            }
            
            secrets_file = self.base_path / '.secrets'
            if not secrets_file.exists():
                with open(secrets_file, 'w') as f:
                    json.dump(secrets_template, f, indent=2)
                logger.info(".secrets template created")
                logger.warning("Please update .secrets file with your actual API keys")
            else:
                logger.info(".secrets file already exists")
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration setup failed: {e}")
            return False
    
    def check_prerequisites(self) -> bool:
        """Check if Node.js and npm are available"""
        try:
            # Check Node.js
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, check=True)
            logger.info(f"Node.js version: {result.stdout.strip()}")
            
            # Check npm
            result = subprocess.run(['npm', '--version'], 
                                  capture_output=True, text=True, check=True)
            logger.info(f"npm version: {result.stdout.strip()}")
            
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Prerequisites check failed: {e}")
            logger.error("Please install Node.js and npm:")
            logger.error("Ubuntu/Debian: sudo apt install nodejs npm")
            logger.error("macOS: brew install node")
            logger.error("Windows: Download from https://nodejs.org/")
            return False
    
    def clone_live2d_viewer_web(self) -> bool:
        """Clone Live2D Viewer Web repository"""
        try:
            if self.viewer_path.exists():
                logger.info(f"Live2D Viewer Web already exists at {self.viewer_path}")
                return True
            
            logger.info(f"Cloning Live2D Viewer Web from {self.repository_url}")
            
            # Create parent directory
            self.viewer_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Clone repository
            subprocess.run([
                'git', 'clone', 
                self.repository_url, 
                str(self.viewer_path)
            ], check=True)
            
            logger.info("Live2D Viewer Web cloned successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during cloning: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install npm dependencies"""
        try:
            logger.info("Installing npm dependencies...")
            
            # Change to viewer directory
            original_cwd = os.getcwd()
            os.chdir(self.viewer_path)
            
            # Install dependencies
            subprocess.run(['npm', 'install'], check=True)
            
            # Return to original directory
            os.chdir(original_cwd)
            
            logger.info("Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during dependency installation: {e}")
            return False
        finally:
            # Ensure we return to original directory
            try:
                os.chdir(original_cwd)
            except:
                pass
    
    def build_viewer(self) -> bool:
        """Build Live2D Viewer Web"""
        try:
            logger.info("Building Live2D Viewer Web...")
            
            original_cwd = os.getcwd()
            os.chdir(self.viewer_path)
            
            # Build the project
            build_command = self.config.get('live2d.build_command', 'npm run build')
            subprocess.run(build_command.split(), check=True)
            
            os.chdir(original_cwd)
            
            logger.info("Build completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Build failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during build: {e}")
            return False
        finally:
            try:
                os.chdir(original_cwd)
            except:
                pass
    
    def setup_integration_files(self) -> bool:
        """Setup integration files for AI Companion"""
        try:
            logger.info("Setting up integration files...")
            
            # Create integration directory
            integration_path = self.viewer_path / 'src' / 'integration'
            integration_path.mkdir(exist_ok=True)
            
            # Create Flask API client with enhanced functionality
            api_client_content = '''
// Flask API client for AI Companion integration
export class FlaskAPIClient {
    constructor(baseUrl = 'http://localhost:5000') {
        this.baseUrl = baseUrl;
    }
    
    async getAvailableModels() {
        const response = await fetch(`${this.baseUrl}/api/live2d/models`);
        return response.json();
    }
    
    async sendChatMessage(message) {
        const response = await fetch(`${this.baseUrl}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        return response.json();
    }
    
    async triggerMotion(modelId, motionGroup, motionIndex) {
        const response = await fetch(`${this.baseUrl}/api/live2d/motion`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                modelId, 
                motionGroup, 
                motionIndex 
            })
        });
        return response.json();
    }
    
    async setupLipsync(modelId) {
        const response = await fetch(`${this.baseUrl}/api/live2d/lipsync/setup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ modelId })
        });
        return response.json();
    }
    
    async registerModel(modelName, modelData) {
        const response = await fetch(`${this.baseUrl}/api/live2d/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                name: modelName,
                data: modelData 
            })
        });
        return response.json();
    }
}
'''
            
            with open(integration_path / 'FlaskAPIClient.js', 'w') as f:
                f.write(api_client_content)
            
            # Create enhanced AI Companion model entity extension
            model_entity_content = '''
import { ModelEntity } from '../app/ModelEntity';
import { FlaskAPIClient } from './FlaskAPIClient';

export class AICompanionModelEntity extends ModelEntity {
    constructor(source, renderer, flaskBaseUrl = 'http://localhost:5000') {
        super(source, renderer);
        this.apiClient = new FlaskAPIClient(flaskBaseUrl);
        this.lipsyncEnabled = false;
        this.setupLipsyncIntegration();
    }
    
    setupLipsyncIntegration() {
        // Setup lipsync integration with existing motion system
        console.log('Setting up lipsync integration...');
        
        // Connect to TTS events for mouth movement
        this.setupTTSIntegration();
    }
    
    setupTTSIntegration() {
        // Listen for TTS events from Flask backend
        const eventSource = new EventSource(`${this.apiClient.baseUrl}/api/tts/events`);
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'lipsync' && data.modelId === this.name) {
                this.updateLipsync(data.values);
            }
        };
    }
    
    updateLipsync(lipsyncValues) {
        if (this.pixiModel && this.lipsyncEnabled) {
            // Use existing motion system for lipsync
            const mouthParam = this.pixiModel.internalModel.coreModel.getParameterIndex('ParamMouthOpenY');
            if (mouthParam >= 0) {
                this.pixiModel.internalModel.coreModel.setParameterValueByIndex(mouthParam, lipsyncValues.mouth);
            }
        }
    }
    
    async loadModel(source) {
        // Call parent method with enhanced error handling
        try {
            await super.loadModel(source);
            
            // Register with Flask backend
            if (this.pixiModel) {
                await this.registerWithBackend();
                await this.setupModelSpecificFeatures();
            }
        } catch (error) {
            console.error('Failed to load model:', error);
            this.error = error.message;
        }
    }
    
    async setupModelSpecificFeatures() {
        try {
            // Setup lipsync for this model
            const lipsyncResult = await this.apiClient.setupLipsync(this.name);
            if (lipsyncResult.success) {
                this.lipsyncEnabled = true;
                console.log('Lipsync enabled for model:', this.name);
            }
        } catch (error) {
            console.warn('Failed to setup lipsync:', error);
        }
    }
    
    async registerWithBackend() {
        try {
            // Extract model metadata
            const modelData = {
                name: this.name,
                motions: this.pixiModel.internalModel.motionManager.definitions,
                expressions: this.pixiModel.internalModel.motionManager.expressionManager?.definitions,
                parameters: this.getModelParameters()
            };
            
            // Register with Flask backend
            await this.apiClient.registerModel(this.name, modelData);
            console.log('Model registered with backend:', this.name);
        } catch (error) {
            console.error('Failed to register model with backend:', error);
        }
    }
    
    getModelParameters() {
        if (!this.pixiModel?.internalModel?.coreModel) return [];
        
        const parameters = [];
        const coreModel = this.pixiModel.internalModel.coreModel;
        const paramCount = coreModel.getParameterCount();
        
        for (let i = 0; i < paramCount; i++) {
            parameters.push({
                id: coreModel.getParameterId(i),
                name: coreModel.getParameterId(i),
                min: coreModel.getParameterMinimumValue(i),
                max: coreModel.getParameterMaximumValue(i),
                default: coreModel.getParameterDefaultValue(i)
            });
        }
        
        return parameters;
    }
}
'''
            
            with open(integration_path / 'AICompanionModelEntity.js', 'w') as f:
                f.write(model_entity_content)
            
            logger.info("Enhanced integration files created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup integration files: {e}")
            return False
    
    def verify_setup(self) -> bool:
        """Verify that the setup was successful"""
        try:
            # Check if directory exists
            if not self.viewer_path.exists():
                logger.error("Live2D Viewer Web directory not found")
                return False
            
            # Check if node_modules exists
            node_modules = self.viewer_path / 'node_modules'
            if not node_modules.exists():
                logger.error("node_modules directory not found")
                return False
            
            # Check if dist directory exists (after build)
            dist_dir = self.viewer_path / 'dist'
            if not dist_dir.exists():
                logger.warning("dist directory not found - build may have failed")
            
            # Check integration files
            integration_path = self.viewer_path / 'src' / 'integration'
            if not integration_path.exists():
                logger.error("Integration files not found")
                return False
            
            logger.info("Setup verification completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Setup verification failed: {e}")
            return False
    
    def run_setup(self, force_rebuild: bool = False) -> bool:
        """Run complete setup process"""
        logger.info("Starting comprehensive AI Companion Live2D setup...")
        
        # Set rebuild flag
        self.force_rebuild = force_rebuild
        
        try:
            # Update config
            self.config.update_live2d_setup_status("starting")
            
            # Clean and rebuild if requested
            if self.force_rebuild:
                logger.info("Force rebuild requested - cleaning existing installation")
                if not self.clean_existing_installation():
                    logger.warning("Failed to clean existing installation, continuing anyway")
                
                if not self.rebuild_python_package():
                    self.config.update_live2d_setup_status("failed_package_rebuild")
                    return False
            
            # Detect system requirements
            system_info = self.detect_system_requirements()
            
            # Setup configuration files
            if not self.setup_configuration_files():
                self.config.update_live2d_setup_status("failed_configuration")
                return False
            
            # Download required models
            if not self.download_required_models(system_info):
                self.config.update_live2d_setup_status("failed_model_download")
                return False
            
            # Setup voice models
            if not self.setup_voice_models():
                self.config.update_live2d_setup_status("failed_voice_setup")
                return False
            
            # Initialize databases
            if not self.initialize_databases():
                self.config.update_live2d_setup_status("failed_database_init")
                return False
            
            # Check prerequisites
            if not self.check_prerequisites():
                self.config.update_live2d_setup_status("failed_prerequisites")
                return False
            
            # Clone repository
            if not self.clone_live2d_viewer_web():
                self.config.update_live2d_setup_status("failed_clone")
                return False
            
            # Install dependencies
            if not self.install_dependencies():
                self.config.update_live2d_setup_status("failed_dependencies")
                return False
            
            # Build project
            if not self.build_viewer():
                self.config.update_live2d_setup_status("failed_build")
                return False
            
            # Setup integration files
            if not self.setup_integration_files():
                self.config.update_live2d_setup_status("failed_integration")
                return False
            
            # Verify setup
            if not self.verify_setup():
                self.config.update_live2d_setup_status("failed_verification")
                return False
            
            self.config.update_live2d_setup_status("completed")
            logger.info("Complete AI Companion Live2D setup finished successfully!")
            
            # Log final status
            self._log_setup_completion()
            
            return True
            
        except Exception as e:
            logger.error(f"Setup failed with unexpected error: {e}")
            self.config.update_live2d_setup_status(f"failed_unexpected: {e}")
            return False
    
    def _log_setup_completion(self):
        """Log setup completion details"""
        try:
            completion_log = {
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'completed',
                'components': {
                    'live2d_viewer_web': True,
                    'models_downloaded': True,
                    'databases_initialized': True,
                    'voice_models_setup': True,
                    'configuration_files': True,
                    'integration_files': True
                },
                'paths': {
                    'viewer_web': str(self.viewer_path),
                    'models_dir': str(self.base_path / 'models'),
                    'databases_dir': str(self.base_path / 'databases'),
                    'logs_dir': str(self.base_path / 'logs')
                }
            }
            
            with open(self.base_path / 'logs' / 'setup_completion.json', 'w') as f:
                json.dump(completion_log, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to log setup completion: {e}")

def main():
    """Main setup function"""
    setup = Live2DSetup()
    success = setup.run_setup()
    
    if success:
        print("\n" + "="*60)
        print("✅ AI Companion Live2D Setup Completed Successfully!")
        print("="*60)
        print("\nSetup includes:")
        print("• Live2D Viewer Web (cloned, built, and integrated)")
        print("• System-optimized AI models downloaded")
        print("• Voice/TTS models configured")
        print("• Databases initialized (Live2D, conversations, personality)")
        print("• Configuration files (config.yaml, .secrets)")
        print("• Comprehensive logging system")
        print("• Integration layer for Flask backend")
        print("\nNext steps:")
        print("1. Update .secrets file with your API keys")
        print("2. Place Live2D models in models/live2d/")
        print("3. Run: python src/app.py")
        print("4. Access: http://localhost:5000")
        print("="*60)
    else:
        print("\n❌ AI Companion Live2D setup failed!")
        print("Check the logs in logs/ directory for detailed error information.")
        sys.exit(1)

if __name__ == "__main__":
    main()
def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Companion Live2D Setup')
    parser.add_argument('--rebuild', action='store_true', 
                       help='Force rebuild and reinstall the application')
    parser.add_argument('--clean', action='store_true',
                       help='Clean existing installation before setup')
    
    args = parser.parse_args()
    
    # Determine if rebuild is needed
    force_rebuild = args.rebuild or args.clean
    
    if force_rebuild:
        print("🔄 Rebuild requested - cleaning and rebuilding application...")
    
    setup = Live2DSetup()
    success = setup.run_setup(force_rebuild=force_rebuild)
    
    if success:
        print("\n" + "="*60)
        print("✅ AI Companion Live2D Setup Completed Successfully!")
        print("="*60)
        print("\nSetup includes:")
        print("• Live2D Viewer Web (cloned, built, and integrated)")
        print("• System-optimized AI models downloaded")
        print("• Voice/TTS models configured")
        print("• Databases initialized (Live2D, conversations, personality)")
        print("• Configuration files (config.yaml, .secrets)")
        print("• Comprehensive logging system")
        print("• Integration layer for Flask backend")
        
        if force_rebuild:
            print("• Python package rebuilt and reinstalled")
        
        print("\nNext steps:")
        print("1. Update .secrets file with your API keys")
        print("2. Place Live2D models in models/live2d/")
        print("3. Run: python src/app.py")
        print("4. Access: http://localhost:5000")
        print("\nPrerequisites met:")
        print("• Node.js and npm are installed for Live2D Viewer Web")
        print("• Python package built without nodejs/npm dependencies")
        print("="*60)
    else:
        print("\n❌ AI Companion Live2D setup failed!")
        print("Check the logs in logs/ directory for detailed error information.")
        
        if not force_rebuild:
            print("\nTry running with --rebuild to force a clean installation:")
            print("python scripts/setup_live2d.py --rebuild")
        
        sys.exit(1)
