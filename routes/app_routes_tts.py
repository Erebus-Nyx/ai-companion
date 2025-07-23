"""
app_routes_tts.py
TTS-related Flask route definitions for the AI Companion backend.
"""
from flask import Blueprint, jsonify, request
import time
import app_globals
import logging
import json

logger = logging.getLogger(__name__)
tts_bp = Blueprint('tts', __name__)

@tts_bp.route('/api/tts', methods=['POST'])
def api_tts():
    """Basic TTS synthesis endpoint"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Use the global TTS handler
        if not hasattr(app_globals, 'tts_handler') or not app_globals.tts_handler:
            return jsonify({'error': 'TTS handler not available'}), 503
            
        # Generate basic TTS
        audio_data = app_globals.tts_handler.synthesize_speech(text)
        
        if audio_data:
            return jsonify({
                'audio_data': audio_data.tolist() if hasattr(audio_data, 'tolist') else audio_data,
                'text': text,
                'timestamp': time.time(),
                'sample_rate': 22050
            })
        else:
            return jsonify({'error': 'Failed to generate audio'}), 500
            
    except Exception as e:
        logger.error(f"TTS API error: {e}")
        return jsonify({'error': str(e)}), 500

@tts_bp.route('/api/tts/emotional', methods=['POST'])
def api_emotional_tts():
    """Emotional TTS synthesis with personality and avatar parameters"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        emotion = data.get('emotion', 'neutral')
        intensity = data.get('intensity', 0.5)
        avatar_id = data.get('avatar_id', '')
        personality_traits = data.get('personality_traits', {})
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Use the global TTS handler
        if not hasattr(app_globals, 'tts_handler') or not app_globals.tts_handler:
            return jsonify({'error': 'TTS handler not available'}), 503
            
        # Check if TTS handler supports emotional synthesis
        if hasattr(app_globals.tts_handler, 'synthesize_emotional_speech'):
            # Enhanced emotional synthesis
            audio_data = app_globals.tts_handler.synthesize_emotional_speech(
                text=text,
                emotion=emotion,
                intensity=intensity,
                personality_traits=personality_traits
            )
        else:
            # Fallback to basic synthesis
            audio_data = app_globals.tts_handler.synthesize_speech(text)
            
        if audio_data:
            # Calculate TTS parameters based on emotion and personality
            tts_params = calculate_tts_parameters(emotion, intensity, personality_traits)
            
            return jsonify({
                'audio_data': audio_data.tolist() if hasattr(audio_data, 'tolist') else audio_data,
                'text': text,
                'emotion': emotion,
                'intensity': intensity,
                'avatar_id': avatar_id,
                'tts_params': tts_params,
                'timestamp': time.time(),
                'sample_rate': 22050
            })
        else:
            return jsonify({'error': 'Failed to generate emotional audio'}), 500
            
    except Exception as e:
        logger.error(f"Emotional TTS API error: {e}")
        return jsonify({'error': str(e)}), 500

@tts_bp.route('/api/tts/avatar', methods=['POST'])
def api_avatar_tts():
    """Avatar-specific TTS with synchronized expressions and lipsync"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        avatar_id = data.get('avatar_id', '')
        emotion = data.get('emotion', 'neutral')
        intensity = data.get('intensity', 0.5)
        personality_traits = data.get('personality_traits', {})
        sync_with_expressions = data.get('sync_with_expressions', True)
        
        if not text or not avatar_id:
            return jsonify({'error': 'Text and avatar_id required'}), 400
            
        # Use the global TTS handler
        if not hasattr(app_globals, 'tts_handler') or not app_globals.tts_handler:
            return jsonify({'error': 'TTS handler not available'}), 503
            
        # Generate emotional TTS
        if hasattr(app_globals.tts_handler, 'synthesize_emotional_speech'):
            audio_data = app_globals.tts_handler.synthesize_emotional_speech(
                text=text,
                emotion=emotion,
                intensity=intensity,
                personality_traits=personality_traits
            )
        else:
            audio_data = app_globals.tts_handler.synthesize_speech(text)
            
        if audio_data:
            # Calculate comprehensive parameters for avatar synchronization
            tts_params = calculate_tts_parameters(emotion, intensity, personality_traits)
            live2d_params = calculate_live2d_sync_parameters(emotion, intensity, personality_traits)
            lipsync_data = generate_lipsync_data(text, audio_data) if sync_with_expressions else None
            
            return jsonify({
                'audio_data': audio_data.tolist() if hasattr(audio_data, 'tolist') else audio_data,
                'text': text,
                'emotion': emotion,
                'intensity': intensity,
                'avatar_id': avatar_id,
                'tts_params': tts_params,
                'live2d_params': live2d_params,
                'lipsync_data': lipsync_data,
                'timestamp': time.time(),
                'sample_rate': 22050,
                'duration': len(audio_data) / 22050 if audio_data else 0
            })
        else:
            return jsonify({'error': 'Failed to generate avatar TTS'}), 500
            
    except Exception as e:
        logger.error(f"Avatar TTS API error: {e}")
        return jsonify({'error': str(e)}), 500

def calculate_tts_parameters(emotion, intensity, personality_traits):
    """Calculate TTS parameters based on emotion and personality"""
    base_params = {
        'speed': 1.0,
        'pitch': 1.0,
        'volume': 1.0,
        'warmth': 0.5,
        'stability': 0.5
    }
    
    # Emotion-based adjustments
    emotion_adjustments = {
        'happy': {'speed': 1.1, 'pitch': 1.1, 'warmth': 0.8},
        'excited': {'speed': 1.2, 'pitch': 1.2, 'warmth': 0.9},
        'sad': {'speed': 0.8, 'pitch': 0.9, 'warmth': 0.3},
        'angry': {'speed': 1.1, 'pitch': 0.9, 'stability': 0.3},
        'curious': {'speed': 1.05, 'pitch': 1.05, 'warmth': 0.6},
        'seductive': {'speed': 0.9, 'pitch': 0.95, 'warmth': 0.9},
        'shy': {'speed': 0.9, 'pitch': 1.0, 'volume': 0.8},
        'confident': {'speed': 1.1, 'pitch': 1.0, 'stability': 0.8},
        'passionate': {'speed': 1.0, 'pitch': 1.1, 'warmth': 0.9}
    }
    
    if emotion in emotion_adjustments:
        for param, value in emotion_adjustments[emotion].items():
            base_params[param] = value
    
    # Intensity scaling
    for param in ['speed', 'pitch', 'warmth']:
        if param in base_params:
            # Scale the adjustment by intensity
            adjustment = (base_params[param] - 1.0) * intensity
            base_params[param] = 1.0 + adjustment
    
    # Personality adjustments
    if personality_traits:
        # Extroversion affects speed and volume
        extroversion = personality_traits.get('extroversion', 0.5)
        base_params['speed'] *= (0.8 + extroversion * 0.4)
        base_params['volume'] *= (0.8 + extroversion * 0.4)
        
        # Seductive traits affect pitch and warmth
        seductive = personality_traits.get('seductive', 0.0)
        if seductive > 0.3:
            base_params['pitch'] *= (0.95 + seductive * 0.1)
            base_params['warmth'] = min(1.0, base_params['warmth'] + seductive * 0.3)
            
        # Confidence affects stability
        confidence = personality_traits.get('confident', 0.5)
        base_params['stability'] = min(1.0, base_params['stability'] + confidence * 0.3)
    
    return base_params

def calculate_live2d_sync_parameters(emotion, intensity, personality_traits):
    """Calculate Live2D synchronization parameters"""
    return {
        'motion': get_emotion_motion(emotion),
        'expression': get_emotion_expression(emotion),
        'intensity': intensity,
        'duration': 2.0 + intensity,  # Motion duration
        'sync_with_speech': True,
        'eye_blink_rate': get_eye_blink_rate(emotion, personality_traits),
        'mouth_sync': True,
        'body_sway': get_body_sway(emotion, personality_traits)
    }

def get_emotion_motion(emotion):
    """Map emotions to Live2D motions with fallback handling"""
    # Primary emotion mapping
    motion_map = {
        'happy': 'happy',
        'excited': 'excited',
        'sad': 'sad',
        'angry': 'angry',
        'surprised': 'surprised',
        'curious': 'thinking',
        'seductive': 'flirt',
        'shy': 'shy',
        'confident': 'confident',
        'passionate': 'passionate',
        'neutral': 'idle',
        'love': 'love',
        'flirtatious': 'flirt',
        'horny': 'flirt',  # Map to available motion
        'romantic': 'love',
        'nervous': 'shy',
        'embarrassed': 'shy',
        'dominant': 'confident',
        'submissive': 'shy',
        'mischievous': 'happy',
        'playful': 'happy',
        'sensual': 'flirt',
        'worried': 'sad',
        'frustrated': 'angry',
        'thoughtful': 'thinking',
        'amazed': 'surprised'
    }
    
    # Direct mapping if available
    if emotion in motion_map:
        return motion_map[emotion]
    
    # Semantic fallback mapping for unknown emotions
    semantic_fallbacks = {
        # Positive emotions fall back to happy
        'joyful': 'happy',
        'cheerful': 'happy',
        'delighted': 'happy',
        'elated': 'happy',
        'ecstatic': 'excited',
        'enthusiastic': 'excited',
        'thrilled': 'excited',
        
        # Negative emotions fall back to sad/angry
        'depressed': 'sad',
        'melancholy': 'sad',
        'disappointed': 'sad',
        'upset': 'sad',
        'furious': 'angry',
        'irritated': 'angry',
        'annoyed': 'angry',
        'rage': 'angry',
        
        # Surprised variations
        'shocked': 'surprised',
        'astonished': 'surprised',
        'startled': 'surprised',
        'bewildered': 'surprised',
        
        # Social emotions
        'affectionate': 'love',
        'caring': 'love',
        'tender': 'love',
        'intimate': 'love',
        'attracted': 'flirt',
        'lustful': 'flirt',
        'aroused': 'flirt',
        
        # Contemplative emotions
        'pensive': 'thinking',
        'reflective': 'thinking',
        'contemplative': 'thinking',
        'confused': 'thinking',
        
        # Confidence variations
        'assertive': 'confident',
        'bold': 'confident',
        'proud': 'confident',
        'determined': 'confident',
        
        # Shyness variations
        'timid': 'shy',
        'bashful': 'shy',
        'reserved': 'shy',
        'withdrawn': 'shy',
        'insecure': 'shy'
    }
    
    if emotion in semantic_fallbacks:
        return semantic_fallbacks[emotion]
    
    # Intensity-based fallback - classify by emotional intensity
    emotion_lower = emotion.lower()
    
    # High-intensity emotions
    if any(word in emotion_lower for word in ['intense', 'extreme', 'overwhelming', 'powerful']):
        return 'excited'
    
    # Low-intensity emotions  
    if any(word in emotion_lower for word in ['mild', 'slight', 'gentle', 'soft']):
        return 'idle'
    
    # Default fallback based on emotional valence
    positive_indicators = ['good', 'nice', 'pleasant', 'warm', 'bright', 'up']
    negative_indicators = ['bad', 'unpleasant', 'dark', 'down', 'cold', 'harsh']
    
    if any(indicator in emotion_lower for indicator in positive_indicators):
        return 'happy'
    elif any(indicator in emotion_lower for indicator in negative_indicators):
        return 'sad'
    
    # Final fallback - neutral idle motion
    logger.warning(f"Unknown emotion '{emotion}' mapped to default 'idle' motion")
    return 'idle'

def get_emotion_expression(emotion):
    """Map emotions to Live2D expressions with fallback handling"""
    # Primary expression mapping
    expression_map = {
        'happy': 'smile',
        'excited': 'excited',
        'sad': 'sad',
        'angry': 'angry',
        'surprised': 'surprised',
        'curious': 'curious',
        'seductive': 'wink',
        'shy': 'embarrassed',
        'confident': 'smile',
        'passionate': 'love',
        'neutral': 'default',
        'love': 'love',
        'flirtatious': 'wink',
        'horny': 'wink',  # Map to available expression
        'romantic': 'love',
        'nervous': 'embarrassed',
        'embarrassed': 'embarrassed',
        'dominant': 'smile',
        'submissive': 'embarrassed',
        'mischievous': 'wink',
        'playful': 'smile',
        'sensual': 'love',
        'worried': 'sad',
        'frustrated': 'angry',
        'thoughtful': 'curious',
        'amazed': 'surprised'
    }
    
    # Direct mapping if available
    if emotion in expression_map:
        return expression_map[emotion]
    
    # Semantic fallback mapping for unknown expressions
    semantic_fallbacks = {
        # Positive expressions fall back to smile
        'joyful': 'smile',
        'cheerful': 'smile',
        'delighted': 'smile',
        'elated': 'smile',
        'ecstatic': 'excited',
        'enthusiastic': 'excited',
        'thrilled': 'excited',
        
        # Negative expressions fall back to sad/angry
        'depressed': 'sad',
        'melancholy': 'sad',
        'disappointed': 'sad',
        'upset': 'sad',
        'furious': 'angry',
        'irritated': 'angry',
        'annoyed': 'angry',
        'rage': 'angry',
        
        # Surprised variations
        'shocked': 'surprised',
        'astonished': 'surprised',
        'startled': 'surprised',
        'bewildered': 'surprised',
        
        # Love/attraction expressions
        'affectionate': 'love',
        'caring': 'love',
        'tender': 'love',
        'intimate': 'love',
        'attracted': 'wink',
        'lustful': 'wink',
        'aroused': 'wink',
        
        # Contemplative expressions
        'pensive': 'curious',
        'reflective': 'curious',
        'contemplative': 'curious',
        'confused': 'curious',
        
        # Confidence variations
        'assertive': 'smile',
        'bold': 'smile',
        'proud': 'smile',
        'determined': 'smile',
        
        # Shyness variations
        'timid': 'embarrassed',
        'bashful': 'embarrassed',
        'reserved': 'embarrassed',
        'withdrawn': 'embarrassed',
        'insecure': 'embarrassed'
    }
    
    if emotion in semantic_fallbacks:
        return semantic_fallbacks[emotion]
    
    # Fallback based on emotional intensity and valence
    emotion_lower = emotion.lower()
    
    # High-intensity expressions
    if any(word in emotion_lower for word in ['intense', 'extreme', 'overwhelming', 'powerful']):
        return 'excited'
    
    # Default fallback based on emotional valence
    positive_indicators = ['good', 'nice', 'pleasant', 'warm', 'bright', 'up']
    negative_indicators = ['bad', 'unpleasant', 'dark', 'down', 'cold', 'harsh']
    
    if any(indicator in emotion_lower for indicator in positive_indicators):
        return 'smile'
    elif any(indicator in emotion_lower for indicator in negative_indicators):
        return 'sad'
    
    # Final fallback - default neutral expression
    logger.warning(f"Unknown emotion '{emotion}' mapped to default expression")
    return 'default'

def get_eye_blink_rate(emotion, personality_traits):
    """Calculate eye blink rate based on emotion and personality"""
    base_rate = 1.0
    
    emotion_rates = {
        'nervous': 1.5,
        'shy': 1.3,
        'excited': 0.7,
        'confident': 0.8,
        'seductive': 0.6
    }
    
    rate = emotion_rates.get(emotion, base_rate)
    
    # Personality adjustments
    if personality_traits:
        neuroticism = personality_traits.get('neuroticism', 0.3)
        rate *= (0.8 + neuroticism * 0.4)
    
    return rate

def get_body_sway(emotion, personality_traits):
    """Calculate body sway intensity for expressions"""
    base_sway = 0.3
    
    emotion_sway = {
        'excited': 0.8,
        'happy': 0.6,
        'seductive': 0.7,
        'confident': 0.5,
        'shy': 0.1,
        'sad': 0.2
    }
    
    sway = emotion_sway.get(emotion, base_sway)
    
    # Personality adjustments
    if personality_traits:
        extroversion = personality_traits.get('extroversion', 0.5)
        sway *= (0.5 + extroversion * 0.5)
    
    return sway

def generate_lipsync_data(text, audio_data):
    """Generate basic lipsync data for mouth movement"""
    # Simple lipsync based on text phonemes
    words = text.split()
    word_count = len(words)
    
    if not audio_data:
        return None
    
    # Calculate timing for mouth movements
    duration = len(audio_data) / 22050  # Assuming 22050 Hz sample rate
    
    lipsync_frames = []
    for i, word in enumerate(words):
        start_time = (i / word_count) * duration
        end_time = ((i + 1) / word_count) * duration
        
        # Simple mouth shape based on vowels
        mouth_shape = get_mouth_shape_for_word(word)
        
        lipsync_frames.append({
            'start_time': start_time,
            'end_time': end_time,
            'mouth_shape': mouth_shape,
            'intensity': 0.7  # Default intensity
        })
    
    return lipsync_frames

def get_mouth_shape_for_word(word):
    """Get mouth shape based on word content"""
    word_lower = word.lower()
    
    # Simple vowel-based mouth shapes
    if any(vowel in word_lower for vowel in ['a', 'ah']):
        return 'A'
    elif any(vowel in word_lower for vowel in ['e', 'eh']):
        return 'E'
    elif any(vowel in word_lower for vowel in ['i', 'ih']):
        return 'I'
    elif any(vowel in word_lower for vowel in ['o', 'oh']):
        return 'O'
    elif any(vowel in word_lower for vowel in ['u', 'uh']):
        return 'U'
    else:
        return 'default'
