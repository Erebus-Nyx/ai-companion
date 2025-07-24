// tts-audio.js
// Emotional TTS audio playback system for frontend

// Global TTS state management
window.ttsState = {
    isPlaying: false,
    currentEmotion: 'neutral',
    currentIntensity: 0.5,
    queue: []
};

function triggerEmotionalTTS(text, emotion, avatarId, personalityTraits = {}, intensity = 0.5) {
    return new Promise(async (resolve, reject) => {
        try {
            console.log(`🎤 Triggering emotional TTS: "${text}" with emotion: ${emotion} for avatar: ${avatarId}`);
            
            // Update TTS state
            window.ttsState.isPlaying = true;
            window.ttsState.currentEmotion = emotion;
            window.ttsState.currentIntensity = intensity;
            
            // Calculate enhanced personality-based parameters
            const enhancedParams = calculatePersonalityTTSParams(emotion, intensity, personalityTraits);
            
            // Get API base URL
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
            
            // Request emotional TTS from backend
            const response = await fetch(`${apiBaseUrl}/api/tts/avatar`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    emotion: emotion,
                    intensity: intensity,
                    avatar_id: avatarId,
                    personality_traits: personalityTraits,
                    sync_with_expressions: true
                })
            });
            
            if (!response.ok) {
                throw new Error(`TTS API error: ${response.status}`);
            }
            
            const ttsData = await response.json();
            console.log('🎵 Received TTS data:', ttsData);
            
            // Trigger avatar expressions first
            if (ttsData.live2d_params && window.triggerAvatarMotion) {
                await triggerAvatarExpressionSync(avatarId, ttsData.live2d_params, ttsData.duration);
            }
            
            // Start lipsync and audio playback simultaneously
            const audioPromise = playEmotionalTTSAudio(ttsData);
            
            // Apply enhanced lipsync
            if (ttsData.lipsync_data && Array.isArray(ttsData.lipsync_data)) {
                applyLipsyncToAvatar(avatarId, ttsData.lipsync_data);
            } else {
                // Use estimated duration for basic lipsync
                const estimatedDuration = ttsData.duration || estimateAudioDuration(ttsData.audio_data);
                createBasicLipsyncPattern(avatarId, estimatedDuration * 1000);
            }
            
            // Wait for audio to complete
            await audioPromise;
            
            // Update TTS state
            window.ttsState.isPlaying = false;
            
            resolve(ttsData);
            
        } catch (error) {
            console.error('Emotional TTS error:', error);
            window.ttsState.isPlaying = false;
            
            // Fallback to basic TTS if emotional TTS fails
            try {
                await fallbackEmotionalTTS(text, emotion, avatarId);
                resolve({ fallback: true });
            } catch (fallbackError) {
                reject(fallbackError);
            }
        }
    });
}

function calculatePersonalityTTSParams(emotion, intensity, personalityTraits) {
    const baseParams = {
        speed: 1.0,
        pitch: 1.0,
        warmth: 0.5,
        breathiness: 0.3
    };
    
    // Personality-based adjustments
    if (personalityTraits.seductive > 0.5) {
        baseParams.pitch *= 0.95;
        baseParams.breathiness += 0.3;
        baseParams.speed *= 0.9;
    }
    
    if (personalityTraits.confident > 0.7) {
        baseParams.pitch *= 1.05;
        baseParams.speed *= 1.1;
    }
    
    if (personalityTraits.shy > 0.5) {
        baseParams.pitch *= 1.1;
        baseParams.speed *= 0.9;
        baseParams.breathiness += 0.2;
    }
    
    if (personalityTraits.horny > 0.4) {
        baseParams.breathiness += 0.4;
        baseParams.warmth += 0.3;
        baseParams.speed *= 0.85;
    }
    
    // Emotion intensity scaling
    const emotionScale = 0.5 + (intensity * 0.5);
    for (let param in baseParams) {
        if (param !== 'speed') {
            baseParams[param] *= emotionScale;
        }
    }
    
    return baseParams;
}

async function triggerAvatarExpressionSync(avatarId, live2dParams, duration) {
    try {
        console.log(`🎭 Triggering avatar expressions for ${avatarId}:`, live2dParams);
        
        // Get the avatar model
        const avatarModel = getAvatarModel(avatarId);
        if (!avatarModel) {
            console.warn(`⚠️ Avatar model not found for ${avatarId}, skipping expression sync`);
            return;
        }
        
        let expressionsSynced = false;
        
        // Trigger motion with robust error handling
        if (live2dParams.motion && window.triggerAvatarMotion) {
            try {
                await window.triggerAvatarMotion(avatarModel, live2dParams.motion, {
                    intensity: live2dParams.intensity,
                    duration: duration,
                    avatar_id: avatarId,
                    personality_traits: live2dParams.personality_influence,
                    sync_with_speech: live2dParams.sync_with_speech
                });
                expressionsSynced = true;
                console.log(`✅ Motion "${live2dParams.motion}" synced for ${avatarId}`);
            } catch (motionError) {
                console.warn(`⚠️ Motion "${live2dParams.motion}" failed for ${avatarId}:`, motionError);
                // Try fallback motion
                await tryFallbackAvatarMotion(avatarModel, avatarId);
            }
        }
        
        // Trigger expression with robust error handling
        if (live2dParams.expression && window.triggerAvatarExpression) {
            try {
                await window.triggerAvatarExpression(avatarModel, live2dParams.expression, {
                    intensity: live2dParams.intensity,
                    avatar_id: avatarId
                });
                expressionsSynced = true;
                console.log(`✅ Expression "${live2dParams.expression}" synced for ${avatarId}`);
            } catch (expressionError) {
                console.warn(`⚠️ Expression "${live2dParams.expression}" failed for ${avatarId}:`, expressionError);
                // Try fallback expression
                await tryFallbackAvatarExpression(avatarModel, avatarId);
            }
        }
        
        // Adjust eye blink rate with error handling
        if (live2dParams.eye_blink_rate && window.setAvatarBlinkRate) {
            try {
                window.setAvatarBlinkRate(avatarId, live2dParams.eye_blink_rate);
                console.log(`👁️ Blink rate adjusted for ${avatarId}`);
            } catch (blinkError) {
                console.warn(`⚠️ Blink rate adjustment failed for ${avatarId}:`, blinkError);
            }
        }
        
        // Apply body sway with error handling
        if (live2dParams.body_sway && window.setAvatarBodySway) {
            try {
                window.setAvatarBodySway(avatarId, live2dParams.body_sway);
                console.log(`🎭 Body sway applied for ${avatarId}`);
            } catch (swayError) {
                console.warn(`⚠️ Body sway failed for ${avatarId}:`, swayError);
            }
        }
        
        // Log sync status
        if (!expressionsSynced) {
            console.warn(`⚠️ No expressions could be synced for ${avatarId}, using basic fallback`);
            // Apply basic visual feedback
            await applyBasicVisualFeedback(avatarId, live2dParams);
        }
        
        console.log(`✨ Avatar expressions synchronized for ${avatarId} (${duration}s)`);
        
    } catch (error) {
        console.error('❌ Avatar expression sync error:', error);
        // Continue gracefully even if expressions fail
        console.log(`🔄 Continuing TTS playback without avatar expressions for ${avatarId}`);
    }
}

function getAvatarModel(avatarId) {
    // Get the Live2D model for this avatar with multiple fallback methods
    try {
        // Method 1: Check window.live2dMultiModelManager
        if (window.live2dMultiModelManager) {
            const models = window.live2dMultiModelManager.getAllModels();
            const avatarModel = models.find(model => model.name === avatarId);
            if (avatarModel && avatarModel.pixiModel) {
                return avatarModel.pixiModel;
            }
        }
        
        // Method 2: Check global avatar chat manager
        if (window.avatarChatManager && window.avatarChatManager.activeAvatars) {
            const activeAvatar = window.avatarChatManager.activeAvatars.get(avatarId);
            if (activeAvatar && activeAvatar.pixiModel) {
                return activeAvatar.pixiModel;
            }
        }
        
        // Method 3: Check if avatar model is available globally
        if (window[`${avatarId}Model`]) {
            return window[`${avatarId}Model`];
        }
        
        // Method 4: Look for Live2D model in global scope
        if (window.live2dModels && window.live2dModels[avatarId]) {
            return window.live2dModels[avatarId];
        }
        
        console.warn(`⚠️ Avatar model not found for ${avatarId} using any method`);
        return null;
        
    } catch (error) {
        console.error(`❌ Error getting avatar model for ${avatarId}:`, error);
        return null;
    }
}

async function tryFallbackAvatarMotion(avatarModel, avatarId) {
    // Try basic fallback motions when primary motion fails
    const fallbackMotions = ['idle', 'default', 'neutral'];
    
    for (const motion of fallbackMotions) {
        try {
            if (typeof avatarModel.motion === 'function') {
                await avatarModel.motion(motion);
                console.log(`✅ Fallback motion "${motion}" succeeded for ${avatarId}`);
                return;
            }
        } catch (error) {
            console.warn(`⚠️ Fallback motion "${motion}" failed for ${avatarId}`);
        }
    }
    
    console.warn(`⚠️ All fallback motions failed for ${avatarId}`);
}

async function tryFallbackAvatarExpression(avatarModel, avatarId) {
    // Try basic fallback expressions when primary expression fails
    const fallbackExpressions = ['default', 'neutral', 'smile'];
    
    for (const expression of fallbackExpressions) {
        try {
            if (typeof avatarModel.expression === 'function') {
                await avatarModel.expression(expression);
                console.log(`✅ Fallback expression "${expression}" succeeded for ${avatarId}`);
                return;
            }
        } catch (error) {
            console.warn(`⚠️ Fallback expression "${expression}" failed for ${avatarId}`);
        }
    }
    
    console.warn(`⚠️ All fallback expressions failed for ${avatarId}`);
}

async function applyBasicVisualFeedback(avatarId, live2dParams) {
    // Apply basic visual feedback when avatar expressions aren't available
    try {
        // Create visual indicator that TTS is playing
        createTTSVisualIndicator(avatarId, live2dParams.emotion || 'speaking');
        
        // Try simple model highlighting or scaling if possible
        const avatarModel = getAvatarModel(avatarId);
        if (avatarModel) {
            // Subtle scale animation to show activity
            const originalScale = avatarModel.scale ? avatarModel.scale.x : 1.0;
            const targetScale = originalScale * 1.02;
            
            // Simple animation loop
            let animationFrame = 0;
            const animate = () => {
                if (animationFrame < 30) { // 0.5 second animation
                    const progress = animationFrame / 30;
                    const currentScale = originalScale + (targetScale - originalScale) * Math.sin(progress * Math.PI);
                    
                    if (avatarModel.scale) {
                        avatarModel.scale.set(currentScale);
                    }
                    
                    animationFrame++;
                    requestAnimationFrame(animate);
                } else {
                    // Reset to original scale
                    if (avatarModel.scale) {
                        avatarModel.scale.set(originalScale);
                    }
                }
            };
            
            animate();
        }
        
        console.log(`🎨 Applied basic visual feedback for ${avatarId}`);
        
    } catch (error) {
        console.warn(`⚠️ Basic visual feedback failed for ${avatarId}:`, error);
    }
}

function createTTSVisualIndicator(avatarId, emotion) {
    // Create a visual indicator that shows TTS is active for this avatar
    try {
        let indicator = document.getElementById(`tts-indicator-${avatarId}`);
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = `tts-indicator-${avatarId}`;
            indicator.style.cssText = `
                position: absolute;
                top: 10px;
                left: 10px;
                background: rgba(0, 123, 255, 0.8);
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 10px;
                z-index: 1000;
                pointer-events: none;
                transition: opacity 0.3s ease;
            `;
            
            // Try to position near the avatar if possible
            const avatarElement = document.querySelector(`[data-avatar-id="${avatarId}"]`) || 
                                document.querySelector('.live2d-canvas') || 
                                document.body;
            
            avatarElement.appendChild(indicator);
        }
        
        const emotionIcon = getEmotionIcon(emotion);
        indicator.textContent = `${emotionIcon} ${avatarId}`;
        indicator.style.opacity = '1';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            indicator.style.opacity = '0';
            setTimeout(() => {
                if (indicator.parentNode) {
                    indicator.parentNode.removeChild(indicator);
                }
            }, 300);
        }, 3000);
        
    } catch (error) {
        console.warn(`⚠️ Failed to create TTS visual indicator for ${avatarId}:`, error);
    }
}

function applyLipsyncToAvatar(avatarId, lipsyncData) {
    if (!lipsyncData || !Array.isArray(lipsyncData)) {
        // Create basic rhythm if no lipsync data
        createBasicLipsyncPattern(avatarId);
        return;
    }
    
    console.log(`👄 Applying enhanced lipsync to avatar ${avatarId}:`, lipsyncData);
    
    lipsyncData.forEach((frame, index) => {
        setTimeout(() => {
            if (window.setAvatarMouthShape) {
                window.setAvatarMouthShape(avatarId, frame.mouth_shape, frame.intensity);
            }
        }, frame.start_time * 1000);
        
        // Reset mouth shape at end of frame
        setTimeout(() => {
            if (window.setAvatarMouthShape) {
                window.setAvatarMouthShape(avatarId, 'default', 0.3);
            }
        }, frame.end_time * 1000);
    });
}

// Create basic lipsync pattern when no data is available
function createBasicLipsyncPattern(avatarId, durationMs = 3000) {
    const frameInterval = 150; // 150ms between changes (6.7 FPS)
    const frames = Math.floor(durationMs / frameInterval);
    const mouthShapes = ['A', 'I', 'U', 'E', 'O', 'default'];
    
    console.log(`👄 Creating basic lipsync pattern for ${avatarId} (${frames} frames)`);
    
    for (let i = 0; i < frames; i++) {
        setTimeout(() => {
            if (window.setAvatarMouthShape) {
                // More varied pattern with weighted probabilities
                let mouthShape;
                const rand = Math.random();
                if (rand < 0.3) mouthShape = 'A';        // Open mouth
                else if (rand < 0.5) mouthShape = 'I';   // Narrow mouth
                else if (rand < 0.65) mouthShape = 'U';  // Round mouth
                else if (rand < 0.8) mouthShape = 'E';   // Medium open
                else if (rand < 0.9) mouthShape = 'O';   // Wide round
                else mouthShape = 'default';             // Closed
                
                const intensity = 0.6 + (Math.random() * 0.4); // 0.6-1.0 intensity
                window.setAvatarMouthShape(avatarId, mouthShape, intensity);
            }
        }, i * frameInterval);
    }
    
    // Ensure mouth closes at the end
    setTimeout(() => {
        if (window.setAvatarMouthShape) {
            window.setAvatarMouthShape(avatarId, 'default', 0.3);
        }
    }, durationMs);
}

// Estimate audio duration from data (rough approximation)
function estimateAudioDuration(audioData) {
    if (!audioData) return 3; // Default 3 seconds
    
    if (typeof audioData === 'string') {
        // For base64 strings, estimate based on length
        // Rough calculation: 44.1kHz, 16-bit, mono WAV
        const base64Length = audioData.replace(/^data:audio\/wav;base64,/, '').length;
        const byteLength = (base64Length * 3) / 4; // Base64 to byte conversion
        const sampleRate = 22050; // Common TTS sample rate
        const bytesPerSample = 2; // 16-bit
        const duration = byteLength / (sampleRate * bytesPerSample);
        return Math.max(1, Math.min(10, duration)); // Clamp between 1-10 seconds
    }
    
    if (Array.isArray(audioData)) {
        // For float arrays, assume 22050 Hz sample rate
        return audioData.length / 22050;
    }
    
    return 3; // Default fallback
}

async function fallbackEmotionalTTS(text, emotion, avatarId) {
    console.log('🔄 Using fallback TTS...');
    
    try {
        // Get API base URL
        const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
        
        // Use basic TTS endpoint
        const response = await fetch(`${apiBaseUrl}/api/tts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text
            })
        });
        
        if (response.ok) {
            const ttsData = await response.json();
            await playEmotionalTTSAudio({
                ...ttsData,
                emotion: emotion,
                intensity: 0.5
            });
            
            // Trigger basic avatar motion
            if (window.triggerAvatarMotion) {
                await window.triggerAvatarMotion(avatarId, emotion, 0.5);
            }
        }
    } catch (error) {
        console.error('Fallback TTS failed:', error);
        throw error;
    }
}

function playEmotionalTTSAudio(ttsData) {
    return new Promise((resolve, reject) => {
        try {
            const { audio_data, emotion, intensity, voice } = ttsData;
            if (!audio_data || audio_data.length === 0) {
                console.warn('No TTS audio data to play');
                resolve();
                return;
            }
            
            console.log('🔊 Starting TTS audio playback with data type:', typeof audio_data);
            
            // Handle base64 data URL format (new backend format)
            if (typeof audio_data === 'string' && audio_data.startsWith('data:audio/wav;base64,')) {
                console.log('🔊 Playing TTS audio (base64 format)');
                
                // Use audio context manager for better browser compatibility
                if (window.audioContextManager && window.audioContextManager.isAudioUnlocked()) {
                    console.log('🔊 Using audio context manager');
                    window.audioContextManager.playAudio(audio_data, {
                        onStart: () => {
                            console.log(`🔊 Playing emotional TTS: ${emotion} (intensity: ${intensity})`);
                        },
                        onEnd: () => {
                            console.log('🔊 TTS audio playback completed');
                            resolve();
                        }
                    }).catch(error => {
                        console.error('Audio context manager playback failed:', error);
                        // Fallback to direct playback
                        fallbackDirectPlayback(audio_data, resolve, reject);
                    });
                } else {
                    // Try to unlock audio first
                    console.log('🔊 Audio not unlocked, attempting direct playback');
                    fallbackDirectPlayback(audio_data, resolve, reject);
                }
                return;
            }
            
            // Handle base64 string (convert to data URL)
            if (typeof audio_data === 'string') {
                const dataUrl = `data:audio/wav;base64,${audio_data}`;
                console.log('🔊 Converting base64 string to data URL');
                fallbackDirectPlayback(dataUrl, resolve, reject);
                return;
            }
            
            // Legacy float array format (fallback)
            console.log('🔊 Using legacy float array audio format');
            if (!window.audioContext) {
                window.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            const audioArray = new Float32Array(audio_data);
            const audioBuffer = window.audioContext.createBuffer(1, audioArray.length, 24000);
            audioBuffer.copyToChannel(audioArray, 0);
            
            const source = window.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            
            const { gainNode, filterNode } = createEmotionalAudioEffects(emotion, intensity);
            
            source.connect(gainNode);
            gainNode.connect(filterNode);
            filterNode.connect(window.audioContext.destination);
            
            source.onended = () => {
                console.log('🔊 TTS playback completed');
                resolve();
            };
            
            source.start(0);
            console.log(`🔊 Playing emotional TTS: ${emotion} (intensity: ${intensity})`);
            showTTSPlaybackIndicator(emotion, intensity);
            
        } catch (error) {
            console.error('Error playing emotional TTS audio:', error);
            fallbackTTSPlayback(ttsData).then(resolve).catch(reject);
        }
    });
}

// Fallback direct playback method
function fallbackDirectPlayback(audio_data, resolve, reject) {
    const audio = new Audio();
    audio.src = audio_data;
    
    audio.oncanplaythrough = () => {
        audio.play().catch(error => {
            console.error('TTS audio playback failed:', error);
            reject(error);
        });
    };
    
    audio.onerror = (error) => {
        console.error('TTS audio loading failed:', error);
        reject(error);
    };
    
    audio.onended = () => {
        console.log('🔊 TTS audio playback completed');
        resolve();
    };
    
    audio.load();
}

function createEmotionalAudioEffects(emotion, intensity) {
    const audioContext = window.audioContext;
    const gainNode = audioContext.createGain();
    const filterNode = audioContext.createBiquadFilter();
    
    // Enhanced emotional audio processing
    switch (emotion) {
        case 'excited':
        case 'happy':
        case 'joyful':
            gainNode.gain.value = 1.0 + (intensity * 0.2);
            filterNode.type = 'highpass';
            filterNode.frequency.value = 100 + (intensity * 50);
            break;
            
        case 'seductive':
        case 'horny':
        case 'flirtatious':
            gainNode.gain.value = 0.9 + (intensity * 0.1);
            filterNode.type = 'lowpass';
            filterNode.frequency.value = 4000 - (intensity * 500);
            // Add slight warmth/breathiness effect
            break;
            
        case 'passionate':
        case 'romantic':
            gainNode.gain.value = 1.1 + (intensity * 0.15);
            filterNode.type = 'peaking';
            filterNode.frequency.value = 1000;
            filterNode.Q.value = 1.5;
            filterNode.gain.value = intensity * 4;
            break;
            
        case 'sad':
        case 'disappointed':
        case 'empathetic':
            gainNode.gain.value = 0.8 - (intensity * 0.1);
            filterNode.type = 'lowpass';
            filterNode.frequency.value = 3000 - (intensity * 500);
            break;
            
        case 'surprised':
        case 'amazed':
            gainNode.gain.value = 1.1 + (intensity * 0.3);
            filterNode.type = 'peaking';
            filterNode.frequency.value = 2000;
            filterNode.Q.value = 2;
            filterNode.gain.value = intensity * 6;
            break;
            
        case 'curious':
        case 'thoughtful':
            gainNode.gain.value = 0.9 + (intensity * 0.1);
            filterNode.type = 'peaking';
            filterNode.frequency.value = 1500;
            filterNode.Q.value = 1;
            filterNode.gain.value = intensity * 3;
            break;
            
        case 'confident':
        case 'dominant':
            gainNode.gain.value = 1.1 + (intensity * 0.2);
            filterNode.type = 'highpass';
            filterNode.frequency.value = 80;
            break;
            
        case 'shy':
        case 'nervous':
            gainNode.gain.value = 0.7 + (intensity * 0.1);
            filterNode.type = 'bandpass';
            filterNode.frequency.value = 1500;
            filterNode.Q.value = 0.7;
            break;
            
        default:
            gainNode.gain.value = 1.0;
            filterNode.type = 'allpass';
            filterNode.frequency.value = 1000;
            break;
    }
    
    return { gainNode, filterNode };
}

function fallbackTTSPlayback(ttsData) {
    return new Promise((resolve, reject) => {
        try {
            const audio = new Audio();
            const audioArray = new Float32Array(ttsData.audio_data);
            const audioBuffer = new ArrayBuffer(audioArray.length * 4);
            const view = new DataView(audioBuffer);
            
            for (let i = 0; i < audioArray.length; i++) {
                view.setFloat32(i * 4, audioArray[i], true);
            }
            
            const blob = new Blob([audioBuffer], { type: 'audio/wav' });
            const url = URL.createObjectURL(blob);
            audio.src = url;
            
            audio.onended = () => {
                URL.revokeObjectURL(url);
                resolve();
            };
            
            audio.onerror = () => {
                URL.revokeObjectURL(url);
                reject(new Error('Audio playback failed'));
            };
            
            audio.play();
            console.log('🔊 TTS playback via fallback method');
            
        } catch (error) {
            console.error('Fallback TTS playback failed:', error);
            reject(error);
        }
    });
}

function showTTSPlaybackIndicator(emotion, intensity) {
    let ttsIndicator = document.getElementById('tts-indicator');
    if (!ttsIndicator) {
        ttsIndicator = document.createElement('div');
        ttsIndicator.id = 'tts-indicator';
        ttsIndicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 123, 255, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 12px;
            z-index: 1000;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(ttsIndicator);
    }
    
    // Enhanced indicator with personality context
    const emotionIcon = getEmotionIcon(emotion);
    ttsIndicator.textContent = `${emotionIcon} ${emotion} (${(intensity * 100).toFixed(0)}%)`;
    ttsIndicator.style.opacity = '1';
    
    setTimeout(() => {
        ttsIndicator.style.opacity = '0';
    }, 3000);
}

function getEmotionIcon(emotion) {
    const icons = {
        'happy': '😊',
        'excited': '🤩',
        'sad': '😢',
        'angry': '😠',
        'surprised': '😲',
        'curious': '🤔',
        'seductive': '😏',
        'horny': '😈',
        'passionate': '🔥',
        'shy': '😳',
        'confident': '😎',
        'neutral': '🔊'
    };
    return icons[emotion] || '🔊';
}

// Export to window for global access
window.triggerEmotionalTTS = triggerEmotionalTTS;
window.playEmotionalTTSAudio = playEmotionalTTSAudio;
window.createEmotionalAudioEffects = createEmotionalAudioEffects;
window.fallbackTTSPlayback = fallbackTTSPlayback;
window.showTTSPlaybackIndicator = showTTSPlaybackIndicator;
window.calculatePersonalityTTSParams = calculatePersonalityTTSParams;
window.triggerAvatarExpressionSync = triggerAvatarExpressionSync;
window.applyLipsyncToAvatar = applyLipsyncToAvatar;
window.createBasicLipsyncPattern = createBasicLipsyncPattern;
window.estimateAudioDuration = estimateAudioDuration;
