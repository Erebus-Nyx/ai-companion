"""
Database schemas for AI Companion application.
Defines the structure for conversations, personality traits, user preferences, and memories.
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Any
import json

# SQL schema definitions
SCHEMA_SQL = {
    'conversations': """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            message_type TEXT NOT NULL CHECK(message_type IN ('user', 'assistant')),
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            emotion_state TEXT,
            context_tags TEXT  -- JSON array of context tags
        )
    """,
    
    'personality_traits': """
        CREATE TABLE IF NOT EXISTS personality_traits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            trait_name TEXT NOT NULL,
            trait_value REAL NOT NULL DEFAULT 0.5,  -- 0.0 to 1.0 scale
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, trait_name)
        )
    """,
    
    'user_memories': """
        CREATE TABLE IF NOT EXISTS user_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            memory_type TEXT NOT NULL,  -- 'preference', 'fact', 'interest', 'relationship'
            key_topic TEXT NOT NULL,
            value_content TEXT NOT NULL,
            importance_score REAL DEFAULT 0.5,  -- 0.0 to 1.0
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 1
        )
    """,
    
    'bonding_progress': """
        CREATE TABLE IF NOT EXISTS bonding_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            bond_level INTEGER DEFAULT 1,  -- 1-10 scale
            experience_points INTEGER DEFAULT 0,
            relationship_stage TEXT DEFAULT 'stranger',  -- stranger, acquaintance, friend, close_friend, best_friend
            total_conversations INTEGER DEFAULT 0,
            personality_data TEXT,  -- JSON blob for personality state
            last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
            creation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id)
        )
    """,
    
    'avatar_states': """
        CREATE TABLE IF NOT EXISTS avatar_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            current_mood TEXT DEFAULT 'neutral',
            energy_level REAL DEFAULT 0.8,  -- 0.0 to 1.0
            happiness_level REAL DEFAULT 0.7,
            curiosity_level REAL DEFAULT 0.6,
            trust_level REAL DEFAULT 0.3,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id)
        )
    """,
    
    'user_preferences': """
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            preference_category TEXT NOT NULL,  -- 'voice', 'ui', 'behavior', 'privacy'
            preference_key TEXT NOT NULL,
            preference_value TEXT NOT NULL,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, preference_category, preference_key)
        )
    """,
    
    'conversation_summaries': """
        CREATE TABLE IF NOT EXISTS conversation_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            date_range TEXT NOT NULL,  -- 'YYYY-MM-DD' or 'YYYY-MM-DD_to_YYYY-MM-DD'
            summary_text TEXT NOT NULL,
            key_topics TEXT,  -- JSON array of important topics discussed
            emotional_tone TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """,
    
    'conversation_context': """
        CREATE TABLE IF NOT EXISTS conversation_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            session_id TEXT NOT NULL,
            context_window TEXT NOT NULL,  -- JSON array of recent messages
            embeddings TEXT,  -- Optional: stored embeddings for semantic search
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, session_id)
        )
    """,
    
    'memory_clusters': """
        CREATE TABLE IF NOT EXISTS memory_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            cluster_name TEXT NOT NULL,
            cluster_description TEXT,
            memory_ids TEXT NOT NULL,  -- JSON array of memory IDs in this cluster
            importance_score REAL DEFAULT 0.5,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """,
    
    'llm_cache': """
        CREATE TABLE IF NOT EXISTS llm_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_hash TEXT NOT NULL UNIQUE,  -- Hash of input prompt
            response_text TEXT NOT NULL,
            model_name TEXT NOT NULL,
            temperature REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 1,
            last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
}

# Default personality traits
DEFAULT_PERSONALITY_TRAITS = {
    'friendliness': 0.8,
    'curiosity': 0.7,
    'playfulness': 0.6,
    'empathy': 0.8,
    'intelligence': 0.7,
    'humor': 0.5,
    'patience': 0.8,
    'enthusiasm': 0.6,
    'supportiveness': 0.9,
    'creativity': 0.6
}

# Default user preferences
DEFAULT_USER_PREFERENCES = {
    'voice': {
        'tts_voice': 'default_voice',
        'speech_rate': '1.0',
        'voice_enabled': 'true'
    },
    'ui': {
        'animation_speed': '1.0',
        'theme': 'default',
        'show_timestamps': 'true'
    },
    'behavior': {
        'response_length': 'medium',
        'personality_adaptation': 'true',
        'memory_retention': 'high'
    },
    'privacy': {
        'data_retention_days': '365',
        'share_analytics': 'false'
    }
}
