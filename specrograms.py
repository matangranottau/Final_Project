import numpy as np
import matplotlib.pyplot as plt
import librosa
import time
import os
from tsm import compute_stft_custom, create_hpss_masks, apply_masks

def process_and_plot(song_path, save_dir):
    print("-> Loading audio (first 60 seconds)...")
    x, sr = librosa.load(song_path, sr=None, duration=60) 
    
    print("-> Computing STFT...")
    f, t, Zxx = compute_stft_custom(x, sr)
    
    print("-> Calculating Harmonic & Percussive masks...")
    harm_mask, perc_mask, residual_mask = create_hpss_masks(Zxx)
    
    print("-> Applying masks...")
    Zxx_harm, Zxx_perc, _ = apply_masks(Zxx, harm_mask, perc_mask, residual_mask)
    
    # --- UPDATED dB CONVERSION ---
    # We normalize to the absolute maximum value of the original STFT 
    # so that the loudest point is exactly 0 dB, matching your screenshot.
    ref_max = np.max(np.abs(Zxx))
    def to_db(Z):
        return 20 * np.log10(np.abs(Z) / ref_max + 1e-10)
        
    mag_db = to_db(Zxx)
    harm_db = to_db(Zxx_harm)
    perc_db = to_db(Zxx_perc)
    
    print("-> Rendering plots...")
    plt.figure(figsize=(12, 10))
    
    # --- UPDATED PLOT STYLING ---
    # cmap='viridis' matches your image's colors
    # vmin=-80, vmax=0 locks the color range to match your colorbars exactly
    cmap_style = 'viridis'
    vmin, vmax = -80, 0 
    
    # Plot 1: Original
    plt.subplot(3, 1, 1)
    plt.pcolormesh(t, f, mag_db, cmap=cmap_style, vmin=vmin, vmax=vmax)
    plt.title('Original Spectrogram')
    plt.ylabel('Frequency [Hz]')
    plt.colorbar(format='%+2.0f dB', label='Magnitude [dB]')
    
    # Plot 2: Harmonic
    plt.subplot(3, 1, 2)
    plt.pcolormesh(t, f, harm_db, cmap=cmap_style, vmin=vmin, vmax=vmax)
    plt.title('Harmonic Component')
    plt.ylabel('Frequency [Hz]')
    plt.colorbar(format='%+2.0f dB', label='Magnitude [dB]')
    
    # Plot 3: Percussive
    plt.subplot(3, 1, 3)
    plt.pcolormesh(t, f, perc_db, cmap=cmap_style, vmin=vmin, vmax=vmax)
    plt.title('Percussive Component')
    plt.xlabel('Time [sec]')
    plt.ylabel('Frequency [Hz]')
    plt.colorbar(format='%+2.0f dB', label='Magnitude [dB]')
    
    plt.tight_layout()

    # Save logic
    os.makedirs(save_dir, exist_ok=True)
    song_filename = os.path.basename(song_path).replace(".mp3", "")
    save_path = os.path.join(save_dir, f"{song_filename}_Spectrograms.png")
    
    print(f"-> Saving image to: {save_path}")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close() 
    print("-> Finished successfully!")

if __name__ == "__main__":
    song_path = r"Songs\Seven Nation Army.mp3"
    save_directory = r"Plots\TSM\Graphs" 
    
    process_and_plot(song_path, save_directory)