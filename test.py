from oop import wave
from cadence import make_cadence, PATTERNS
from plotter import plot_audio_onsets_beats, plot_cadence_pattern
from preprocessing import BPM_preprocssing, phase_shift
from scipy.io.wavfile import write
import numpy as np
import os
import matplotlib.pyplot as plt


# Get audio instance, extract beats
path = "Songs/Seven Nation Army.mp3"
song = wave(path)
song.extract()
song.mode = 1

## Tests ----------------------------------------------------------## 

### --- Test block 1: Plot beats => FAIL : Beats stop at 206 sec ###
## Plot onset envelope and beats between 30s and 60s
# plot_audio_onsets_beats(song, start=30.0, end=60.0, save_path="Plots/seven_nation_onsets.png")


# ### --- Test block 2: Clicks Audio => PASS###
# ## Add clicks on beats and save to WAV
# clicks = song.add_clicks()
# write("clicks.wav", song.sr, clicks)


# ### --- Test block 3: "Slow and steady" => FAIL :  ###
# # Plot slow and steady cadence
# long_interval_pattern = [160, 0, 170, 0, 130, 0, 180, 0]
# cad = make_cadence(song, pattern="noisy_natural", output="energy", segment_length=30.0)
# plot_cadence_pattern(cad, pattern_name="noisy_natural")

# # ZOOMED view (This fixes your visual issue!)
# print("Plotting zoomed cadence ...")
# plot_cadence_pattern(cad, pattern_name="noisy_natural", 
#                      start=40.0, end=80.0, 
#                      save_path="Plots/zoomed_cadence_noisy_natural.png")

# ## --- Test block 4: "Check Preprocessing with synthetic trains" => PASS ###

# long_interval_pattern = [150, 180, 140, 175, 130, 160, 180, 145]
# cadence = make_cadence(song, pattern="noisy_natural", output="energy", segment_length=30.0)
# cadence.mode = 2
# BPM_preprocssing(song, cadence, dt=0.5)
# ## Show a graph with: song.tempo(Title or constant value on graph), cadence.spm_list (list of spm every dt = 0.5 sec), song.r_list(list of r every dt = 0.5 sec) - Save graph
# # Create time axis for the lists (0.5s steps)
# dt = 0.5
# time_axis = np.arange(len(cadence.spm_list)) * dt

# fig, ax1 = plt.subplots(figsize=(10, 6))

# # Plot SPM (Left Y-axis)
# color = 'tab:blue'
# ax1.set_xlabel('Time (s)')
# ax1.set_ylabel('Cadence SPM', color=color)
# ax1.plot(time_axis, cadence.spm_list, color=color, label='Detected SPM')
# ax1.tick_params(axis='y', labelcolor=color)
# ax1.grid(True, alpha=0.3)

# # Plot Ratio 'r' (Right Y-axis)
# ax2 = ax1.twinx()  
# color = 'tab:red'
# ax2.set_ylabel('Ratio r (SPM/BPM)', color=color)
# ax2.plot(time_axis, song.r_list, color=color, linestyle='--', label='Ratio r')
# ax2.tick_params(axis='y', labelcolor=color)

# plt.title(f"Preprocessing Result: Song Tempo ~{song.tempo:.1f} BPM")
# fig.tight_layout()
# plt.savefig("Plots/noisy_natural.png")
# plt.show()

### --- Test case: mode in opp => PASS: ###
## Test if mode is OK 
# general_wave = 0
# song_wave = 1
# cadence_mode = 2
# err_list = [wave(song)]

# for i in range (4):
#     dummy = wave(path, mode=i)
#     print(f"Test {i} passed" if dummy.mode == i else f"Test {i} FAILED")

# Passes error tests

# ### ---  Generate and Plot All Patterns with Noise --- ###
# print("--- Generating All Patterns with Noise (Std=2.0) ---")

# # We iterate over every pattern name available in your library
# for pattern_name in PATTERNS.keys():
#     print(f"Processing pattern: {pattern_name}...")
    
#     # 1. Create the noisy cadence
#     # We add noise_std=2.0 and drift_std=0.5 to simulate a 'rough' runner
#     cadence = make_cadence(song, 
#                            pattern=pattern_name, 
#                            output="energy", 
#                            segment_length=30.0, # length for interval/start_stop
#                            noise_std=2.0, 
#                            drift_std=0.5,
#                            seed=42) # Fixed seed so results are reproducible
    
#     # 2. Explicitly set mode (just to be safe)
#     cadence.mode = 2

#     # 3. Plot and Save
#     # We save each one with a unique name so you can compare them
#     plot_cadence_pattern(cadence, 
#                          pattern_name=f"{pattern_name} (Noisy)", 
#                          save_path=f"Plots/Cadence Making & Pre-Processing/Noisy Cadence - Impulse Train/noisy_{pattern_name}.png")
    
#     # Close the plot to clear memory for the next loop
#     plt.close()

# print("All noisy patterns generated and saved in /Plots folder.")

### --- Test block: Preprocessing & Ratio Plotting on All Noisy Patterns --- ###
# print("\n--- Running Preprocessing on All Noisy Patterns ---")

# 1. Setup folders
# output_folder = "Plots/Cadence Making & Pre-Processing/Noisy Cadence - Impulse Train"
# os.makedirs(output_folder, exist_ok=True)

# # 2. Loop through all patterns
# for pattern_name in PATTERNS.keys():
#     print(f"Processing {pattern_name}...")
    
#     song.r_list = []

#     # --- B. Create Noisy Cadence ---
#     cadence = make_cadence(song, 
#                            pattern=pattern_name, 
#                            output="energy", 
#                            segment_length=30.0, 
#                            noise_std=2.0,   # Add your noise here
#                            drift_std=0.5,
#                            seed=42)
    
#     # --- C. Set Modes & Run Preprocessing ---
#     cadence.mode = 2
#     # song.mode is likely already 1, but we can ensure it:
#     song.mode = 1
    
#     try:
#         BPM_preprocssing(song, cadence, dt=0.5, dr=0.01)
#     except Exception as e:
#         print(f"Skipping {pattern_name} due to error: {e}")
#         continue

#     # --- D. Plotting (Logic from Test Block 4) ---
#     dt = 0.5
#     # cadence.list is filled by BPM_preprocssing
#     # song.r_list is filled by BPM_preprocssing
#     time_axis = np.arange(len(cadence.spm_list)) * dt

#     fig, ax1 = plt.subplots(figsize=(10, 6))

#     # Plot SPM (Left Y-axis)
#     color = 'tab:blue'
#     ax1.set_xlabel('Time (s)')
#     ax1.set_ylabel('Cadence SPM', color=color)
#     ax1.plot(time_axis, cadence.spm_list, color=color, label='Detected SPM')
#     ax1.tick_params(axis='y', labelcolor=color)
#     ax1.grid(True, alpha=0.3)

#     # Plot Ratio 'r' (Right Y-axis)
#     ax2 = ax1.twinx()  
#     color = 'tab:red'
#     ax2.set_ylabel('Ratio r (SPM/BPM)', color=color)
#     ax2.plot(time_axis, song.r_list, color=color, linestyle='--', label='Ratio r')
#     ax2.tick_params(axis='y', labelcolor=color)

#     plt.title(f"Preprocessing: {pattern_name} (Noise=2.0)")
#     fig.tight_layout()

#     # --- E. Save ---
#     save_path = f"{output_folder}/preproc_{pattern_name}.png"
#     plt.savefig(save_path)
#     plt.close() # Close figure to free memory

# print(f"All preprocessing plots saved in: {output_folder}")


# ## --- Test block: "Check Phase Shift Function" ###
# test phase shift function
cadence = make_cadence(song, output="energy", segment_length=30.0)
ps = phase_shift(song, cadence, r=1.0, start_time=10.0, end_time=50.0, debug=True)
