import librosa
import numpy as np



class wave:
    def __init__(self, path, sr=None, hop_length=512, mode=0):
        # mode = 0 is Deafult -> General Wave
        # mode = 1 is Song
        # mode = 2 is Cadence
        self.path = path
        self.signal = None 
        self.sr = sr
        self.beats = None 
        self.tempo = None
        self.hop_length = hop_length

        #   if mode == 0:
        #    mode = "General Wave"
        #   if mode == 1:   
        #    mode_str = "Song" 
        #   if mode == 2
        #    mode_str = "Cadence"
        #   else
        #    Unknown

        if mode not in [0, 1, 2]:
            mode = None
            raise ValueError("Mode must be 0, 1, or 2")

        self.mode = mode

        self.length = None # In Seconds
        self.sample_length = None # In Samples
        self.r_list=[]  # Relevant for BPM pp only for song
        self.spm_list = [] # Relevant for BPM pp only for cadnence

    def load(self):
        self.signal, self.sr = librosa.load(self.path, sr=None)
        self.sample_length = self.signal.size
        self.length = self.sample_length / self.sr
        

    def extract(self):
        if self.signal is None or self.sr is None:
            self.load()
        
        # Perform beat tracking
        tempo, beat_frames = librosa.beat.beat_track(y=self.signal, sr=self.sr, hop_length=self.hop_length)

        # Convert beat frames to time (in seconds)
        self.beats = self.hop_length * beat_frames / self.sr
        
        self.tempo = float(tempo)

    def add_clicks(self, magnitude=10, click_ms = 2, click_decay = 4):
        # Convert time of beats to impulse array
        beats = np.zeros(self.signal.shape)
        indices = (self.beats * self.sr).astype(int)
        beats[indices] = np.max(np.abs(self.signal))

        # Click kernel
        click_len = int(0.001 * click_ms * self.sr)
        n = np.arange(click_len)
        kernel = np.exp(-n / (0.0001 * click_decay * self.sr))
        clicks = np.convolve(beats, kernel, mode='same')

        return self.signal/magnitude + clicks


