import numpy as np
from oop import wave


def spm_slow_smooth_change(t, spm_start=140, spm_end=180, **kwargs):
    # 1) Slow and steady change
    if t.size == 0:
        return np.array([], dtype=float)
    return spm_start + (spm_end - spm_start) * (t / t[-1])


def spm_fast_jump(t, t_jump=20.0, spm_before=140, spm_after=180, **kwargs):
    # 2) Sudden change at t_jump
    return np.where(t < t_jump, spm_before, spm_after).astype(float)


def spm_interval_training(t, segment_length=12.0, spm_values=(150, 180, 130, 175, 160), **kwargs):
    # 3) Interval training
    spm = np.zeros_like(t, dtype=float)
    n_segments = len(spm_values)

    for i, spm_val in enumerate(spm_values):
        t_start = i * segment_length
        t_end = (i + 1) * segment_length
        spm[(t >= t_start) & (t < t_end)] = float(spm_val)

    # If total time longer than segments, hold last SPM
    if (n_segments * segment_length) < t[-1]:
        spm[t >= n_segments * segment_length] = float(spm_values[-1])

    return spm


def spm_noisy_natural(t, base_spm=165, noise_std=3.0, drift_std=0.03, rng=None, **kwargs):
    # 4) Natural running with small noises
    if t.size < 2:
        return np.full_like(t, float(base_spm), dtype=float)

    if rng is None:
        rng = np.random.default_rng()

    dt = float(t[1] - t[0])
    n = len(t)

    drift = np.cumsum(rng.normal(scale=drift_std * np.sqrt(dt), size=n))
    noise = rng.normal(scale=noise_std, size=n)

    spm = base_spm + drift + noise
    return np.clip(spm, 140, 190).astype(float)


def spm_start_stop(t, t_run1=(10, 30), t_run2=(35, 60), spm_run1=155, spm_run2=175, **kwargs):
    # 5) Start/stop training
    spm = np.zeros_like(t, dtype=float)
    spm[(t >= t_run1[0]) & (t < t_run1[1])] = float(spm_run1)
    spm[(t >= t_run2[0]) & (t < t_run2[1])] = float(spm_run2)
    return spm


PATTERNS = {
    "slow_smooth_change": spm_slow_smooth_change,
    "fast_jump": spm_fast_jump,
    "interval_training": spm_interval_training,
    "noisy_natural": spm_noisy_natural,
    "start_stop": spm_start_stop,
}



def spm_curve_to_step_times(t_spm, spm_curve):
    """
    Converts an SPM(t) curve (defined on t_spm) into step event times (seconds).
    Uses a simple "next step time += 60/SPM(current_time)" loop.
    """
    if t_spm.size == 0:
        return np.array([], dtype=float)

    dt = float(t_spm[1] - t_spm[0]) if t_spm.size > 1 else 1e-3
    t_end = float(t_spm[-1])

    step_times = []
    current_time = 0.0

    while current_time <= t_end:
        idx = int(current_time / dt)
        if idx >= len(spm_curve):
            break

        local_spm = float(spm_curve[idx])

        if local_spm > 0.0:
            period = 60.0 / local_spm
            step_times.append(current_time)
            current_time += period
        else:
            # standing still: advance a bit and re-check
            current_time += 0.1

    return np.array(step_times, dtype=float)


def step_times_to_impulses(step_times, sr, n_samples):
    """
    Render step times (seconds) to an audio-rate impulse train (length n_samples).
    """
    x = np.zeros(int(n_samples), dtype=np.float32)
    if step_times.size == 0:
        return x

    idx = np.round(step_times * float(sr)).astype(int)
    idx = idx[(idx >= 0) & (idx < n_samples)]
    x[idx] = 1.0
    return x


def impulses_to_energy(impulses, sr, window_ms=80):
    """
    Smooth impulses into an 'energy envelope' so beat_track/onset_strength behave better.
    """
    win_len = int(np.round(window_ms * 1e-3 * float(sr)))
    win_len = max(1, win_len)
    window = np.ones(win_len, dtype=np.float32) / float(win_len)
    return np.convolve(impulses.astype(np.float32), window, mode="same").astype(np.float32)


def _wave_from_array(signal, sr, hop_length=512):
    """
    Create an oop.wave instance 
    """
    w = wave.__new__(wave)  # bypass __init__
    w.signal = np.asarray(signal, dtype=np.float32)
    w.sr = int(sr)
    w.length = w.signal.size / float(w.sr)

    # fields your code uses later
    w.hop_length = int(hop_length)
    w.tempo = None
    w.beats = None
    w.r_list = []
    w.spm_list = []
    return w

def make_cadence(song: wave,
                pattern="slow_smooth_change",
                cadence_dt=0.02,
                output="energy",
                window_ms=80,
                seed=None,
                noise_std=0.0,   # Gaussian noise amount
                drift_std=0.0,   # NEW: Random drift amount
                **pattern_kwargs):
    """
    Returns a cadence signal as an oop.wave instance, SAME sr and SAME length as the song,
    so it passes BPM_preprocssing checks. :contentReference[oaicite:2]{index=2}

    output: "energy" (recommended) or "impulses"
    """
    if not (type(song) is wave):
        raise ValueError("make_cadence: song must be type oop.wave")

    if pattern not in PATTERNS:
        raise ValueError(f"Unknown pattern '{pattern}'. Available: {list(PATTERNS.keys())}")

    sr = song.sr
    n_samples = song.signal.size
    duration_sec = n_samples / float(sr)

    # low-rate timeline for SPM curve
    n_spm = max(2, int(np.floor(duration_sec / float(cadence_dt))) + 1)
    t_spm = np.linspace(0.0, duration_sec, n_spm)

    dt = float(t_spm[1] - t_spm[0])

    rng = np.random.default_rng(seed)

    # build SPM(t)
    spm_curve = PATTERNS[pattern](t_spm, rng=rng, **pattern_kwargs)

    # Inject Global Noise / Drift (if requested)
    if noise_std > 0 or drift_std > 0:
        drift = 0.0
        if drift_std > 0:
            # Random walk 
            drift = np.cumsum(rng.normal(scale=drift_std * np.sqrt(dt), size=len(t_spm)))
        
        white_noise = 0.0
        if noise_std > 0:
            # White Gaussian noise
            white_noise = rng.normal(scale=noise_std, size=len(t_spm))

        spm_curve = spm_curve + drift + white_noise
        
        # Safety clip to prevent negative or impossible SPM
        spm_curve = np.clip(spm_curve, 30, 250)

    # step events -> audio-rate impulses -> (optional) energy
    step_times = spm_curve_to_step_times(t_spm, spm_curve)
    impulses = step_times_to_impulses(step_times, sr=sr, n_samples=n_samples)
    energy = impulses_to_energy(impulses, sr=sr, window_ms=window_ms)

    signal = energy if output == "energy" else impulses
    c = _wave_from_array(signal, sr=sr, hop_length=getattr(song, "hop_length", 512))

    # useful debug for plotting (instead of c.signals/c.time from the old class)
    c.debug = {
        "pattern": pattern,
        "t_spm": t_spm,
        "spm_curve": spm_curve,
        "step_times": step_times,
        "impulses": impulses,
        "energy": energy,
        "true_global_spm": (len(step_times) * 60.0 / duration_sec) if duration_sec > 0 else 0.0,
    }

    return c
