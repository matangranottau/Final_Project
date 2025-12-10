from audio import audio
from plotter import plot_audio_onsets_beats
from scipy.io.wavfile import write
import numpy as np

# Get audio instance, extract beats
path = "Songs/Seven Nation Army.mp3"
song = audio(path)
song.extract()

# Plot onset envelope and beats between 30s and 60s
plot_audio_onsets_beats(song, start=30.0, end=60.0, save_path="Plots/seven_nation_onsets.png")

# Add clicks on beats and save to WAV
clicks = song.add_clicks()
write("clicks.wav", song.sr, clicks)