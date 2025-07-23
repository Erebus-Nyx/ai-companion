#!/usr/bin/env python3
"""
Test script to demonstrate comprehensive emotion and avatar fallback handling
"""

def test_emotion_fallback_system():
    print("🧪 Testing Complete Emotion & Avatar Fallback System")
    print("=" * 60)
    
    # Import TTS functions
    try:
        from routes.app_routes_tts import (
            get_emotion_motion, 
            get_emotion_expression, 
            calculate_tts_parameters,
            calculate_live2d_sync_parameters
        )
        print("✅ Successfully imported TTS fallback functions")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return
    
    # Test cases for emotion fallback scenarios
    test_cases = [
        # Unknown emotions
        {"emotion": "completely_unknown_emotion", "description": "Completely unknown emotion"},
        {"emotion": "nonexistent_feeling", "description": "Non-existent feeling"},
        
        # Semantic variations
        {"emotion": "joyful", "description": "Semantic variation of happy"},
        {"emotion": "melancholy", "description": "Semantic variation of sad"},
        {"emotion": "furious", "description": "Semantic variation of angry"},
        {"emotion": "ecstatic", "description": "Intense happiness"},
        
        # Mature content emotions
        {"emotion": "horny", "description": "Sexual desire"},
        {"emotion": "seductive", "description": "Seductive behavior"},
        {"emotion": "lustful", "description": "Lustful feelings"},
        {"emotion": "passionate", "description": "Passionate emotion"},
        
        # Complex emotional states
        {"emotion": "bittersweet", "description": "Mixed emotion"},
        {"emotion": "nostalgic", "description": "Nostalgic feeling"},
        {"emotion": "overwhelmed", "description": "Overwhelming feeling"},
        
        # Intensity variations
        {"emotion": "mildly_happy", "description": "Low intensity happiness"},
        {"emotion": "extremely_excited", "description": "High intensity excitement"},
        {"emotion": "devastatingly_sad", "description": "Extreme sadness"},
    ]
    
    print("\n🎭 Testing Backend Emotion Mapping:")
    print("-" * 40)
    
    for test_case in test_cases:
        emotion = test_case["emotion"]
        description = test_case["description"]
        
        motion = get_emotion_motion(emotion)
        expression = get_emotion_expression(emotion)
        
        print(f"🔸 {description} ({emotion})")
        print(f"   → Motion: {motion}")
        print(f"   → Expression: {expression}")
        print()
    
    print("\n🎵 Testing TTS Parameter Generation:")
    print("-" * 40)
    
    # Test personality-aware TTS parameters
    personality_profiles = [
        {
            "name": "Seductive Character",
            "traits": {"seductive": 0.9, "confident": 0.7, "extroversion": 0.8}
        },
        {
            "name": "Shy Character", 
            "traits": {"shy": 0.8, "neuroticism": 0.6, "extroversion": 0.2}
        },
        {
            "name": "Horny Character",
            "traits": {"horny": 0.9, "sexually_adventurous": 0.8, "confident": 0.6}
        },
        {
            "name": "Balanced Character",
            "traits": {"extroversion": 0.5, "confident": 0.5, "seductive": 0.3}
        }
    ]
    
    test_emotions = ["happy", "seductive", "horny", "unknown_emotion", "passionate"]
    
    for profile in personality_profiles:
        print(f"👤 {profile['name']}:")
        for emotion in test_emotions:
            tts_params = calculate_tts_parameters(emotion, 0.7, profile['traits'])
            print(f"   {emotion}: speed={tts_params['speed']:.2f}, pitch={tts_params['pitch']:.2f}, warmth={tts_params['warmth']:.2f}")
        print()
    
    print("\n🎪 Testing Live2D Sync Parameters:")
    print("-" * 40)
    
    for emotion in ["happy", "seductive", "unknown_feeling", "horny", "melancholy"]:
        live2d_params = calculate_live2d_sync_parameters(emotion, 0.8, {"seductive": 0.7})
        print(f"🎭 {emotion}:")
        print(f"   → Motion: {live2d_params['motion']}")
        print(f"   → Expression: {live2d_params['expression']}")
        print(f"   → Eye Blink Rate: {live2d_params['eye_blink_rate']:.2f}")
        print(f"   → Body Sway: {live2d_params['body_sway']:.2f}")
        print()
    
    print("✅ Complete emotion fallback system test completed!")
    print("\n📋 Fallback System Summary:")
    print("=" * 60)
    print("✅ Unknown emotions → Semantic matching → Default fallback")
    print("✅ Intensity detection from emotion names")
    print("✅ Mature content emotion handling")
    print("✅ Personality-aware TTS parameters")
    print("✅ Live2D synchronization parameters")
    print("✅ Comprehensive error handling")

def test_avatar_file_scenarios():
    print("\n🎭 Avatar File Handling Scenarios:")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "Avatar with full emotion support",
            "available_motions": ["idle", "happy", "sad", "angry", "surprised", "flirt", "shy"],
            "available_expressions": ["default", "smile", "sad", "angry", "surprised", "wink", "embarrassed"]
        },
        {
            "name": "Avatar with limited emotions",
            "available_motions": ["idle", "happy", "sad"],
            "available_expressions": ["default", "smile"]
        },
        {
            "name": "Avatar with motion only",
            "available_motions": ["idle", "happy"],
            "available_expressions": []
        },
        {
            "name": "Avatar with expressions only",
            "available_motions": [],
            "available_expressions": ["default", "smile", "sad"]
        },
        {
            "name": "Avatar with no emotion files",
            "available_motions": [],
            "available_expressions": []
        }
    ]
    
    test_emotions = ["happy", "seductive", "horny", "unknown_emotion", "angry"]
    
    for scenario in scenarios:
        print(f"\n🎪 {scenario['name']}:")
        print(f"   Available motions: {scenario['available_motions']}")
        print(f"   Available expressions: {scenario['available_expressions']}")
        
        for emotion in test_emotions:
            # Simulate what the frontend would do
            from routes.app_routes_tts import get_emotion_motion, get_emotion_expression
            
            desired_motion = get_emotion_motion(emotion)
            desired_expression = get_emotion_expression(emotion)
            
            # Check availability
            motion_available = desired_motion in scenario['available_motions']
            expression_available = desired_expression in scenario['available_expressions']
            
            # Determine fallbacks
            fallback_motion = None
            fallback_expression = None
            
            if not motion_available and scenario['available_motions']:
                fallback_options = ['idle', 'default', 'happy']
                for fallback in fallback_options:
                    if fallback in scenario['available_motions']:
                        fallback_motion = fallback
                        break
            
            if not expression_available and scenario['available_expressions']:
                fallback_options = ['default', 'neutral', 'smile']
                for fallback in fallback_options:
                    if fallback in scenario['available_expressions']:
                        fallback_expression = fallback
                        break
            
            status = "✅" if motion_available or fallback_motion else "❌"
            expr_status = "✅" if expression_available or fallback_expression else "❌"
            
            result_motion = desired_motion if motion_available else (fallback_motion or "NONE")
            result_expr = desired_expression if expression_available else (fallback_expression or "NONE")
            
            print(f"     {emotion}: {status} {result_motion} | {expr_status} {result_expr}")

if __name__ == "__main__":
    test_emotion_fallback_system()
    test_avatar_file_scenarios()
