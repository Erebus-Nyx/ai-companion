"""
OpenAPI 3.0.3 specification for AI Companion API
Separated for better maintainability and organization
"""

from datetime import datetime
from typing import Dict, Any

def get_openapi_spec() -> Dict[str, Any]:
    """Generate OpenAPI 3.0.3 specification for AI Companion API"""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "AI Companion API",
            "description": "Comprehensive AI Companion API with Live2D, LLM, and TTS integration. Enhanced with dynamic motion system and emotional responses.",
            "version": "2.1.0",
            "contact": {
                "name": "AI Companion Support",
                "url": "https://github.com/ai2d_chat/api"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "http://localhost:13443",
                "description": "Development server"
            },
            {
                "url": "http://127.0.0.1:13443", 
                "description": "Local development server"
            }
        ],
        "tags": [
            {
                "name": "system",
                "description": "Core system functionality including audio processing, memory management, and status monitoring"
            },
            {
                "name": "live2d", 
                "description": "Live2D model management, motion detection, and animation control with dynamic database integration"
            },
            {
                "name": "llm",
                "description": "Large Language Model chat, response generation, and emotional text-to-speech synthesis"
            }
        ],
        "components": {
            "schemas": {
                "ChatMessage": {
                    "type": "object",
                    "required": ["message"],
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "User message to send to the AI live2d chat",
                            "example": "Hello, how are you feeling today?"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Optional user identifier for conversation tracking",
                            "default": "default_user",
                            "example": "user_12345"
                        }
                    }
                },
                "ChatResponse": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "AI live2d chat response text",
                            "example": "Hello! I'm feeling quite cheerful today. How can I help you?"
                        },
                        "personality_state": {
                            "$ref": "#/components/schemas/PersonalityState"
                        },
                        "animation_triggers": {
                            "$ref": "#/components/schemas/AnimationTriggers"
                        },
                        "tts_audio": {
                            "$ref": "#/components/schemas/TTSAudio"
                        },
                        "timestamp": {
                            "type": "number",
                            "description": "Unix timestamp of response generation",
                            "example": 1735776000.123
                        }
                    }
                },
                "PersonalityState": {
                    "type": "object",
                    "properties": {
                        "bonding_level": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 10.0,
                            "description": "Current bonding level with user",
                            "example": 3.5
                        },
                        "relationship_stage": {
                            "type": "string",
                            "enum": ["stranger", "acquaintance", "friend", "close_friend", "companion"],
                            "description": "Current relationship stage",
                            "example": "friend"
                        },
                        "dominant_traits": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of dominant personality traits",
                            "example": ["cheerful", "empathetic", "curious"]
                        },
                        "emotional_state": {
                            "type": "string",
                            "description": "Current emotional state",
                            "example": "happy"
                        },
                        "energy_level": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Current energy level",
                            "example": 0.8
                        }
                    }
                },
                "AnimationTriggers": {
                    "type": "object",
                    "properties": {
                        "primary_emotion": {
                            "type": "string",
                            "description": "Primary emotion for Live2D animation",
                            "example": "happy"
                        },
                        "emotion_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of emotion tags extracted from response",
                            "example": ["cheerful", "excited"]
                        },
                        "intensity": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Emotion intensity for animation scaling",
                            "example": 0.7
                        }
                    }
                },
                "TTSAudio": {
                    "type": "object",
                    "properties": {
                        "audio_data": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Audio data as array of float values"
                        },
                        "emotion": {
                            "type": "string",
                            "description": "Emotion used for TTS synthesis",
                            "example": "happy"
                        },
                        "intensity": {
                            "type": "number",
                            "description": "Emotional intensity used in synthesis",
                            "example": 0.7
                        },
                        "voice": {
                            "type": "string",
                            "description": "Voice profile used",
                            "example": "af_nova"
                        }
                    }
                },
                "Live2DModel": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "Database ID of the model",
                            "example": 1
                        },
                        "model_name": {
                            "type": "string",
                            "description": "Name of the Live2D model",
                            "example": "kanade"
                        },
                        "model_path": {
                            "type": "string",
                            "description": "Path to model assets",
                            "example": "/static/assets/kanade"
                        },
                        "config_file": {
                            "type": "string",
                            "description": "Model configuration file",
                            "example": "17kanade_unit2_t04.model3.json"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Model registration timestamp"
                        }
                    }
                },
                "Motion": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "Motion database ID",
                            "example": 1
                        },
                        "motion_group": {
                            "type": "string",
                            "description": "Motion group name",
                            "example": "Idle"
                        },
                        "motion_index": {
                            "type": "integer",
                            "description": "Motion index within group",
                            "example": 0
                        },
                        "motion_name": {
                            "type": "string",
                            "description": "Human-readable motion name",
                            "example": "idle_breathing"
                        },
                        "motion_type": {
                            "type": "string",
                            "enum": ["body", "head", "expression", "special"],
                            "description": "Type of motion",
                            "example": "body"
                        }
                    }
                },
                "SystemStatus": {
                    "type": "object",
                    "properties": {
                        "is_initializing": {
                            "type": "boolean",
                            "description": "Whether system is still initializing",
                            "example": false
                        },
                        "initialization_progress": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Initialization progress percentage",
                            "example": 100
                        },
                        "audio_enabled": {
                            "type": "boolean",
                            "description": "Whether audio processing is enabled",
                            "example": true
                        },
                        "connected_clients": {
                            "type": "integer",
                            "description": "Number of connected WebSocket clients",
                            "example": 2
                        },
                        "system_info": {
                            "type": "object",
                            "description": "System capability information"
                        }
                    }
                },
                "Live2DSystemStatus": {
                    "type": "object",
                    "properties": {
                        "live2d_manager_available": {
                            "type": "boolean",
                            "description": "Whether Live2D manager is initialized",
                            "example": true
                        },
                        "database_connection": {
                            "type": "boolean",
                            "description": "Whether database connection is active",
                            "example": true
                        },
                        "models_count": {
                            "type": "integer",
                            "description": "Number of registered models",
                            "example": 5
                        },
                        "total_motions": {
                            "type": "integer",
                            "description": "Total number of registered motions",
                            "example": 1217
                        },
                        "models_detail": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "model_name": {"type": "string"},
                                    "motions_count": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "string",
                            "description": "Error message",
                            "example": "System is initializing"
                        }
                    }
                },
                "SuccessResponse": {
                    "type": "object",
                    "properties": {
                        "success": {
                            "type": "boolean",
                            "description": "Operation success status",
                            "example": true
                        },
                        "message": {
                            "type": "string",
                            "description": "Success message",
                            "example": "Operation completed successfully"
                        }
                    }
                }
            }
        },
        "paths": {
            "/": {
                "get": {
                    "tags": ["system"],
                    "summary": "Main application interface",
                    "description": "Serves the main AI live2d chat web interface with Live2D viewer and chat functionality",
                    "responses": {
                        "200": {
                            "description": "Main application HTML page",
                            "content": {
                                "text/html": {
                                    "schema": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },
            "/status": {
                "get": {
                    "tags": ["system"],
                    "summary": "Get application status",
                    "description": "Returns current application status including initialization progress, audio state, and connected clients",
                    "responses": {
                        "200": {
                            "description": "Current system status",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SystemStatus"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/chat": {
                "post": {
                    "tags": ["llm"],
                    "summary": "Send message to AI live2d chat",
                    "description": "Send a message to the AI live2d chat and receive a response with personality state, animation triggers, and optional TTS audio",
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ChatMessage"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "AI live2d chat response with animation and audio data",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ChatResponse"}
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - no message provided",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "503": {
                            "description": "Service unavailable - system still initializing",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/v1/chat": {
                "post": {
                    "tags": ["llm"],
                    "summary": "Enhanced chat endpoint (v1)",
                    "description": "Enhanced version of the chat endpoint with additional features and improved response format",
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ChatMessage"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Enhanced AI live2d chat response",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ChatResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/tts": {
                "post": {
                    "tags": ["llm"],
                    "summary": "Text-to-Speech synthesis",
                    "description": "Convert text to speech with optional emotional synthesis and voice selection",
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["text"],
                                    "properties": {
                                        "text": {
                                            "type": "string",
                                            "description": "Text to synthesize",
                                            "example": "Hello, how are you today?"
                                        },
                                        "voice": {
                                            "type": "string",
                                            "description": "Voice profile to use",
                                            "default": "default",
                                            "example": "af_nova"
                                        },
                                        "emotion": {
                                            "type": "string",
                                            "description": "Emotion for synthesis",
                                            "example": "happy"
                                        },
                                        "intensity": {
                                            "type": "number",
                                            "minimum": 0,
                                            "maximum": 1,
                                            "description": "Emotional intensity",
                                            "example": 0.7
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "TTS audio data with metadata",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "allOf": [
                                            {"$ref": "#/components/schemas/TTSAudio"},
                                            {
                                                "type": "object",
                                                "properties": {
                                                    "status": {
                                                        "type": "string",
                                                        "example": "success"
                                                    },
                                                    "timestamp": {
                                                        "type": "number",
                                                        "example": 1735776000.123
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - no text provided",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/tts/emotional": {
                "post": {
                    "tags": ["llm"],
                    "summary": "Emotional Text-to-Speech synthesis",
                    "description": "Specialized endpoint for emotional TTS synthesis with enhanced emotion processing",
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["text"],
                                    "properties": {
                                        "text": {
                                            "type": "string",
                                            "description": "Text to synthesize",
                                            "example": "I'm so excited to see you!"
                                        },
                                        "emotion": {
                                            "type": "string",
                                            "description": "Target emotion for synthesis",
                                            "default": "neutral",
                                            "example": "excited"
                                        },
                                        "intensity": {
                                            "type": "number",
                                            "minimum": 0,
                                            "maximum": 1,
                                            "description": "Emotional intensity",
                                            "default": 0.5,
                                            "example": 0.8
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Emotional TTS audio data",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TTSAudio"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/live2d/models": {
                "get": {
                    "tags": ["live2d"],
                    "summary": "Get available Live2D models",
                    "description": "Returns list of all available Live2D models from the database with their metadata",
                    "responses": {
                        "200": {
                            "description": "List of Live2D models",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "models": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Live2DModel"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/live2d/model/{model_name}": {
                "get": {
                    "tags": ["live2d"],
                    "summary": "Get specific model data",
                    "description": "Returns detailed configuration data for a specific Live2D model",
                    "parameters": [
                        {
                            "name": "model_name",
                            "in": "path",
                            "required": true,
                            "schema": {"type": "string"},
                            "description": "Name of the Live2D model",
                            "example": "kanade"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Model configuration data",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "version": {"type": "string"},
                                            "url": {"type": "string"},
                                            "FileReferences": {"type": "object"},
                                            "Groups": {"type": "array"},
                                            "HitAreas": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/live2d/model/{model_name}/motions": {
                "get": {
                    "tags": ["live2d"],
                    "summary": "Get model motions",
                    "description": "Returns all available motions for a specific Live2D model from the database",
                    "parameters": [
                        {
                            "name": "model_name",
                            "in": "path",
                            "required": true,
                            "schema": {"type": "string"},
                            "description": "Name of the Live2D model",
                            "example": "kanade"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of motions for the model",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "motions": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Motion"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/live2d/model/{model_name}/register_motions": {
                "post": {
                    "tags": ["live2d"],
                    "summary": "Register model motions",
                    "description": "Register detected motions for a Live2D model (called by frontend after model loads)",
                    "parameters": [
                        {
                            "name": "model_name",
                            "in": "path",
                            "required": true,
                            "schema": {"type": "string"},
                            "description": "Name of the Live2D model"
                        }
                    ],
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "motions": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Motion"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Motions registered successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "allOf": [
                                            {"$ref": "#/components/schemas/SuccessResponse"},
                                            {
                                                "type": "object",
                                                "properties": {
                                                    "registered_count": {"type": "integer"}
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/live2d/system_status": {
                "get": {
                    "tags": ["live2d"],
                    "summary": "Get Live2D system status",
                    "description": "Returns comprehensive status information for the Live2D system including database connection and model counts",
                    "responses": {
                        "200": {
                            "description": "Live2D system status",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Live2DSystemStatus"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/live2d/comprehensive_test": {
                "get": {
                    "tags": ["live2d"],
                    "summary": "Run comprehensive Live2D tests",
                    "description": "Runs a comprehensive test suite for the Live2D system including manager, database, and asset validation",
                    "responses": {
                        "200": {
                            "description": "Test results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "test_results": {
                                                "type": "object",
                                                "properties": {
                                                    "summary": {
                                                        "type": "object",
                                                        "properties": {
                                                            "total_tests": {"type": "integer"},
                                                            "passed_tests": {"type": "integer"},
                                                            "failed_tests": {"type": "integer"}
                                                        }
                                                    },
                                                    "details": {"type": "object"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/live2d/clear_database": {
                "post": {
                    "tags": ["live2d"],
                    "summary": "Clear Live2D database (DESTRUCTIVE)",
                    "description": "⚠️ WARNING: This permanently deletes all Live2D models and motions from the database. This action cannot be undone.",
                    "responses": {
                        "200": {
                            "description": "Database cleared successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "deleted_models": {"type": "integer"},
                                            "deleted_motions": {"type": "integer"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Error during database clear operation",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/live2d/reimport_all": {
                "post": {
                    "tags": ["live2d"],
                    "summary": "Re-import all Live2D data",
                    "description": "Re-import all Live2D models and motions from asset directories, registering them in the database",
                    "responses": {
                        "200": {
                            "description": "Re-import completed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "models_imported": {"type": "integer"},
                                            "motions_imported": {"type": "integer"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/debug/test_motion_detection": {
                "get": {
                    "tags": ["live2d"],
                    "summary": "Debug motion detection",
                    "description": "Debug endpoint for testing motion detection functionality",
                    "responses": {
                        "200": {
                            "description": "Motion detection test results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "motion_detection_results": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/audio/start": {
                "post": {
                    "tags": ["system"],
                    "summary": "Start audio processing",
                    "description": "Starts the audio pipeline for voice input processing including wake word detection and transcription",
                    "responses": {
                        "200": {
                            "description": "Audio processing started successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "example": "started"
                                            },
                                            "enabled": {
                                                "type": "boolean",
                                                "example": true
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/audio/stop": {
                "post": {
                    "tags": ["system"],
                    "summary": "Stop audio processing",
                    "description": "Stops the audio pipeline and disables voice input processing",
                    "responses": {
                        "200": {
                            "description": "Audio processing stopped successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "example": "stopped"
                                            },
                                            "enabled": {
                                                "type": "boolean",
                                                "example": false
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/audio/status": {
                "get": {
                    "tags": ["system"],
                    "summary": "Get audio pipeline status",
                    "description": "Returns current status and configuration of the audio processing pipeline",
                    "responses": {
                        "200": {
                            "description": "Audio pipeline status",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "enabled": {"type": "boolean"},
                                            "state": {"type": "string"},
                                            "config": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/personality": {
                "get": {
                    "tags": ["system"],
                    "summary": "Get personality state",
                    "description": "Returns current personality configuration, traits, and emotional state",
                    "responses": {
                        "200": {
                            "description": "Current personality state",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/PersonalityState"}
                                }
                            }
                        },
                        "503": {
                            "description": "Personality system not available",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/v1/memory": {
                "get": {
                    "tags": ["system"],
                    "summary": "Get memory system data",
                    "description": "Returns memory system data including conversation history and context",
                    "responses": {
                        "200": {
                            "description": "Memory system data",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "memories": {"type": "array"},
                                            "context": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/v1/memory/clusters": {
                "get": {
                    "tags": ["system"],
                    "summary": "Get memory clusters",
                    "description": "Returns memory clusters and their relationships for advanced memory analysis",
                    "responses": {
                        "200": {
                            "description": "Memory clusters data",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "clusters": {"type": "array"},
                                            "relationships": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

def get_api_docs_html(spec: Dict[str, Any]) -> str:
    """Generate HTML documentation page with embedded Swagger UI"""
    
    # Extract some stats from the spec
    total_endpoints = len(spec.get('paths', {}))
    system_endpoints = len([path for path, data in spec.get('paths', {}).items() 
                           if any(tag in ['system'] for method_data in data.values() 
                                 for tag in method_data.get('tags', []))])
    live2d_endpoints = len([path for path, data in spec.get('paths', {}).items() 
                           if any(tag in ['live2d'] for method_data in data.values() 
                                 for tag in method_data.get('tags', []))])
    llm_endpoints = len([path for path, data in spec.get('paths', {}).items() 
                        if any(tag in ['llm'] for method_data in data.values() 
                              for tag in method_data.get('tags', []))])
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Companion API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
        <style>
            body {{
                margin: 0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
            }}
            .header .version {{
                opacity: 0.9;
                margin-top: 10px;
            }}
            .stats {{
                display: flex;
                justify-content: center;
                gap: 30px;
                margin: 20px 0;
                flex-wrap: wrap;
            }}
            .stat {{
                text-align: center;
                background: rgba(255,255,255,0.1);
                padding: 15px;
                border-radius: 10px;
                min-width: 120px;
            }}
            .stat-number {{
                font-size: 2em;
                font-weight: bold;
                color: #ffd700;
            }}
            .stat-label {{
                font-size: 0.9em;
                opacity: 0.9;
            }}
            #swagger-ui {{
                max-width: none;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 AI Companion API Documentation</h1>
            <div class="version">Version {spec.get('info', {}).get('version', '2.1.0')} - Enhanced Live2D Integration</div>
            <div class="version">Generated: {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}</div>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{system_endpoints}</div>
                    <div class="stat-label">System Endpoints</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{live2d_endpoints}</div>
                    <div class="stat-label">Live2D Endpoints</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{llm_endpoints}</div>
                    <div class="stat-label">LLM Endpoints</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{total_endpoints}</div>
                    <div class="stat-label">Total Endpoints</div>
                </div>
            </div>
        </div>
        
        <div id="swagger-ui"></div>
        
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
        <script>
            const spec = {spec};
            
            SwaggerUIBundle({{
                url: '',
                spec: spec,
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                tryItOutEnabled: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                defaultModelsExpandDepth: 1,
                defaultModelExpandDepth: 1,
                docExpansion: 'list',
                filter: true,
                showExtensions: true,
                showCommonExtensions: true
            }});
        </script>
    </body>
    </html>
    """
