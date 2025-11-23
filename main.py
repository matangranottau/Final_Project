from Beat_BPM import extract
from plotter import plot_beats_with_onset_background

path = "Songs/Seven Nation Army.mp3"
beats, BPM = extract(path)

plot_beats_with_onset_background(audio_path=path, beat_times=beats, bpm=BPM, show=True)

