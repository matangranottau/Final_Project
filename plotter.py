import matplotlib.pyplot as plt
import librosa
import numpy as np
from audio import audio


def plot_audio_onsets_beats(a: audio, start: float = None, end: float = None, figsize=(12, 6), save_path: str = None):
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











