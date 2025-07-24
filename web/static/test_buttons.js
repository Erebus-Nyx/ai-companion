// Autonomous Greeting Test Functions
// Add these to the browser console or main interface

function addTestButtons() {
    // Create test panel
    const testPanel = document.createElement('div');
    testPanel.id = 'test-panel';
    testPanel.style.cssText = `
        position: fixed;
        top: 10px;
        left: 10px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 15px;
        border-radius: 8px;
        font-family: monospace;
        font-size: 12px;
        z-index: 10000;
        max-width: 300px;
    `;
    
    testPanel.innerHTML = `
        <h3 style="margin: 0 0 10px 0; color: #4CAF50;">🧪 Audio/Lipsync Test Panel</h3>
        <button id="test-lipsync" style="margin: 5px; padding: 8px 12px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer;">Test Lipsync</button>
        <button id="test-audio" style="margin: 5px; padding: 8px 12px; background: #FF9800; color: white; border: none; border-radius: 4px; cursor: pointer;">Test Audio</button>
        <button id="test-tts" style="margin: 5px; padding: 8px 12px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">Test TTS</button>
        <button id="test-autonomous" style="margin: 5px; padding: 8px 12px; background: #9C27B0; color: white; border: none; border-radius: 4px; cursor: pointer;">Test Autonomous</button>
        <button id="close-panel" style="margin: 5px; padding: 4px 8px; background: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer; float: right;">×</button>
        <div id="test-status" style="margin-top: 10px; padding: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; min-height: 50px; font-size: 11px;"></div>
    `;
    
    document.body.appendChild(testPanel);
    
    // Add event listeners
    document.getElementById('test-lipsync').onclick = testLipsyncOnly;
    document.getElementById('test-audio').onclick = testAudioOnly;
    document.getElementById('test-tts').onclick = testTTSComplete;
    document.getElementById('test-autonomous').onclick = testAutonomousGreeting;
    document.getElementById('close-panel').onclick = () => testPanel.remove();
    
    updateTestStatus('Test panel ready. Click buttons to test different features.');
}

function updateTestStatus(message) {
    const statusDiv = document.getElementById('test-status');
    if (statusDiv) {
        const timestamp = new Date().toLocaleTimeString();
        statusDiv.innerHTML += `<div>[${timestamp}] ${message}</div>`;
        statusDiv.scrollTop = statusDiv.scrollHeight;
    }
    console.log('🧪', message);
}

function testLipsyncOnly() {
    updateTestStatus('🗣️ Testing lipsync shapes...');
    
    if (!window.setAvatarMouthShape) {
        updateTestStatus('❌ setAvatarMouthShape not available');
        return;
    }
    
    const testAvatar = 'iori';
    const mouthShapes = ['A', 'I', 'U', 'E', 'O', 'default'];
    
    mouthShapes.forEach((shape, index) => {
        setTimeout(() => {
            window.setAvatarMouthShape(testAvatar, shape);
            updateTestStatus(`👄 Applied ${shape} to ${testAvatar}`);
        }, index * 800);
    });
}

function testAudioOnly() {
    updateTestStatus('🔊 Testing audio playback...');
    
    if (!window.audioContextManager) {
        updateTestStatus('❌ Audio context manager not available');
        return;
    }
    
    // Test with a simple beep tone (base64 WAV)
    const testAudio = 'data:audio/wav;base64,UklGRh4CAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YfoAAACBhYqFg4eKhYuDjIWOhI6Ej4SOhI6EjoSPhI6Ej4SOhI6EjoSPhI6Ej4SOhI+Ej4WOho6Gj4aPho+Gj4aPhY+Fj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+Gj4aPho+G';
    
    window.audioContextManager.playAudio(testAudio, {
        onStart: () => updateTestStatus('🔊 Audio playback started'),
        onEnd: () => updateTestStatus('✅ Audio test completed')
    }).catch(error => {
        updateTestStatus(`❌ Audio test failed: ${error.message}`);
    });
}

async function testTTSComplete() {
    updateTestStatus('🎤 Testing complete TTS pipeline...');
    
    if (!window.triggerEmotionalTTS) {
        updateTestStatus('❌ triggerEmotionalTTS not available');
        return;
    }
    
    try {
        await window.triggerEmotionalTTS(
            "Hello! This is a test of the audio and lipsync system.", 
            "happy", 
            "iori", 
            {}, 
            0.7
        );
        updateTestStatus('✅ TTS test completed successfully');
    } catch (error) {
        updateTestStatus(`❌ TTS test failed: ${error.message}`);
    }
}

async function testAutonomousGreeting() {
    updateTestStatus('🤖 Testing autonomous greeting...');
    
    try {
        const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
        
        // Trigger autonomous conversation
        const response = await fetch(`${apiBaseUrl}/api/autonomous/start_conversation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                avatar_id: 'iori',
                conversation_type: 'greeting'
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            updateTestStatus('✅ Autonomous greeting triggered successfully');
            updateTestStatus(`📝 Response: ${JSON.stringify(result)}`);
        } else {
            updateTestStatus(`❌ Autonomous greeting failed: ${response.status}`);
        }
    } catch (error) {
        updateTestStatus(`❌ Autonomous greeting error: ${error.message}`);
    }
}

// Auto-add test panel when script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addTestButtons);
} else {
    addTestButtons();
}

// Make functions globally available
window.addTestButtons = addTestButtons;
window.testLipsyncOnly = testLipsyncOnly;
window.testAudioOnly = testAudioOnly;
window.testTTSComplete = testTTSComplete;
window.testAutonomousGreeting = testAutonomousGreeting;

console.log('🔧 Test buttons script loaded. Test panel should appear in top-left corner.');
