// voice-recording.js
// Enhanced voice recording and speech-to-text integration

class VoiceRecording {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.audioContext = null;
        this.analyser = null;
        this.visualizationCanvas = null;
    }

    async initialize() {
        try {
            // Initialize audio context for visualization
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('🎤 Voice recording system initialized');
            return true;
        } catch (error) {
            console.error('Failed to initialize voice recording:', error);
            return false;
        }
    }

    async startRecording() {
        try {
            // Request microphone access
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000
                } 
            });

            // Set up media recorder
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            this.audioChunks = [];

            // Set up event handlers
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };

            // Set up audio visualization
            this.setupVisualization();

            // Start recording
            this.mediaRecorder.start();
            this.isRecording = true;
            
            console.log('🎤 Recording started');
            this.updateUI(true);
            
            return true;
        } catch (error) {
            console.error('Error starting recording:', error);
            this.showError('Microphone access denied or not available');
            return false;
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        
        this.isRecording = false;
        console.log('🛑 Recording stopped');
        this.updateUI(false);
    }

    setupVisualization() {
        if (!this.stream || !this.audioContext) return;

        // Create audio analyser
        this.analyser = this.audioContext.createAnalyser();
        const source = this.audioContext.createMediaStreamSource(this.stream);
        source.connect(this.analyser);

        this.analyser.fftSize = 256;
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        // Simple visualization in console (can be enhanced with canvas)
        const visualize = () => {
            if (!this.isRecording) return;
            
            this.analyser.getByteFrequencyData(dataArray);
            const average = dataArray.reduce((a, b) => a + b, 0) / bufferLength;
            
            // Simple volume indicator in console
            if (average > 20) {
                console.log(`🎵 Recording volume: ${'█'.repeat(Math.floor(average / 10))}`);
            }
            
            requestAnimationFrame(visualize);
        };
        
        visualize();
    }

    async processRecording() {
        if (this.audioChunks.length === 0) {
            this.showError('No audio data recorded');
            return;
        }

        // Create audio blob
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        console.log(`🎤 Processing audio blob: ${audioBlob.size} bytes`);

        // Send to server for speech-to-text
        await this.sendToSpeechAPI(audioBlob);
    }

    async sendToSpeechAPI(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');

            // Show processing indicator
            this.showProcessing(true);

            const response = await fetch('/api/speech-to-text', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                this.handleSpeechResult(data);
            } else {
                // Fallback to simple audio processing
                await this.fallbackProcessing(audioBlob);
            }
        } catch (error) {
            console.error('Error processing speech:', error);
            this.showError('Failed to process voice recording');
        } finally {
            this.showProcessing(false);
        }
    }

    async fallbackProcessing(audioBlob) {
        try {
            // Convert blob to base64 for simple transmission
            const base64Audio = await this.blobToBase64(audioBlob);
            
            // Send to general chat API with audio flag
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: '[Voice Message]',
                    audio_data: base64Audio,
                    is_voice: true
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.handleSpeechResult(data);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Fallback processing failed:', error);
            this.showError('Voice processing unavailable');
        }
    }

    blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(',')[1]);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    handleSpeechResult(data) {
        if (data.text || data.transcription) {
            const text = data.text || data.transcription;
            
            // Put transcribed text in chat input
            const chatInput = document.getElementById('chatInput');
            if (chatInput) {
                chatInput.value = text;
                chatInput.focus();
            }
            
            // Show success message
            this.showSuccess(`Voice transcribed: "${text}"`);
            
            // Auto-send if configured
            if (data.auto_send || window.voiceAutoSend) {
                setTimeout(() => {
                    if (typeof window.sendMessage === 'function') {
                        window.sendMessage();
                    }
                }, 500);
            }
        } else {
            this.showError('No speech detected in recording');
        }
    }

    updateUI(recording) {
        const voiceButton = document.getElementById('voiceButton');
        if (voiceButton) {
            if (recording) {
                voiceButton.innerHTML = '🛑';
                voiceButton.style.backgroundColor = '#ff4444';
                voiceButton.title = 'Stop Recording';
            } else {
                voiceButton.innerHTML = '🎤';
                voiceButton.style.backgroundColor = '';
                voiceButton.title = 'Start Voice Recording';
            }
        }
    }

    showProcessing(show) {
        const voiceButton = document.getElementById('voiceButton');
        if (voiceButton) {
            if (show) {
                voiceButton.innerHTML = '⏳';
                voiceButton.style.backgroundColor = '#ff9800';
                voiceButton.disabled = true;
            } else {
                voiceButton.innerHTML = '🎤';
                voiceButton.style.backgroundColor = '';
                voiceButton.disabled = false;
            }
        }
    }

    showSuccess(message) {
        console.log(`✅ ${message}`);
        if (typeof window.addSystemMessage === 'function') {
            window.addSystemMessage(message, 'success');
        }
    }

    showError(message) {
        console.error(`❌ ${message}`);
        if (typeof window.addSystemMessage === 'function') {
            window.addSystemMessage(message, 'error');
        }
    }
}

// Global voice recording instance
window.voiceRecording = new VoiceRecording();

// Enhanced toggle function for the UI
async function toggleVoiceRecording() {
    if (!window.voiceRecording) {
        console.error('Voice recording system not initialized');
        return;
    }

    if (!window.voiceRecording.isRecording) {
        const success = await window.voiceRecording.startRecording();
        if (!success) {
            window.voiceRecording.showError('Failed to start recording');
        }
    } else {
        window.voiceRecording.stopRecording();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
    if (window.voiceRecording) {
        await window.voiceRecording.initialize();
        console.log('🎤 Voice recording system ready');
    }
});

// Global voice recording instance and functions
let globalVoiceRecording = null;

// Initialize global voice recording system
async function initializeVoiceRecording() {
    if (!globalVoiceRecording) {
        globalVoiceRecording = new VoiceRecording();
        const initialized = await globalVoiceRecording.initialize();
        if (!initialized) {
            console.error('Failed to initialize voice recording system');
            return false;
        }
    }
    return true;
}

// Global toggle function for UI buttons
async function toggleVoiceRecording() {
    if (!globalVoiceRecording) {
        const initialized = await initializeVoiceRecording();
        if (!initialized) {
            return;
        }
    }

    try {
        if (globalVoiceRecording.isRecording) {
            await globalVoiceRecording.stopRecording();
            console.log('🛑 Voice recording stopped');
        } else {
            await globalVoiceRecording.startRecording();
            console.log('🎤 Voice recording started');
        }
    } catch (error) {
        console.error('Error toggling voice recording:', error);
        globalVoiceRecording.showError('Microphone access denied or not available');
    }
}

// Fallback function for enhanced chat system compatibility
async function sendAudioToServer(audioBlob) {
    if (!globalVoiceRecording) {
        globalVoiceRecording = new VoiceRecording();
        await globalVoiceRecording.initialize();
    }
    
    return await globalVoiceRecording.sendToSpeechAPI(audioBlob);
}

// Export functions for global access
window.toggleVoiceRecording = toggleVoiceRecording;
window.initializeVoiceRecording = initializeVoiceRecording;
window.sendAudioToServer = sendAudioToServer;
window.VoiceRecording = VoiceRecording;
