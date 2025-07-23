# app_routes_users.py
# User profile management API routes

from flask import Blueprint, request, jsonify, session
import logging
import traceback
import json
import os
from datetime import datetime
import sqlite3
from databases.database_manager import get_users_connection, get_user_profiles_connection, get_user_data_dir

# Blueprint definition
users_routes = Blueprint('users_routes', __name__)

def get_user_by_username(username):
    """Get user information by username"""
    try:
        with get_users_connection() as conn:
            user = conn.execute('''
                SELECT id, username, display_name, email, is_admin, permissions, created_at
                FROM users 
                WHERE username = ?
            ''', (username,)).fetchone()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'display_name': user[2],
                    'email': user[3],
                    'is_admin': user[4],
                    'permissions': user[5],
                    'created_at': user[6]
                }
        return None
    except Exception as e:
        logging.error(f"Error getting user by username: {str(e)}")
        return None


def init_user_tables():
    """Initialize user tables if they don't exist"""
    try:
        # Initialize users table
        with get_users_connection() as conn:
            # Check if users table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new users table with full authentication schema for future compatibility
                conn.execute('''
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        email TEXT UNIQUE,
                        password_hash TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        display_name TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        is_admin BOOLEAN DEFAULT 0,
                        permissions TEXT DEFAULT '["chat", "voice", "model_switch"]',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_login DATETIME,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.execute('CREATE INDEX idx_users_username ON users(username)')
                logging.info("Created new users table with authentication schema")
            
            # Create default user if none exists using config settings
            cursor = conn.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                # Get default user settings from config
                try:
                    from config.config_manager import ConfigManager
                    config_manager = ConfigManager()
                    default_user = config_manager.config.get('authentication', {}).get('default_user', {})
                    
                    username = default_user.get('username', 'admin')
                    display_name = default_user.get('display_name', 'Administrator')
                    email = default_user.get('email', 'admin@localhost')
                    is_admin = default_user.get('is_admin', True)
                    
                    # Create default user with config settings
                    conn.execute('''
                        INSERT INTO users (username, display_name, password_hash, salt, email, is_admin, is_active) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (username, display_name, 'no_password_yet', 'no_salt_yet', email, is_admin, 1))
                    logging.info(f"Created default admin user: {username} (password authentication disabled)")
                    
                except Exception as e:
                    # Fallback to hardcoded defaults if config loading fails
                    conn.execute('''
                        INSERT INTO users (username, display_name, password_hash, salt, email, is_admin, is_active) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', ('admin', 'Administrator', 'no_password_yet', 'no_salt_yet', 'admin@localhost', 1, 1))
                    logging.info("Created fallback default admin user (config not available)")
                
        # Initialize user profiles table with our custom fields
        with get_user_profiles_connection() as conn:
            # Check if user_profiles table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new user profiles table
                conn.execute('''
                    CREATE TABLE user_profiles (
                        user_id INTEGER PRIMARY KEY,
                        display_name TEXT,
                        age INTEGER,
                        avatar_preferences TEXT,
                        conversation_settings TEXT,
                        privacy_settings TEXT,
                        theme_preferences TEXT,
                        language_preference TEXT DEFAULT 'en',
                        timezone TEXT,
                        gender TEXT DEFAULT 'not_specified',
                        age_range TEXT DEFAULT 'adult',
                        nsfw_enabled BOOLEAN DEFAULT 0,
                        explicit_enabled BOOLEAN DEFAULT 0,
                        allow_nsfw_content BOOLEAN DEFAULT 0,
                        allow_mature_themes BOOLEAN DEFAULT 0,
                        allow_violence BOOLEAN DEFAULT 0,
                        allow_strong_language BOOLEAN DEFAULT 0,
                        content_warnings_enabled BOOLEAN DEFAULT 1,
                        safe_mode BOOLEAN DEFAULT 1,
                        explicit_comfort_level TEXT DEFAULT 'none',
                        roleplay_engagement_level TEXT DEFAULT 'moderate',
                        preferred_narrative_style TEXT DEFAULT 'conversational',
                        immersion_preference TEXT DEFAULT 'medium',
                        character_consistency_expectation TEXT DEFAULT 'high',
                        roleplay_experience_level TEXT DEFAULT 'intermediate',
                        bio TEXT DEFAULT '',
                        preferences TEXT DEFAULT '{}',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                ''')
                conn.execute('CREATE INDEX idx_profiles_user ON user_profiles(user_id)')
                logging.info("Created new user_profiles table")
            else:
                # Table exists, add our custom columns if they don't exist
                cursor = conn.execute("PRAGMA table_info(user_profiles)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'gender' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN gender TEXT DEFAULT "not_specified"')
                    logging.info("Added gender column to user_profiles table")
                
                if 'age_range' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN age_range TEXT DEFAULT "adult"')
                    logging.info("Added age_range column to user_profiles table")
                    
                if 'nsfw_enabled' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN nsfw_enabled BOOLEAN DEFAULT 0')
                    logging.info("Added nsfw_enabled column to user_profiles table")
                    
                if 'explicit_enabled' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN explicit_enabled BOOLEAN DEFAULT 0')
                    logging.info("Added explicit_enabled column to user_profiles table")
                    
                if 'allow_nsfw_content' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN allow_nsfw_content BOOLEAN DEFAULT 0')
                    logging.info("Added allow_nsfw_content column to user_profiles table")
                    
                if 'allow_mature_themes' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN allow_mature_themes BOOLEAN DEFAULT 0')
                    logging.info("Added allow_mature_themes column to user_profiles table")
                    
                if 'allow_violence' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN allow_violence BOOLEAN DEFAULT 0')
                    logging.info("Added allow_violence column to user_profiles table")
                    
                if 'allow_strong_language' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN allow_strong_language BOOLEAN DEFAULT 0')
                    logging.info("Added allow_strong_language column to user_profiles table")
                    
                if 'content_warnings_enabled' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN content_warnings_enabled BOOLEAN DEFAULT 1')
                    logging.info("Added content_warnings_enabled column to user_profiles table")
                    
                if 'safe_mode' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN safe_mode BOOLEAN DEFAULT 1')
                    logging.info("Added safe_mode column to user_profiles table")
                    
                if 'explicit_comfort_level' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN explicit_comfort_level TEXT DEFAULT "none"')
                    logging.info("Added explicit_comfort_level column to user_profiles table")
                    
                if 'roleplay_engagement_level' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN roleplay_engagement_level TEXT DEFAULT "moderate"')
                    logging.info("Added roleplay_engagement_level column to user_profiles table")
                    
                if 'preferred_narrative_style' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN preferred_narrative_style TEXT DEFAULT "conversational"')
                    logging.info("Added preferred_narrative_style column to user_profiles table")
                    
                if 'immersion_preference' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN immersion_preference TEXT DEFAULT "medium"')
                    logging.info("Added immersion_preference column to user_profiles table")
                    
                if 'character_consistency_expectation' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN character_consistency_expectation TEXT DEFAULT "high"')
                    logging.info("Added character_consistency_expectation column to user_profiles table")
                    
                if 'roleplay_experience_level' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN roleplay_experience_level TEXT DEFAULT "intermediate"')
                    logging.info("Added roleplay_experience_level column to user_profiles table")
                    
                if 'bio' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN bio TEXT DEFAULT ""')
                    logging.info("Added bio column to user_profiles table")
                    
                if 'preferences' not in columns:
                    conn.execute('ALTER TABLE user_profiles ADD COLUMN preferences TEXT DEFAULT "{}"')
                    logging.info("Added preferences column to user_profiles table")
            
            # Create default profile if none exists
            cursor = conn.execute('SELECT COUNT(*) FROM user_profiles WHERE user_id = 1')
            profile_count = cursor.fetchone()[0]
            
            if profile_count == 0:
                # Create default profile for first user
                conn.execute('''
                    INSERT INTO user_profiles (user_id, display_name, preferences)
                    VALUES (?, ?, ?)
                ''', (1, 'Administrator', '{}'))
                logging.info("Created default user profile")
                
        logging.info("User tables initialized successfully")
        
    except Exception as e:
        logging.error(f"Error initializing user tables: {str(e)}")
        raise

@users_routes.route('/api/users', methods=['GET'])
def api_get_users():
    """Get all users"""
    try:
        init_user_tables()
        
        with get_users_connection() as conn:
            cursor = conn.execute('''
                SELECT id, username, display_name, email, created_at, last_login, is_active
                FROM users 
                ORDER BY created_at DESC
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'display_name': row[2],
                    'email': row[3],
                    'created_at': row[4],
                    'last_login': row[5],
                    'is_active': bool(row[6])
                })
        
        return jsonify({'users': users})
        
    except Exception as e:
        error_msg = f"Users API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@users_routes.route('/api/users/current', methods=['GET'])
def get_current_user():
    """Get the current active user."""
    try:
        # Initialize tables first
        init_user_tables()
        
        with get_users_connection() as conn:
            # Check if users table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users';
            """)
            
            if not cursor.fetchone():
                return jsonify({'error': 'Users table not initialized'}), 404
            
            # Get the most recent active user
            cursor = conn.execute("""
                SELECT id, username, display_name, email, created_at, last_login, is_active
                FROM users 
                WHERE is_active = 1 
                ORDER BY last_login DESC 
                LIMIT 1
            """)
            
            user = cursor.fetchone()
            
            if user:
                return jsonify({
                    'id': user[0],
                    'username': user[1],
                    'display_name': user[2],
                    'email': user[3],
                    'created_at': user[4],
                    'last_active': user[5],
                    'is_active': bool(user[6])
                })
            else:
                return jsonify({'error': 'No active users found'}), 404
            
    except Exception as e:
        # Log the specific error for debugging
        print(f"Error in get_current_user: {e}")
        return jsonify({'error': 'Database error', 'details': str(e)}), 500

@users_routes.route('/api/users/<int:user_id>/profile', methods=['GET'])
def api_get_user_profile(user_id):
    """Get user profile"""
    try:
        init_user_tables()
        
        # First get user info from users table
        with get_users_connection() as users_conn:
            user_cursor = users_conn.execute('''
                SELECT username, display_name FROM users WHERE id = ?
            ''', (user_id,))
            user_info = user_cursor.fetchone()
            
            if not user_info:
                return jsonify({'error': 'User not found'}), 404
        
        # Then get profile info from user_profiles table
        with get_user_profiles_connection() as profiles_conn:
            profile_cursor = profiles_conn.execute('''
                SELECT user_id, display_name, age, avatar_preferences, conversation_settings, 
                       privacy_settings, theme_preferences, language_preference, timezone,
                       gender, age_range, nsfw_enabled, explicit_enabled, allow_nsfw_content,
                       allow_mature_themes, allow_violence, allow_strong_language, 
                       content_warnings_enabled, safe_mode, explicit_comfort_level,
                       roleplay_engagement_level, preferred_narrative_style, immersion_preference,
                       character_consistency_expectation, roleplay_experience_level, bio, preferences
                FROM user_profiles WHERE user_id = ?
            ''', (user_id,))
            
            profile = profile_cursor.fetchone()
            
            if not profile:
                # Create default profile if it doesn't exist
                profiles_conn.execute('''
                    INSERT INTO user_profiles (user_id, display_name, preferences)
                    VALUES (?, ?, ?)
                ''', (user_id, user_info[1] or user_info[0], '{}'))
                
                # Fetch the newly created profile
                profile_cursor = profiles_conn.execute('''
                    SELECT user_id, display_name, age, avatar_preferences, conversation_settings, 
                           privacy_settings, theme_preferences, language_preference, timezone,
                           gender, age_range, nsfw_enabled, explicit_enabled, allow_nsfw_content,
                           allow_mature_themes, allow_violence, allow_strong_language, 
                           content_warnings_enabled, safe_mode, explicit_comfort_level,
                           roleplay_engagement_level, preferred_narrative_style, immersion_preference,
                           character_consistency_expectation, roleplay_experience_level, bio, preferences
                    FROM user_profiles WHERE user_id = ?
                ''', (user_id,))
                profile = profile_cursor.fetchone()
                
            return jsonify({
                'user_id': profile[0],
                'profile_display_name': profile[1],
                'age': profile[2],
                'avatar_preferences': profile[3],
                'conversation_settings': profile[4],
                'privacy_settings': profile[5],
                'theme_preferences': profile[6],
                'language_preference': profile[7],
                'timezone': profile[8],
                'gender': profile[9],
                'age_range': profile[10],
                'nsfw_enabled': bool(profile[11]) if profile[11] is not None else False,
                'explicit_enabled': bool(profile[12]) if profile[12] is not None else False,
                'allow_nsfw_content': bool(profile[13]) if profile[13] is not None else False,
                'allow_mature_themes': bool(profile[14]) if profile[14] is not None else False,
                'allow_violence': bool(profile[15]) if profile[15] is not None else False,
                'allow_strong_language': bool(profile[16]) if profile[16] is not None else False,
                'content_warnings_enabled': bool(profile[17]) if profile[17] is not None else True,
                'safe_mode': bool(profile[18]) if profile[18] is not None else True,
                'explicit_comfort_level': profile[19] or 'none',
                'roleplay_engagement_level': profile[20] or 'moderate',
                'preferred_narrative_style': profile[21] or 'conversational',
                'immersion_preference': profile[22] or 'medium',
                'character_consistency_expectation': profile[23] or 'high',
                'roleplay_experience_level': profile[24] or 'intermediate',
                'bio': profile[25] or '',
                'preferences': profile[26] or '{}',
                'username': user_info[0],
                'user_display_name': user_info[1]
            })
            
    except Exception as e:
        error_msg = f"Get user profile API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@users_routes.route('/api/users/<int:user_id>/profile', methods=['PUT'])
def api_update_user_profile(user_id):
    """Update user profile via API"""
    try:
        with get_user_profiles_connection() as profiles_conn:
            data = request.get_json()
            
            # Build the UPDATE query dynamically based on provided fields
            update_fields = []
            values = []
            
            field_mapping = {
                'display_name': 'display_name',
                'age': 'age',
                'avatar_preferences': 'avatar_preferences',
                'conversation_settings': 'conversation_settings',
                'privacy_settings': 'privacy_settings',
                'theme_preferences': 'theme_preferences',
                'language_preference': 'language_preference',
                'timezone': 'timezone',
                'gender': 'gender',
                'age_range': 'age_range',
                'nsfw_enabled': 'nsfw_enabled',
                'explicit_enabled': 'explicit_enabled',
                'allow_nsfw_content': 'allow_nsfw_content',
                'allow_mature_themes': 'allow_mature_themes',
                'allow_violence': 'allow_violence',
                'allow_strong_language': 'allow_strong_language',
                'content_warnings_enabled': 'content_warnings_enabled',
                'safe_mode': 'safe_mode',
                'explicit_comfort_level': 'explicit_comfort_level',
                'roleplay_engagement_level': 'roleplay_engagement_level',
                'preferred_narrative_style': 'preferred_narrative_style',
                'immersion_preference': 'immersion_preference',
                'character_consistency_expectation': 'character_consistency_expectation',
                'roleplay_experience_level': 'roleplay_experience_level',
                'bio': 'bio',
                'preferences': 'preferences'
            }
            
            for field, column in field_mapping.items():
                if field in data:
                    update_fields.append(f"{column} = ?")
                    values.append(data[field])
            
            if update_fields:
                update_fields.append("last_updated = CURRENT_TIMESTAMP")
                values.append(user_id)
                
                query = f"UPDATE user_profiles SET {', '.join(update_fields)} WHERE user_id = ?"
                profiles_conn.execute(query, values)
                profiles_conn.commit()
                
                return jsonify({'status': 'success', 'message': 'Profile updated successfully'})
            else:
                return jsonify({'status': 'error', 'message': 'No valid fields provided'}), 400
                
    except Exception as e:
        error_msg = f"Update user profile API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@users_routes.route('/api/users/<int:user_id>/content-preferences', methods=['GET'])
def api_get_user_content_preferences(user_id):
    """Get user content preferences for avatar system"""
    try:
        with get_user_profiles_connection() as profiles_conn:
            cursor = profiles_conn.execute('''
                SELECT allow_nsfw_content, allow_mature_themes, allow_violence, 
                       allow_strong_language, content_warnings_enabled, safe_mode,
                       explicit_comfort_level, roleplay_engagement_level,
                       preferred_narrative_style, immersion_preference,
                       character_consistency_expectation, roleplay_experience_level
                FROM user_profiles WHERE user_id = ?
            ''', (user_id,))
            
            profile = cursor.fetchone()
            
            if not profile:
                # Return safe defaults if no profile exists
                return jsonify({
                    'allow_nsfw_content': False,
                    'allow_mature_themes': False,
                    'allow_violence': False,
                    'allow_strong_language': False,
                    'content_warnings_enabled': True,
                    'safe_mode': True,
                    'explicit_comfort_level': 'none',
                    'roleplay_engagement_level': 'moderate',
                    'preferred_narrative_style': 'conversational',
                    'immersion_preference': 'medium',
                    'character_consistency_expectation': 'high',
                    'roleplay_experience_level': 'intermediate'
                })
            
            return jsonify({
                'allow_nsfw_content': bool(profile[0]) if profile[0] is not None else False,
                'allow_mature_themes': bool(profile[1]) if profile[1] is not None else False,
                'allow_violence': bool(profile[2]) if profile[2] is not None else False,
                'allow_strong_language': bool(profile[3]) if profile[3] is not None else False,
                'content_warnings_enabled': bool(profile[4]) if profile[4] is not None else True,
                'safe_mode': bool(profile[5]) if profile[5] is not None else True,
                'explicit_comfort_level': profile[6] or 'none',
                'roleplay_engagement_level': profile[7] or 'moderate',
                'preferred_narrative_style': profile[8] or 'conversational',
                'immersion_preference': profile[9] or 'medium',
                'character_consistency_expectation': profile[10] or 'high',
                'roleplay_experience_level': profile[11] or 'intermediate'
            })
            
    except Exception as e:
        error_msg = f"Get content preferences API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500
    """Update user profile"""
    try:
        data = request.get_json()
        init_user_tables()
        
        with get_user_profiles_connection() as conn:
            # Update profile
            conn.execute('''
                UPDATE user_profiles SET 
                    display_name = ?, 
                    age = ?, 
                    preferences = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (
                data.get('display_name'),
                data.get('age'),
                json.dumps(data.get('preferences', {})),
                user_id
            ))
            
            return jsonify({'message': 'Profile updated successfully'})
            
    except Exception as e:
        error_msg = f"Update user profile API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@users_routes.route('/api/users', methods=['POST'])
def api_create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        init_user_tables()
        
        with get_users_connection() as conn:
            try:
                # Insert new user
                cursor = conn.execute('''
                    INSERT INTO users (username, display_name, email, password_hash, salt, is_admin, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['username'],
                    data.get('display_name', data['username']),
                    data.get('email', ''),
                    'no_password_yet',
                    'no_salt_yet',
                    data.get('is_admin', False),
                    True
                ))
                
                user_id = cursor.lastrowid
                
                # Create default profile
                with get_user_profiles_connection() as profile_conn:
                    profile_conn.execute('''
                        INSERT INTO user_profiles (user_id, display_name, preferences)
                        VALUES (?, ?, ?)
                    ''', (user_id, data.get('display_name', data['username']), '{}'))
                
                return jsonify({
                    'message': 'User created successfully',
                    'user': {
                        'id': user_id,
                        'username': data['username'],
                        'display_name': data.get('display_name', data['username']),
                        'email': data.get('email', ''),
                        'is_admin': data.get('is_admin', False)
                    }
                })
                
            except sqlite3.IntegrityError as e:
                if 'username' in str(e):
                    return jsonify({'error': 'Username already exists'}), 400
                elif 'email' in str(e):
                    return jsonify({'error': 'Email already exists'}), 400
                else:
                    return jsonify({'error': 'User creation failed'}), 400
        
    except Exception as e:
        error_msg = f"Create user API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@users_routes.route('/api/users/<int:user_id>/activate', methods=['POST'])
def api_activate_user(user_id):
    """Set user as current active user"""
    try:
        init_user_tables()
        
        with get_users_connection() as conn:
            # Update last_active for the selected user
            conn.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user_id,))
            
            # Verify user exists
            cursor = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True, 
            'message': f'User {user[0]} activated successfully'
        })
        
    except Exception as e:
        error_msg = f"Activate user API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@users_routes.route('/api/users/set-current', methods=['POST'])
def api_set_current_user():
    """Set current user for session"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        init_user_tables()
        
        with get_users_connection() as conn:
            # Update last_login for the selected user and set as active
            conn.execute('''
                UPDATE users SET 
                    last_login = CURRENT_TIMESTAMP,
                    is_active = 1
                WHERE id = ?
            ''', (user_id,))
            
            # Set all other users as inactive
            conn.execute('''
                UPDATE users SET is_active = 0 WHERE id != ?
            ''', (user_id,))
            
            # Verify user exists and get info
            cursor = conn.execute('''
                SELECT id, username, display_name, email, is_admin 
                FROM users WHERE id = ?
            ''', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
        
        # Store in session (simple session management)
        session['current_user_id'] = user_id
        session['current_user'] = {
            'id': user[0],
            'username': user[1],
            'display_name': user[2],
            'email': user[3],
            'is_admin': bool(user[4])
        }
        
        return jsonify({
            'success': True, 
            'message': f'Logged in as {user[2] or user[1]}',
            'user': session['current_user']
        })
        
    except Exception as e:
        error_msg = f"Set current user API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@users_routes.route('/api/users/logout', methods=['POST'])
def logout_user():
    """Logout current user"""
    try:
        # Clear session
        session.pop('current_user', None)
        session.pop('current_user_id', None)
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        error_msg = f"Logout API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

# Initialize tables when module is imported
try:
    init_user_tables()
except Exception as e:
    logging.error(f"Failed to initialize user tables on import: {e}")
