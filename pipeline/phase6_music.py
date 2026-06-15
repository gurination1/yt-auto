"""
phase6_music.py — Procedural ambient background music generator.
Generates calm chord-pad loops with a soft shaker pulse using pure numpy.
No torch, no transformers, no model download, no OOM risk. Runs in <2s.
"""
import os
import random
import numpy as np
import wave

SAMPLE_RATE = 44100
_NOTE_FREQS = {  # octave-4 reference frequencies
    "C": 261.63, "C#": 277.18, "D": 293.66, "D#": 311.13, "E": 329.63,
    "F": 349.23, "F#": 369.99, "G": 392.00, "G#": 415.30, "A": 440.00,
    "A#": 466.16, "B": 493.88,
}
# Calm/ambient 4-chord loops: (root, quality)
_PROGRESSIONS = [
    [("C", "maj"), ("A", "min"), ("F", "maj"), ("G", "maj")],
    [("A", "min"), ("F", "maj"), ("C", "maj"), ("G", "maj")],
    [("D", "min"), ("A#", "maj"), ("F", "maj"), ("C", "maj")],
    [("E", "min"), ("C", "maj"), ("G", "maj"), ("D", "maj")],
]


def _adsr(n, attack, release):
    env = np.ones(n)
    a, r = min(attack, n // 2), min(release, n // 2)
    if a:
        env[:a] = np.linspace(0, 1, a)
    if r:
        env[-r:] = np.linspace(1, 0, r)
    return env


def _chord(root, quality, duration, base_octave=3):
    intervals = [0, 4, 7] if quality == "maj" else [0, 3, 7]
    root_freq = _NOTE_FREQS[root] / (2 ** (4 - base_octave))
    n = int(duration * SAMPLE_RATE)
    t = np.linspace(0, duration, n, endpoint=False)
    wave = sum(np.sin(2 * np.pi * root_freq * (2 ** (iv / 12)) * t) for iv in intervals)
    wave += 0.6 * np.sin(2 * np.pi * (root_freq / 2) * t)          # sub-bass, -1 octave
    return wave * _adsr(n, int(0.35 * SAMPLE_RATE), int(0.6 * SAMPLE_RATE))


def _shaker(n_samples, beat_samples):
    track = np.zeros(n_samples)
    tt = np.linspace(0, 0.05, int(0.05 * SAMPLE_RATE))
    hit = np.random.randn(len(tt)) * np.exp(-tt * 90) * 0.08
    for start in range(0, n_samples - len(hit), beat_samples):
        track[start:start + len(hit)] += hit
    return track


def generate_music(topic: str, duration_seconds: int = 35) -> str:
    out_path = "output/music.wav"
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        print("Background music already exists, skipping generation.")
        return out_path
    print(f"Generating procedural ambient background music ({duration_seconds}s)...")
    os.makedirs("output", exist_ok=True)

    progression = random.choice(_PROGRESSIONS)
    chord_dur = 4.0
    loop = np.concatenate([_chord(r, q, chord_dur) for r, q in progression])
    reps = int(np.ceil(duration_seconds * SAMPLE_RATE / len(loop))) + 1
    track = np.tile(loop, reps)[: int(duration_seconds * SAMPLE_RATE)]
    track = track + _shaker(len(track), int(chord_dur * SAMPLE_RATE / 2))

    track = track / (np.max(np.abs(track)) + 1e-9) * 0.65
    track_int16 = (track * 32767).clip(-32768, 32767).astype(np.int16)
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(track_int16.tobytes())
    print(f"Procedural music saved ({progression})")
    return out_path
