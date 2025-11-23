import matplotlib.pyplot as plt
import librosa
import numpy as np
from Beat_BPM import extract as _extract_beats


def plot_beats_with_onset_background(audio_path=None, y=None, sr=None, beat_times=None, hop_length=512, show=True, save_path=None, bpm=None):
	"""
	Plot the waveform with the onset envelope shown as a faint background and beats as vertical red lines.

	Parameters
	----------
	audio_path : str, optional
		Path to an audio file. If provided, `y` and `sr` are ignored and audio will be loaded from this path.
	y : np.ndarray, optional
		Audio time series. Required if `audio_path` is None.
	sr : int, optional
		Sampling rate of `y`. Required if `audio_path` is None.
	beat_times : array-like, optional
		Beat times in seconds. If None and `audio_path` is provided, beats will be computed using `Beat_BPM.extract`.
	hop_length : int, optional
		Hop length used when computing onset strength (default 512).
	show : bool, optional
		If True, calls `plt.show()` after plotting.
	save_path : str, optional
		If given, the figure will be saved to this path.

	Behavior
	--------
	- Draws the onset-strength envelope as a faint filled area in the background of the waveform plot.
	- Draws beats as vertical red lines across the waveform.
	"""

	if audio_path is not None:
		y, sr = librosa.load(audio_path, sr=None)
	elif y is None or sr is None:
		raise ValueError("Either audio_path or both y and sr must be provided.")

	# BPM may be provided by the caller (bpm). Initialize local BPM variable.
	BPM = None
	if beat_times is None and audio_path is not None:
		beat_times, __ = _extract_beats(audio_path)
	else:
		# If caller provided bpm explicitly, use it
		if bpm is not None:
			BPM = bpm

	# Compute onset envelope
	onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
	frames = np.arange(len(onset_env))
	times_env = librosa.frames_to_time(frames, sr=sr, hop_length=hop_length)

	# Prepare figure
	fig, ax = plt.subplots(figsize=(12, 3.5))

	# Map onset envelope to waveform amplitude range so it appears as a background texture
	y_min, y_max = float(np.min(y)), float(np.max(y))
	amp_range = y_max - y_min if (y_max - y_min) > 0 else 1.0
	if onset_env.max() > 0:
		env_norm = onset_env / float(onset_env.max())
	else:
		env_norm = onset_env * 0.0
	# Scale envelope to a fraction of amplitude range and shift to sit above ymin
	env_mapped = y_min + env_norm * amp_range * 0.6

	# Fill onset background (low alpha)
	ax.fill_between(times_env, y_min, env_mapped, color='C0', alpha=0.18, step='pre')

	# Waveform on top
	times_wave = np.arange(len(y)) / float(sr)
	ax.plot(times_wave, y, color='k', linewidth=0.6, zorder=2)

	# Beats as vertical red lines
	if beat_times is not None and len(beat_times) > 0:
		ax.vlines(beat_times, ymin=y_min, ymax=y_max, color='r', linewidth=1.2, alpha=0.9, zorder=3)

	ax.set_xlim(times_wave[0], times_wave[-1])
	ax.set_xlabel('Time (s)')
	ax.set_ylabel('Amplitude')
	ax.set_title(f'Song Waveform - BPM = {bpm if bpm is not None else "unknown"}')

	ax.set_xlim(times_wave[0], times_wave[-1])

	# Create a legend using proxy artists (fill_between doesn't create an automatic legend entry reliably)
	from matplotlib.patches import Patch
	from matplotlib.lines import Line2D

	handles = [Patch(facecolor='C0', alpha=0.18, label='Onset envelope'),
			   Line2D([0], [0], color='k', lw=0.6, label='Waveform'),
			   Line2D([0], [0], color='r', lw=1.2, label='Beats')]
	ax.legend(handles=handles, loc='upper right')

	plt.tight_layout()
	if save_path:
		plt.savefig(save_path, dpi=200)
	if show:
		plt.show()
	plt.close(fig)


__all__ = ['plot_beats_with_onset_background']





