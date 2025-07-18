"""
OpenAPI 3.0.3 specification for AI Companion API
Separated for better maintainability and organization
"""

def get_openapi_spec():
    """Generate OpenAPI 3.0.3 specification"""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "AI Companion API",
            "description": "Comprehensive AI Companion API with Live2D, LLM, and TTS integration. Enhanced with dynamic motion system and emotional responses.",
            "version": "2.1.0",
            "contact": {
                "name": "AI Companion Support",
                "url": "https://github.com/ai-companion/api"
            }
        },
        "servers": [
            {
                "url": "http://localhost:13443",
                "description": "Development server"
            }
        ],
        "tags": [
            {
                "name": "system",
                "description": "Core system functionality including audio processing and memory management"
            },
            {
                "name": "live2d", 
                "description": "Live2D model management and animation control"
            },
            {
                "name": "llm",
                "description": "Large Language Model chat and response generation"
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
                            "description": "Optional user identifier",
                            "default": "default_user"
                        }
                    }
                },
                "ChatResponse": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "AI companion response"
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
                            "description": "Unix timestamp"
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
                        "model_name": {
                            "type": "string",
                            "description": "Name of the Live2D model"
                        },
                        "model_path": {
                            "type": "string",
                            "description": "Path to model assets"
                        },
                        "config_file": {
                            "type": "string",
                            "description": "Model configuration file"
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
                        "is_initializing": {
                            "type": "boolean",
                            "description": "Whether system is still initializing"
                        },
                        "audio_enabled": {
                            "type": "boolean",
                            "description": "Whether audio processing is enabled"
                        },
                        "connected_clients": {
                            "type": "integer",
                            "description": "Number of connected clients"
                        }
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "string",
                            "description": "Error message"
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
                    "description": "Serves the main AI companion web interface",
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
                    "tags": ["llm"],
                    "summary": "Send message to AI companion",
                    "description": "Send a message to the AI companion and receive a response with personality state and animation triggers",
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
                            "description": "AI companion response",
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
                    "tags": ["llm"],
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
                            "description": "AI companion response",
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
                    "description": "Convert text to speech with optional emotional synthesis",
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
            "/api/audio/start": {
                "post": {
                    "tags": ["system"],
                    "summary": "Start audio processing",
                    "description": "Starts the audio pipeline for voice input processing",
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
                    "tags": ["system"],
                    "summary": "Stop audio processing",
                    "description": "Stops the audio pipeline",
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
        <title>AI Companion API Documentation v2.1</title>
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
