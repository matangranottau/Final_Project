import numpy as np
from audio import audio

class cadence:
    def __init__(self):
        self.signal = None  # Numpy array of cadence signal
        self.sr = None  # Sampling rate of cadence signal
        self.srm = None # Steps per minute

    def copy_sr(self, audio):
        # Copy sampling rate from audio instance
        self.sr = audio.sr

    def create_cadence(self):
        # YOGEV: Create a simulated cadence signal
        pass

    def calc_SRM(self):
        # YOGEV: Calculate steps per minute (SRM) from cadence signal
        pass
    