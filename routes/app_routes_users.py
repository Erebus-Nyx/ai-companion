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
            
            # Create default user if none exists (compatible with existing schema)
            cursor = conn.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                # Create default user with dummy authentication data for now
                conn.execute('''
                    INSERT INTO users (username, display_name, password_hash, salt, email, is_admin) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ('default_user', 'Default User', 'no_password_yet', 'no_salt_yet', 'default@local', 1))
                logging.info("Created default admin user (password authentication disabled)")
                
        # Initialize user profiles table with our custom fields
        with get_user_profiles_connection() as conn:
            # Check if user_profiles table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new user profiles table
                conn.execute('''
                    CREATE TABLE user_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL UNIQUE,
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
                conn.execute('''
                    INSERT INTO user_profiles (user_id, display_name, gender, age_range) 
                    VALUES (?, ?, ?, ?)
                ''', (1, 'Default User', 'not_specified', 'adult'))
                logging.info("Created default user profile")
        
        logging.info("User tables initialized successfully with authentication compatibility")
        
    except Exception as e:
        logging.error(f"Error initializing user tables: {e}")
        raise

@users_routes.route('/api/users', methods=['GET'])
def api_get_users():
    """Get all users"""
    try:
        init_user_tables()
        
        with get_users_connection() as conn:
            cursor = conn.execute('''
                SELECT id, username, display_name, created_at, last_active, is_active 
                FROM users 
                WHERE is_active = 1
                ORDER BY last_active DESC
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'display_name': row[2],
                    'created_at': row[3],
                    'last_active': row[4],
                    'is_active': bool(row[5])
                })
        
        return jsonify({'users': users})
        
    except Exception as e:
        error_msg = f"Users API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@users_routes.route('/api/users/current', methods=['GET'])
def api_get_current_user():
    """Get current user (defaults to first user for now)"""
    try:
        init_user_tables()
        
        # Simple implementation - get the first active user
        # In a real implementation, this would check session/authentication
        with get_users_connection() as conn:
            cursor = conn.execute('''
                SELECT id, username, display_name, created_at, last_active, is_active 
                FROM users 
                WHERE is_active = 1
                ORDER BY last_active DESC
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            if row:
                user = {
                    'id': row[0],
                    'username': row[1],
                    'display_name': row[2],
                    'created_at': row[3],
                    'last_active': row[4],
                    'is_active': bool(row[5])
                }
                return jsonify(user)
            else:
                return jsonify({'error': 'No active user found'}), 404
        
    except Exception as e:
        error_msg = f"Current user API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@users_routes.route('/api/users/<int:user_id>/profile', methods=['GET'])
def api_get_user_profile(user_id):
    """Get user profile"""
    try:
        init_user_tables()
        
        with get_user_profiles_connection() as conn:
            cursor = conn.execute('''
                SELECT up.*, u.username, u.display_name
                FROM user_profiles up
                JOIN users u ON up.user_id = u.id
                WHERE up.user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                profile = {
                    'id': row[0],
                    'user_id': row[1],
                    'gender': row[2],
                    'age_range': row[3],
                    'nsfw_enabled': bool(row[4]),
                    'explicit_enabled': bool(row[5]),
                    'preferences': json.loads(row[6]) if row[6] else {},
                    'bio': row[7],
                    'created_at': row[8],
                    'updated_at': row[9],
                    'username': row[10],
                    'display_name': row[11]
                }
                return jsonify(profile)
            else:
                return jsonify({'error': f'Profile for user {user_id} not found'}), 404
        
    except Exception as e:
        error_msg = f"User profile API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@users_routes.route('/api/users/<int:user_id>/profile', methods=['PUT'])
def api_update_user_profile(user_id):
    """Update user profile"""
    try:
        init_user_tables()
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate data
        gender = data.get('gender', 'not_specified')
        age_range = data.get('age_range', 'adult')
        nsfw_enabled = bool(data.get('nsfw_enabled', False))
        explicit_enabled = bool(data.get('explicit_enabled', False))
        preferences = data.get('preferences', {})
        bio = data.get('bio', '')
        
        # Update user profile
        with get_user_profiles_connection() as conn:
            # Check if profile exists
            cursor = conn.execute('SELECT id FROM user_profiles WHERE user_id = ?', (user_id,))
            profile_exists = cursor.fetchone()
            
            if profile_exists:
                # Update existing profile
                conn.execute('''
                    UPDATE user_profiles 
                    SET gender = ?, age_range = ?, nsfw_enabled = ?, explicit_enabled = ?, 
                        preferences = ?, bio = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (gender, age_range, nsfw_enabled, explicit_enabled, 
                      json.dumps(preferences), bio, user_id))
            else:
                # Create new profile
                conn.execute('''
                    INSERT INTO user_profiles 
                    (user_id, gender, age_range, nsfw_enabled, explicit_enabled, preferences, bio)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, gender, age_range, nsfw_enabled, explicit_enabled, 
                      json.dumps(preferences), bio))
        
        # Update user's last_active timestamp
        with get_users_connection() as conn:
            conn.execute('''
                UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user_id,))
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
        
    except Exception as e:
        error_msg = f"Update user profile API error: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@users_routes.route('/api/users', methods=['POST'])
def api_create_user():
    """Create a new user"""
    try:
        init_user_tables()
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        display_name = data.get('display_name', '').strip()
        email = data.get('email', '').strip()
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        if not display_name:
            display_name = username
            
        if not email:
            email = f"{username}@local"  # Default local email
        
        with get_users_connection() as conn:
            try:
                # Create user with authentication fields (placeholder values for now)
                cursor = conn.execute('''
                    INSERT INTO users (username, display_name, email, password_hash, salt, is_admin) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (username, display_name, email, 'no_password_yet', 'no_salt_yet', 0))
                
                user_id = cursor.lastrowid
                
                # Create default profile for new user
                with get_user_profiles_connection() as profile_conn:
                    profile_conn.execute('''
                        INSERT INTO user_profiles (user_id, display_name, gender, age_range) 
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, display_name, 'not_specified', 'adult'))
                
                return jsonify({
                    'success': True, 
                    'message': 'User created successfully',
                    'user_id': user_id
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
                UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = ?
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

# Initialize tables when module is imported
try:
    init_user_tables()
except Exception as e:
    logging.error(f"Failed to initialize user tables on import: {e}")
