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


import numpy as np
import matplotlib.pyplot as plt
from oop import wave

def plot_cadence_pattern(c: wave, pattern_name: str = "slow_smooth_change",figsize=(12, 6),save_path: str = None):
    """
    Plot cadence outputs produced by the NEW function-based cadence generator:
      c = make_cadence(song, pattern=..., output=...)

    Expects:
      - c is oop.wave
      - c.debug dict exists with:
          "pattern", "t_spm", "spm_curve", "step_times", "impulses", "energy"
    """

    # Basic validation
    if not isinstance(c, wave):
        raise ValueError("plot_cadence_pattern: c must be an oop.wave instance")

    if not hasattr(c, "debug") or c.debug is None:
        raise ValueError("plot_cadence_pattern: c has no debug info. "
                         "Make sure you generated it using make_cadence(...).")

    dbg = c.debug

    # verify pattern_name matches what was generated
    generated_pattern = dbg.get("pattern", None)
    if generated_pattern is not None and pattern_name is not None:
        if pattern_name != generated_pattern:
            raise ValueError(
                f"Requested pattern_name '{pattern_name}', but this cadence wave was generated with "
                f"'{generated_pattern}'. Either regenerate cadence with that pattern or pass "
                f"pattern_name='{generated_pattern}'."
            )

    # Low-rate SPM curve (t_spm)
    t_spm = np.asarray(dbg.get("t_spm", []), dtype=float)
    spm_curve = np.asarray(dbg.get("spm_curve", []), dtype=float)

    # High-rate signals (audio-rate)
    impulses = np.asarray(dbg.get("impulses", []), dtype=float)
    energy = np.asarray(dbg.get("energy", []), dtype=float)

    # Step times (seconds)
    step_times = np.asarray(dbg.get("step_times", []), dtype=float)

    # Build audio time axis (for energy plot)
    if getattr(c, "sr", None) is None:
        raise ValueError("plot_cadence_pattern: c.sr is missing")
    sr = float(c.sr)

    if energy.size > 0:
        t_audio = np.arange(energy.size, dtype=float) / sr
    elif impulses.size > 0:
        t_audio = np.arange(impulses.size, dtype=float) / sr
    else:
        t_audio = np.array([], dtype=float)

    fig, axes = plt.subplots(
        3, 1, figsize=figsize, sharex=False,
        gridspec_kw={"height_ratios": [1, 0.8, 0.8]}
    )

    # 1) SPM(t)
    ax_spm = axes[0]
    if t_spm.size > 0 and spm_curve.size > 0:
        ax_spm.plot(t_spm, spm_curve, label="SPM(t)")
    ax_spm.set_ylabel("SPM")
    ax_spm.set_title(f"Cadence pattern: {generated_pattern if generated_pattern else pattern_name}")
    ax_spm.legend(loc="upper right")

    # 2) Impulses (step events)
    ax_imp = axes[1]
    if step_times.size > 0:
        ax_imp.vlines(step_times, 0, 1, alpha=0.7, label="Steps")
    ax_imp.set_ylabel("Impulses")
    ax_imp.set_ylim(0, 1.2)
    ax_imp.legend(loc="upper right")

    # 3) Energy envelope (or fallback to c.signal if you generated impulses-only)
    ax_energy = axes[2]
    if energy.size > 0 and t_audio.size > 0:
        ax_energy.plot(t_audio, energy, label="Energy")
    elif getattr(c, "signal", None) is not None and t_audio.size > 0:
        ax_energy.plot(t_audio, np.asarray(c.signal, dtype=float), label="Cadence signal")
    ax_energy.set_xlabel("Time (s)")
    ax_energy.set_ylabel("Energy")
    ax_energy.legend(loc="upper right")

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)

    plt.show()
    return fig, axes








