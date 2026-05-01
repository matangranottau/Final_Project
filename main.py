## Imports ##
import os
import numpy as np
import matplotlib.pyplot as plt
import librosa
import time
import soundfile as sf
import pp
from tsm import custom_phase_vocoder, librosa_phase_vocoder_compare, compute_stft_custom, create_hpss_masks, apply_masks, reconstruct_signal_custom, custom_wsola, librosa_time_stretch_compare

def save_audio(file_path, x, sr):
    max_val = np.max(np.abs(x))
    if max_val > 0:
        x = x / (max_val + 1e-10)
    sf.write(file_path, x, sr)

def add_clicks(signal, beats, sr, magnitude=10, click_ms = 2, click_decay = 4):
    # Convert beat times (in seconds) to sample indices
    click_samples = np.round(beats * sr).astype(int)
    click_samples = click_samples[(click_samples >= 0) & (click_samples < len(signal))]
        
    # Create click envelope (exponential decay)
    click_duration_samples = int(click_ms * sr / 1000)
    click_envelope = np.exp(-np.arange(click_duration_samples) / (click_decay * sr / 1000))
    click_waveform = magnitude * click_envelope
        
    # Add clicks to signal
    signal_with_clicks = signal.copy()
    for click_sample in click_samples:
        end_sample = min(click_sample + click_duration_samples, len(signal_with_clicks))
        click_len = end_sample - click_sample
        signal_with_clicks[click_sample:end_sample] += click_waveform[:click_len]
        
    return signal_with_clicks

def process_music(song_path, spm_array):
    #===================================
    ########## PP - Parameters ##########
    #===================================
    debug = True
    preload_audio = True
    path = song_path
    segment = 2.5  # Segment Duration in seconds
    spm = spm_array
    std_dev = 0.05


    #===================================
    ########## Code Execution ##########
    #===================================
    start = time.time()

    #===================================
    ########## Pre-Processing ##########
    #===================================

    if preload_audio:
        if (not os.path.exists('sna.npy') or not os.path.exists('sna_sr.npy') or not os.path.exists('sna_BPM.npy') or not os.path.exists('sna_beats.npy')):
            print("Preprocessing audio and saving to .npy files...")
            sna, sna_sr = pp.load_audio(path, debug=debug)
            sna_BPM, sna_beats = pp.beat_tracking(sna, sna_sr, debug=debug)
            np.save('sna.npy', sna)
            np.save('sna_sr.npy', sna_sr)
            np.save('sna_BPM.npy', sna_BPM)
            np.save('sna_beats.npy', sna_beats)

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

    #===================================
    ########## TSM ##########
    #===================================

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Calculate exactly how many chunks the song contains
    total_song_duration = len(sna) / sna_sr
    total_chunks = int(total_song_duration // segment)

    print(f"Song is {total_song_duration:.1f} seconds long.")
    print(f"Dividing into {total_chunks} chunks of {segment}s each.")

    # strech_rates
    stretch_rates = r_opt

    # engine set up
    chunk_samples = int(segment * sna_sr)
    pad_samples = int(0.5 * sna_sr)    
    # --- STFT PARAMETERS ---
    nperseg = 2048
    noverlap = 1536
    hop_length = nperseg - noverlap 

    # --- INITIALIZE MEMORY STATES ---
    pv_phase_harm = None
    pv_phase_res = None

    wsola_win_size = 2048
    wsola_syn_hop = 512
    wsola_overlap = wsola_win_size - wsola_syn_hop

    wsola_input_buf = np.array([])
    wsola_output_tail = np.zeros(wsola_overlap)

    final_output = []

    print("Starting dynamic chunk processing for runner...")

    # Loop through the audio in 2.5s blocks
    for chunk_index, start_idx in enumerate(range(0, len(sna), chunk_samples)):
        # The last chunk might be shorter
        current_chunk_samples = min(chunk_samples, len(sna) - start_idx)
        if current_chunk_samples < hop_length: # Not enough audio to create a single frame
            break
        end_idx = start_idx + current_chunk_samples
        
        # Pull the stretch rate from the array. 
        # If the song has more chunks than our array, we just keep using the last rate in the array.
        safe_index = min(chunk_index, len(stretch_rates) - 1)
        current_stretch_rate = stretch_rates[safe_index]

        print(f"Chunk {chunk_index}: {start_idx/sna_sr:.1f}s to {end_idx/sna_sr:.1f}s | Speed: {current_stretch_rate:.2f}x")
        
        # 1. EXTRACT PADDED CHUNK
        pad_start = max(0, start_idx - pad_samples)
        pad_end = min(len(sna), end_idx + pad_samples)
        x_chunk_padded = sna[pad_start:pad_end]
        actual_pad_start_samples = start_idx - pad_start
        actual_pad_end_samples = pad_end - end_idx
        
        # 2. HPSS
        _, _, Zxx = compute_stft_custom(x_chunk_padded, sna_sr, nperseg, noverlap)
        h_mask, p_mask, r_mask = create_hpss_masks(Zxx, margin=1.2)
        Z_harm, Z_perc, Z_res = apply_masks(Zxx, h_mask, p_mask, r_mask)
        
        # 3. TRIM PADDING
        frames_to_trim_start = int(actual_pad_start_samples / hop_length)
        frames_to_trim_end = int(actual_pad_end_samples / hop_length)
        end_frame = Zxx.shape[1] - frames_to_trim_end if frames_to_trim_end > 0 else Zxx.shape[1]
        
        Z_harm_trimmed = Z_harm[:, frames_to_trim_start:end_frame]
        Z_res_trimmed = Z_res[:, frames_to_trim_start:end_frame]
        
        # 4. PHASE VOCODER (Using the dynamic current_stretch_rate!)
        Z_harm_stretched, pv_phase_harm = custom_phase_vocoder(
            Z_harm_trimmed, current_stretch_rate, hop_length, prev_phase=pv_phase_harm
        )
        Z_res_stretched, pv_phase_res = custom_phase_vocoder(
            Z_res_trimmed, current_stretch_rate, hop_length, prev_phase=pv_phase_res
        )
        
        x_harm_stretched = reconstruct_signal_custom(Z_harm_stretched, sna_sr, nperseg, noverlap)
        x_res_stretched = reconstruct_signal_custom(Z_res_stretched, sna_sr, nperseg, noverlap)
        
        # 5. WSOLA ON PERCUSSIVE (Using the dynamic current_stretch_rate!)
        x_perc_padded = reconstruct_signal_custom(Z_perc, sna_sr, nperseg, noverlap)
        x_perc_trimmed = x_perc_padded[actual_pad_start_samples : actual_pad_start_samples + current_chunk_samples]
        
        x_perc_stretched, wsola_input_buf, wsola_output_tail = custom_wsola(
            x_perc_trimmed, current_stretch_rate, wsola_input_buf, wsola_output_tail,
            win_size=wsola_win_size, syn_hop=wsola_syn_hop, delta=512
        )
        
        # 6. MIX CHUNK
        min_len = min(len(x_harm_stretched), len(x_perc_stretched), len(x_res_stretched))
        x_chunk_final = x_harm_stretched[:min_len] + x_perc_stretched[:min_len] + x_res_stretched[:min_len]
        
        final_output.append(x_chunk_final)

    print("Stitching dynamic chunks together...")
    final_song = np.concatenate(final_output)

    #===================================
    ########## Output Saving ##########
    #===================================

    print("Saving Output...")
    save_audio(os.path.join(output_dir, "Dynamic_Runner_Song.wav"), final_song, sna_sr)
    print("Done! Go listen to the tempo ramp up and down.")

    final_song_clicked = add_clicks(final_song, run_steps, sna_sr)
    save_audio(os.path.join(output_dir, "Dynamic_Runner_Song_Clicked.wav"), final_song_clicked, sna_sr)

    #===================================
    ########## End of Simulation #######
    #===================================
    end = time.time()
    print(f"~ TSM time: {(end-pp_time):.3f} sec ~\n")
    print(f"~~ Average Segment Latency: {(end-start)/N:.3f} sec ~~\n")
    print(f"~~ Elapsed Time: {(end-start):.3f} sec ~~")
    print("~~ END OF PROGRAM ~~\n")


if __name__ == '__main__':
    process_music("Songs\Seven Nation Army.mp3", [10.0, 12.0, 14.0, 16.0, 18.0, 20.0])


