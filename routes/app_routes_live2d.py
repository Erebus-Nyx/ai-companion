"""
app_routes_live2d.py
Live2D-related Flask route definitions for the AI Companion backend.
"""
from flask import Blueprint, jsonify, request
import os
import time
from datetime import datetime
import app_globals
import logging
import json

logger = logging.getLogger(__name__)
live2d_bp = Blueprint('live2d', __name__)

def analyze_motion_type(motion_file_path):
    """
    Analyze a motion file to determine if it's primarily facial or body motion.
    Returns: dictionary with detailed analysis
    """
    try:
        # Use the new user data directory for Live2D models
        user_data_dir = os.path.expanduser("~/.local/share/ai2d_chat")
        full_path = os.path.join(user_data_dir, motion_file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                motion_data = json.load(f)
                
            curves = motion_data.get('Curves', [])
            
            # Count facial vs body parameters and track specific parameters
            face_params = 0
            body_params = 0
            affected_facial_params = set()
            affected_body_params = set()
            
            facial_indicators = {
                'eye', 'brow', 'mouth', 'tere', 'tear', 'sweat', 'rage',
                'parameye', 'parambrow', 'parammouth', 'paramteary'
            }
            
            body_indicators = {
                'body_angle', 'arm', 'breath', 'hair', 'position', 'rotation',
                'paramposition', 'paramrotation', 'paramarm', 'parambreath'
            }
            
            for curve in curves:
                param_id = curve.get('Id', '').lower()
                
                if any(indicator in param_id for indicator in facial_indicators):
                    face_params += 1
                    affected_facial_params.add(param_id)
                elif any(indicator in param_id for indicator in body_indicators):
                    body_params += 1
                    affected_body_params.add(param_id)
            
            # Determine motion type based on parameter counts
            if face_params > body_params * 2:
                motion_type = 'face'
            elif body_params > face_params * 2:
                motion_type = 'body'
            else:
                motion_type = 'mixed'
            
            return {
                'type': motion_type,
                'face_param_count': face_params,
                'body_param_count': body_params,
                'affected_facial_params': list(affected_facial_params),
                'affected_body_params': list(affected_body_params),
                'has_facial_conflict_potential': face_params > 0,
                'has_body_conflict_potential': body_params > 0
            }
                
    except Exception as e:
        logger.warning(f"Error analyzing motion file {motion_file_path}: {e}")
        return {
            'type': 'unknown',
            'face_param_count': 0,
            'body_param_count': 0,
            'affected_facial_params': [],
            'affected_body_params': [],
            'has_facial_conflict_potential': False,
            'has_body_conflict_potential': False
        }
    
    return {
        'type': 'unknown',
        'face_param_count': 0,
        'body_param_count': 0,
        'affected_facial_params': [],
        'affected_body_params': [],
        'has_facial_conflict_potential': False,
        'has_body_conflict_potential': False
    }

def smart_group_motions(motions_config):
    """
    Intelligently group motions based on file analysis and naming patterns.
    Separates facial expressions from body motions using actual motion file data.
    Also provides conflict detection information.
    """
    motions = {}
    
    # Define emotion/expression keywords for fallback
    emotion_keywords = {
        'angry', 'anger', 'mad', 'rage',
        'sad', 'cry', 'tear', 'upset', 'sorrow',
        'happy', 'smile', 'laugh', 'joy', 'glad',
        'surprise', 'shock', 'gasp', 'wow',
        'blushed', 'blush', 'shy', 'embarrassed',
        'normal', 'neutral', 'default',
        'wink', 'closeeye', 'blink',
        'trouble', 'worry', 'concern',
        'disgust', 'yuck', 'ew',
        'eat', 'delicious', 'yum',
        'hawawa', 'confusion', 'daze'
    }
    
    # Define motion/pose keywords for fallback
    motion_keywords = {
        'pose', 'tilt', 'head', 'nod', 'shake',
        'tap', 'touch', 'pat', 'stroke',
        'wave', 'point', 'gesture',
        'dance', 'move', 'sway',
        'jump', 'hop', 'bounce',
        'idle', 'stand', 'wait'
    }
    
    for motion_name, motion_data in motions_config.items():
        if not isinstance(motion_data, list) or len(motion_data) == 0:
            continue
            
        motion_file = motion_data[0].get('File', '')
        motion_file_name = motion_file.split('/')[-1].replace('.motion3.json', '') if motion_file else motion_name
        
        # Analyze the actual motion file to determine type and conflicts
        motion_analysis = analyze_motion_type(motion_file)
        motion_type = motion_analysis['type']
        
        # Determine the appropriate group based on file analysis + naming patterns
        group_name = 'default'
        motion_name_lower = motion_name.lower()
        
        # Use file analysis as primary categorization method
        if motion_type == 'face':
            # This is primarily a facial expression
            if motion_name_lower.startswith('face_'):
                # Extract the emotion from face motions
                for emotion in emotion_keywords:
                    if emotion in motion_name_lower:
                        if 'band' in motion_name_lower:
                            group_name = f'face_band_{emotion}'
                        elif 'idol' in motion_name_lower:
                            group_name = f'face_idol_{emotion}'
                        else:
                            group_name = f'face_{emotion}'
                        break
                if group_name == 'default':
                    group_name = 'face_other'
            else:
                # Check for emotion keywords in non-face prefixed motions
                for emotion in emotion_keywords:
                    if emotion in motion_name_lower:
                        group_name = f'expressions_{emotion}'
                        break
                if group_name == 'default':
                    group_name = 'expressions_other'
        
        elif motion_type == 'body':
            # This is primarily a body motion
            if any(keyword in motion_name_lower for keyword in motion_keywords):
                if 'adult' in motion_name_lower:
                    # Extract motion type for adult motions
                    for motion_type_kw in motion_keywords:
                        if motion_type_kw in motion_name_lower:
                            group_name = f'adult_{motion_type_kw}'
                            break
                    if group_name == 'default':
                        group_name = 'adult_motion'
                elif 'pose' in motion_name_lower:
                    group_name = 'poses'
                elif 'nod' in motion_name_lower:
                    group_name = 'nod'
                elif 'idle' in motion_name_lower:
                    group_name = 'idle'
                else:
                    group_name = 'body_motion'
            else:
                # Check for emotion keywords in body motions
                for emotion in emotion_keywords:
                    if emotion in motion_name_lower:
                        if 'adult' in motion_name_lower:
                            group_name = f'adult_{emotion}'
                        else:
                            group_name = f'body_{emotion}'
                        break
                if group_name == 'default':
                    group_name = 'body_other'
        
        elif motion_type == 'mixed':
            # This motion affects both face and body - potential conflict source
            # Check if it's emotion-based mixed motion
            for emotion in emotion_keywords:
                if emotion in motion_name_lower:
                    group_name = f'mixed_{emotion}'
                    break
            if group_name == 'default':
                group_name = 'mixed_motion'
        
        else:
            # Fallback to name-based analysis for unknown motion types
            if motion_name_lower.startswith('face_'):
                # Extract the emotion from face motions
                for emotion in emotion_keywords:
                    if emotion in motion_name_lower:
                        if 'band' in motion_name_lower:
                            group_name = f'face_band_{emotion}'
                        elif 'idol' in motion_name_lower:
                            group_name = f'face_idol_{emotion}'
                        else:
                            group_name = f'face_{emotion}'
                        break
                if group_name == 'default':
                    group_name = 'face_other'
            
            # Check for body motions/poses
            elif any(keyword in motion_name_lower for keyword in motion_keywords):
                if 'adult' in motion_name_lower:
                    # Extract motion type for adult motions
                    for motion_type_kw in motion_keywords:
                        if motion_type_kw in motion_name_lower:
                            group_name = f'adult_{motion_type_kw}'
                            break
                    if group_name == 'default':
                        group_name = 'adult_motion'
                elif 'pose' in motion_name_lower:
                    group_name = 'poses'
                elif 'nod' in motion_name_lower:
                    group_name = 'nod'
                elif 'idle' in motion_name_lower:
                    group_name = 'idle'
                else:
                    group_name = 'body_motion'
            
            # Check for emotion-based motions
            elif any(emotion in motion_name_lower for emotion in emotion_keywords):
                for emotion in emotion_keywords:
                    if emotion in motion_name_lower:
                        if 'adult' in motion_name_lower:
                            group_name = f'adult_{emotion}'
                        else:
                            group_name = f'emotion_{emotion}'
                        break
        
        # Create group if it doesn't exist
        if group_name not in motions:
            motions[group_name] = []
        
        # Add motion to the appropriate group with conflict information
        motions[group_name].append({
            'name': motion_file_name,
            'file': motion_file,
            'fadeInTime': motion_data[0].get('FadeInTime', 0.5),
            'fadeOutTime': motion_data[0].get('FadeOutTime', 0.5),
            'index': len(motions[group_name]),
            'conflict_info': {
                'type': motion_analysis['type'],
                'affects_face': motion_analysis['has_facial_conflict_potential'],
                'affects_body': motion_analysis['has_body_conflict_potential'],
                'face_param_count': motion_analysis['face_param_count'],
                'body_param_count': motion_analysis['body_param_count'],
                'affected_facial_params': motion_analysis['affected_facial_params'],
                'affected_body_params': motion_analysis['affected_body_params']
            }
        })
    
    return motions

@live2d_bp.route('/api/live2d/system_status')
def api_live2d_system_status():
    try:
        live2d_manager = app_globals.live2d_manager
        status = {
            'live2d_manager_available': live2d_manager is not None,
            'database_connection': False,
            'models_count': 0,
            'total_motions': 0,
            'models_detail': [],
            'system_info': {
                'assets_directory_exists': os.path.exists('web/static/assets'),
                'available_model_directories': []
            }
        }
        if live2d_manager:
            try:
                models = live2d_manager.get_all_models()
                status['database_connection'] = True
                status['models_count'] = len(models)
                total_motions = 0
                for model in models:
                    model_name = model['model_name']
                    motions = live2d_manager.get_model_motions(model_name)
                    motion_count = len(motions)
                    total_motions += motion_count
                    status['models_detail'].append({
                        'name': model_name,
                        'id': model['id'],
                        'motion_count': motion_count,
                        'model_path': model['model_path'],
                        'config_file': model['config_file']
                    })
                status['total_motions'] = total_motions
            except Exception as e:
                logger.error(f"Error getting Live2D status: {e}")
                status['database_error'] = str(e)
        # Use user data directory for Live2D models
        user_data_dir = os.path.expanduser("~/.local/share/ai2d_chat")
        assets_dir = os.path.join(user_data_dir, "live2d_models")
        if os.path.exists(assets_dir):
            try:
                status['system_info']['available_model_directories'] = [
                    d for d in os.listdir(assets_dir)
                    if os.path.isdir(os.path.join(assets_dir, d))
                ]
            except Exception as e:
                status['system_info']['directory_scan_error'] = str(e)
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/comprehensive_test')
def api_live2d_comprehensive_test():
    try:
        live2d_manager = app_globals.live2d_manager
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0
            }
        }
        def add_test_result(test_name, passed, details=None):
            test_results['tests'][test_name] = {
                'passed': passed,
                'details': details or {}
            }
            test_results['summary']['total_tests'] += 1
            if passed:
                test_results['summary']['passed_tests'] += 1
            else:
                test_results['summary']['failed_tests'] += 1
        manager_available = live2d_manager is not None
        add_test_result('live2d_manager_available', manager_available, {
            'message': 'Live2D manager instance available' if manager_available else 'Live2D manager not initialized'
        })
        try:
            if live2d_manager:
                models = live2d_manager.get_all_models()
                add_test_result('database_connection', True, {
                    'models_count': len(models),
                    'message': f'Database connected, {len(models)} models found'
                })
            else:
                add_test_result('database_connection', False, {
                    'message': 'No Live2D manager available'
                })
        except Exception as e:
            add_test_result('database_connection', False, {
                'error': str(e),
                'message': 'Database connection failed'
            })
        # Use user data directory for Live2D models
        user_data_dir = os.path.expanduser("~/.local/share/ai2d_chat")
        assets_dir = os.path.join(user_data_dir, "live2d_models")
        assets_exist = os.path.exists(assets_dir)
        add_test_result('assets_directory_exists', assets_exist, {
            'path': assets_dir,
            'message': 'Assets directory found' if assets_exist else 'Assets directory missing'
        })
        expected_models = ['kanade', 'kanade_2', 'kuromi', 'miku_2', 'saki_child']
        found_models = []
        missing_models = []
        for model_name in expected_models:
            model_path = os.path.join(assets_dir, model_name)
            if os.path.exists(model_path):
                found_models.append(model_name)
            else:
                missing_models.append(model_name)
        add_test_result('model_assets_available', len(missing_models) == 0, {
            'expected_models': expected_models,
            'found_models': found_models,
            'missing_models': missing_models,
            'message': f'Found {len(found_models)}/{len(expected_models)} expected model directories'
        })
        if live2d_manager:
            try:
                models = live2d_manager.get_all_models()
                total_motions = 0
                models_with_motions = 0
                for model in models:
                    motions = live2d_manager.get_model_motions(model['model_name'])
                    motion_count = len(motions)
                    total_motions += motion_count
                    if motion_count > 0:
                        models_with_motions += 1
                add_test_result('motion_data_available', total_motions > 0, {
                    'total_motions': total_motions,
                    'models_with_motions': models_with_motions,
                    'total_models': len(models),
                    'message': f'{total_motions} motions available across {models_with_motions} models'
                })
            except Exception as e:
                add_test_result('motion_data_available', False, {
                    'error': str(e),
                    'message': 'Failed to check motion data'
                })
        else:
            add_test_result('motion_data_available', False, {
                'message': 'Cannot check motion data - no Live2D manager'
            })
        if test_results['summary']['total_tests'] > 0:
            success_rate = (test_results['summary']['passed_tests'] / test_results['summary']['total_tests']) * 100
            test_results['summary']['success_rate'] = round(success_rate, 1)
        else:
            test_results['summary']['success_rate'] = 0
        logger.info(f"🧪 Comprehensive test completed: {test_results['summary']['passed_tests']}/{test_results['summary']['total_tests']} tests passed")
        return jsonify(test_results)
    except Exception as e:
        logger.error(f"Error running comprehensive test: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/debug_paths')
def api_debug_paths():
    """Debug endpoint to check path resolution"""
    import os
    import sys
    user_data_dir = os.path.expanduser("~/.local/share/ai2d_chat")
    live2d_models_path = os.path.join(user_data_dir, "live2d_models")
    return jsonify({
        'current_working_directory': os.getcwd(),
        'python_path': sys.path[0] if sys.path else None,
        'user_data_directory': user_data_dir,
        'live2d_models_path': live2d_models_path,
        'path_tests': {
            'user_data_dir_exists': os.path.exists(user_data_dir),
            'live2d_models_exists': os.path.exists(live2d_models_path),
            'old_web_static_assets': os.path.exists('web/static/assets'),
            'old_web_static_assets': os.path.exists('web/static/assets'),
        },
        'directory_listings': {
            'current_dir': os.listdir('.') if os.path.exists('.') else 'Not found',
            'live2d_models_contents': os.listdir(live2d_models_path) if os.path.exists(live2d_models_path) else 'Not found',
            'web_exists': os.path.exists('web'),
            'web_static_exists': os.path.exists('web/static') if os.path.exists('web') else False
        }
    })

@live2d_bp.route('/api/live2d/models')
def api_live2d_models():
    """Get all available Live2D models"""
    try:
        live2d_manager = app_globals.live2d_manager
        if not live2d_manager:
            return jsonify({'error': 'Live2D manager not available'}), 500
        
        models = live2d_manager.get_all_models()
        return jsonify(models)
    except Exception as e:
        logger.error(f"Error getting Live2D models: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/models/detailed')
def api_live2d_models_detailed():
    """Get detailed model information for chat system integration"""
    try:
        live2d_manager = app_globals.live2d_manager
        if not live2d_manager:
            return jsonify({'error': 'Live2D manager not available'}), 500
        
        models = live2d_manager.get_all_models()
        detailed_models = []
        
        for model in models:
            model_info = live2d_manager.get_model_info(model['model_name'])
            if model_info:
                detailed_models.append(model_info)
            else:
                # Fallback to basic info if detailed lookup fails
                detailed_models.append({
                    'model_name': model['model_name'],
                    'description': model.get('description', ''),
                    'motions': {},
                    'expressions': {},
                    'motion_count': 0
                })
        
        return jsonify(detailed_models)
    except Exception as e:
        logger.error(f"Error getting detailed Live2D models: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/loaded_models')
def api_live2d_loaded_models():
    """Get currently loaded Live2D models from the frontend"""
    try:
        # Return the currently loaded models tracked by SocketIO
        return jsonify(app_globals.loaded_models)
    except Exception as e:
        logger.error(f"Error getting loaded Live2D models: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/model/<model_name>/expressions')
def api_live2d_model_expressions(model_name):
    """Get expressions for a specific Live2D model"""
    try:
        live2d_manager = app_globals.live2d_manager
        if not live2d_manager:
            return jsonify({'error': 'Live2D manager not available'}), 500
        
        # Get model information
        models = live2d_manager.get_all_models()
        model = next((m for m in models if m['model_name'] == model_name), None)
        
        if not model:
            return jsonify({'error': f'Model {model_name} not found'}), 404
        
        # Try to load model configuration to get expressions
        user_data_dir = os.path.expanduser("~/.local/share/ai2d_chat")
        model_config_path = os.path.join(user_data_dir, "live2d_models", model_name, model['config_file'])
        expressions = []
        
        if os.path.exists(model_config_path):
            try:
                with open(model_config_path, 'r') as f:
                    config = json.load(f)
                    
                # Handle different Live2D model formats
                if 'FileReferences' in config and 'Expressions' in config['FileReferences']:
                    for expr in config['FileReferences']['Expressions']:
                        expressions.append({
                            'name': expr.get('Name', 'unknown'),
                            'file': expr.get('File', '')
                        })
                elif 'expressions' in config:
                    for expr in config['expressions']:
                        expressions.append({
                            'name': expr.get('name', 'unknown'),
                            'file': expr.get('file', '')
                        })
            except Exception as e:
                logger.warning(f"Error reading model config for {model_name}: {e}")
        
        # If no expressions found, provide mock data
        if not expressions:
            expressions = [
                {'name': 'happy', 'file': 'expressions/happy.exp3.json'},
                {'name': 'sad', 'file': 'expressions/sad.exp3.json'},
                {'name': 'surprised', 'file': 'expressions/surprised.exp3.json'},
                {'name': 'angry', 'file': 'expressions/angry.exp3.json'},
                {'name': 'neutral', 'file': 'expressions/neutral.exp3.json'}
            ]
        
        return jsonify({
            'model_name': model_name,
            'expressions': expressions,
            'total_expressions': len(expressions)
        })
        
    except Exception as e:
        logger.error(f"Error getting expressions for model {model_name}: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/model/<model_name>/motions')
@live2d_bp.route('/api/live2d/motions/<model_name>')
def api_live2d_model_motions(model_name):
    """Get motions for a specific Live2D model"""
    try:
        live2d_manager = app_globals.live2d_manager
        if not live2d_manager:
            return jsonify({'error': 'Live2D manager not available'}), 500
        
        # Get model information
        models = live2d_manager.get_all_models()
        model = next((m for m in models if m['model_name'] == model_name), None)
        
        if not model:
            return jsonify({'error': f'Model {model_name} not found'}), 404
        
        # Try to get motions from model configuration file first
        user_data_dir = os.path.expanduser("~/.local/share/ai2d_chat")
        model_config_path = os.path.join(user_data_dir, "live2d_models", model_name, model['config_file'])
        motions = {}
        
        if os.path.exists(model_config_path):
            try:
                with open(model_config_path, 'r') as f:
                    config = json.load(f)                    # Handle different Live2D model formats
                    if 'FileReferences' in config and 'Motions' in config['FileReferences']:
                        motions_config = config['FileReferences']['Motions']
                        if isinstance(motions_config, dict):
                            # Check if this is a model with many individual motion entries (like miku_2)
                            if len(motions_config) > 50:  # Threshold for "many individual motions"
                                # Smart grouping for models with individual motion entries
                                motions = smart_group_motions(motions_config)
                            else:
                                # Standard grouping for properly grouped models
                                for motion_group, motion_list in motions_config.items():
                                    if not motion_group or motion_group.strip() == '':
                                        motion_group = 'default'
                                    motions[motion_group] = []
                                    if isinstance(motion_list, list):
                                        for i, motion in enumerate(motion_list):
                                            motion_file = motion.get('File', '')
                                            # Extract motion name from file path
                                            motion_name = motion_file.split('/')[-1].replace('.motion3.json', '') if motion_file else f'{motion_group}_{i:02d}'
                                            motions[motion_group].append({
                                                'name': motion_name,
                                                'file': motion_file,
                                                'fadeInTime': motion.get('FadeInTime', 0.5),
                                                'fadeOutTime': motion.get('FadeOutTime', 0.5),
                                                'index': i
                                            })
                    elif 'motions' in config:
                        motions_config = config['motions']
                        if isinstance(motions_config, dict):
                            for motion_group, motion_list in motions_config.items():
                                if not motion_group or motion_group.strip() == '':
                                    motion_group = 'default'
                                motions[motion_group] = []
                                if isinstance(motion_list, list):
                                    for i, motion in enumerate(motion_list):
                                        motion_file = motion.get('file', '')
                                        # Extract motion name from file path
                                        motion_name = motion_file.split('/')[-1].replace('.motion3.json', '') if motion_file else f'{motion_group}_{i:02d}'
                                        motions[motion_group].append({
                                            'name': motion_name,
                                        'file': motion_file,
                                        'fadeInTime': motion.get('fadeInTime', 0.5),
                                        'fadeOutTime': motion.get('fadeOutTime', 0.5),
                                        'index': i
                                    })
            except Exception as e:
                logger.warning(f"Error reading model config for {model_name}: {e}")
        
        # Fallback to database if config file reading failed
        if not motions:
            motions_data = live2d_manager.get_model_motions(model_name)
            if motions_data:
                for motion in motions_data:
                    group = motion.get('motion_group', 'default')
                    if not group or group.strip() == '':
                        group = 'default'
                    
                    motion_name = motion.get('motion_name', '')
                    if not motion_name or motion_name.strip() == '' or motion_name == 'unknown':
                        # Generate name from motion index or file pattern
                        motion_index = motion.get('motion_index', 0)
                        motion_name = f"{group}_{motion_index:02d}" if group != 'default' else f"motion_{motion_index:02d}"
                    
                    if group not in motions:
                        motions[group] = []
                    
                    motions[group].append({
                        'name': motion_name,
                        'file': f"motions/{motion_name}.motion3.json",
                        'fadeInTime': 0.5,
                        'fadeOutTime': 0.5,
                        'index': motion.get('motion_index', 0)
                    })
        
        # If still no motions found, provide fallback data
        if not motions:
            motions = {
                'idle': [
                    {'name': 'idle_01', 'file': 'motions/idle_01.motion3.json', 'fadeInTime': 0.5, 'fadeOutTime': 0.5, 'index': 0},
                    {'name': 'idle_02', 'file': 'motions/idle_02.motion3.json', 'fadeInTime': 0.5, 'fadeOutTime': 0.5, 'index': 1}
                ],
                'tap': [
                    {'name': 'tap_01', 'file': 'motions/tap_01.motion3.json', 'fadeInTime': 0.5, 'fadeOutTime': 0.5, 'index': 0}
                ]
            }
        
        # Clean up any empty groups
        motions = {k: v for k, v in motions.items() if v and len(v) > 0}
        
        # Calculate total motions and get group list
        total_motions = sum(len(motion_list) for motion_list in motions.values())
        motion_groups = list(motions.keys())
        
        return jsonify({
            'model_name': model_name,
            'motions': motions,
            'total_motions': total_motions,
            'motion_groups': motion_groups
        })
        
    except Exception as e:
        logger.error(f"Error getting motions for model {model_name}: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/model/<model_name>/animation_compatibility')
def api_live2d_animation_compatibility(model_name):
    """Get animation compatibility information for conflict prevention"""
    try:
        live2d_manager = app_globals.live2d_manager
        if not live2d_manager:
            return jsonify({'error': 'Live2D manager not available'}), 500
        
        # Get model information
        models = live2d_manager.get_all_models()
        model = next((m for m in models if m['model_name'] == model_name), None)
        
        if not model:
            return jsonify({'error': f'Model {model_name} not found'}), 404
        
        # Get motions with conflict information
        user_data_dir = os.path.expanduser("~/.local/share/ai2d_chat")
        model_config_path = os.path.join(user_data_dir, "live2d_models", model_name, model['config_file'])
        compatibility_rules = {
            'face_only_groups': [],
            'body_only_groups': [],
            'mixed_groups': [],
            'safe_combinations': [],
            'conflicting_combinations': [],
            'motion_details': {}
        }
        
        if os.path.exists(model_config_path):
            try:
                with open(model_config_path, 'r') as f:
                    config = json.load(f)
                    
                if 'FileReferences' in config and 'Motions' in config['FileReferences']:
                    motions_config = config['FileReferences']['Motions']
                    if isinstance(motions_config, dict) and len(motions_config) > 50:
                        # Get detailed motion analysis
                        analyzed_motions = smart_group_motions(motions_config)
                        
                        for group_name, motion_list in analyzed_motions.items():
                            if not motion_list:
                                continue
                                
                            # Analyze the group type based on the motions within it
                            group_affects_face = any(motion.get('conflict_info', {}).get('affects_face', False) for motion in motion_list)
                            group_affects_body = any(motion.get('conflict_info', {}).get('affects_body', False) for motion in motion_list)
                            
                            if group_affects_face and group_affects_body:
                                compatibility_rules['mixed_groups'].append(group_name)
                            elif group_affects_face:
                                compatibility_rules['face_only_groups'].append(group_name)
                            elif group_affects_body:
                                compatibility_rules['body_only_groups'].append(group_name)
                            
                            # Store detailed motion information
                            compatibility_rules['motion_details'][group_name] = []
                            for motion in motion_list:
                                compatibility_rules['motion_details'][group_name].append({
                                    'name': motion['name'],
                                    'file': motion['file'],
                                    'type': motion.get('conflict_info', {}).get('type', 'unknown'),
                                    'affects_face': motion.get('conflict_info', {}).get('affects_face', False),
                                    'affects_body': motion.get('conflict_info', {}).get('affects_body', False),
                                    'facial_params': motion.get('conflict_info', {}).get('affected_facial_params', []),
                                    'body_params': motion.get('conflict_info', {}).get('affected_body_params', [])
                                })
                        
                        # Generate safe and conflicting combinations
                        all_groups = list(analyzed_motions.keys())
                        for i, group1 in enumerate(all_groups):
                            for group2 in all_groups[i+1:]:
                                group1_affects_face = group1 in compatibility_rules['face_only_groups'] or group1 in compatibility_rules['mixed_groups']
                                group1_affects_body = group1 in compatibility_rules['body_only_groups'] or group1 in compatibility_rules['mixed_groups']
                                group2_affects_face = group2 in compatibility_rules['face_only_groups'] or group2 in compatibility_rules['mixed_groups']
                                group2_affects_body = group2 in compatibility_rules['body_only_groups'] or group2 in compatibility_rules['mixed_groups']
                                
                                # Check for conflicts
                                has_face_conflict = group1_affects_face and group2_affects_face
                                has_body_conflict = group1_affects_body and group2_affects_body
                                
                                if has_face_conflict or has_body_conflict:
                                    compatibility_rules['conflicting_combinations'].append({
                                        'group1': group1,
                                        'group2': group2,
                                        'conflict_type': 'face' if has_face_conflict else 'body',
                                        'reason': f"Both groups affect {'facial' if has_face_conflict else 'body'} parameters"
                                    })
                                else:
                                    compatibility_rules['safe_combinations'].append({
                                        'group1': group1,
                                        'group2': group2,
                                        'reason': 'No parameter conflicts detected'
                                    })
                        
            except Exception as e:
                logger.warning(f"Error analyzing compatibility for {model_name}: {e}")
        
        return jsonify({
            'model_name': model_name,
            'compatibility_rules': compatibility_rules,
            'recommendations': {
                'for_random_animation': 'Avoid mixing face_* and mixed_* groups simultaneously',
                'for_expression_overlay': 'Use face_* groups only, avoid mixed_* groups',
                'for_body_animation': 'Use body_* groups, safe to combine with face_* expressions',
                'animation_priority': 'expressions > face_motions > body_motions > mixed_motions'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting animation compatibility for model {model_name}: {e}")
        return jsonify({'error': str(e)}), 500

# Debug endpoint to check model data
@live2d_bp.route('/debug/model/<model_name>')
def debug_model_data(model_name):
    """Debug endpoint to check model data."""
    try:
        live2d_manager = app_globals.live2d_manager
        if not live2d_manager:
            return jsonify({'error': 'Live2D manager not initialized'}), 500
        
        # Get all models and find the one we want
        models = live2d_manager.get_all_models()
        model_info = None
        for model in models:
            if model['model_name'] == model_name:
                model_info = model
                break
        
        if not model_info:
            return jsonify({'error': f'Model {model_name} not found'}), 404
        
        # Debug the path construction
        debug_info = {
            'model_info': model_info,
            'model_path_raw': model_info['model_path'],
            'config_file_raw': model_info['config_file'],
            'constructed_path': f"web{model_info['model_path']}/{model_info['config_file']}"
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add API route for texture requests
@live2d_bp.route('/api/live2d/textures/<model_name>')
def api_live2d_model_textures(model_name):
    """API endpoint for getting model textures via API path."""
    return get_model_textures(model_name)

@live2d_bp.route('/textures/<model_name>')
def get_model_textures(model_name):
    """
    Get texture information for a specific Live2D model.
    Returns texture file paths and metadata.
    """
    try:
        # Get model manager
        live2d_manager = app_globals.live2d_manager
        if not live2d_manager:
            return jsonify({'error': 'Live2D manager not initialized'}), 500
        
        # Find the model
        model_info = None
        models = live2d_manager.get_all_models()
        logger.info(f"DEBUG: Found {len(models)} models")
        for model in models:
            logger.info(f"DEBUG: Model {model['model_name']} has path '{model['model_path']}'")
            if model['model_name'] == model_name:
                model_info = model
                break
        
        if not model_info:
            return jsonify({'error': f'Model {model_name} not found'}), 404
        
        # Read model configuration
        # model_path is now like static/assets/miku_1, Flask runs from root so we need web/ prefix
        model_config_path = f"web/{model_info['model_path']}/{model_info['config_file']}"
        logger.info(f"DEBUG: model_config_path = '{model_config_path}'")
        
        if not os.path.exists(model_config_path):
            return jsonify({'error': f'Model config file not found: {model_config_path}'}), 404
        
        with open(model_config_path, 'r') as f:
            model_config = json.load(f)
        
        # Extract texture information
        textures = []
        texture_files = []
        
        # Check different possible texture locations
        if 'textures' in model_config:
            texture_files = model_config['textures']
        elif 'FileReferences' in model_config:
            if 'Textures' in model_config['FileReferences']:
                texture_files = model_config['FileReferences']['Textures']
            elif 'Texture' in model_config['FileReferences']:
                texture_files = [model_config['FileReferences']['Texture']]
        
        # Process each texture
        for texture_file in texture_files:
            # Texture paths in model config are relative to the config file
            # If config is in runtime/model.json, then textures are relative to runtime/
            config_dir = os.path.dirname(model_info['config_file'])
            if config_dir:
                texture_relative_path = f"{config_dir}/{texture_file}"
            else:
                texture_relative_path = texture_file
            
            # Construct full paths
            texture_path = f"/{model_info['model_path']}/{texture_relative_path}"
            full_texture_path = f"web{texture_path}"  # Flask runs from root so we need web/ prefix
            
            texture_info = {
                'filename': texture_file,
                'path': texture_path,
                'url': texture_path,  # This will be like /static/assets/miku_1/runtime/texture_00.png
                'exists': os.path.exists(full_texture_path)
            }
            
            # Get file size if it exists
            if texture_info['exists']:
                try:
                    stat = os.stat(full_texture_path)
                    texture_info['size'] = stat.st_size
                    texture_info['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                except Exception as e:
                    logger.warning(f"Could not get file info for {full_texture_path}: {e}")
            
            textures.append(texture_info)
        
        return jsonify({
            'model_name': model_name,
            'textures': textures,
            'primary_texture': textures[0] if textures else None,
            'texture_count': len(textures)
        })
        
    except Exception as e:
        logger.error(f"Error getting textures for model {model_name}: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/preview/<model_name>')
def api_live2d_model_preview(model_name):
    """
    Get a cached preview image for a Live2D model from the database.
    Returns the base64 preview data if available.
    """
    try:
        # Get model manager
        live2d_manager = app_globals.live2d_manager
        if not live2d_manager:
            return jsonify({'error': 'Live2D manager not initialized'}), 500
        
        # Get cached preview from database
        preview_data = live2d_manager.get_model_preview(model_name)
        
        if preview_data:
            return jsonify({
                'model_name': model_name,
                'preview': preview_data,
                'cached': True,
                'success': True
            })
        else:
            return jsonify({
                'model_name': model_name,
                'preview': None,
                'cached': False,
                'success': False,
                'message': 'No cached preview found - generate one in the frontend'
            }), 404
        
    except Exception as e:
        logger.error(f"Error getting preview for model {model_name}: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/preview/<model_name>', methods=['POST'])
def api_live2d_save_model_preview(model_name):
    """Save preview image for a Live2D model to database"""
    try:
        live2d_manager = app_globals.live2d_manager
        if not live2d_manager:
            return jsonify({'error': 'Live2D manager not initialized'}), 500
        
        data = request.get_json()
        if not data or 'preview' not in data:
            return jsonify({'error': 'No preview data provided'}), 400
        
        preview_data = data['preview']
        success = live2d_manager.save_model_preview(model_name, preview_data)
        
        if success:
            return jsonify({
                'success': True,
                'model_name': model_name,
                'message': 'Preview saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save preview',
                'model_name': model_name
            }), 500
            
    except Exception as e:
        logger.error(f"Error saving model preview: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/preview/<model_name>/check')
def api_live2d_check_model_preview(model_name):
    """Check if a model has a cached preview image"""
    try:
        live2d_manager = app_globals.live2d_manager
        if not live2d_manager:
            return jsonify({'error': 'Live2D manager not initialized'}), 500
        
        has_preview = live2d_manager.has_model_preview(model_name)
        
        return jsonify({
            'success': True,
            'has_preview': has_preview,
            'model_name': model_name
        })
            
    except Exception as e:
        logger.error(f"Error checking model preview: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/models/import', methods=['POST'])
def import_live2d_model():
    """Import a new Live2D model with ZIP file upload and character data"""
    try:
        # Only support file upload scenario (ZIP files only)
        if 'model_files' in request.files:
            return handle_model_file_upload()
        else:
            return jsonify({
                'error': 'Live2D models must be uploaded as ZIP archives to preserve directory structure. Please upload a .zip file containing your complete model package.'
            }), 400
            
    except Exception as e:
        logger.error(f"Error importing Live2D model: {e}")
        return jsonify({'error': str(e)}), 500

def handle_model_file_upload():
    """Handle uploading model files and registering the model"""
    try:
        from werkzeug.utils import secure_filename
        from pathlib import Path
        import zipfile
        import tempfile
        import shutil
        
        files = request.files.getlist('model_files')
        model_name = request.form.get('model_name')
        character_data = request.form.get('character_data')
        
        if not model_name:
            return jsonify({'error': 'model_name is required'}), 400
        
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        # Enforce zip-only uploads to preserve directory structure
        non_zip_files = [f.filename for f in files if f.filename and not f.filename.lower().endswith('.zip')]
        if non_zip_files:
            return jsonify({
                'error': 'Live2D models must be uploaded as .zip archives to preserve the complete directory structure with motions, textures, and other assets.',
                'invalid_files': non_zip_files
            }), 400
        
        # Get models directory
        try:
            from config.config_manager import ConfigManager
            config_manager = ConfigManager()
            models_base_path = config_manager.get_live2d_models_path()
        except ImportError:
            models_base_path = Path.home() / ".local/share/ai2d_chat/live2d_models"
        
        model_dir = models_base_path / secure_filename(model_name)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = None
        uploaded_files = []
        
        # Handle uploaded zip files
        for file in files:
            if file.filename and file.filename.lower().endswith('.zip'):
                filename = secure_filename(file.filename)
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_zip = Path(temp_dir) / filename
                    file.save(temp_zip)
                    
                    # Extract zip and preserve directory structure
                    with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                        zip_ref.extractall(model_dir)
                        uploaded_files.extend([model_dir / name for name in zip_ref.namelist()])
        
        # Find config file in extracted contents
        config_files = list(model_dir.rglob('*.model3.json'))
        if config_files:
            config_file = str(config_files[0].relative_to(models_base_path))
        
        if not config_file:
            # Clean up on failure
            shutil.rmtree(model_dir, ignore_errors=True)
            return jsonify({
                'error': 'No .model3.json config file found in uploaded zip archive. Please ensure your Live2D model package is complete.'
            }), 400
        
        # Register the model
        from databases.live2d_models_separated import Live2DModelsDB
        live2d_db = Live2DModelsDB()
        
        model_id = live2d_db.register_model(
            model_name=model_name,
            model_path=str(model_dir.relative_to(models_base_path)),
            config_file=config_file,
            description=f"Imported Live2D model: {model_name}"
        )
        
        # Scan and register motions
        live2d_db.scan_and_register_motions(model_name, str(model_dir))
        
        # Create personality data if character_data provided
        if character_data:
            try:
                char_data = json.loads(character_data)
                from databases.database_manager import DatabaseManager
                db_manager = DatabaseManager()
                db_manager.create_model_personality(model_name.lower(), char_data)
            except json.JSONDecodeError:
                logger.warning(f"Invalid character_data JSON for model {model_name}")
            except Exception as e:
                logger.warning(f"Failed to create personality for model {model_name}: {e}")
        
        return jsonify({
            'success': True,
            'model_id': model_id,
            'model_name': model_name,
            'config_file': config_file,
            'uploaded_files': [str(f) for f in uploaded_files],
            'message': f'Successfully imported model: {model_name}'
        })
        
    except Exception as e:
        logger.error(f"Error handling model file upload: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/characters', methods=['GET'])
def get_all_characters():
    """Get list of all available characters/personalities"""
    try:
        from databases.database_manager import DatabaseManager
        from databases.live2d_models_separated import Live2DModelsDB
        
        db_manager = DatabaseManager()
        live2d_db = Live2DModelsDB()
        
        # Get all registered models
        models = live2d_db.get_all_models()
        characters = []
        
        for model in models:
            try:
                personality = db_manager.get_model_personality(model['model_name'].lower())
                if personality:
                    characters.append({
                        'model_id': model['model_name'].lower(),
                        'model_name': model['model_name'],
                        'name': personality.get('name', model['model_name']),
                        'description': personality.get('description', ''),
                        'personality_notes': personality.get('personality_notes', ''),
                        'appearance_notes': personality.get('appearance_notes', ''),
                        'has_character_data': True
                    })
                else:
                    # Model without character data
                    characters.append({
                        'model_id': model['model_name'].lower(),
                        'model_name': model['model_name'],
                        'name': model['model_name'],
                        'description': model.get('description', ''),
                        'personality_notes': '',
                        'appearance_notes': '',
                        'has_character_data': False
                    })
            except Exception as e:
                logger.warning(f"Error getting personality for model {model['model_name']}: {e}")
                # Still include the model without character data
                characters.append({
                    'model_id': model['model_name'].lower(),
                    'model_name': model['model_name'],
                    'name': model['model_name'],
                    'description': model.get('description', ''),
                    'personality_notes': '',
                    'appearance_notes': '',
                    'has_character_data': False
                })
        
        return jsonify(characters)
        
    except Exception as e:
        logger.error(f"Error getting all characters: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/models/<model_name>/character', methods=['GET'])
def get_character_data(model_name):
    """Get character/personality data for a model"""
    try:
        from databases.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        personality = db_manager.get_model_personality(model_name.lower())
        
        if not personality:
            return jsonify({'error': f'No character data found for model: {model_name}'}), 404
        
        return jsonify({
            'model_id': model_name.lower(),
            'character_data': personality
        })
        
    except Exception as e:
        logger.error(f"Error getting character data for {model_name}: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/models/<model_name>/character', methods=['PUT'])
def update_character_data(model_name):
    """Update character/personality data for a model"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        from databases.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        # Extract updatable fields
        update_fields = {}
        
        # Direct personality fields
        for field in ['name', 'description', 'background_story', 'favorite_things', 
                     'personality_notes', 'appearance_notes']:
            if field in data:
                update_fields[field] = data[field]
        
        # Trait data (should be JSON serializable)
        for field in ['base_traits', 'current_traits']:
            if field in data:
                update_fields[field] = data[field]
        
        # Handle character_data structure (from characters.json format)
        if 'character_data' in data:
            char_data = data['character_data']
            
            # Extract basic info
            basic_info = char_data.get('basic_info', {})
            if basic_info.get('display_name'):
                update_fields['name'] = basic_info['display_name']
            
            # Extract personality info
            personality = char_data.get('personality', {})
            if personality.get('archetype'):
                update_fields['description'] = personality['archetype']
            
            # Extract and convert traits
            core_traits = personality.get('core_traits', [])
            if core_traits:
                traits = {trait: 0.8 for trait in core_traits}
                update_fields['base_traits'] = traits
                update_fields['current_traits'] = traits
            
            # Extract backstory
            backstory = char_data.get('backstory', {})
            if backstory.get('origin'):
                background = backstory['origin']
                if backstory.get('motivation'):
                    background += f" {backstory['motivation']}"
                update_fields['background_story'] = background
            
            # Extract interests as favorite things
            behavioral = char_data.get('behavioral_patterns', {})
            interests = behavioral.get('interests', [])
            if interests:
                update_fields['favorite_things'] = ', '.join(interests)
            
            # Extract appearance notes
            appearance = char_data.get('appearance', {})
            appearance_notes = []
            
            physical = appearance.get('physical', {})
            if physical.get('eye_color'):
                appearance_notes.append(f"Eyes: {physical['eye_color']}")
            if physical.get('skin_tone'):
                appearance_notes.append(f"Skin: {physical['skin_tone']}")
            
            hair = appearance.get('hair', {})
            if hair.get('color'):
                hair_desc = f"Hair: {hair['color']}"
                if hair.get('length'):
                    hair_desc += f" {hair['length']}"
                appearance_notes.append(hair_desc)
            
            if appearance_notes:
                update_fields['appearance_notes'] = '; '.join(appearance_notes)
        
        if not update_fields:
            return jsonify({'error': 'No valid update fields provided'}), 400
        
        # Update the personality
        db_manager.update_model_personality(model_name.lower(), **update_fields)
        
        # Get updated data
        updated_personality = db_manager.get_model_personality(model_name.lower())
        
        return jsonify({
            'success': True,
            'model_id': model_name.lower(),
            'updated_fields': list(update_fields.keys()),
            'character_data': updated_personality,
            'message': f'Successfully updated character data for {model_name}'
        })
        
    except Exception as e:
        logger.error(f"Error updating character data for {model_name}: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/models/<model_name>/character', methods=['POST'])
def create_character_data(model_name):
    """Create new character/personality data for a model"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No character data provided'}), 400
        
        from databases.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        # Check if personality already exists
        existing = db_manager.get_model_personality(model_name.lower())
        if existing:
            return jsonify({'error': f'Character data already exists for model: {model_name}'}), 409
        
        # Create personality data
        character_data = data.get('character_data', data)
        db_manager.create_model_personality(model_name.lower(), character_data)
        
        # Get created data
        created_personality = db_manager.get_model_personality(model_name.lower())
        
        return jsonify({
            'success': True,
            'model_id': model_name.lower(),
            'character_data': created_personality,
            'message': f'Successfully created character data for {model_name}'
        })
        
    except Exception as e:
        logger.error(f"Error creating character data for {model_name}: {e}")
        return jsonify({'error': str(e)}), 500

@live2d_bp.route('/api/live2d/models/scan', methods=['POST'])
def scan_and_import_models():
    """Scan the models directory and import any new models found"""
    try:
        data = request.get_json() or {}
        create_personalities = data.get('create_personalities', True)
        
        from databases.live2d_models_separated import Live2DModelsDB
        live2d_db = Live2DModelsDB()
        
        # Scan for models
        live2d_db.scan_and_register_models()
        
        # Get all models after scan
        models = live2d_db.get_all_models()
        
        # Create personalities for models that don't have them
        created_personalities = []
        if create_personalities:
            from databases.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            for model in models:
                model_name = model['model_name']
                personality = db_manager.get_model_personality(model_name.lower())
                if not personality:
                    # Try to load character data from characters.json
                    try:
                        from pathlib import Path
                        characters_path = Path(__file__).parent.parent / "databases" / "characters.json"
                        character_data = None
                        
                        if characters_path.exists():
                            with open(characters_path, 'r') as f:
                                characters = json.load(f).get('characters', {})
                                character_data = characters.get(model_name.lower())
                        
                        db_manager.create_model_personality(model_name.lower(), character_data)
                        created_personalities.append(model_name)
                    except Exception as e:
                        logger.warning(f"Failed to create personality for {model_name}: {e}")
        
        return jsonify({
            'success': True,
            'models_found': len(models),
            'personalities_created': len(created_personalities),
            'created_personalities': created_personalities,
            'models': [{'name': m['model_name'], 'id': m['id']} for m in models],
            'message': f'Scan complete. Found {len(models)} models, created {len(created_personalities)} personalities.'
        })
        
    except Exception as e:
        logger.error(f"Error scanning and importing models: {e}")
        return jsonify({'error': str(e)}), 500


# SocketIO Events for Live2D Model Tracking
def setup_live2d_socketio_handlers(socketio):
    """Setup SocketIO handlers for Live2D model tracking"""
    
    @socketio.on('live2d_models_updated')
    def handle_models_updated(data):
        """Handle when the frontend updates the list of loaded models"""
        try:
            models = data.get('models', [])
            app_globals.loaded_models = models
            logger.info(f"Updated loaded models: {[m.get('name', 'Unknown') for m in models]}")
            
            # Emit to all clients that models have been updated
            socketio.emit('loaded_models_changed', {'models': models})
            
        except Exception as e:
            logger.error(f"Error handling models updated: {e}")
    
    @socketio.on('live2d_model_loaded')
    def handle_model_loaded(data):
        """Handle when a model is loaded"""
        try:
            model_name = data.get('modelName')
            model_info = data.get('modelInfo', {})
            
            # Add to loaded models if not already present
            existing = next((m for m in app_globals.loaded_models if m.get('name') == model_name), None)
            if not existing:
                new_model = {
                    'name': model_name,
                    'id': model_name.lower(),
                    'personality': model_info.get('personality', 'neutral'),
                    'loaded_at': data.get('timestamp', time.time())
                }
                app_globals.loaded_models.append(new_model)
                logger.info(f"Model loaded: {model_name}")
                
                # Emit to all clients
                socketio.emit('model_loaded', {'model': new_model})
                socketio.emit('loaded_models_changed', {'models': app_globals.loaded_models})
            
        except Exception as e:
            logger.error(f"Error handling model loaded: {e}")
    
    @socketio.on('live2d_model_unloaded')
    def handle_model_unloaded(data):
        """Handle when a model is unloaded"""
        try:
            model_name = data.get('modelName')
            
            # Remove from loaded models
            app_globals.loaded_models = [m for m in app_globals.loaded_models if m.get('name') != model_name]
            logger.info(f"Model unloaded: {model_name}")
            
            # Emit to all clients
            socketio.emit('model_unloaded', {'modelName': model_name})
            socketio.emit('loaded_models_changed', {'models': app_globals.loaded_models})
            
        except Exception as e:
            logger.error(f"Error handling model unloaded: {e}")
    
    logger.info("Live2D SocketIO handlers setup complete")
