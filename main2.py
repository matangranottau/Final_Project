import os
import numpy as np
import soundfile as sf
import librosa
from tsm import custom_phase_vocoder, librosa_phase_vocoder_compare, compute_stft_custom, create_hpss_masks, apply_masks, reconstruct_signal_custom, custom_wsola, librosa_time_stretch_compare


def save_audio(file_path, x, sr):
    max_val = np.max(np.abs(x))
    if max_val > 0:
        x = x / (max_val + 1e-10)
    sf.write(file_path, x, sr)

def main():
    input_path = r"C:\Users\yogev\source\Final project\Stft part\Seven Nation Army.mp3"
    output_dir = r"C:\Users\yogev\source\Final project\Stft part"
    os.makedirs(output_dir, exist_ok=True)
    
    sr = 44100
    chunk_duration = 2.5 # Process 2.5 seconds at a time
    
    # Load the song 
    print("Loading full song into memory (sorry butthis may take a moment)...")
    x_full, _ = librosa.load(input_path, sr=sr, mono=True)
    
    # Calculate exactly how many chunks the song contains
    total_song_duration = len(x_full) / sr
    total_chunks = int(total_song_duration // chunk_duration)
    
    print(f"Song is {total_song_duration:.1f} seconds long.")
    print(f"Dividing into {total_chunks} chunks of {chunk_duration}s each.")

    # Dummy strech_rates
    stretch_rates = np.linspace(1.0, 1.3, total_chunks)

    # engine set up
    chunk_samples = int(chunk_duration * sr)
    pad_samples = int(0.5 * sr)    
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
    for chunk_index, start_idx in enumerate(range(0, len(x_full), chunk_samples)):
        # The last chunk might be shorter
        current_chunk_samples = min(chunk_samples, len(x_full) - start_idx)
        if current_chunk_samples < hop_length: # Not enough audio to create a single frame
            break
        end_idx = start_idx + current_chunk_samples
        
        # Pull the stretch rate from the array. 
        # If the song has more chunks than our array, we just keep using the last rate in the array.
        safe_index = min(chunk_index, len(stretch_rates) - 1)
        current_stretch_rate = stretch_rates[safe_index]

        print(f"Chunk {chunk_index}: {start_idx/sr:.1f}s to {end_idx/sr:.1f}s | Speed: {current_stretch_rate:.2f}x")
        
        # 1. EXTRACT PADDED CHUNK
        pad_start = max(0, start_idx - pad_samples)
        pad_end = min(len(x_full), end_idx + pad_samples)
        x_chunk_padded = x_full[pad_start:pad_end]
        actual_pad_start_samples = start_idx - pad_start
        actual_pad_end_samples = pad_end - end_idx
        
        # 2. HPSS
        _, _, Zxx = compute_stft_custom(x_chunk_padded, sr, nperseg, noverlap)
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
        
        x_harm_stretched = reconstruct_signal_custom(Z_harm_stretched, sr, nperseg, noverlap)
        x_res_stretched = reconstruct_signal_custom(Z_res_stretched, sr, nperseg, noverlap)
        
        # 5. WSOLA ON PERCUSSIVE (Using the dynamic current_stretch_rate!)
        x_perc_padded = reconstruct_signal_custom(Z_perc, sr, nperseg, noverlap)
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
    
    print("Saving Output...")
    save_audio(os.path.join(output_dir, "Dynamic_Runner_Song.wav"), final_song, sr)
    print("Done! Go listen to the tempo ramp up and down.")

if __name__ == "__main__":
    main()