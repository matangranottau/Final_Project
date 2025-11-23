import librosa
import numpy as np

def extract(audio_path):
    """
    Extracts the beat times and estimated BPM from an audio file.

    Parameters:
    audio_path (str): Path to the audio file.

    Returns:
    tuple: A tuple containing a list of beat times (in seconds) and the estimated BPM.
    """
    # Load the audio file
    y, sr = librosa.load(audio_path)

    # Perform beat tracking
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

    # Convert beat frames to time (in seconds)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    return beat_times.tolist(), tempo

