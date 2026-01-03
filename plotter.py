import matplotlib.pyplot as plt
import librosa
import numpy as np
from oop import wave
#from cadence import cadence


def plot_audio_onsets_beats(a: wave, start: float = None, end: float = None, figsize=(12, 6), save_path: str = None):
	"""Plot an audio instance's waveform, onset envelope and beat markers in time.

	Parameters
	- a: `audio` instance (must have `signal`, `sr`, `hop_length`, and `beats` filled).
	- start, end: optional start/end times in seconds to zoom the plot.
	- figsize: figure size tuple.
	- save_path: optional path to save the figure (PNG, etc.). If None, the figure is shown.

	Returns the matplotlib `fig, axes` tuple.
	"""
	if a.signal is None or a.sr is None:
		raise ValueError("Audio instance has no loaded signal or sampling rate.")

	# Compute onset envelope (frames -> times)
	onset_env = librosa.onset.onset_strength(y=a.signal, sr=a.sr, hop_length=a.hop_length)
	onset_times = librosa.frames_to_time(np.arange(len(onset_env)), sr=a.sr, hop_length=a.hop_length)

	# Waveform times
	wave_times = np.arange(len(a.signal)) / float(a.sr)

	# Optionally crop by start/end
	if start is not None or end is not None:
		s = 0 if start is None else float(start)
		e = wave_times[-1] if end is None else float(end)
		# Mask waveform
		wave_mask = (wave_times >= s) & (wave_times <= e)
		wave_times = wave_times[wave_mask]
		wave_signal = a.signal[wave_mask]
		# Mask onset envelope
		onset_mask = (onset_times >= s) & (onset_times <= e)
		onset_times = onset_times[onset_mask]
		onset_env = onset_env[onset_mask]
		# Mask beats
		beats = np.array([]) if a.beats is None else np.array(a.beats)
		beats = beats[(beats >= s) & (beats <= e)]
	else:
		wave_signal = a.signal
		beats = np.array([]) if a.beats is None else np.array(a.beats)

	# Create plot: top = onset envelope, bottom = waveform (share x)
	fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True, gridspec_kw={"height_ratios": [1, 1.2]})

	# Top: onset envelope
	ax_env = axes[0]
	ax_env.plot(onset_times, onset_env, color="C1", label="Onset envelope")
	if beats.size:
		ax_env.vlines(beats, 0, onset_env.max() if onset_env.size else 1.0, color="C2", alpha=0.7, linestyle="--", label="Beats")
	ax_env.set_ylabel("Onset strength")
	ax_env.legend(loc="upper right")

	# Bottom: waveform
	ax_wave = axes[1]
	ax_wave.plot(wave_times, wave_signal, color="0.3", linewidth=0.6)
	if beats.size:
		ax_wave.vlines(beats, wave_signal.min(), wave_signal.max(), color="C2", alpha=0.6, linestyle="--")
	ax_wave.set_xlabel("Time (s)")
	ax_wave.set_ylabel("Amplitude")

	plt.tight_layout()

	if save_path:
		fig.savefig(save_path, dpi=150)

	plt.show()
	return fig, axes


def plot_cadence_pattern(c: wave, pattern_name: str = "slow_smooth_change",
                         start: float = None, end: float = None,
                         figsize=(12, 6), save_path: str = None):
    """
    Plot cadence outputs produced by the NEW function-based cadence generator:

      c = make_cadence(song, pattern=..., output=...)



    Expects:

      - c is oop.wave

      - c.debug dict exists with:

          "pattern", "t_spm", "spm_curve", "step_times", "impulses", "energy"
    """
    #Validation 
    if not isinstance(c, wave):
        raise ValueError("plot_cadence_pattern: c must be an oop.wave instance")

    if not hasattr(c, "debug") or c.debug is None:
        raise ValueError("plot_cadence_pattern: c has no debug info.")

    dbg = c.debug
    
    # EXTRACT DATA 
    t_spm = np.asarray(dbg.get("t_spm", []), dtype=float)
    spm_curve = np.asarray(dbg.get("spm_curve", []), dtype=float)
    step_times = np.asarray(dbg.get("step_times", []), dtype=float)
    impulses = np.asarray(dbg.get("impulses", []), dtype=float)
    energy = np.asarray(dbg.get("energy", []), dtype=float)
    
    if getattr(c, "sr", None) is None:
        raise ValueError("plot_cadence_pattern: c.sr is missing")
    sr = float(c.sr)

    #  Define t_audio BEFORE slicing
    if energy.size > 0:
        t_audio = np.arange(energy.size, dtype=float) / sr
    elif impulses.size > 0:
        t_audio = np.arange(impulses.size, dtype=float) / sr
    else:
        t_audio = np.array([], dtype=float)

    # 2. SLICING LOGIC 
    start = 0.0 if start is None else float(start)
    
    if end is None:
        end = t_spm[-1] if len(t_spm) > 0 else 300.0
    else:
        end = float(end)

    # Slice SPM Curve
    mask_spm = (t_spm >= start) & (t_spm <= end)
    t_spm_view = t_spm[mask_spm]
    spm_curve_view = spm_curve[mask_spm]

    # Slice Steps
    step_times_view = step_times[(step_times >= start) & (step_times <= end)]

    # Slice Audio/Energy
    idx_start = int(start * sr)
    idx_end = int(end * sr)
    
    # Clip indices
    idx_start = max(0, min(idx_start, len(energy)))
    idx_end = max(0, min(idx_end, len(energy)))

    # Now t_audio exists, so this works:
    t_audio_view = t_audio[idx_start:idx_end]
    energy_view = energy[idx_start:idx_end]


    #  PLOTTING 
    fig, axes = plt.subplots(
        3, 1, figsize=figsize, sharex=False, # sharex=False because we manually align them
        gridspec_kw={"height_ratios": [1, 0.8, 0.8]}
    )

    # Plot 1: SPM (Use the VIEW, not the full array)
    ax_spm = axes[0]
    if t_spm_view.size > 0:
        ax_spm.plot(t_spm_view, spm_curve_view, label="SPM(t)") # FIX 2: Use view
    ax_spm.set_ylabel("SPM")
    ax_spm.set_title(f"Cadence pattern: {pattern_name} (Zoom: {start}-{end}s)")
    ax_spm.legend(loc="upper right")
    ax_spm.set_xlim(start, end) # Enforce sync

    # Plot 2: Impulses
    ax_imp = axes[1]
    if step_times_view.size > 0:
        ax_imp.vlines(step_times_view, 0, 1, alpha=0.7, label="Steps") # FIX 2: Use view
    ax_imp.set_ylabel("Impulses")
    ax_imp.set_ylim(0, 1.2)
    ax_imp.legend(loc="upper right")
    ax_imp.set_xlim(start, end)

    # Plot 3: Energy
    ax_energy = axes[2]
    if energy_view.size > 0:
        ax_energy.plot(t_audio_view, energy_view, label="Energy") # FIX 2: Use view
    ax_energy.set_xlabel("Time (s)")
    ax_energy.set_ylabel("Energy")
    ax_energy.legend(loc="upper right")
    ax_energy.set_xlim(start, end)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)

    plt.show()
    return fig, axes








