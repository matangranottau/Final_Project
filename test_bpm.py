import numpy as np
from oop import wave
from preprocessing import preprocssing
from cadence import make_cadence
import matplotlib.pyplot as plt
import traceback

# Synthetic Signal Generator 
def make_click_track(bpm, sr, duration_sec):
    """
    Creates a synthetic audio signal with precise BPM.
    Used to verify that the algorithm calculates 'r' correctly.
    """
    N = int(sr * duration_sec)
    x = np.zeros(N, dtype=np.float32)
    
    # Calculate samples per beat
    samples_per_beat = int((60.0 / bpm) * sr)
    
    # Create a "click" sound (decaying sine wave) so Librosa can detect it
    click_len = int(0.05 * sr) # 50ms
    if click_len > samples_per_beat: click_len = samples_per_beat // 2
    n = np.arange(click_len)
    # 1kHz tone with exponential decay
    kernel = np.sin(2 * np.pi * 1000 * n / sr) * np.exp(-n / (0.005 * sr))

    current_idx = 0
    while current_idx + click_len < N:
        x[current_idx : current_idx + click_len] += kernel
        current_idx += samples_per_beat

    # Normalize
    if np.max(np.abs(x)) > 0:
        x = x / np.max(np.abs(x))
        
    return x

def create_wave_object(signal, sr):
    """
    Wraps a numpy array in a 'wave' object 
    to satisfy the type check: if not (type(song) is wave).
    """
    # Path is dummy, dont load from it
    w = wave(path="__synthetic__", sr=sr)
    
    # Manually inject data to bypass w.load()
    w.signal = signal
    w.sr = sr
    w.sample_length = signal.size
    w.length = signal.size / sr
    w.r_list = [] # Ensure list is ready
    
    return w

def run_constant_bpm_test():
    print(" Test 1: Constant BPM Verification")
    sr = 22050
    duration = 60
    dt = 0.5
    
    target_song_bpm = 120
    target_run_bpm = 132 # Expected ratio r = 1.10
    
    print(f"Generating Song: {target_song_bpm} BPM")
    print(f"Generating Run : {target_run_bpm} BPM")

    # 1. Generate Signals
    song_sig = make_click_track(target_song_bpm, sr, duration)
    run_sig = make_click_track(target_run_bpm, sr, duration)

    # 2. Enforce Size Constraint 
    # Floating point math might cause 1 sample difference
    min_len = min(song_sig.size, run_sig.size)
    song_sig = song_sig[:min_len]
    run_sig = run_sig[:min_len]

    # 3. Create 'wave' objects 
    song_obj = create_wave_object(song_sig, sr)
    cadence_obj = create_wave_object(run_sig, sr)

    # 4. Run Preprocessing
    try:
        preprocssing(song_obj, cadence_obj, dt=dt)
        
        # 5. Analyze Results
        print(f"Librosa detected Song BPM: {song_obj.tempo:.2f}")
        print(f"Librosa detected Run BPM: {cadence_obj.tempo:.2f}")

        # Ignore first 5 seconds 
        start_index = int(5.0 / dt)
        r_values = song_obj.r_list[start_index:]
        avg_r = float(np.mean(r_values))
        target_r = target_run_bpm / target_song_bpm
        tol = 0.02  # Tolerance

        print(f"Calculated Average 'r': {avg_r:.4f}")
        print(f"Target 'r': {target_r:.4f}")

        # Many time Librosa locks to double or half tempo
        candidates = [
            ("avg_r", avg_r),
            ("avg_r*2", avg_r * 2.0),
            ("avg_r/2", avg_r / 2.0),
        ]

        best_name, best_val, best_err = None, None, None
        for name, val in candidates:
            err = abs(val - target_r)
            if best_err is None or err < best_err:
                best_name, best_val, best_err = name, val, err

        if best_err <= tol:
            print(f"PASS: best match is {best_name} = {best_val:.4f} (error {best_err:.4f})")
        else:
            print(f"FAIL: best match is {best_name} = {best_val:.4f} (error {best_err:.4f})")
            print("      (librosa might be locking to a wrong tempo, or r_list hasn't converged yet)")

            
    except Exception as e:
        print(f"CRASH: {e}")
        traceback.print_exc()

def run_cadence_class_integration():
    print("\nTest 2: Integration with cadence.py factory")
    sr = 22050
    duration = 60
    
    # 1. Create a steady song (150 BPM) FIRST
    # We do this first so we can pass it to make_cadence to match length/sr
    song_signal = make_click_track(150, sr, duration)
    song_obj = create_wave_object(song_signal, sr)

    # 2. Use make_cadence to generate the Runner's signal
    # make_cadence now returns a READY-TO-USE wave object. 
    # No need to manually convolve or wrap it again!
    cadence_obj = make_cadence(
        song=song_obj,
        pattern="slow_smooth_change",
        output="energy" # This ensures the signal is continuous (audible), not just empty impulses
    )

    # 3. Run Processing
    try:
        preprocssing(song_obj, cadence_obj, dt=0.5)
        print("Integration successful: preprocessing ran without errors.")
        
        # Verify it actually detected something
        print(f"Song Tempo: {song_obj.tempo}")
        print(f"Cadence Global Tempo: {cadence_obj.tempo}")
        
        print(f"Resulting r_list length: {len(song_obj.r_list)}")
        if len(song_obj.r_list) > 0:
            print(f"First 5 r values: {song_obj.r_list[:5]}")
            print(f"Last 5 r values: {song_obj.r_list[-5:]}")
        
    except Exception as e:
        print(f"Integration Failed: {e}")
        traceback.print_exc()

        
if __name__ == "__main__":
    run_constant_bpm_test()
    run_cadence_class_integration()