/**
 * Configuration and API Helper Functions
 * Handles server configuration loading and API communication
 */

// AI Companion API Configuration - Dynamic configuration loading
window.ai2d_chat_CONFIG = {
    // Default fallback configuration
    API_BASE_URL: (() => {
        const protocol = window.location.protocol;
        const hostname = window.location.hostname;
        const port = window.location.port;
        
        // Use current protocol and host
        if (port) {
            return `${protocol}//${hostname}:${port}`;
        }
        return `${protocol}//${hostname}`;
    })(),
    
    // Configuration loading status
    _configLoaded: false,
    _configPromise: null
};

// Function to load server configuration dynamically
async function loadServerConfig() {
    if (window.ai2d_chat_CONFIG._configLoaded) {
        return window.ai2d_chat_CONFIG;
    }
    
    if (window.ai2d_chat_CONFIG._configPromise) {
        return window.ai2d_chat_CONFIG._configPromise;
    }
    
    window.ai2d_chat_CONFIG._configPromise = (async () => {
        try {
            console.log('Loading server configuration from API...');
            
            // Try to fetch configuration from the server
            const configResponse = await fetch('/api/system/config');
            if (configResponse.ok) {
                const serverConfig = await configResponse.json();
                
                // Update the configuration
                window.ai2d_chat_CONFIG.API_BASE_URL = serverConfig.server.base_url;
                window.ai2d_chat_CONFIG.serverConfig = serverConfig;
                window.ai2d_chat_CONFIG._configLoaded = true;
                
                console.log('✅ Server configuration loaded successfully:', serverConfig.server.base_url);
                return window.ai2d_chat_CONFIG;
            } else {
                throw new Error(`Config API returned ${configResponse.status}`);
            }
        } catch (error) {
            console.warn('⚠️ Failed to load server config from API, using fallback:', error.message);
            
            // Fallback: use current location as base
            const protocol = window.location.protocol;
            const hostname = window.location.hostname;
            const port = window.location.port;
            
            window.ai2d_chat_CONFIG.API_BASE_URL = port ? 
                `${protocol}//${hostname}:${port}` : 
                `${protocol}//${hostname}`;
            
            window.ai2d_chat_CONFIG._configLoaded = true;
            
            console.log('Using fallback configuration:', window.ai2d_chat_CONFIG.API_BASE_URL);
            return window.ai2d_chat_CONFIG;
        }
    })();
    
    return window.ai2d_chat_CONFIG._configPromise;
}

// Helper function for making API calls with proper config loading
window.makeApiCall = async function(endpoint, options = {}) {
    // Ensure config is loaded
    await loadServerConfig();
    
    const url = `${window.ai2d_chat_CONFIG.API_BASE_URL}${endpoint}`;
    console.log(`Making API call to: ${url}`);
    
    return fetch(url, options);
};

// Enhanced Chat System functions
async function sendAudioToServer(audioBlob) {
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        
        // Use the same fallback system as other API calls
        let apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL;
        let response;
        
        // Try primary API URL first
        if (apiBaseUrl) {
            try {
                response = await fetch(`${apiBaseUrl}/api/speech-to-text`, {
                    method: 'POST',
                    body: formData
                });
                if (response.ok) {
                    const data = await response.json();
                    if (data.text) {
                        document.getElementById('chatInput').value = data.text;
                        addSystemMessage(`Voice transcribed: "${data.text}"`, 'success');
                    }
                    return;
                }
            } catch (error) {
                console.warn(`Speech-to-text API failed with primary URL ${apiBaseUrl}:`, error.message);
            }
        }
        
        // Try fallback URLs if primary failed
        const fallbackUrls = window.ai2d_chat_CONFIG?.FALLBACK_URLS || [];
        for (const fallbackUrl of fallbackUrls) {
            try {
                console.log(`Trying speech-to-text API fallback URL: ${fallbackUrl}`);
                response = await fetch(`${fallbackUrl}/api/speech-to-text`, {
                    method: 'POST',
                    body: formData
                });
                if (response.ok) {
                    console.log(`Speech-to-text API successful with fallback URL: ${fallbackUrl}`);
                    // Update the working URL for future requests
                    window.ai2d_chat_CONFIG.API_BASE_URL = fallbackUrl;
                    const data = await response.json();
                    if (data.text) {
                        document.getElementById('chatInput').value = data.text;
                        addSystemMessage(`Voice transcribed: "${data.text}"`, 'success');
                    }
                    return;
                }
            } catch (error) {
                console.warn(`Speech-to-text API fallback failed with ${fallbackUrl}:`, error.message);
            }
        }
        
        // If all URLs failed, throw error
        throw new Error('All speech-to-text API endpoints failed');
        
    } catch (error) {
        console.error('Error sending audio to server:', error);
        addSystemMessage('Failed to process voice recording', 'error');
    }
}

async function sendChatToAPI(message) {
    try {
        const response = await makeApiCall('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.response) {
                addMessageToChat('assistant', data.response);
            }
        } else {
            addMessageToChat('system', 'Error: Failed to get response from AI');
        }
    } catch (error) {
        console.error('Chat API error:', error);
        addMessageToChat('system', 'Error: Could not send message');
    }
}

// Live2D Emotional Response Integration
function triggerEmotionalResponse(emotion, intensity = 0.5) {
    if (!window.live2dIntegration || !window.live2dIntegration.motionManager) {
        console.warn('Live2D integration not available for emotional response');
        return;
    }
    
    // Map emotions to Live2D motions
    const emotionMotionMap = {
        'happy': 'idle',
        'excited': 'head',
        'sad': 'body',
        'surprised': 'expression',
        'curious': 'special',
        'thoughtful': 'talk'
    };
    
    const motionType = emotionMotionMap[emotion] || 'idle';
    
    console.log(`🎭 Triggering emotional response: ${emotion} (${motionType})`);
    
    // Trigger motion via Live2D integration
    if (typeof window.triggerMotion === 'function') {
        window.triggerMotion(motionType);
    }
}

// System Utility Functions
function addSystemMessage(message, type = 'info') {
    if (typeof addChatMessage === 'function') {
        addChatMessage('system', message, type);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export functions for global access
window.loadServerConfig = loadServerConfig;
window.sendAudioToServer = sendAudioToServer;
window.sendChatToAPI = sendChatToAPI;
window.triggerEmotionalResponse = triggerEmotionalResponse;
window.addSystemMessage = addSystemMessage;
window.escapeHtml = escapeHtml;
