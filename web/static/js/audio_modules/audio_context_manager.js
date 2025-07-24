// Audio Context Manager - Handle browser audio restrictions
class AudioContextManager {
    constructor() {
        this.audioContext = null;
        this.isUnlocked = false;
        this.pendingAudio = [];
        this.userInteractionHandlers = [];
        
        this.initializeAudioContext();
        this.setupUserInteractionHandlers();
    }
    
    initializeAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('🔊 Audio context initialized');
        } catch (error) {
            console.error('Failed to initialize audio context:', error);
        }
    }
    
    setupUserInteractionHandlers() {
        // List of events that count as user interaction
        const interactionEvents = ['click', 'touchstart', 'keydown', 'mousedown'];
        
        const unlockAudio = async () => {
            if (this.isUnlocked) return;
            
            try {
                // Resume audio context if suspended
                if (this.audioContext && this.audioContext.state === 'suspended') {
                    await this.audioContext.resume();
                }
                
                // Create and play a silent audio to unlock
                const audio = new Audio();
                audio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAAEAA==';
                await audio.play().catch(() => {}); // Ignore errors
                
                this.isUnlocked = true;
                console.log('🔓 Audio context unlocked by user interaction');
                
                // Remove event listeners
                interactionEvents.forEach(event => {
                    document.removeEventListener(event, unlockAudio);
                });
                
                // Play any pending audio
                this.playPendingAudio();
                
            } catch (error) {
                console.warn('Failed to unlock audio context:', error);
            }
        };
        
        // Add event listeners for user interaction
        interactionEvents.forEach(event => {
            document.addEventListener(event, unlockAudio, { once: false });
        });
    }
    
    async playAudio(audioData, options = {}) {
        if (!this.isUnlocked) {
            console.log('🔒 Audio locked, adding to pending queue');
            this.pendingAudio.push({ audioData, options });
            this.showAudioPrompt();
            return false;
        }
        
        return this.playAudioDirect(audioData, options);
    }
    
    async playAudioDirect(audioData, options = {}) {
        try {
            const audio = new Audio();
            
            // Handle different audio data formats
            if (typeof audioData === 'string') {
                if (audioData.startsWith('data:')) {
                    audio.src = audioData;
                } else if (audioData.startsWith('http')) {
                    audio.src = audioData;
                } else {
                    audio.src = `data:audio/wav;base64,${audioData}`;
                }
            } else {
                console.error('Unsupported audio data format');
                return false;
            }
            
            // Set up event handlers
            return new Promise((resolve, reject) => {
                audio.oncanplaythrough = () => {
                    console.log('🔊 Playing audio');
                    audio.play().then(() => {
                        if (options.onStart) options.onStart();
                        resolve(true);
                    }).catch(error => {
                        console.error('Audio playback failed:', error);
                        reject(error);
                    });
                };
                
                audio.onerror = (error) => {
                    console.error('Audio loading failed:', error);
                    reject(error);
                };
                
                audio.onended = () => {
                    console.log('🔊 Audio playback completed');
                    if (options.onEnd) options.onEnd();
                };
                
                audio.load();
            });
            
        } catch (error) {
            console.error('Error playing audio:', error);
            return false;
        }
    }
    
    playPendingAudio() {
        console.log(`🔊 Playing ${this.pendingAudio.length} pending audio files`);
        
        while (this.pendingAudio.length > 0) {
            const { audioData, options } = this.pendingAudio.shift();
            this.playAudioDirect(audioData, options);
        }
    }
    
    showAudioPrompt() {
        // Show a subtle prompt to the user about clicking to enable audio
        if (document.getElementById('audio-unlock-prompt')) return;
        
        const prompt = document.createElement('div');
        prompt.id = 'audio-unlock-prompt';
        prompt.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            font-size: 14px;
            z-index: 10000;
            cursor: pointer;
            animation: fadeIn 0.3s ease;
        `;
        prompt.innerHTML = '🔊 Click anywhere to enable audio';
        
        prompt.onclick = () => {
            prompt.remove();
        };
        
        document.body.appendChild(prompt);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (prompt.parentNode) {
                prompt.remove();
            }
        }, 5000);
    }
    
    getAudioContext() {
        return this.audioContext;
    }
    
    isAudioUnlocked() {
        return this.isUnlocked;
    }
}

// Create global audio context manager
window.audioContextManager = new AudioContextManager();

// Export for use in other modules
window.AudioContextManager = AudioContextManager;
