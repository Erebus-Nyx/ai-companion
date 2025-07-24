#!/usr/bin/env python3
"""
Phoneme/Viseme Detection for Live2D Lipsync
Integrates with PyVTS for realistic mouth movements
"""

import asyncio
import logging
import numpy as np
from typing import List, Tuple, Optional
import tempfile
import os

try:
    import librosa
except ImportError:
    librosa = None
    logging.warning("librosa not installed. Install with: pip install librosa")

try:
    import speech_recognition as sr
except ImportError:
    sr = None
    logging.warning("SpeechRecognition not installed. Install with: pip install SpeechRecognition")

class PhonemeDetector:
    """Detect phonemes/visemes from audio for lipsync"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Basic phoneme to viseme mapping
        self.phoneme_viseme_map = {
            # Vowels
            'AA': 'A', 'AE': 'A', 'AH': 'A', 'AO': 'O', 'AW': 'A',
            'AY': 'A', 'EH': 'E', 'ER': 'E', 'EY': 'E', 'IH': 'I',
            'IY': 'I', 'OW': 'O', 'OY': 'O', 'UH': 'U', 'UW': 'U',
            
            # Consonants
            'B': 'M', 'P': 'M', 'M': 'M',  # Bilabial
            'F': 'F', 'V': 'F',  # Labiodental
            'TH': 'TH', 'DH': 'TH',  # Dental
            'T': 'T', 'D': 'T', 'N': 'T', 'L': 'T',  # Alveolar
            'S': 'S', 'Z': 'S', 'SH': 'S', 'ZH': 'S',  # Sibilant
            'CH': 'S', 'JH': 'S',  # Affricates
            'K': 'K', 'G': 'K', 'NG': 'K',  # Velar
            'HH': 'silent', 'Y': 'I', 'W': 'U', 'R': 'R'
        }
        
        # Enhanced viseme mapping for Live2D
        self.viseme_mouth_shapes = {
            'A': 'A',      # Open mouth (aa, ae, ah)
            'E': 'E',      # Medium open (eh, ey)
            'I': 'I',      # Narrow mouth (ih, iy)
            'O': 'O',      # Round mouth (ao, ow, oy)
            'U': 'U',      # Small round (uh, uw)
            'M': 'M',      # Closed mouth (m, b, p)
            'F': 'F',      # Lower lip to teeth (f, v)
            'TH': 'TH',    # Tongue between teeth
            'T': 'T',      # Tongue to roof (t, d, n, l)
            'S': 'S',      # Narrow with airflow (s, z, sh, zh, ch, jh)
            'K': 'K',      # Back of tongue (k, g, ng)
            'R': 'R',      # Rounded with tension
            'silent': 'silent'  # Mouth closed/neutral
        }
    
    def extract_phonemes_from_audio(self, audio_data: np.ndarray, sample_rate: int = 22050) -> List[Tuple[str, float, float]]:
        """
        Extract phonemes from audio data
        Returns list of (phoneme, start_time, end_time) tuples
        """
        if not librosa:
            self.logger.warning("librosa not available, using fallback phoneme detection")
            return self._fallback_phoneme_extraction(audio_data, sample_rate)
        
        try:
            # Simple onset detection for basic timing
            onset_frames = librosa.onset.onset_detect(
                y=audio_data, 
                sr=sample_rate, 
                units='time'
            )
            
            # Create phoneme sequence based on audio characteristics
            phonemes = []
            
            # Analyze spectral features
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
            
            # Segment audio and classify
            segment_duration = 0.1  # 100ms segments
            num_segments = int(len(audio_data) / (sample_rate * segment_duration))
            
            for i in range(num_segments):
                start_time = i * segment_duration
                end_time = (i + 1) * segment_duration
                
                start_sample = int(start_time * sample_rate)
                end_sample = int(end_time * sample_rate)
                
                if end_sample > len(audio_data):
                    break
                
                segment = audio_data[start_sample:end_sample]
                
                # Simple phoneme classification based on audio features
                phoneme = self._classify_audio_segment(segment, sample_rate)
                phonemes.append((phoneme, start_time, end_time))
            
            return self._smooth_phoneme_sequence(phonemes)
            
        except Exception as e:
            self.logger.error(f"Error extracting phonemes: {e}")
            return self._fallback_phoneme_extraction(audio_data, sample_rate)
    
    def _classify_audio_segment(self, segment: np.ndarray, sample_rate: int) -> str:
        """Classify audio segment into phoneme category"""
        try:
            # Calculate basic features
            energy = np.sum(segment ** 2)
            
            if energy < 0.001:  # Very quiet
                return 'silent'
            
            # Simple spectral analysis
            fft = np.fft.fft(segment)
            freqs = np.fft.fftfreq(len(segment), 1/sample_rate)
            magnitude = np.abs(fft)
            
            # Find dominant frequency
            dominant_freq_idx = np.argmax(magnitude[:len(magnitude)//2])
            dominant_freq = abs(freqs[dominant_freq_idx])
            
            # Basic phoneme classification
            if dominant_freq < 500:
                return 'U'  # Low frequency - rounded vowels
            elif dominant_freq < 1000:
                return 'O'  # Mid-low frequency
            elif dominant_freq < 2000:
                return 'A'  # Mid frequency - open vowels
            elif dominant_freq < 3000:
                return 'E'  # Mid-high frequency
            elif dominant_freq < 4000:
                return 'I'  # High frequency - narrow vowels
            else:
                return 'S'  # Very high frequency - sibilants
                
        except Exception:
            return 'A'  # Default fallback
    
    def _fallback_phoneme_extraction(self, audio_data: np.ndarray, sample_rate: int) -> List[Tuple[str, float, float]]:
        """Fallback phoneme extraction when advanced libraries aren't available"""
        duration = len(audio_data) / sample_rate
        num_segments = max(1, int(duration * 10))  # 10 segments per second
        
        phonemes = []
        vowels = ['A', 'E', 'I', 'O', 'U']
        consonants = ['M', 'S', 'T', 'K']
        
        import random
        
        for i in range(num_segments):
            start_time = i * duration / num_segments
            end_time = (i + 1) * duration / num_segments
            
            # Simple pattern: alternate vowels and consonants with some silence
            if i % 4 == 0:
                phoneme = 'silent'
            elif i % 2 == 1:
                phoneme = random.choice(vowels)
            else:
                phoneme = random.choice(consonants)
            
            phonemes.append((phoneme, start_time, end_time))
        
        return phonemes
    
    def _smooth_phoneme_sequence(self, phonemes: List[Tuple[str, float, float]]) -> List[Tuple[str, float, float]]:
        """Smooth phoneme transitions for better lipsync"""
        if len(phonemes) < 2:
            return phonemes
        
        smoothed = []
        prev_phoneme = None
        
        for phoneme, start, end in phonemes:
            # Avoid rapid transitions between similar phonemes
            if prev_phoneme and prev_phoneme == phoneme:
                # Extend previous phoneme duration
                if smoothed:
                    smoothed[-1] = (smoothed[-1][0], smoothed[-1][1], end)
                    continue
            
            # Filter out very short segments
            if end - start < 0.05:  # Less than 50ms
                continue
            
            smoothed.append((phoneme, start, end))
            prev_phoneme = phoneme
        
        return smoothed
    
    def _calculate_speech_envelope(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Calculate speech envelope for natural mouth movement intensity"""
        try:
            # Calculate amplitude envelope
            frame_length = int(0.025 * sample_rate)  # 25ms frames
            hop_length = int(0.010 * sample_rate)    # 10ms hop
            
            # Apply Hilbert transform for envelope
            analytic_signal = np.abs(librosa.stft(audio_data, hop_length=hop_length))
            envelope = np.mean(analytic_signal, axis=0)
            
            # Smooth envelope
            from scipy.signal import savgol_filter
            if len(envelope) > 10:
                envelope = savgol_filter(envelope, min(11, len(envelope)//2*2+1), 3)
            
            # Normalize to 0-1 range
            if np.max(envelope) > 0:
                envelope = envelope / np.max(envelope)
            
            return envelope
            
        except Exception as e:
            self.logger.error(f"Error calculating speech envelope: {e}")
            # Fallback: simple RMS envelope
            window_size = int(0.025 * sample_rate)
            envelope = []
            for i in range(0, len(audio_data) - window_size, window_size // 2):
                window = audio_data[i:i + window_size]
                rms = np.sqrt(np.mean(window ** 2))
                envelope.append(rms)
            
            envelope = np.array(envelope)
            if np.max(envelope) > 0:
                envelope = envelope / np.max(envelope)
            
            return envelope
    
    def phonemes_to_visemes(self, phonemes: List[Tuple[str, float, float]]) -> List[Tuple[str, float, float]]:
        """Convert phoneme sequence to viseme sequence for Live2D"""
        visemes = []
        
        for phoneme, start, end in phonemes:
            # Map phoneme to viseme
            viseme = self.viseme_mouth_shapes.get(phoneme, 'A')
            visemes.append((viseme, start, end))
        
        return visemes
    
    async def process_tts_audio(self, audio_data: np.ndarray, sample_rate: int = 22050) -> Tuple[List[str], List[float]]:
        """
        Process TTS audio and return phonemes and timing for PyVTS
        Returns (phonemes, timing) suitable for trigger_pyvts_lipsync()
        """
        try:
            # Extract phonemes with timing
            phoneme_sequence = self.extract_phonemes_from_audio(audio_data, sample_rate)
            
            # Convert to visemes
            viseme_sequence = self.phonemes_to_visemes(phoneme_sequence)
            
            # Extract phonemes and timing arrays
            phonemes = []
            timing = []
            
            for viseme, start, end in viseme_sequence:
                phonemes.append(viseme)
                timing.append(end - start)  # Duration of each phoneme
            
            self.logger.info(f"Processed {len(phonemes)} phonemes for lipsync")
            return phonemes, timing
            
        except Exception as e:
            self.logger.error(f"Error processing TTS audio: {e}")
            # Return basic fallback
            duration = len(audio_data) / sample_rate
            return ['A', 'I', 'O', 'E', 'silent'], [duration/5] * 5

# Global instance
phoneme_detector = None

def get_phoneme_detector():
    """Get or create phoneme detector instance"""
    global phoneme_detector
    if phoneme_detector is None:
        phoneme_detector = PhonemeDetector()
    return phoneme_detector

async def extract_phonemes_from_tts(audio_data: np.ndarray, sample_rate: int = 22050) -> tuple:
    """Extract phonemes from TTS audio for lipsync"""
    try:
        detector = get_phoneme_detector()
        phonemes = detector.extract_phonemes_from_audio(audio_data, sample_rate)
        
        # Convert to PyVTS timing format
        timing_data = []
        for phoneme, start_time, end_time in phonemes:
            timing_data.append({
                'phoneme': phoneme,
                'viseme': detector.phoneme_to_viseme.get(phoneme, 'neutral'),
                'start': start_time,
                'end': end_time,
                'duration': end_time - start_time
            })
        
        # Add speech envelope for natural mouth movement
        envelope = detector._calculate_speech_envelope(audio_data, sample_rate)
        
        return phonemes, timing_data, envelope
        
    except Exception as e:
        # Fallback with simple speech detection
        detector = get_phoneme_detector()
        fallback_phonemes = detector._fallback_phoneme_extraction(audio_data, sample_rate)
        timing_data = [{'phoneme': p[0], 'viseme': 'neutral', 'start': p[1], 'end': p[2], 'duration': p[2]-p[1]} for p in fallback_phonemes]
        envelope = np.abs(audio_data)  # Simple envelope
        return fallback_phonemes, timing_data, envelope
