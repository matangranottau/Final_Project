from oop import wave
from plotter import plot_audio_onsets_beats
from scipy.io.wavfile import write
import numpy as np

# Get audio instance, extract beats
path = "Songs/Seven Nation Army.mp3"
song = wave(path)
song.extract()

