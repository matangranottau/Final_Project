import numpy as np
from oop import wave
from helper_functions import clip
from librosa import time_to_samples, samples_to_time
from librosa.beat import beat_track

def BPM_preprocssing(song, cadence, dt=0.5, W=5, alpha = 0.2, beta = 0.4, k= 0.05, dr = 0.02, phase_mode=True): #OFFLINE ONLY!!
    # Assumption 1: both song cadence is from wave class and not cadence class
    # Assumption 2: cadence is offline
    # Assumption 3: audio and cadence are with exact same length (in samples)
    # Assumption 4: audio and cadence has same sr 22050
    
  
    if not (type(cadence) is wave):
        raise ValueError("Cadence is not wave type")
    
    if not (type(song) is wave):
        raise ValueError("Song is not wave type")
    
    if (cadence.sr != song.sr):
        raise ValueError("Not Same sr")
    
    if (cadence.signal.size != song.signal.size):
        raise ValueError("Not Same Size")
    
    if song.mode != 1:
        raise ValueError("Song mode not correct")
    
    if cadence.mode != 2:
        raise ValueError("Cadence mode not correct")
    
    sr = cadence.sr # Sampling rate
    N = cadence.signal.size # N = Number of samples in both signals

    r_min = 0.8 # Project limit
    r_max = 1.5 # Project limit

    

    song.extract() # This gets BPM of the audio.
    # Only calculate global tempo if not already present
    if cadence.tempo is None:
        cadence.extract() # This gets global SPM of the cadence.
    
    t = np.arange(0, cadence.length, dt) # Time axis (dt jumps)

    r = 1 #init r 

    # Ensure variables are initialized before use
    spm = float(cadence.tempo) if cadence.tempo is not None else 120.0
    bpm = float(song.tempo) if song.tempo is not None else 120.0
    
    for n in range(t.size): # I do here a loop because t.size is not that big (~350 iterations)
        current_time = t[n]
        
        if (current_time < W): # Init - use global SPM
            spm = float(cadence.tempo) if cadence.tempo is not None else 0.0
            bpm = float(song.tempo) if song.tempo is not None else 0.0
            r = spm / bpm if (bpm != 0 and spm != 0) else 1.0
            
        else:
            start_idx = clip(time_to_samples(current_time - W, sr=sr), 0, N) 
            stop_idx = clip(time_to_samples(current_time, sr=sr), 0, N) 

            #NO need? start_idx = clip(start_idx, 0, N)

            cadence_signal_chunk = (cadence.signal)[start_idx:stop_idx] # Get the chunk from the cadence signal
            prior_guess = spm if spm > 0 else 120.0 # This prevents Librosa from jumping to 80 BPM when we are at 160 BPM.

            spm_tilde, _  = beat_track(y=cadence_signal_chunk, sr=sr, hop_length=cadence.hop_length, start_bpm=prior_guess)
            spm_tilde = float(spm_tilde)
            # Check double time - Helper function
            spm = alpha * spm_tilde + (1 - alpha) * spm
        
            if phase_mode:
                r_tilde = (spm / bpm) + k * phase_shift(song, cadence, r, current_time - W, current_time)
            else:
                r_tilde = spm / bpm
            
            r_tilde = clip(r_tilde, r_min, r_max)

            r_prev = r
            r = beta * r_tilde + (1 - beta) * r_prev
            r = clip(r, r_prev-dr, r_prev + dr)

        (cadence.spm_list).append(spm)
        (song.r_list).append(r)


def phase_shift(song, cadence, r, start_time, end_time, debug=False):
    # Assuming song and cadence beats are with the same "frequnecy" (after r adjustment)
    
    if song.beats is None:
        song.extract()

    if cadence.beats is None:
        cadence.extract()

    if debug:
        print(f"Original song beats (first 10): {song.beats[:10]}")
        print(f"Cadence beats (first 10): {cadence.beats[:10]}")

    b = (song.beats/r)

    if debug:
        print(f"Adjusted song beats (first 10): {b[:10]}")
        print(f"Cadence beats (first 10): {cadence.beats[:10]}")

    b = b[(b >= start_time) & (b <= end_time)]

    s = cadence.beats
    s = s[(s >= start_time) & (s <= end_time)]

    if debug:
        print(f"Adjusted song beats in range (first 10): {b[:10]}")
        print(f"Cadence beats in range (first 10): {s[:10]}")

    if b.size == 0 or s.size == 0:
        raise ValueError("No beats in the specified time range for phase shift calculation.")
    
    N = min(b.size, s.size)
    phase_diffs = b[:N] - s[:N]

    if debug:
        print(f"Phase differences (first 10): {phase_diffs[:10]}")
        
    return np.median(phase_diffs) # Postive phase -> song slower than cadence -> bigger r needed
    