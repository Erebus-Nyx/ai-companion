def load_audio_file(file_path):
    # Function to load an audio file and return the audio data
    import librosa
    audio_data, sample_rate = librosa.load(file_path, sr=None)
    return audio_data, sample_rate

def save_audio_file(file_path, audio_data, sample_rate):
    # Function to save audio data to a file
    import soundfile as sf
    sf.write(file_path, audio_data, sample_rate)

def normalize_audio(audio_data):
    # Function to normalize audio data
    return audio_data / max(abs(audio_data))

def split_audio(audio_data, start_time, end_time, sample_rate):
    # Function to split audio data between start_time and end_time
    start_sample = int(start_time * sample_rate)
    end_sample = int(end_time * sample_rate)
    return audio_data[start_sample:end_sample]

def get_duration(audio_data, sample_rate):
    # Function to get the duration of the audio in seconds
    return len(audio_data) / sample_rate

def convert_to_mono(audio_data):
    # Function to convert stereo audio to mono
    if audio_data.ndim > 1:
        return audio_data.mean(axis=1)
    return audio_data