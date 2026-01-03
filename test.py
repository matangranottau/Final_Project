from oop import wave
from cadence import make_cadence
from plotter import plot_audio_onsets_beats, plot_cadence_pattern
from preprocessing import BPM_preprocssing
from scipy.io.wavfile import write
import numpy as np
import os
import matplotlib.pyplot as plt


# Get audio instance, extract beats
path = "Songs/Seven Nation Army.mp3"
song = wave(path)
song.extract()

## Tests ----------------------------------------------------------## 

### --- Test block 1: Plot beats => FAIL : Beats stop at 206 sec ###
## Plot onset envelope and beats between 30s and 60s
# plot_audio_onsets_beats(song, start=30.0, end=60.0, save_path="Plots/seven_nation_onsets.png")


# ### --- Test block 2: Clicks Audio => PASS###
# ## Add clicks on beats and save to WAV
# clicks = song.add_clicks()
# write("clicks.wav", song.sr, clicks)


### --- Test block 3: "Slow and steady" => FAIL :  ###
## Plot slow and steady cadence
# long_interval_pattern = [160, 0, 170, 0, 130, 0, 180, 0]
# cad = make_cadence(song, pattern="interval_training", output="energy", segment_length=30.0, spm_values=long_interval_pattern)
# plot_cadence_pattern(cad, pattern_name="start_stop")

# # 2. ZOOMED view (This fixes your visual issue!)
# print("Plotting zoomed cadence ...")
# plot_cadence_pattern(cad, pattern_name="start_stop", 
#                      start=40.0, end=80.0, 
#                      save_path="Plots/zoomed_cadence_start_stop.png")

### --- Test block 4: "Check Preprocessing with synthetic trains" => PASS ###

long_interval_pattern = [150, 180, 140, 175, 130, 160, 180, 145]
bibi = make_cadence(song, pattern="interval_training", output="energy", segment_length=30.0, spm_values=long_interval_pattern)
BPM_preprocssing(song, bibi, dt=0.5)
## Show a graph with: song.tempo(Title or constant value on graph), cadence.spm_list (list of spm every dt = 0.5 sec), song.r_list(list of r every dt = 0.5 sec) - Save graph
# Create time axis for the lists (0.5s steps)
dt = 0.5
time_axis = np.arange(len(bibi.spm_list)) * dt

fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot SPM (Left Y-axis)
color = 'tab:blue'
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Cadence SPM', color=color)
ax1.plot(time_axis, bibi.spm_list, color=color, label='Detected SPM')
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, alpha=0.3)

# Plot Ratio 'r' (Right Y-axis)
ax2 = ax1.twinx()  
color = 'tab:red'
ax2.set_ylabel('Ratio r (SPM/BPM)', color=color)
ax2.plot(time_axis, song.r_list, color=color, linestyle='--', label='Ratio r')
ax2.tick_params(axis='y', labelcolor=color)

plt.title(f"Preprocessing Result: Song Tempo ~{song.tempo:.1f} BPM")
fig.tight_layout()
plt.savefig("Plots/preprocessing_result_start_stop.png")
plt.show()