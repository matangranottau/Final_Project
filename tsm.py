import numpy as np
from scipy.signal import correlate
import librosa
from scipy.signal import stft, istft
from scipy.ndimage import median_filter


def compute_stft_custom(x, sr, nperseg=2048, noverlap=1536):
    f, t, Zxx = stft(x, fs=sr, window="hann", nperseg=nperseg, noverlap=noverlap)
    return f, t, Zxx

def create_hpss_masks(Zxx, harm_kernel=31, perc_kernel=31, margin=1.2, power=2.0):
    mag = np.abs(Zxx)
    eps = 1e-10

    harm_smooth = median_filter(mag, size=(1, harm_kernel))
    perc_smooth = median_filter(mag, size=(perc_kernel, 1))

    harm_mask = (harm_smooth ** power) / ((harm_smooth ** power) + ((margin * perc_smooth) ** power) + eps)
    perc_mask = (perc_smooth ** power) / ((perc_smooth ** power) + ((margin * harm_smooth) ** power) + eps)
    
    residual_mask = np.clip(1.0 - (harm_mask + perc_mask), 0.0, 1.0) 
    return harm_mask, perc_mask, residual_mask

def apply_masks(Zxx, harm_mask, perc_mask, residual_mask):
    return Zxx * harm_mask, Zxx * perc_mask, Zxx * residual_mask

def reconstruct_signal_custom(Zxx, sr, nperseg=2048, noverlap=1536):
    _, x_rec = istft(Zxx, fs=sr, window="hann", nperseg=nperseg, noverlap=noverlap)
    return x_rec

def custom_phase_vocoder(Zxx, rate, hop_length, prev_phase=None):
    """
    Functional Phase Vocoder. 
    Takes the phase from the previous chunk, and returns the new phase for the next chunk.
    """
    n_fft = (Zxx.shape[0] - 1) * 2
    time_steps = np.arange(0, Zxx.shape[1], rate)
    n_out = len(time_steps)
    Zxx_out = np.zeros((Zxx.shape[0], n_out), dtype=np.complex128)
    
    k = np.arange(Zxx.shape[0])
    phi_advance = 2 * np.pi * k * hop_length / n_fft
    
    # Use the memory passed in, or start fresh
    if prev_phase is None:
        current_phase = np.angle(Zxx[:, 0])
    else:
        current_phase = prev_phase
        
    for i in range(n_out):
        t = time_steps[i]
        col0 = int(np.floor(t))
        col1 = min(col0 + 1, Zxx.shape[1] - 1)
        alpha = t - col0
        
        mag = (1 - alpha) * np.abs(Zxx[:, col0]) + alpha * np.abs(Zxx[:, col1])
        dp = np.angle(Zxx[:, col1]) - np.angle(Zxx[:, col0]) - phi_advance
        dp = dp - 2 * np.pi * np.round(dp / (2 * np.pi))
        
        # Accumulate phase
        current_phase = current_phase + phi_advance + dp
        Zxx_out[:, i] = mag * np.exp(1j * current_phase)
        
    # Spit out the audio AND the memory for the next round!
    return Zxx_out, current_phase

def librosa_phase_vocoder_compare(Zxx, rate, hop_length):


    return librosa.phase_vocoder(Zxx, rate=rate, hop_length=hop_length)

def custom_wsola(x, rate, prev_input_buffer, prev_output_tail, win_size=2048, syn_hop=512, delta=512):
    """
    Functional WSOLA.
    Takes overlap buffers from the previous chunk and returns updated ones for the next chunk.
    """
    ana_hop = int(syn_hop * rate)
    overlap = win_size - syn_hop
    w = np.hanning(win_size)
    
    # Combine leftover audio from the previous chunk with the new incoming audio
    x_padded = np.concatenate((prev_input_buffer, x))
    
    out_len = int(len(x_padded) / rate)
    y = np.zeros(out_len + win_size)
    
    # Initialize the first frame using the tail from the previous chunk
    y[:overlap] = prev_output_tail
    
    syn_p = 0
    ana_p = delta
    
    while ana_p + win_size + delta < len(x_padded) and syn_p + win_size < len(y):
        template = y[syn_p : syn_p + overlap]
        search_region = x_padded[ana_p - delta : ana_p + delta + overlap]
        
        corr = correlate(search_region, template, mode='valid')
        best_shift = np.argmax(corr) - delta
        
        y[syn_p : syn_p + win_size] += x_padded[ana_p + best_shift : ana_p + best_shift + win_size] * w
        
        syn_p += syn_hop
        ana_p += ana_hop
        
    # Calculate the new memory buffers for the next round
    new_output_tail = y[syn_p : syn_p + overlap]
    new_input_buffer = x_padded[ana_p - delta :]
    
    # Spit out the audio AND the memory!
    return y[:syn_p], new_input_buffer, new_output_tail

def librosa_time_stretch_compare(x, rate):
    return librosa.effects.time_stretch(x, rate=rate)