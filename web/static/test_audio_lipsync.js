// Test script for audio and lipsync functionality
// Run this in the browser console after loading the page

async function testAudioLipsyncFixes() {
    console.log('🧪 Testing Audio and Lipsync Fixes');
    console.log('==================================================');
    
    // 1. Check if audio context manager is available
    console.log('1. Checking Audio Context Manager...');
    if (window.audioContextManager) {
        console.log('   ✅ Audio Context Manager available');
        console.log('   🔒 Audio unlocked:', window.audioContextManager.isAudioUnlocked());
    } else {
        console.log('   ❌ Audio Context Manager not found');
    }
    
    // 2. Check Live2D models
    console.log('\n2. Checking Live2D Models...');
    if (window.live2dMultiModelManager && window.live2dMultiModelManager.models) {
        const models = window.live2dMultiModelManager.models;
        console.log(`   📊 Found ${models.size} Live2D models:`);
        models.forEach((model, modelId) => {
            console.log(`      - ${modelId}: ${model.constructor.name}`);
        });
    } else {
        console.log('   ❌ Live2D Multi Model Manager not available');
    }
    
    // 3. Check if setAvatarMouthShape is available
    console.log('\n3. Checking Lipsync Functions...');
    if (window.setAvatarMouthShape) {
        console.log('   ✅ setAvatarMouthShape function available');
    } else {
        console.log('   ❌ setAvatarMouthShape function not found');
    }
    
    // 4. Test mouth shape functionality
    console.log('\n4. Testing Mouth Shape Control...');
    const testAvatar = 'iori'; // Use iori as test avatar
    
    if (window.setAvatarMouthShape) {
        try {
            const mouthShapes = ['A', 'I', 'U', 'E', 'O', 'default'];
            
            for (let i = 0; i < mouthShapes.length; i++) {
                const shape = mouthShapes[i];
                console.log(`   🗣️ Testing mouth shape: ${shape}`);
                
                setTimeout(() => {
                    window.setAvatarMouthShape(testAvatar, shape);
                    console.log(`      Applied ${shape} shape to ${testAvatar}`);
                }, i * 1000);
            }
        } catch (error) {
            console.log('   ❌ Mouth shape test failed:', error);
        }
    }
    
    // 5. Test TTS audio (if available)
    console.log('\n5. Testing TTS Audio...');
    try {
        // Check if TTS functions are available
        if (window.triggerEmotionalTTS) {
            console.log('   ✅ triggerEmotionalTTS function available');
            
            // Test with a simple greeting
            setTimeout(async () => {
                try {
                    console.log('   🎤 Testing TTS with: "Hello, testing audio and lipsync"');
                    await window.triggerEmotionalTTS(
                        "Hello, testing audio and lipsync", 
                        "happy", 
                        testAvatar, 
                        {}, 
                        0.7
                    );
                    console.log('   ✅ TTS test completed successfully');
                } catch (error) {
                    console.log('   ❌ TTS test failed:', error);
                }
            }, 6000); // Wait for mouth shape tests to complete
            
        } else {
            console.log('   ❌ triggerEmotionalTTS function not available');
        }
    } catch (error) {
        console.log('   ❌ TTS test setup failed:', error);
    }
    
    console.log('\n==================================================');
    console.log('🏁 Test initialization complete!');
    console.log('💡 Watch the console for mouth shape and audio test results.');
    console.log('💡 Click anywhere on the page to unlock audio if needed.');
}

// Auto-run when script is loaded
testAudioLipsyncFixes();

// Also make available globally for manual testing
window.testAudioLipsyncFixes = testAudioLipsyncFixes;

console.log('🔧 Audio/Lipsync test script loaded. Run testAudioLipsyncFixes() to test again.');
