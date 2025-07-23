"""
OpenAPI 3.0.3 specification for AI Companion API v0.5.0a
Comprehensive specification including RAG system, dynamic personality, and enhanced features
"""

def get_openapi_spec():
    """Generate OpenAPI 3.0.3 specification"""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "AI Companion API",
            "description": "Comprehensive AI Companion API with Live2D avatars, RAG system, dynamic personality, enhanced audio processing, and advanced AI integration features.",
            "version": "0.5.0a",
            "contact": {
                "name": "AI Companion Support",
                "url": "https://github.com/Erebus-Nyx/ai2d_chat"
            }
        },
        "servers": [
            {
                "url": "http://localhost:19080",
                "description": "Production server (default)"
            },
            {
                "url": "http://localhost:19081", 
                "description": "Development server"
            }
        ],
        "tags": [
            {
                "name": "chat",
                "description": "Chat system with RAG-enhanced responses and memory integration"
            },
            {
                "name": "rag",
                "description": "Retrieval-Augmented Generation system for semantic search and context"
            },
            {
                "name": "live2d", 
                "description": "Live2D model management, animations, and avatar control"
            },
            {
                "name": "audio",
                "description": "Audio processing, VAD, and voice interaction"
            },
            {
                "name": "tts",
                "description": "Text-to-speech with emotional synthesis"
            },
            {
                "name": "users",
                "description": "User management and profiles"
            },
            {
                "name": "characters",
                "description": "Character management and personality configuration"
            },
            {
                "name": "system",
                "description": "System information, health checks, and configuration"
            },
            {
                "name": "logging",
                "description": "Enhanced logging system with timestamped files"
            },
            {
                "name": "autonomous",
                "description": "Autonomous conversation and proactive AI behavior"
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
                            "description": "User message to send to the AI companion"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User identifier for conversation context"
                        },
                        "character_id": {
                            "type": "string",
                            "description": "Character identifier for personality context"
                        }
                    }
                },
                "ChatResponse": {
                    "type": "object",
                    "properties": {
                        "success": {
                            "type": "boolean",
                            "description": "Response success status"
                        },
                        "response": {
                            "type": "string",
                            "description": "AI companion response"
                        },
                        "emotion": {
                            "type": "string",
                            "description": "Current emotional state"
                        },
                        "timestamp": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Response timestamp"
                        },
                        "conversation_id": {
                            "type": "string",
                            "description": "Conversation identifier"
                        }
                    }
                },
                "RAGSearchRequest": {
                    "type": "object",
                    "required": ["query", "user_id"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for semantic search"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User identifier for filtered results"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        }
                    }
                },
                "RAGSearchResponse": {
                    "type": "object",
                    "properties": {
                        "success": {
                            "type": "boolean"
                        },
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "content": {
                                        "type": "string",
                                        "description": "Retrieved conversation content"
                                    },
                                    "score": {
                                        "type": "number",
                                        "description": "Relevance score (0.0-1.0)"
                                    },
                                    "timestamp": {
                                        "type": "string",
                                        "format": "date-time"
                                    },
                                    "conversation_id": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    }
                },
                "RAGStatus": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "RAG system status"
                        },
                        "vector_db_size": {
                            "type": "integer",
                            "description": "Number of documents in vector database"
                        },
                        "embedding_model": {
                            "type": "string",
                            "description": "Current embedding model"
                        },
                        "last_sync": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Last synchronization timestamp"
                        }
                    }
                },
                "PersonalityState": {
                    "type": "object",
                    "properties": {
                        "bonding_level": {
                            "type": "number",
                            "description": "Current bonding level (0.0-10.0)"
                        },
                        "relationship_stage": {
                            "type": "string",
                            "description": "Current relationship stage"
                        },
                        "dominant_traits": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of dominant personality traits"
                        },
                        "emotional_state": {
                            "type": "string",
                            "description": "Current emotional state"
                        }
                    }
                },
                "AnimationTriggers": {
                    "type": "object",
                    "properties": {
                        "primary_emotion": {
                            "type": "string",
                            "description": "Primary emotion for animation"
                        },
                        "emotion_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of emotion tags"
                        },
                        "intensity": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Emotion intensity (0.0-1.0)"
                        }
                    }
                },
                "TTSAudio": {
                    "type": "object",
                    "properties": {
                        "audio_data": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Audio data as array of floats"
                        },
                        "emotion": {
                            "type": "string",
                            "description": "Emotion used for TTS synthesis"
                        },
                        "intensity": {
                            "type": "number",
                            "description": "Emotional intensity"
                        }
                    }
                },
                "Live2DModel": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Model name"
                        },
                        "path": {
                            "type": "string",
                            "description": "Model file path"
                        },
                        "version": {
                            "type": "string",
                            "description": "Cubism version (cubism2, cubism3, cubism4, cubism5)"
                        },
                        "has_expressions": {
                            "type": "boolean",
                            "description": "Whether model has expressions"
                        },
                        "has_motions": {
                            "type": "boolean",
                            "description": "Whether model has motions"
                        }
                    }
                },
                "TTSRequest": {
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to synthesize"
                        },
                        "voice": {
                            "type": "string",
                            "description": "Voice identifier",
                            "default": "default"
                        },
                        "emotion": {
                            "type": "string",
                            "description": "Emotion for emotional TTS"
                        },
                        "intensity": {
                            "type": "number",
                            "description": "Emotion intensity (0.0-1.0)",
                            "minimum": 0.0,
                            "maximum": 1.0
                        }
                    }
                },
                "TTSResponse": {
                    "type": "object",
                    "properties": {
                        "success": {
                            "type": "boolean"
                        },
                        "audio_url": {
                            "type": "string",
                            "description": "URL to generated audio file"
                        },
                        "duration": {
                            "type": "number",
                            "description": "Audio duration in seconds"
                        },
                        "emotion_applied": {
                            "type": "string",
                            "description": "Applied emotion"
                        }
                    }
                },
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "User identifier"
                        },
                        "username": {
                            "type": "string",
                            "description": "Username"
                        },
                        "email": {
                            "type": "string",
                            "description": "User email"
                        },
                        "profile": {
                            "type": "object",
                            "description": "User profile data"
                        },
                        "preferences": {
                            "type": "object",
                            "description": "User preferences"
                        }
                    }
                },
                "Character": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Character identifier"
                        },
                        "name": {
                            "type": "string",
                            "description": "Character name"
                        },
                        "personality": {
                            "type": "object",
                            "description": "Character personality traits"
                        }
                    }
                },
                "Motion": {
                    "type": "object",
                    "properties": {
                        "motion_group": {
                            "type": "string",
                            "description": "Motion group name"
                        },
                        "motion_index": {
                            "type": "integer",
                            "description": "Motion index within group"
                        },
                        "motion_name": {
                            "type": "string",
                            "description": "Motion name"
                        },
                        "motion_type": {
                            "type": "string",
                            "description": "Type of motion (body, head, expression)"
                        }
                    }
                },
                "SystemStatus": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "System health status"
                        },
                        "uptime": {
                            "type": "integer",
                            "description": "System uptime in seconds"
                        },
                        "memory_usage": {
                            "type": "string",
                            "description": "Memory usage percentage"
                        },
                        "cpu_usage": {
                            "type": "string",
                            "description": "CPU usage percentage"
                        },
                        "active_connections": {
                            "type": "integer",
                            "description": "Number of active connections"
                        }
                    }
                },
                "AutonomousStatus": {
                    "type": "object",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "description": "Whether autonomous mode is enabled"
                        },
                        "conversation_mode": {
                            "type": "string",
                            "description": "Current conversation mode"
                        },
                        "engagement_level": {
                            "type": "number",
                            "description": "Current engagement level (0.0-1.0)"
                        },
                        "last_interaction": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Last interaction timestamp"
                        }
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "success": {
                            "type": "boolean",
                            "example": False
                        },
                        "error": {
                            "type": "string",
                            "description": "Error description"
                        },
                        "code": {
                            "type": "string",
                            "description": "Error code"
                        },
                        "timestamp": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Error timestamp"
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
                    "description": "Serves the main AI live2d chat web interface",
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
                    "description": "Returns current application status and health information",
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
                    "tags": ["chat"],
                    "summary": "Send message to AI companion",
                    "description": "Send a message to the AI companion and receive a response with RAG-enhanced context",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ChatMessage"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "AI live2d chat response",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ChatResponse"}
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "503": {
                            "description": "Service unavailable (system initializing)",
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
                    "tags": ["chat"],
                    "summary": "Enhanced chat endpoint (v1)",
                    "description": "Enhanced version of the chat endpoint with additional features",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ChatMessage"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "AI live2d chat response",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ChatResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/rag/status": {
                "get": {
                    "tags": ["rag"],
                    "summary": "Get RAG system status",
                    "description": "Returns the current status of the Retrieval-Augmented Generation system",
                    "responses": {
                        "200": {
                            "description": "RAG system status",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/RAGStatus"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/rag/search": {
                "post": {
                    "tags": ["rag"],
                    "summary": "Semantic search",
                    "description": "Perform semantic search across conversation history using RAG system",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/RAGSearchRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Search results",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/RAGSearchResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/rag/context": {
                "post": {
                    "tags": ["rag"],
                    "summary": "Get enhanced context",
                    "description": "Get enhanced conversation context using RAG system",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["message", "user_id"],
                                    "properties": {
                                        "message": {"type": "string"},
                                        "user_id": {"type": "string"},
                                        "context_limit": {"type": "integer", "default": 5}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Enhanced context data",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "context": {"type": "array", "items": {"type": "object"}}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/rag/add_conversation": {
                "post": {
                    "tags": ["rag"],
                    "summary": "Add conversation to RAG",
                    "description": "Add a conversation to the RAG vector database",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["user_id", "user_message", "ai_response"],
                                    "properties": {
                                        "user_id": {"type": "string"},
                                        "user_message": {"type": "string"},
                                        "ai_response": {"type": "string"},
                                        "metadata": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Conversation added successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "conversation_id": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/tts": {
                "post": {
                    "tags": ["tts"],
                    "summary": "Basic Text-to-Speech synthesis",
                    "description": "Convert text to speech with basic voice synthesis",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["text"],
                                    "properties": {
                                        "text": {
                                            "type": "string",
                                            "description": "Text to synthesize"
                                        },
                                        "voice": {
                                            "type": "string",
                                            "description": "Voice to use",
                                            "default": "default"
                                        },
                                        "emotion": {
                                            "type": "string",
                                            "description": "Emotion for synthesis"
                                        },
                                        "intensity": {
                                            "type": "number",
                                            "description": "Emotional intensity"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "TTS audio data",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TTSAudio"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/tts/emotional": {
                "post": {
                    "tags": ["tts"],
                    "summary": "Emotional Text-to-Speech synthesis",
                    "description": "Convert text to speech with emotional synthesis capabilities (New in v0.5.0a)",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TTSRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Emotional TTS audio data",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TTSResponse"}
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
                    "description": "Returns list of all available Live2D models",
                    "responses": {
                        "200": {
                            "description": "List of Live2D models",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Live2DModel"}
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
                    "description": "Returns all available motions for a specific Live2D model",
                    "parameters": [
                        {
                            "name": "model_name",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Name of the Live2D model"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of motions",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Motion"}
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
                    "description": "Returns comprehensive status information for the Live2D system",
                    "responses": {
                        "200": {
                            "description": "Live2D system status",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "live2d_manager_available": {"type": "boolean"},
                                            "database_connection": {"type": "boolean"},
                                            "models_count": {"type": "integer"},
                                            "total_motions": {"type": "integer"}
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
                    "description": "⚠️ WARNING: This permanently deletes all Live2D models and motions from the database",
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
                                            "deleted_motions": {"type": "integer"}
                                        }
                                    }
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
                    "description": "Re-import all Live2D models and motions from asset directories",
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
                                            "motions_imported": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/live2d/models/detailed": {
                "get": {
                    "tags": ["live2d"],
                    "summary": "Get detailed model information",
                    "description": "Get comprehensive information about all Live2D models including expressions and motions",
                    "responses": {
                        "200": {
                            "description": "Detailed model information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
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
            "/api/live2d/model/{model_name}/expressions": {
                "get": {
                    "tags": ["live2d"],
                    "summary": "Get model expressions",
                    "description": "Get all available expressions for a specific Live2D model",
                    "parameters": [
                        {
                            "name": "model_name",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Name of the Live2D model"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of expressions",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "expressions": {
                                                "type": "array",
                                                "items": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/live2d/model/{model_name}/animation_compatibility": {
                "get": {
                    "tags": ["live2d"],
                    "summary": "Check animation compatibility",
                    "description": "Check animation compatibility for a specific Live2D model",
                    "parameters": [
                        {
                            "name": "model_name",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Name of the Live2D model"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Animation compatibility information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "compatible": {"type": "boolean"},
                                            "version": {"type": "string"},
                                            "details": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/live2d/comprehensive_test": {
                "get": {
                    "tags": ["live2d"],
                    "summary": "Run comprehensive Live2D test",
                    "description": "Run comprehensive tests on the Live2D system",
                    "responses": {
                        "200": {
                            "description": "Test results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "tests_passed": {"type": "integer"},
                                            "tests_failed": {"type": "integer"},
                                            "details": {"type": "array", "items": {"type": "object"}}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/live2d/debug_paths": {
                "get": {
                    "tags": ["live2d"],
                    "summary": "Debug Live2D paths",
                    "description": "Get debug information about Live2D file paths and structure",
                    "responses": {
                        "200": {
                            "description": "Debug path information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "paths": {"type": "object"},
                                            "file_counts": {"type": "object"}
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
                    "tags": ["audio"],
                    "summary": "Start audio processing",
                    "description": "Starts the enhanced audio pipeline for voice input processing",
                    "responses": {
                        "200": {
                            "description": "Audio processing started",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "enabled": {"type": "boolean"}
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
                    "tags": ["audio"],
                    "summary": "Stop audio processing",
                    "description": "Stops the enhanced audio pipeline",
                    "responses": {
                        "200": {
                            "description": "Audio processing stopped",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "enabled": {"type": "boolean"}
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
                    "tags": ["audio"],
                    "summary": "Get audio status",
                    "description": "Get current status of the enhanced audio processing system",
                    "responses": {
                        "200": {
                            "description": "Audio system status",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "mode": {"type": "string"},
                                            "processing": {"type": "boolean"},
                                            "vad_active": {"type": "boolean"}
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
                    "description": "Returns current personality configuration and state",
                    "responses": {
                        "200": {
                            "description": "Current personality state",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/PersonalityState"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/users": {
                "get": {
                    "tags": ["users"],
                    "summary": "List users",
                    "description": "Get a list of all users with optional filtering and pagination",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 20},
                            "description": "Maximum number of users to return"
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "schema": {"type": "integer", "default": 0},
                            "description": "Number of users to skip"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of users",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "users": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/User"}
                                            },
                                            "total": {"type": "integer"},
                                            "has_more": {"type": "boolean"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "tags": ["users"],
                    "summary": "Create user",
                    "description": "Create a new user account",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username"],
                                    "properties": {
                                        "username": {"type": "string"},
                                        "email": {"type": "string"},
                                        "profile": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/users/current": {
                "get": {
                    "tags": ["users"],
                    "summary": "Get current user",
                    "description": "Get the currently active user profile",
                    "responses": {
                        "200": {
                            "description": "Current user profile",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/users/{user_id}/profile": {
                "get": {
                    "tags": ["users"],
                    "summary": "Get user profile",
                    "description": "Get a specific user's profile by ID",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "User identifier"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "User profile",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                },
                "put": {
                    "tags": ["users"],
                    "summary": "Update user profile",
                    "description": "Update a user's profile information",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "User identifier"
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "preferences": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "User profile updated",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/characters": {
                "get": {
                    "tags": ["characters"],
                    "summary": "List characters",
                    "description": "Get a list of all available characters",
                    "responses": {
                        "200": {
                            "description": "List of characters",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "characters": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Character"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/characters/{character_id}": {
                "get": {
                    "tags": ["characters"],
                    "summary": "Get character details",
                    "description": "Get detailed information about a specific character",
                    "parameters": [
                        {
                            "name": "character_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Character identifier"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Character details",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Character"}
                                }
                            }
                        }
                    }
                },
                "put": {
                    "tags": ["characters"],
                    "summary": "Update character",
                    "description": "Update a character's configuration and personality",
                    "parameters": [
                        {
                            "name": "character_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Character identifier"
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "personality": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Character updated",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Character"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/system/version": {
                "get": {
                    "tags": ["system"],
                    "summary": "Get system version",
                    "description": "Get the current application version and build information",
                    "responses": {
                        "200": {
                            "description": "System version information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "version": {"type": "string"},
                                            "title": {"type": "string"},
                                            "description": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/system/status": {
                "get": {
                    "tags": ["system"],
                    "summary": "Get detailed system status",
                    "description": "Get comprehensive system status including resource usage",
                    "responses": {
                        "200": {
                            "description": "Detailed system status",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SystemStatus"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/system/health": {
                "get": {
                    "tags": ["system"],
                    "summary": "Health check",
                    "description": "Perform a comprehensive health check of all system components",
                    "responses": {
                        "200": {
                            "description": "System health information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "healthy": {"type": "boolean"},
                                            "components": {"type": "object"},
                                            "checks": {"type": "array", "items": {"type": "object"}}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/system/config": {
                "get": {
                    "tags": ["system"],
                    "summary": "Get system configuration",
                    "description": "Get current system configuration settings",
                    "responses": {
                        "200": {
                            "description": "System configuration",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "config": {"type": "object"},
                                            "version": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/system/info": {
                "get": {
                    "tags": ["system"],
                    "summary": "Get system information",
                    "description": "Get comprehensive system information including hardware and environment details",
                    "responses": {
                        "200": {
                            "description": "System information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "system": {"type": "object"},
                                            "environment": {"type": "object"},
                                            "resources": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/autonomous/status": {
                "get": {
                    "tags": ["autonomous"],
                    "summary": "Get autonomous status",
                    "description": "Get the current status of the autonomous conversation system (New in v0.5.0a)",
                    "responses": {
                        "200": {
                            "description": "Autonomous system status",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AutonomousStatus"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/autonomous/enable": {
                "post": {
                    "tags": ["autonomous"],
                    "summary": "Enable autonomous mode",
                    "description": "Enable autonomous conversation mode with proactive AI behavior (New in v0.5.0a)",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "mode": {"type": "string", "default": "proactive"},
                                        "engagement_threshold": {"type": "number", "default": 0.6}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Autonomous mode enabled",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AutonomousStatus"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/autonomous/disable": {
                "post": {
                    "tags": ["autonomous"],
                    "summary": "Disable autonomous mode",
                    "description": "Disable autonomous conversation mode",
                    "responses": {
                        "200": {
                            "description": "Autonomous mode disabled",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AutonomousStatus"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }

def get_swagger_ui_html():
    """Generate Swagger UI HTML interface"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>AI Companion API Documentation v0.5.0a</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
        <style>
            body { margin: 0; padding: 0; }
            .swagger-ui .topbar { display: none; }
            .swagger-ui .info .title { color: #4a9eff; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                const ui = SwaggerUIBundle({
                    url: '/api/docs?json=1',
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
                    filter: true,
                    showRequestHeaders: true,
                    showCommonExtensions: true,
                    displayRequestDuration: true
                });
            };
        </script>
    </body>
    </html>
    """
