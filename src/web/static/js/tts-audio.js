// tts-audio.js
// Emotional TTS audio playback system for frontend

function playEmotionalTTSAudio(ttsData) {
    try {
        const { audio_data, emotion, intensity, voice } = ttsData;
        if (!audio_data || audio_data.length === 0) {
            console.warn('No TTS audio data to play');
            return;
        }
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
        source.start(0);
        console.log(`🔊 Playing emotional TTS: ${emotion} (intensity: ${intensity})`);
        showTTSPlaybackIndicator(emotion, intensity);
    } catch (error) {
        console.error('Error playing emotional TTS audio:', error);
        fallbackTTSPlayback(ttsData);
    }
}

function createEmotionalAudioEffects(emotion, intensity) {
    const audioContext = window.audioContext;
    const gainNode = audioContext.createGain();
    const filterNode = audioContext.createBiquadFilter();
    switch (emotion) {
        case 'excited':
        case 'happy':
        case 'joyful':
            gainNode.gain.value = 1.0 + (intensity * 0.2);
            filterNode.type = 'highpass';
            filterNode.frequency.value = 100 + (intensity * 50);
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
        default:
            gainNode.gain.value = 1.0;
            filterNode.type = 'allpass';
            filterNode.frequency.value = 1000;
            break;
    }
    return { gainNode, filterNode };
}

function fallbackTTSPlayback(ttsData) {
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
        audio.play();
        audio.addEventListener('ended', () => {
            URL.revokeObjectURL(url);
        });
        console.log('🔊 TTS playback via fallback method');
    } catch (error) {
        console.error('Fallback TTS playback failed:', error);
    }
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
    ttsIndicator.textContent = `🔊 ${emotion} (${(intensity * 100).toFixed(0)}%)`;
    ttsIndicator.style.opacity = '1';
    setTimeout(() => {
        ttsIndicator.style.opacity = '0';
    }, 3000);
}

// Export to window for global access
window.playEmotionalTTSAudio = playEmotionalTTSAudio;
window.createEmotionalAudioEffects = createEmotionalAudioEffects;
window.fallbackTTSPlayback = fallbackTTSPlayback;
window.showTTSPlaybackIndicator = showTTSPlaybackIndicator;
