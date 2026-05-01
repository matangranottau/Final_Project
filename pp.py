## Imports ##
import numpy as np
import matplotlib.pyplot as plt
import librosa
import time
import soundfile as sf



## Functions ##
def cute_print(array):
    """Print the first 10 columns of an array."""
    if array.dtype == np.float64:
        if array.ndim == 1:
            print(f'{np.round(array[:10], 2)}\n')
        if array.ndim == 2:
            print(f'{np.round(array[:,:10],2)}\n')
        if array.ndim == 3:
            print(f'{np.round(array[:,0,:],2)}\n')
    else:
        if array.ndim == 1:
            print(f'{array[:10]}\n')
        if array.ndim == 2:
            print(f'{array[:,:10]}\n')
        if array.ndim == 3:
            print(f'{array[:,0,:]}\n')
            
def spm_to_r_nom(spm,BPM):
    """Convert steps per minute to nominal ratio."""
    return spm/BPM

def load_audio(file_path, debug=False):
    """Load an audio file."""
    audio, audio_sr = librosa.load(file_path, sr=None)
    if debug:
        print(f"Loaded audio from {file_path}\n")
        print(f"Audio shape: {audio.shape}\n")
        print(f"Audio sample rate: {audio_sr}\n")
    return audio, audio_sr

def beat_tracking(audio, sr, debug=False):
    """Perform beat tracking on the audio signal."""
    tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
    tempo = tempo[0]
    beats = librosa.frames_to_time(beats, sr=sr)
    if debug:
        print(f"Tempo: {tempo}\n")
        print(f"Beats (First 20):\n{np.round(beats[:19],2)}\n")
    return tempo, beats

def create_run_steps(beats, BPM, r_nom, std_dev=0.04, debug=False):
    """Create run steps based on beats and a nominal ratio."""
    L = len(beats)
   # FIX 1: Over-repeat the array, then slice it to exactly length L
    repeats_per_element = int(np.ceil(L / len(r_nom)))
    r_nom_extended = np.repeat(r_nom, repeats_per_element)[:L]
    
    # FIX 2: Use true division (/) to preserve precise sub-second timestamps
    run_steps = beats / r_nom_extended
    dc = 60.0 / BPM / r_nom_extended  # Duration between steps

    e = np.random.normal(0, np.max(dc)*std_dev, size=L)  # Random variability
    for i in range(1, L):
        run_steps[i] = run_steps[i-1] + dc[i] + e[i]  # Add variability to steps
    run_SPM = 60 / dc  # Steps per minute
    if debug:
        print(f" L - Number of beats = {L}")

        print("r_nom:")
        cute_print(r_nom)

        print("dc (Duration of each step):")
        cute_print(dc)

        print(f"Run SPM:")
        cute_print(run_SPM)
        
        print(f"Run Steps:")
        cute_print(run_steps)

    return run_SPM, run_steps

def trim_dim(vect, events_per_minute, segment, debug=False):
    """Get dimensions for trimming a vector into segments."""
    M = int(events_per_minute / 60 * segment)
    N = int(len(vect) / M)
    vect = vect[:M * N]  # Trim to fit segments
    if debug:
        print(f"Matrix dim: {M} x {N}\n")
    return M,N

def reshape_vector(vect, M, N, debug=False, debug_name="Generic Vector"):
    """Reshape a vector into a matrix of dimensions M x N."""
    vect = vect[:M * N]  # Ensure the vector is trimmed to fit the new shape
    reshaped_vect = np.reshape(vect, (M, N), order ='F')  # Reshape in column-major order
    
    if debug:
        print(f"Reshaped vector - {debug_name}:")
        cute_print(reshaped_vect)
    return reshaped_vect

def phase_pp(sna_mat, run_mat, debug=False):
    """Calculate the optimal ratio for each segment."""
    V = sna_mat / run_mat
    W = run_mat
 
    deep_stack = np.stack((V,W),axis=2)
        
    idx = np.argsort(deep_stack[:,:,0], axis=0)
    deep_stack_sorted = np.take_along_axis(deep_stack, idx[:,:,None], axis=0)

    half_points = np.sum(W, axis=0) / 2
    
    deep_stack_cumsum = np.cumsum(deep_stack_sorted[:,:,1], axis=0)
    
    deep_stack_cumsum_mask = (deep_stack_cumsum >= half_points)
    
    diff_mask = np.diff(deep_stack_cumsum_mask.astype(int), axis=0, prepend=0)

    idx_opt = np.argmax(diff_mask, axis=0)
    
    r_opt = deep_stack_sorted[idx_opt, np.arange(N), 0]

    if debug:
        print("V:")
        cute_print(V)

        print("W:")
        cute_print(W)

        print("V,W stack (First column):")
        cute_print(deep_stack)

        print("Sorted V,W stack (First column):")
        cute_print(deep_stack_sorted)

        print("Half point of W:")
        cute_print(half_points)

        print("Cumulative sum of W:")
        cute_print(deep_stack_cumsum)

        print("Cumsum mask:")
        cute_print(deep_stack_cumsum_mask)

        print("Diff mask:")
        cute_print(diff_mask)

        print("Optimal indices:")
        cute_print(idx_opt)

        print("Optimal ratios (r_opt):")
        cute_print(r_opt)

    return r_opt

def phase_pp_2(sna_vect, run_vect, debug=False):
    V = sna_vect / run_vect
    W = run_vect

    sorted_indices = np.argsort(V)
    V_sorted = V[sorted_indices]
    W_sorted = W[sorted_indices]

    half_point = np.sum(W) / 2
    cumulative_sum = np.cumsum(W_sorted)

    optimal_index = np.searchsorted(cumulative_sum, half_point)
    r_opt = V_sorted[optimal_index]

    if debug:
        print("Music Beats (Before Speed-Up):")
        cute_print(sna_vect)

        print("Music Beats (After Speed-Up):")
        cute_print(sna_vect/r_opt)

        print("Run Beats:")
        cute_print(run_vect)

        print("V:")
        cute_print(V)

        print("Optimal ratio (r_opt):")
        print(np.round(r_opt, 1))

    return r_opt

def phase_pp_lsq_shifted(sna_abs, run_abs, t_start, d, debug=False):
    """
    Calculates optimal speed-up using Least Squares, correctly anchoring 
    the time-stretch to the start of the segment and accounting for delay.
    """
    # 1. Isolate the relative time of the music beats within this segment
    B_rel = sna_abs - t_start
    
    # 2. Adjust the target run steps by removing the start time and accumulated delay
    # We are solving for r in: (B_rel / r) = run_abs - t_start - d
    Y = run_abs - t_start - d
    
    # 3. Least Squares optimal ratio
    sum_sq_B = np.sum(B_rel ** 2)
    sum_prod = np.sum(B_rel * Y)
    
    r_opt = sum_sq_B / sum_prod

    if debug:
        # Calculate actual absolute stretched times for debugging
        stretched_abs_beats = (B_rel / r_opt) + t_start + d
        
        print("Music Beats (Before Speed-Up):")
        cute_print(sna_abs)

        print("Music Beats (After Speed-Up):")
        cute_print(stretched_abs_beats)

        print("Run Steps:")
        cute_print(run_abs)

        print(f"Optimal ratio (r_opt) for this segment: {r_opt:.4f}")
        
        error = np.mean(np.abs(stretched_abs_beats - run_abs))
        print(f"Mean Absolute Error for this segment: {error * 1000:.2f} ms\n")
        print("-" * 30)

    return r_opt

def phase_pp_l1_shifted(sna_abs, run_abs, t_start, d, debug=False):
    """
    Calculates optimal speed-up using L1 (Least Absolute Deviations) via 
    Weighted Median, correctly anchoring time-stretch to the segment start.
    Robust against outlier beats or run steps.
    """
    # 1. Relative time and adjusted target steps
    B_rel = sna_abs - t_start
    Y = run_abs - t_start - d
    
    # 2. Calculate individual stretch factors (x = 1/r) and set weights
    x_vals = Y / B_rel
    weights = B_rel
    
    # 3. Sort by x_vals to prepare for weighted median
    sorted_indices = np.argsort(x_vals)
    x_sorted = x_vals[sorted_indices]
    weights_sorted = weights[sorted_indices]
    
    # 4. Find the weighted median (this minimizes L1 error)
    half_weight = np.sum(weights) / 2.0
    cumulative_weight = np.cumsum(weights_sorted)
    optimal_index = np.searchsorted(cumulative_weight, half_weight)

    if optimal_index >= len(x_sorted):
        optimal_index = len(x_sorted) - 1  # Handle edge case where searchsorted returns out of bounds
    
    x_opt = x_sorted[optimal_index]
    r_opt = 1.0 / x_opt  # Convert back to speed-up ratio r

    if debug:
        stretched_abs_beats = (B_rel / r_opt) + t_start + d
        
        print("Music Beats (Before Speed-Up):")
        cute_print(sna_abs)

        print("Music Beats (After Speed-Up):")
        cute_print(stretched_abs_beats)

        print("Run Steps:")
        cute_print(run_abs)

        print(f"Optimal ratio (r_opt) for this segment: {r_opt:.4f}")
        
        error = np.mean(np.abs(stretched_abs_beats - run_abs))
        print(f"Mean Absolute Error for this segment: {error * 1000:.2f} ms\n")
        print("-" * 30)

    return r_opt

def compute_global_average_error(sna_mat, run_mat, r_opt_array, segment_duration, debug=False):
    """
    Computes the global average absolute error across all segments.
    Properly reconstructs the cumulative delay and relative time stretches.
    """
    M, N = sna_mat.shape
    total_error_sum = 0.0
    d = 0.0
    
    for i in range(N):
        t_start = i * segment_duration
        
        # 1. Isolate relative time
        B_rel = sna_mat[:, i] - t_start
        
        # 2. Reconstruct the stretched absolute beats for this segment
        stretched_beats = (B_rel / r_opt_array[i]) + t_start + d
        
        # 3. Sum the absolute errors for this segment
        total_error_sum += np.sum(np.abs(stretched_beats - run_mat[:, i]))
        
        # 4. Update cumulative delay for the next segment
        d = d + segment_duration * (1 / r_opt_array[i] - 1)
        
    # Calculate the mean across all M * N elements
    global_mae = total_error_sum / (M * N)
    
    if debug:
        print("================================")
        print(f"~~ True Global Average Error: {global_mae * 1000:.3f} ms ~~")
        print("================================\n")
        
    return global_mae

