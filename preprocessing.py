import numpy as np
from audio import audio

def BPM_preprocssing(audio, cadence):
    r = cadence.BPM / audio.srm

    r = 1.5 if r > 1.5 else r
    r = 0.8 if r < 0.8 else r
    
    return r
    
    