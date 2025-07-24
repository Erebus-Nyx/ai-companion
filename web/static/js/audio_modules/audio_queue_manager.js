// Audio Queue Manager - Prevents audio overlap between multiple avatars
class AudioQueueManager {
    constructor() {
        this.isPlaying = false;
        this.audioQueue = [];
        this.currentAudio = null;
        this.currentAvatarId = null;
        this.preemptionMode = 'queue'; // 'queue', 'interrupt', 'priority'
        
        // Performance monitoring
        this.stats = {
            totalRequests: 0,
            completedRequests: 0,
            queuedRequests: 0,
            interruptedRequests: 0
        };
        
        console.log('🎵 Audio Queue Manager initialized');
    }
    
    // Add audio to queue with optional priority
    async queueAudio(audioRequest) {
        this.stats.totalRequests++;
        
        const queueItem = {
            id: this.generateRequestId(),
            ...audioRequest,
            priority: audioRequest.priority || 1,
            timestamp: Date.now(),
            retries: 0
        };
        
        console.log(`🎵 Queuing audio request: ${queueItem.id} for avatar: ${queueItem.avatarId}`);
        
        // Handle different modes
        switch (this.preemptionMode) {
            case 'interrupt':
                return this.handleInterruptMode(queueItem);
            
            case 'priority':
                return this.handlePriorityMode(queueItem);
            
            case 'queue':
            default:
                return this.handleQueueMode(queueItem);
        }
    }
    
    // Queue mode: Add to queue and wait for turn
    async handleQueueMode(queueItem) {
        this.audioQueue.push(queueItem);
        this.stats.queuedRequests++;
        
        console.log(`🎵 Added to queue: ${queueItem.id} (position: ${this.audioQueue.length})`);
        
        if (!this.isPlaying) {
            this.processQueue();
        }
        
        return this.waitForCompletion(queueItem.id);
    }
    
    // Interrupt mode: Stop current audio and play immediately
    async handleInterruptMode(queueItem) {
        if (this.isPlaying && this.currentAudio) {
            console.log(`🎵 Interrupting current audio for: ${queueItem.id}`);
            this.stopCurrentAudio();
            this.stats.interruptedRequests++;
        }
        
        // Clear queue and add new item
        this.audioQueue = [queueItem];
        this.processQueue();
        
        return this.waitForCompletion(queueItem.id);
    }
    
    // Priority mode: Insert based on priority, optionally interrupt
    async handlePriorityMode(queueItem) {
        // Check if we should interrupt current audio
        if (this.isPlaying && this.currentAudio && 
            queueItem.priority > (this.currentAudio.priority || 1)) {
            console.log(`🎵 High priority interrupt for: ${queueItem.id}`);
            this.stopCurrentAudio();
            this.stats.interruptedRequests++;
        }
        
        // Insert into queue based on priority
        this.insertByPriority(queueItem);
        this.stats.queuedRequests++;
        
        if (!this.isPlaying) {
            this.processQueue();
        }
        
        return this.waitForCompletion(queueItem.id);
    }
    
    // Insert item into queue based on priority
    insertByPriority(queueItem) {
        let insertIndex = this.audioQueue.length;
        
        for (let i = 0; i < this.audioQueue.length; i++) {
            if (queueItem.priority > (this.audioQueue[i].priority || 1)) {
                insertIndex = i;
                break;
            }
        }
        
        this.audioQueue.splice(insertIndex, 0, queueItem);
        console.log(`🎵 Inserted by priority: ${queueItem.id} at position ${insertIndex}`);
    }
    
    // Process the audio queue
    async processQueue() {
        if (this.isPlaying || this.audioQueue.length === 0) {
            return;
        }
        
        const nextItem = this.audioQueue.shift();
        this.currentAudio = nextItem;
        this.currentAvatarId = nextItem.avatarId;
        this.isPlaying = true;
        
        console.log(`🎵 Processing audio: ${nextItem.id} for avatar: ${nextItem.avatarId}`);
        
        try {
            await this.playAudioItem(nextItem);
            this.onAudioComplete(nextItem.id, true);
        } catch (error) {
            console.error(`🎵 Audio playback failed: ${nextItem.id}`, error);
            
            // Retry logic
            if (nextItem.retries < 2) {
                nextItem.retries++;
                this.audioQueue.unshift(nextItem); // Add back to front of queue
                console.log(`🎵 Retrying audio: ${nextItem.id} (attempt ${nextItem.retries + 1})`);
            } else {
                this.onAudioComplete(nextItem.id, false, error);
            }
        }
        
        this.isPlaying = false;
        this.currentAudio = null;
        this.currentAvatarId = null;
        
        // Process next item in queue
        if (this.audioQueue.length > 0) {
            setTimeout(() => this.processQueue(), 100); // Small delay between audio clips
        }
    }
    
    // Play individual audio item
    async playAudioItem(audioItem) {
        const { text, emotion, avatarId, personalityTraits, intensity, audioData } = audioItem;
        
        // If audio data is provided, play directly
        if (audioData) {
            return this.playAudioData(audioData, audioItem);
        }
        
        // Otherwise, generate TTS
        console.log(`🎵 Generating TTS for: ${audioItem.id}`);
        
        // Get API base URL
        const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
        
        // Request TTS from backend
        const response = await fetch(`${apiBaseUrl}/api/tts/avatar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                emotion: emotion || 'neutral',
                intensity: intensity || 0.5,
                avatar_id: avatarId,
                personality_traits: personalityTraits || {},
                sync_with_expressions: true
            })
        });
        
        if (!response.ok) {
            throw new Error(`TTS API error: ${response.status}`);
        }
        
        const ttsData = await response.json();
        console.log(`🎵 Received TTS data for: ${audioItem.id}`);
        
        // Trigger avatar expressions
        if (ttsData.live2d_params && window.triggerAvatarMotion) {
            this.triggerAvatarExpressionSync(avatarId, ttsData.live2d_params, ttsData.duration);
        }
        
        // Start lipsync
        if (ttsData.lipsync_data && Array.isArray(ttsData.lipsync_data)) {
            this.applyLipsyncToAvatar(avatarId, ttsData.lipsync_data);
        } else {
            const estimatedDuration = ttsData.duration || this.estimateAudioDuration(ttsData.audio_data);
            this.createBasicLipsyncPattern(avatarId, estimatedDuration * 1000);
        }
        
        // Play the audio
        return this.playAudioData(ttsData.audio_data, { ...audioItem, ...ttsData });
    }
    
    // Play audio data with proper management
    async playAudioData(audioData, audioItem) {
        return new Promise((resolve, reject) => {
            if (!audioData || audioData.length === 0) {
                console.warn(`🎵 No audio data for: ${audioItem.id}`);
                resolve();
                return;
            }
            
            console.log(`🎵 Playing audio: ${audioItem.id}`);
            
            // Use audio context manager if available and unlocked
            if (window.audioContextManager && window.audioContextManager.isAudioUnlocked()) {
                window.audioContextManager.playAudio(audioData, {
                    onStart: () => {
                        console.log(`🎵 Started playing: ${audioItem.id}`);
                    },
                    onEnd: () => {
                        console.log(`🎵 Finished playing: ${audioItem.id}`);
                        resolve();
                    }
                }).catch(error => {
                    console.error(`🎵 Audio context playback failed: ${audioItem.id}`, error);
                    this.fallbackAudioPlayback(audioData, audioItem, resolve, reject);
                });
            } else {
                this.fallbackAudioPlayback(audioData, audioItem, resolve, reject);
            }
        });
    }
    
    // Fallback audio playback
    fallbackAudioPlayback(audioData, audioItem, resolve, reject) {
        try {
            const audio = new Audio();
            
            // Handle different audio data formats
            if (typeof audioData === 'string') {
                if (audioData.startsWith('data:')) {
                    audio.src = audioData;
                } else {
                    audio.src = `data:audio/wav;base64,${audioData}`;
                }
            } else {
                console.error(`🎵 Unsupported audio format for: ${audioItem.id}`);
                reject(new Error('Unsupported audio format'));
                return;
            }
            
            audio.oncanplaythrough = () => {
                audio.play().catch(error => {
                    console.error(`🎵 Fallback playback failed: ${audioItem.id}`, error);
                    reject(error);
                });
            };
            
            audio.onerror = (error) => {
                console.error(`🎵 Audio loading failed: ${audioItem.id}`, error);
                reject(error);
            };
            
            audio.onended = () => {
                console.log(`🎵 Fallback playback completed: ${audioItem.id}`);
                resolve();
            };
            
            // Store reference for potential stopping
            audioItem.audioElement = audio;
            
            audio.load();
            
        } catch (error) {
            console.error(`🎵 Fallback setup failed: ${audioItem.id}`, error);
            reject(error);
        }
    }
    
    // Stop current audio
    stopCurrentAudio() {
        if (this.currentAudio) {
            console.log(`🎵 Stopping current audio: ${this.currentAudio.id}`);
            
            if (this.currentAudio.audioElement) {
                this.currentAudio.audioElement.pause();
                this.currentAudio.audioElement.currentTime = 0;
            }
            
            this.onAudioComplete(this.currentAudio.id, false, new Error('Interrupted'));
        }
    }
    
    // Wait for audio completion
    waitForCompletion(requestId) {
        return new Promise((resolve, reject) => {
            const checkCompletion = () => {
                const request = this.findRequest(requestId);
                if (request && request.completed !== undefined) {
                    if (request.completed) {
                        resolve(request.result);
                    } else {
                        reject(request.error || new Error('Audio playback failed'));
                    }
                } else {
                    setTimeout(checkCompletion, 100);
                }
            };
            
            checkCompletion();
        });
    }
    
    // Mark audio as complete
    onAudioComplete(requestId, success, result = null) {
        const request = this.findRequest(requestId);
        if (request) {
            request.completed = success;
            request.result = result;
            if (success) {
                this.stats.completedRequests++;
            }
        }
        
        // Clean up old completed requests
        this.cleanupCompletedRequests();
    }
    
    // Find request by ID
    findRequest(requestId) {
        // Check current audio
        if (this.currentAudio && this.currentAudio.id === requestId) {
            return this.currentAudio;
        }
        
        // Check queue
        return this.audioQueue.find(item => item.id === requestId);
    }
    
    // Generate unique request ID
    generateRequestId() {
        return 'audio_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // Clean up old completed requests
    cleanupCompletedRequests() {
        // Remove completed requests older than 30 seconds
        const cutoff = Date.now() - 30000;
        this.audioQueue = this.audioQueue.filter(item => 
            item.completed === undefined || item.timestamp > cutoff
        );
    }
    
    // Set preemption mode
    setPreemptionMode(mode) {
        if (['queue', 'interrupt', 'priority'].includes(mode)) {
            this.preemptionMode = mode;
            console.log(`🎵 Preemption mode set to: ${mode}`);
        } else {
            console.warn(`🎵 Invalid preemption mode: ${mode}`);
        }
    }
    
    // Clear queue
    clearQueue() {
        console.log(`🎵 Clearing queue (${this.audioQueue.length} items)`);
        this.audioQueue = [];
    }
    
    // Get queue status
    getStatus() {
        return {
            isPlaying: this.isPlaying,
            currentAvatarId: this.currentAvatarId,
            queueLength: this.audioQueue.length,
            preemptionMode: this.preemptionMode,
            stats: { ...this.stats }
        };
    }
    
    // Helper methods for avatar integration
    triggerAvatarExpressionSync(avatarId, liveParams, duration) {
        if (window.triggerAvatarExpressionSync) {
            return window.triggerAvatarExpressionSync(avatarId, liveParams, duration);
        }
    }
    
    applyLipsyncToAvatar(avatarId, lipsyncData) {
        if (window.applyLipsyncToAvatar) {
            return window.applyLipsyncToAvatar(avatarId, lipsyncData);
        }
    }
    
    createBasicLipsyncPattern(avatarId, duration) {
        if (window.createBasicLipsyncPattern) {
            return window.createBasicLipsyncPattern(avatarId, duration);
        }
    }
    
    estimateAudioDuration(audioData) {
        if (window.estimateAudioDuration) {
            return window.estimateAudioDuration(audioData);
        }
        return 3000; // Default 3 seconds
    }
}

// Create global audio queue manager
window.audioQueueManager = new AudioQueueManager();

// Export for use in other modules
window.AudioQueueManager = AudioQueueManager;

console.log('🎵 Audio Queue Manager loaded and initialized');
