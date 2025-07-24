// Quick Test Script for Enhanced Audio and Lipsync Improvements
// Run this in the browser console after the page loads

console.log('🧪 === ENHANCED AUDIO & LIPSYNC VALIDATION TEST ===');

// Test 1: Enhanced Lipsync Timing (0.2 second intervals)
function testEnhancedLipsyncTiming() {
    console.log('👄 Testing enhanced lipsync timing (0.2s intervals)...');
    
    const testAvatar = 'iori';
    const mouthShapes = ['A', 'E', 'I', 'O', 'U', 'A', 'I', 'E', 'O', 'default'];
    
    if (!window.setAvatarMouthShape) {
        console.error('❌ setAvatarMouthShape not available');
        return false;
    }
    
    console.log(`🎭 Testing rapid mouth movements on ${testAvatar}...`);
    
    mouthShapes.forEach((shape, i) => {
        setTimeout(() => {
            window.setAvatarMouthShape(testAvatar, shape);
            console.log(`👄 [${i * 200}ms] Set mouth to: ${shape}`);
        }, i * 200); // 0.2 second intervals (much faster than before)
    });
    
    console.log('✅ Enhanced lipsync timing test initiated');
    return true;
}

// Test 2: Enhanced TTS with Lipsync
async function testEnhancedTTSWithLipsync() {
    console.log('🎤 Testing enhanced TTS with improved lipsync...');
    
    if (!window.triggerEnhancedTTSWithLipsync) {
        console.error('❌ triggerEnhancedTTSWithLipsync not available');
        return false;
    }
    
    try {
        await window.triggerEnhancedTTSWithLipsync(
            "Hello! This is a test of the enhanced TTS system with improved lipsync timing. Watch my mouth move more realistically!",
            'happy',
            'iori',
            {},
            0.7
        );
        console.log('✅ Enhanced TTS with lipsync completed successfully');
        return true;
    } catch (error) {
        console.error('❌ Enhanced TTS test failed:', error);
        return false;
    }
}

// Test 3: Autonomous Greeting with Enhanced Audio
async function testAutonomousGreetingWithAudio() {
    console.log('🤖 Testing autonomous greeting with enhanced audio...');
    
    if (window.testAutonomousGreeting) {
        const result = window.testAutonomousGreeting();
        console.log('✅ Autonomous greeting test result:', result);
        return result;
    } else if (window.autonomousAvatarUI) {
        try {
            const testAvatar = {
                id: 'iori',
                name: 'iori',
                displayName: 'Iori'
            };
            
            await window.autonomousAvatarUI.sendAutonomousGreeting(testAvatar);
            console.log('✅ Manual autonomous greeting test completed');
            return true;
        } catch (error) {
            console.error('❌ Manual autonomous greeting failed:', error);
            return false;
        }
    } else {
        console.error('❌ Autonomous system not available');
        return false;
    }
}

// Test 4: Audio Context Manager Validation
function testAudioContextManager() {
    console.log('🔊 Testing audio context manager...');
    
    if (!window.audioContextManager) {
        console.error('❌ Audio context manager not available');
        return false;
    }
    
    console.log('📊 Audio Context Status:');
    console.log('  - Unlocked:', window.audioContextManager.isAudioUnlocked());
    console.log('  - Context:', window.audioContextManager.getAudioContext()?.state);
    console.log('  - Pending audio items:', window.audioContextManager.pendingAudio?.length || 0);
    
    return true;
}

// Run all tests sequentially
async function runAllValidationTests() {
    console.log('🚀 Starting comprehensive validation tests...');
    
    // Test audio context first
    console.log('\n1. Audio Context Manager:');
    testAudioContextManager();
    
    // Test enhanced lipsync timing
    console.log('\n2. Enhanced Lipsync Timing:');
    setTimeout(() => {
        testEnhancedLipsyncTiming();
    }, 1000);
    
    // Test enhanced TTS with lipsync
    console.log('\n3. Enhanced TTS with Lipsync:');
    setTimeout(async () => {
        await testEnhancedTTSWithLipsync();
    }, 4000); // Wait for lipsync test to finish
    
    // Test autonomous greeting
    console.log('\n4. Autonomous Greeting with Audio:');
    setTimeout(async () => {
        await testAutonomousGreetingWithAudio();
    }, 8000); // Wait for TTS test to finish
    
    console.log('\n🏁 All validation tests scheduled. Watch the console and avatar for results!');
}

// Make functions globally available
window.testEnhancedLipsyncTiming = testEnhancedLipsyncTiming;
window.testEnhancedTTSWithLipsync = testEnhancedTTSWithLipsync;
window.testAutonomousGreetingWithAudio = testAutonomousGreetingWithAudio;
window.testAudioContextManager = testAudioContextManager;
window.runAllValidationTests = runAllValidationTests;

// Auto-run validation tests
console.log('🔧 Enhanced validation script loaded!');
console.log('💡 Run runAllValidationTests() to test all improvements');
console.log('💡 Or run individual tests: testEnhancedLipsyncTiming(), testEnhancedTTSWithLipsync(), etc.');

// Auto-run if page is ready
if (document.readyState === 'complete') {
    setTimeout(runAllValidationTests, 2000);
} else {
    window.addEventListener('load', () => {
        setTimeout(runAllValidationTests, 2000);
    });
}
