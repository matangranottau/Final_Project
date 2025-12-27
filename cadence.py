import numpy as np
from oop import wave

class cadence:
    def __init__(self):
        self.signal = None  # Numpy array of cadence signal
        self.sr = None  # Sampling rate of cadence signal
        self.spm = None # Steps per minute
        self.time = None  # Time axis (seconds)
        self.signals = {}  # Dictionary with 5 synthetic patterns
        self.default_duration = 60  # seconds

    def copy_sr(self, audio):
        # Copy sampling rate from audio instance
        self.sr = audio.sr

    def generate_time_axis(self, duration_s):
        if self.sr is None:
            # If no sampling rate was copied from audio, choose a default
            self.sr = 50.0  # 50 Hz is enough for step impulses
        t = np.arange(0, duration_s, 1.0 / self.sr)
        return t
    
    # 1) Slow and steady change
    def spm_slow_smooth_change(self, t, spm_start=140, spm_end=180):
    
        return spm_start + (spm_end - spm_start) * (t / t[-1])

    #2) SUdden change in t_jump
    def spm_fast_jump(self, t, t_jump=20.0, spm_before=140, spm_after=180):
       
        spm = np.where(t < t_jump, spm_before, spm_after)
        return spm
    
    #3) Interval training
    def spm_interval_training(self, t, segment_length=12.0,
                               spm_values=(150, 180, 130, 175, 160)):
        
        spm = np.zeros_like(t)
        n_segments = len(spm_values)
        for i, spm_val in enumerate(spm_values):
            t_start = i * segment_length
            t_end = (i + 1) * segment_length
            spm[(t >= t_start) & (t < t_end)] = spm_val

        # If the total time is longer than all segments, hold last SPM
        if (n_segments * segment_length) < t[-1]:
            spm[t >= n_segments * segment_length] = spm_values[-1]
        return spm

    #4) Natural Running With small noises
    def spm_noisy_natural(self, t, base_spm=165, noise_std=3.0, drift_std=0.03):
        dt = t[1] - t[0]
        n = len(t)

        # Slow random walk drift
        drift = np.cumsum(np.random.normal(scale=drift_std * np.sqrt(dt), size=n))
        # Short-term jitter
        noise = np.random.normal(scale=noise_std, size=n)

        spm = base_spm + drift + noise
        spm = np.clip(spm, 140, 190)  # keep in reasonable range
        return spm

    #5) Start/Stop Training
    def spm_start_stop(self, t,
                        t_run1=(10, 30), t_run2=(35, 60),
                        spm_run1=155, spm_run2=175):
        spm = np.zeros_like(t)
        spm[(t >= t_run1[0]) & (t < t_run1[1])] = spm_run1
        spm[(t >= t_run2[0]) & (t < t_run2[1])] = spm_run2
        return spm

    #Convert SPM(t) to a discrete-time step impulse train, x[n] = 1 when a step occurs, 0 otherwise.
    def spm_to_step_impulses(self, t, spm):

        dt = t[1] - t[0]
        fs = 1.0 / dt

        x = np.zeros_like(t)
        current_time = 0.0

        while current_time <= t[-1]:
            idx = int(round(current_time * fs))
            if idx >= len(t):
                break

            local_spm = spm[idx]

            if local_spm > 0:
                steps_per_sec = local_spm / 60.0
                period = 1.0 / steps_per_sec  # seconds between steps
                x[idx] = 1.0
                current_time += period
            else:
                # Standing still: move a bit forward and re-check
                current_time += 0.1

        return x   

    #Impulse to energy
    def impulses_to_energy(self, impulses, window_ms=80):

        win_len = int(np.round(window_ms * 1e-3 * self.sr))
        if win_len < 1:
            win_len = 1
        window = np.ones(win_len, dtype=float) / win_len
        energy = np.convolve(impulses, window, mode='same')
        return energy

    def create_cadence(self):
        # Time axis
        t = self.generate_time_axis(self.default_duration)
        self.time = t

        # 1) Slow and steady change 
        spm1 = self.spm_slow_smooth_change(t)
        imp1 = self.spm_to_step_impulses(t, spm1)
        en1 = self.impulses_to_energy(imp1)
        self.signals["slow_smooth_change"] = {
            "spm": spm1,
            "impulses": imp1,
            "energy": en1,
        }

        # 2) SUdden change in t_jump
        spm2 = self.spm_fast_jump(t)
        imp2 = self.spm_to_step_impulses(t, spm2)
        en2 = self.impulses_to_energy(imp2)
        self.signals["fast_jump"] = {
            "spm": spm2,
            "impulses": imp2,
            "energy": en2,
        }

        # 3) Interval training 
        spm3 = self.spm_interval_training(t)
        imp3 = self.spm_to_step_impulses(t, spm3)
        en3 = self.impulses_to_energy(imp3)
        self.signals["interval_training"] = {
            "spm": spm3,
            "impulses": imp3,
            "energy": en3,
        }

        # 4) Natural Running With small noises
        spm4 = self.spm_noisy_natural(t)
        imp4 = self.spm_to_step_impulses(t, spm4)
        en4 = self.impulses_to_energy(imp4)
        self.signals["noisy_natural"] = {
            "spm": spm4,
            "impulses": imp4,
            "energy": en4,
        }

        # 5) Start/stop Training
        spm5 = self.spm_start_stop(t)
        imp5 = self.spm_to_step_impulses(t, spm5)
        en5 = self.impulses_to_energy(imp5)
        self.signals["start_stop"] = {
            "spm": spm5,
            "impulses": imp5,
            "energy": en5,
        }

        # Default: use the impulses of the first pattern as "self.signal"
        self.signal = self.signals["slow_smooth_change"]["impulses"]


    def calc_SRM(self):
        # Calculate steps per minute (SRM) from cadence signal
        if self.signal is None or self.sr is None:
            raise ValueError("cadence.calc_SRM: self.signal or self.sr is not set")

        # Count steps as non-zero samples (impulses)
        n_steps = np.count_nonzero(self.signal)
        duration_s = len(self.signal) / float(self.sr)

        if duration_s == 0:
            self.spm = 0.0
        else:
            self.spm = n_steps * 60.0 / duration_s

        return self.spm