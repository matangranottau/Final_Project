from oop import wave
from cadence import cadence
from plotter import plot_audio_onsets_beats
from preprocessing import BPM_preprocssing
from scipy.io.wavfile import write
import numpy as np


# Get audio instance, extract beats
path = "Songs/Seven Nation Army.mp3"
song = wave(path)
song.extract()

## Tests ----------------------------------------------------------## 

### --- Test block 1: Plot beats => FAIL : Beats stop at 206 sec ###
## Plot onset envelope and beats between 30s and 60s
plot_audio_onsets_beats(song, start=30.0, end=60.0, save_path="Plots/seven_nation_onsets.png")


### --- Test block 2: Clicks Audio => PASS###
## Add clicks on beats and save to WAV
clicks = song.add_clicks()
write("clicks.wav", song.sr, clicks)

### --- Test block 3: "Slow and steady" => FAIL :  ###
## Plot slow and steady cadence



### --- Test block 4: "Check Preprocessing with Slow and Steady"
bibi = cadence()
BPM_preprocssing(song, bibi)
## Show a graph with: song.tempo(Title or constant value on graph), cadence.spm_list (list of spm every dt = 0.5 sec), song.r_list(list of r every dt = 0.5 sec) - Save graph