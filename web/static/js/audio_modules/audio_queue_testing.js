// Audio Queue Testing Functions
// These functions help demonstrate and test the audio queue system

// Test audio overlap scenario
window.testAudioOverlap = function() {
    console.log('🧪 Testing audio overlap scenario...');
    
    // Simulate multiple avatars speaking at once (this would cause overlap without queue)
    const testMessages = [
        { text: "Hello! I'm the first avatar speaking.", emotion: "happy", avatarId: "haruka", priority: 1 },
        { text: "Actually, I was supposed to speak first!", emotion: "excited", avatarId: "haru", priority: 2 },
        { text: "No, no, I have something important to say!", emotion: "determined", avatarId: "epsilon", priority: 3 },
        { text: "Can we all just take turns please?", emotion: "calm", avatarId: "tsumiki", priority: 1 },
        { text: "This is exactly why we need an audio queue!", emotion: "analytical", avatarId: "iori", priority: 1 }
    ];
    
    // Send all messages rapidly (without queue, they would overlap)
    testMessages.forEach((msg, index) => {
        setTimeout(() => {
            if (window.triggerEmotionalTTS) {
                console.log(`🧪 Triggering TTS ${index + 1}: ${msg.avatarId} - "${msg.text}"`);
                window.triggerEmotionalTTS(msg.text, msg.emotion, msg.avatarId, {}, 0.6, msg.priority);
            }
        }, index * 200); // Rapid succession
    });
    
    console.log('🧪 Audio overlap test complete - check if audio plays sequentially');
};

// Test different queue modes
window.testQueueModes = function() {
    console.log('🧪 Testing different queue modes...');
    
    const modes = ['queue', 'interrupt', 'priority'];
    let currentMode = 0;
    
    const testMode = () => {
        const mode = modes[currentMode];
        console.log(`🧪 Testing mode: ${mode}`);
        
        if (window.setAudioQueueMode) {
            window.setAudioQueueMode(mode);
        }
        
        // Test messages for this mode
        const messages = [
            { text: `Testing ${mode} mode - first message`, emotion: "neutral", avatarId: "haruka" },
            { text: `This is the second message in ${mode} mode`, emotion: "happy", avatarId: "haru" },
            { text: `And this is the third message for ${mode} testing`, emotion: "excited", avatarId: "epsilon" }
        ];
        
        messages.forEach((msg, index) => {
            setTimeout(() => {
                if (window.triggerEmotionalTTS) {
                    window.triggerEmotionalTTS(msg.text, msg.emotion, msg.avatarId);
                }
            }, index * 500);
        });
        
        currentMode++;
        if (currentMode < modes.length) {
            setTimeout(testMode, 8000); // Wait for current test to complete
        } else {
            console.log('🧪 Queue mode testing complete');
        }
    };
    
    testMode();
};

// Test priority system
window.testPrioritySystem = function() {
    console.log('🧪 Testing priority system...');
    
    if (window.setAudioQueueMode) {
        window.setAudioQueueMode('priority');
    }
    
    // Send low priority messages first
    setTimeout(() => {
        if (window.triggerEmotionalTTS) {
            window.triggerEmotionalTTS("This is a low priority message that should be interrupted", "calm", "haruka", {}, 0.5, 1);
        }
    }, 100);
    
    setTimeout(() => {
        if (window.triggerEmotionalTTS) {
            window.triggerEmotionalTTS("This is another low priority message", "neutral", "haru", {}, 0.5, 1);
        }
    }, 200);
    
    // Send high priority message that should interrupt
    setTimeout(() => {
        if (window.triggerEmotionalTTS) {
            window.triggerEmotionalTTS("URGENT! This high priority message should interrupt!", "excited", "epsilon", {}, 0.8, 5);
        }
    }, 2000);
    
    console.log('🧪 Priority system test initiated');
};

// Test rapid avatar switching
window.testRapidAvatarSwitching = function() {
    console.log('🧪 Testing rapid avatar switching...');
    
    const avatars = ["haruka", "haru", "epsilon", "tsumiki", "iori"];
    const emotions = ["happy", "excited", "calm", "determined", "analytical"];
    
    avatars.forEach((avatar, index) => {
        setTimeout(() => {
            const emotion = emotions[index] || "neutral";
            const message = `Avatar ${avatar} speaking with ${emotion} emotion`;
            
            if (window.triggerEmotionalTTS) {
                window.triggerEmotionalTTS(message, emotion, avatar);
            }
        }, index * 100); // Very rapid succession
    });
    
    console.log('🧪 Rapid avatar switching test initiated');
};

// Monitor audio queue status
window.startAudioQueueMonitoring = function() {
    console.log('🧪 Starting audio queue monitoring...');
    
    const monitorInterval = setInterval(() => {
        if (window.getAudioQueueStatus) {
            const status = window.getAudioQueueStatus();
            if (status.isPlaying || status.queueLength > 0) {
                console.log('🎵 Queue Status:', {
                    playing: status.isPlaying,
                    avatar: status.currentAvatarId,
                    queueLength: status.queueLength,
                    mode: status.preemptionMode
                });
            }
        }
    }, 1000);
    
    // Stop monitoring after 2 minutes
    setTimeout(() => {
        clearInterval(monitorInterval);
        console.log('🧪 Audio queue monitoring stopped');
    }, 120000);
    
    return monitorInterval;
};

// Clear everything and reset
window.resetAudioQueue = function() {
    console.log('🧪 Resetting audio queue...');
    
    if (window.stopCurrentAudio) {
        window.stopCurrentAudio();
    }
    
    if (window.clearAudioQueue) {
        window.clearAudioQueue();
    }
    
    if (window.setAudioQueueMode) {
        window.setAudioQueueMode('queue');
    }
    
    console.log('🧪 Audio queue reset complete');
};

// Comprehensive test suite
window.runAudioQueueTestSuite = function() {
    console.log('🧪 Running comprehensive audio queue test suite...');
    
    // Reset first
    window.resetAudioQueue();
    
    // Test 1: Basic overlap prevention
    setTimeout(() => {
        console.log('🧪 Test 1: Basic overlap prevention');
        window.testAudioOverlap();
    }, 1000);
    
    // Test 2: Priority system
    setTimeout(() => {
        console.log('🧪 Test 2: Priority system');
        window.testPrioritySystem();
    }, 15000);
    
    // Test 3: Rapid switching
    setTimeout(() => {
        console.log('🧪 Test 3: Rapid avatar switching');
        window.testRapidAvatarSwitching();
    }, 30000);
    
    // Start monitoring
    window.startAudioQueueMonitoring();
    
    console.log('🧪 Test suite initiated - monitoring for 2 minutes');
};

// Add to global console functions
window.audioQueueTestFunctions = {
    testAudioOverlap: window.testAudioOverlap,
    testQueueModes: window.testQueueModes,
    testPrioritySystem: window.testPrioritySystem,
    testRapidAvatarSwitching: window.testRapidAvatarSwitching,
    startAudioQueueMonitoring: window.startAudioQueueMonitoring,
    resetAudioQueue: window.resetAudioQueue,
    runAudioQueueTestSuite: window.runAudioQueueTestSuite
};

console.log('🧪 Audio Queue Test Functions loaded');
console.log('🧪 Available functions:', Object.keys(window.audioQueueTestFunctions));
console.log('🧪 Run window.runAudioQueueTestSuite() to test the system');
