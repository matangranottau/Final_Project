import matplotlib.pyplot as plt
import librosa
import numpy as np
from oop import wave
from cadence import cadence


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


def plot_cadence_pattern(c: cadence,pattern_name: str = "slow_smooth_change", figsize=(12, 6), save_path: str = None):
    """


    Parameters

    - c : cadence A cadence instance with create_cadence() already called.
    - pattern_name : exercise pattern
    - figsize : tupleFigure size.
    - save_path : str or None Optional path to save the figure. If None, just shows it.
    """
    if not c.signals or c.time is None:
        raise ValueError("Cadence instance has no signals. ")
                         
    if pattern_name not in c.signals:
        raise ValueError(f"Unknown pattern_name '{pattern_name}'. "
                         f"Available: {list(c.signals.keys())}")

    t = c.time
    data = c.signals[pattern_name]
    spm = data["spm"]
    impulses = data["impulses"]
    energy = data["energy"]

    # Find step times for plotting impulses as lines
    step_indices = np.nonzero(impulses)[0]
    step_times = t[step_indices]

    fig, axes = plt.subplots(3, 1, figsize=figsize, sharex=True,gridspec_kw={"height_ratios": [1, 0.8, 0.8]})

    # 1) SPM(t)
    ax_spm = axes[0]
    ax_spm.plot(t, spm, label="SPM(t)")
    ax_spm.set_ylabel("SPM")
    ax_spm.set_title(f"Cadence pattern: {pattern_name}")
    ax_spm.legend(loc="upper right")

    # 2) Impulses (step events)
    ax_imp = axes[1]
    ax_imp.vlines(step_times, 0, 1, color="C1", alpha=0.7, label="Steps")
    ax_imp.set_ylabel("Impulses")
    ax_imp.set_ylim(0, 1.2)
    ax_imp.legend(loc="upper right")

    # 3) Energy envelope
    ax_energy = axes[2]
    ax_energy.plot(t, energy, color="C2", label="Energy")
    ax_energy.set_xlabel("Time (s)")
    ax_energy.set_ylabel("Energy")
    ax_energy.legend(loc="upper right")

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)

    plt.show()
    return fig, axes








