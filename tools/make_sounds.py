#!/usr/bin/env python3
"""Synthesizes every sound the app uses, so nothing is copyrighted.

  lobby.mp3      upbeat loop for the hub, the timer and the live boards
  tension.mp3    low, pulsing loop for the diplomacy game
  drumroll.mp3   snare roll with a crescendo, for the attack draw
  explosion.mp3  the hit
  pop.mp3        a small pop when a pair joins

Run from the repo root:  python tools/make_sounds.py
Needs numpy, scipy and ffmpeg (for the mp3 step).
"""
from __future__ import annotations

import os
import subprocess
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "static" / "sounds"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)


# ------------------------------------------------------------------ building blocks
def t_axis(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def env_adsr(n: int, a=0.005, d=0.1, s=0.6, r=0.1) -> np.ndarray:
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    s_n = max(0, n - a_n - d_n - r_n)
    e = np.concatenate([np.linspace(0, 1, a_n, endpoint=False), np.linspace(1, s, d_n, endpoint=False),
                        np.full(s_n, s), np.linspace(s, 0, r_n)])
    return e[:n] if len(e) >= n else np.pad(e, (0, n - len(e)))


def env_exp(n: int, tau: float) -> np.ndarray:
    return np.exp(-np.arange(n) / SR / tau)


def lowpass(x, fc, order=2):
    return sosfilt(butter(order, fc / (SR / 2), btype="low", output="sos"), x)


def highpass(x, fc, order=2):
    return sosfilt(butter(order, fc / (SR / 2), btype="high", output="sos"), x)


def bandpass(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band", output="sos"), x)


def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    y = 2 * ((t * f) % 1) - 1
    if detune:
        y = 0.5 * y + 0.5 * (2 * ((t * f * (1 + detune)) % 1) - 1)
    return y


def square(f, n):
    t = np.arange(n) / SR
    return np.sign(np.sin(2 * np.pi * f * t))


def tri(f, n):
    t = np.arange(n) / SR
    return 2 * np.abs(2 * ((t * f) % 1) - 1) - 1


def sine(f, n, phase=0.0):
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t + phase)


def reverb(x, size=0.25, mix=0.18):
    """A cheap room: convolution with a short decaying noise tail."""
    n = int(size * SR)
    ir = lowpass(rng.standard_normal(n), 3200) * np.exp(-np.arange(n) / SR / (size / 3))
    ir[0] = 1.0
    wet = np.convolve(x, ir)[: len(x)] / np.sqrt(n / 400)
    return (1 - mix) * x + mix * wet


def soft_clip(x, drive=1.0):
    return np.tanh(x * drive) / np.tanh(drive)


def normalize(x, peak=0.92):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


def place(buf: np.ndarray, snd: np.ndarray, at: float, gain: float = 1.0, wrap: bool = False):
    """Mix snd into buf starting at `at` seconds. With wrap, tails past the end come back to the start (seamless loops)."""
    i = int(at * SR)
    n = len(buf)
    if wrap:
        idx = (np.arange(len(snd)) + i) % n
        np.add.at(buf, idx, snd * gain)
    else:
        j = min(n, i + len(snd))
        if i < n:
            buf[i:j] += snd[: j - i] * gain


def note(name: str) -> float:
    """'A3' -> Hz."""
    names = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
             "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
    k, octv = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[k] + 12 * (octv - 4) - 9) / 12)


# ------------------------------------------------------------------ drum kit
def kick(dur=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 42 + 120 * np.exp(-t * 28)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.11)
    click = rng.standard_normal(int(0.004 * SR)) * 0.4
    y[: len(click)] += click
    return soft_clip(y, 1.6)


def snare(dur=0.25, tone=190.0):
    n = int(dur * SR)
    noise = bandpass(rng.standard_normal(n), 900, 7000) * env_exp(n, 0.07)
    body = sine(tone, n) * env_exp(n, 0.04) * 0.8
    return soft_clip((noise * 0.9 + body), 1.3)


def hat(dur=0.06, open_=False):
    n = int((0.28 if open_ else dur) * SR)
    y = highpass(rng.standard_normal(n), 7000) * env_exp(n, 0.09 if open_ else 0.018)
    return y * 0.45


def tom(f=110.0, dur=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    fr = f * (1 + 0.6 * np.exp(-t * 18))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * env_exp(n, 0.16)


def crash(dur=2.2):
    n = int(dur * SR)
    return highpass(rng.standard_normal(n), 4500) * env_exp(n, 0.55) * 0.5


# ------------------------------------------------------------------ instruments
def pluck(f, dur, bright=3200):
    n = int(dur * SR)
    y = saw(f, n, 0.006) * 0.5 + square(f * 0.5, n) * 0.18
    y = lowpass(y, bright) * env_adsr(n, 0.003, 0.18, 0.25, 0.08)
    return y


def bass(f, dur):
    n = int(dur * SR)
    y = saw(f, n) * 0.6 + sine(f, n) * 0.5
    return lowpass(y, 420) * env_adsr(n, 0.004, 0.12, 0.55, 0.05)


def lead(f, dur):
    n = int(dur * SR)
    y = tri(f, n) * 0.6 + sine(f * 2, n) * 0.12
    return y * env_adsr(n, 0.004, 0.08, 0.5, 0.06)


def pad(f, dur, cutoff=900):
    n = int(dur * SR)
    y = saw(f, n, 0.004) + saw(f * 0.5, n, -0.003) * 0.6 + saw(f * 1.5, n, 0.002) * 0.25
    t = np.arange(n) / SR
    y = lowpass(y, cutoff)
    swell = 0.5 - 0.5 * np.cos(2 * np.pi * t / dur)        # rises and falls over the note
    return y * swell * 0.35


# ------------------------------------------------------------------ 1. lobby loop
def make_lobby():
    bpm = 122
    beat = 60 / bpm
    bars = 16
    total = bars * 4 * beat
    buf = np.zeros(int(total * SR))
    # chords, two bars each, twice: Am7 F C G
    prog = [("A2", ["A3", "C4", "E4", "G4"]), ("F2", ["F3", "A3", "C4", "E4"]),
            ("C2", ["C3", "E3", "G3", "C4"]), ("G2", ["G2", "B3", "D4", "G4"])]
    for rep in range(2):
        for ci, (root, chord) in enumerate(prog):
            start = (rep * 8 + ci * 2) * 4 * beat
            # bass: eighths, root with octave on the 'and' of 2 and 4
            for e in range(16):
                f = note(root) * (2 if e in (3, 11) else 1)
                place(buf, bass(f, beat * 0.45), start + e * beat / 2, 0.55, wrap=True)
            # chord stabs on the off-beats
            for b in range(8):
                for k, nm in enumerate(chord):
                    place(buf, pluck(note(nm), beat * 0.42), start + b * beat + beat / 2, 0.16, wrap=True)
            # arpeggio in 16ths through the chord tones, one octave up, with a few rests
            tones = [note(nm) * 2 for nm in chord]
            pattern = [0, 1, 2, 3, 2, 1, 0, 2, 1, 3, 2, 0, 1, 2, 3, 1]
            for s in range(32):
                if (rep + ci + s) % 7 == 3:
                    continue
                place(buf, lead(tones[pattern[s % 16]], beat * 0.22), start + s * beat / 4, 0.11, wrap=True)
    # drums
    for b in range(bars * 4):
        at = b * beat
        place(buf, kick(), at, 0.95, wrap=True)
        if b % 2 == 1:
            place(buf, snare(), at, 0.55, wrap=True)
        place(buf, hat(), at, 0.5, wrap=True)
        place(buf, hat(open_=(b % 8 == 7)), at + beat / 2, 0.42, wrap=True)
        if b % 16 == 15:
            place(buf, snare(0.18, 220), at + beat * 0.75, 0.35, wrap=True)
    return normalize(reverb(buf, 0.18, 0.12), 0.9)


# ------------------------------------------------------------------ 2. tension loop
def make_tension():
    bpm = 92
    beat = 60 / bpm
    bars = 16
    total = bars * 4 * beat
    buf = np.zeros(int(total * SR))
    # drone
    n = len(buf)
    drone = lowpass(saw(note("A1"), n, 0.003) + saw(note("E2"), n, -0.002) * 0.5, 220) * 0.28
    buf += drone
    # slow minor pads, four bars each: Am, Fm/Ab, Dm, E
    prog = [["A2", "C3", "E3"], ["F2", "Ab2", "C3"], ["D2", "F3", "A3"], ["E2", "G#2", "B2"]]
    for ci, chord in enumerate(prog):
        start = ci * 4 * 4 * beat
        for nm in chord:
            place(buf, pad(note(nm), 4 * 4 * beat, 700), start, 0.32, wrap=True)
    # pulse: filtered clicks on eighths, accent on the beat; a low tom now and then
    for e in range(bars * 8):
        at = e * beat / 2
        y = bandpass(rng.standard_normal(int(0.04 * SR)), 1500, 5000) * env_exp(int(0.04 * SR), 0.008)
        place(buf, y, at, 0.22 if e % 2 == 0 else 0.1, wrap=True)
        if e % 16 == 0:
            place(buf, tom(70, 0.9), at, 0.5, wrap=True)
        if e % 32 == 22:
            place(buf, tom(95, 0.6), at, 0.35, wrap=True)
    # a heartbeat under everything
    for b in range(bars * 4):
        at = b * beat
        place(buf, kick(0.3), at, 0.35, wrap=True)
        place(buf, kick(0.25), at + beat * 0.28, 0.22, wrap=True)
    return normalize(reverb(buf, 0.6, 0.22), 0.85)


# ------------------------------------------------------------------ 3. drumroll
def make_drumroll():
    dur = 2.75
    buf = np.zeros(int(dur * SR))
    t = 0.0
    k = 0
    while t < 2.25:
        rate = 11 + 28 * (t / 2.25) ** 1.4           # hits per second, speeding up
        gain = 0.25 + 0.75 * (t / 2.25) ** 1.2        # crescendo
        place(buf, snare(0.16, 185 + rng.uniform(-6, 6)), t, gain * (1.0 if k % 2 == 0 else 0.8))
        t += 1 / rate
        k += 1
    place(buf, snare(0.4, 170), 2.3, 1.1)
    place(buf, crash(1.8), 2.3, 0.7)
    place(buf, kick(0.4), 2.3, 0.8)
    return normalize(reverb(buf, 0.3, 0.15), 0.95)


# ------------------------------------------------------------------ 4. explosion
def make_explosion():
    dur = 4.5
    n = int(dur * SR)
    t = np.arange(n) / SR
    crack = highpass(rng.standard_normal(n), 1200) * env_exp(n, 0.03) * 1.2
    body = bandpass(rng.standard_normal(n), 120, 900) * env_exp(n, 0.45)
    rumble = lowpass(np.cumsum(rng.standard_normal(n)) / 60, 140, 3)
    rumble = rumble / (np.max(np.abs(rumble)) or 1) * env_exp(n, 1.3)
    sub_f = 55 * np.exp(-t * 0.9) + 24
    sub = np.sin(2 * np.pi * np.cumsum(sub_f) / SR) * env_exp(n, 1.1)
    debris = bandpass(rng.standard_normal(n), 2500, 8000) * (env_exp(n, 0.9) * (0.3 + 0.7 * (np.sin(t * 37) > 0.9)))
    y = crack * 0.7 + body * 1.0 + rumble * 1.6 + sub * 1.1 + debris * 0.25
    y = soft_clip(y, 1.8)
    return normalize(reverb(y, 0.8, 0.25), 0.98)


# ------------------------------------------------------------------ 5. pop
def make_pop():
    n = int(0.18 * SR)
    t = np.arange(n) / SR
    f = 420 + 520 * np.exp(-t * 40)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.045)
    return normalize(y, 0.8)


# ------------------------------------------------------------------ write
def write(name: str, y: np.ndarray):
    wav = OUT / f"{name}.wav"
    data = (np.clip(y, -1, 1) * 32767).astype("<i2")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    mp3 = OUT / f"{name}.mp3"
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "128k",
                        str(mp3)], check=True)
        os.remove(wav)
        print(f"{name}.mp3  {mp3.stat().st_size / 1024:.0f} KB  {len(y) / SR:.1f} s")
    except Exception as e:
        print(f"{name}.wav kept (no mp3: {e})")


if __name__ == "__main__":
    write("lobby", make_lobby())
    write("tension", make_tension())
    write("drumroll", make_drumroll())
    write("explosion", make_explosion())
    write("pop", make_pop())
