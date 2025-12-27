import numpy as np
from oop import wave
from helper_functions import clip
from librosa import time_to_samples, samples_to_time
from librosa.beat import beat_track

def BPM_preprocssing(song, cadence, dt=0.5, W=5, alpha = 0.2, beta = 0.4, dr = 0.02): #OFFLINE ONLY!!
    # Assumption 1: both song cadence is from wave class and not cadence class
    # Assumption 2: cadence is offline
    # Assumption 3: audio and cadence are with exact same length (in samples)
    # Assumption 4: audio and cadence has same sr
    
  
    if not (type(cadence) is wave):
        raise ValueError("Cadence is not wave type")
    
    if not (type(song) is wave):
        raise ValueError("Song is not wave type")
    
    if (cadence.sr != song.sr):
        raise ValueError("Not Same sr")
    
    if (cadence.signal.size != song.signal.size):
        raise ValueError("Not Same Size")
    
    sr = cadence.sr # Sampling rate
    N = cadence.signal.size # N = Number of samples in both signals

    r_min = 0.8 # Project limit
    r_max = 1.5 # Project limit

    

    song.extract() # This gets BPM of the audio.
    cadence.extract() # This get GLOBAL SPM of cadence.
    
    t = np.arange(0, cadence.length, dt) # Time axis (dt jumps)

    r = 1 #init r 
    
    for n in range(t.size): # I do here a loop because t.size is not that big (~350 iterations)
        current_time = t[n]
        
        if (current_time < W): # Init - use global SPM
            SPM = cadence.BPM
            r = SPM / song.BPM
            
        else:
            start_idx = clip(time_to_samples(current_time - W, sr), 0, N) 
            stop_idx = clip(time_to_samples(current_time, sr), 0, N) 

            start_idx = clip(start_idx)

            cadence_signal_chunk = (cadence.signal)[start_idx:stop_idx] # Get the chunk from the cadence signal
            SPM_tilde, _  = beat_track(y=cadence_signal_chunk, sr=sr, hop_length=cadence.hop_length)
            # Check double time - Helper function
            SPM = alpha * SPM_tilde + (1 - alpha) * SPM
        
            r_tilde = SPM / song.BPM
            r_tilde = clip(r_tilde, r_min, r_max)

            r_prev = r
            r = beta * r_tilde + (1 - beta) * r_prev
            r = clip(r, r_prev-dr, r_prev + dr)

        (song.r_list).append(r)


            
    

    


    
    