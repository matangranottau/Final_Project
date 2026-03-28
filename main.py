## Imports ##
import numpy as np
import matplotlib.pyplot as plt
import librosa
import time
import soundfile as sf
import pp


#===================================
########## PP - Parameters ##########
#===================================
debug = True
preload_audio = True
path = 'sna.mp3'
segment = 2.5  # Segment Duration in seconds
r_nom = np.array([1.0,1.02,1.04,1.06,1.08])  # Nominal ratios for steps
std_dev = 0.05


#===================================
########## Code Execution ##########
#===================================
start = time.time()

# Preprocessing #

if preload_audio:
    sna = np.load('sna.npy')
    sna_sr = np.load('sna_sr.npy')
    sna_BPM = np.load('sna_BPM.npy')
    sna_beats = np.load('sna_beats.npy')
    if debug:
        print(f"Loaded audio from {path}\n")
        print(f"Audio shape: {sna.shape}\n")
        print(f"Audio sample rate: {sna_sr}\n")
        print(f"Tempo: {sna_BPM}\n")
        print(f"Beats (First 20):\n{np.round(sna_beats[:19],2)}\n")
else:
    sna, sna_sr = pp.load_audio(path, debug=debug)
    sna_BPM, sna_beats = pp.beat_tracking(sna, sna_sr, debug=debug)

run_SPM, run_steps = pp.create_run_steps(sna_beats, sna_BPM, r_nom, std_dev, debug=debug)

M,N = pp.trim_dim(sna_beats, sna_BPM, segment, debug=debug)
sna_mat = pp.reshape_vector(sna_beats, M, N, debug=debug, debug_name="Seven Nations Army")
run_mat = pp.reshape_vector(run_steps, M, N, debug=debug, debug_name="Run Steps")

d = 0
r_opt = np.ones(N)
for i in range(N):
    # Calculate the absolute start time of the current segment
    t_start = i * segment 
    
    # Pass the unmodified absolute timestamps, t_start, and d
    r = pp.phase_pp_l1_shifted(sna_mat[:,i], run_mat[:,i], t_start, d, debug=debug)
    
    r_opt[i] = r
    d = d + segment * (1/r - 1)  # Update cumulative delay for the next segment
    if debug:
        print(f"Segment {i+1}/{N} - Optimal Ratio: {r:.2f}, Cumulative Delay: {d:.3f} sec\n")


# Calculate and print the true global error
global_error = pp.compute_global_average_error(sna_mat, run_mat, r_opt, segment, debug=debug)

pp_time = time.time()
print(f"~ PP time: {1000*(pp_time-start):.3f} msec ~")


# TSM HERE!!! #

end = time.time()
print(f"~ TSM time: {1000*(end-pp_time):.3f} msec ~\n")



print(f"~~ Average Segment Latency: {1000*(end-start)/N:.3f} msec ~~\n")
print(f"~~ Elapsed Time: {1000*(end-start):.3f} msec ~~")
print("~~ END OF PROGRAM ~~\n")



""" THE CODE JUNKYARD:

# Time-Scale Modification (TSM) #

y_output = np.array([])

for i in range(N):
    start_idx = librosa.time_to_samples(i*segment, sr=sna_sr)
    end_idx = librosa.time_to_samples((i+1)*segment, sr=sna_sr)
    y = sna[start_idx:end_idx]
    D       = librosa.stft(y, n_fft=2048, hop_length=512)
    D_fast  = librosa.phase_vocoder(D, rate=r_opt[i], hop_length=512)
    y_fast  = librosa.istft(D_fast, hop_length=512)
    y_output = np.concatenate((y_output, y_fast))

sf.write('sna_output.wav', gain*y_output, sna_sr)

d = 0
r_opt = np.ones(N)
for i in range(N):
    r = phase_pp_2(sna_mat[:,i] + d, run_mat[:,i], debug=debug)
    r_opt[i] = r
    d = d + segment * (1/r - 1)  # Update cumulative delay for the next segment
    print(f"Segment {i+1}/{N} - Optimal Ratio: {r:.2f}, Cumulative Delay: {d:.3f} sec\n")
    print("================================\n")

 """
