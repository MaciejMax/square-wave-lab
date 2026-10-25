"""Hear eight approaches to the same score. Always save, then play."""

import argparse
from pathlib import Path
import wave

import numpy as np

from music import BPM, CHORD_NAMES, CHORDS, MELODY_BARS, SAMPLE_RATE as FS, frequency


VERSIONS = {
    "space": ("ode_space.wav", "Soft stereo instruments and echoes"),
    "chords": ("ode_chords.wav", "Loud square-wave chord baseline"),
    "switch": ("ode_switch.wav", "One oscillator, regular frequency switching"),
    "less-chord": ("ode_less_chord.wav", "Less time for chord tones"),
    "full-cycles": ("ode_full_cycles.wav", "Switch only after complete cycles"),
    "random": ("ode_random.wav", "Random voice every cycle"),
    "packets": ("ode_packets.wav", "Random packets of 4-12 cycles"),
    "summed": ("ode_summed.wav", "Four independent square-wave oscillators"),
}
ROOT = Path(__file__).resolve().parent


def score_arrays():
    durations = [beats * 60 / BPM for bar in MELODY_BARS for _, beats in bar]
    boundaries = np.rint(np.cumsum([0] + durations) * FS).astype(int)
    bars = np.rint(np.cumsum([0] + [sum(b for _, b in bar) for bar in MELODY_BARS])
                   * 60 / BPM * FS).astype(int)
    melody = np.empty(boundaries[-1])
    gate = np.ones(len(melody), dtype=bool)
    notes = [frequency(note) for bar in MELODY_BARS for note, _ in bar]
    for pitch, start, end in zip(notes, boundaries[:-1], boundaries[1:]):
        melody[start:end] = pitch
        gate[end - min(round(.012 * FS), (end - start) // 10):end] = False
    chords = np.empty((len(melody), 3))
    for name, start, end in zip(CHORD_NAMES, bars[:-1], bars[1:]):
        chords[start:end] = [frequency(note) for note in CHORDS[name]]
    return melody, chords, gate, boundaries, bars


def cycle_square(pitches, gate, volume=1., chords=None, share=.25, packet=(1, 1), seed=42):
    """Change pitch/gate at complete-cycle boundaries; retain fractional timing."""
    signal = np.zeros(len(pitches), dtype=np.float32)
    rng = np.random.default_rng(seed)
    position, remaining, previous = 0., 0, None
    while round(position) < len(signal):
        start = round(position)
        pitch = pitches[start]
        if chords is not None and gate[start]:
            voices = np.r_[pitch, chords[start]]
            context = tuple(voices)
            if context != previous:
                remaining = 0
            if remaining == 0:
                # Probability proportional to frequency compensates for period length.
                weights = voices * np.array([1 - share, share / 3, share / 3, share / 3])
                selected = rng.choice(voices, p=weights / weights.sum())
                remaining = int(rng.integers(packet[0], packet[1] + 1))
            pitch = selected
            remaining -= 1
            previous = context
        else:
            remaining, previous = 0, None
        period = FS / pitch
        middle, end = round(position + period / 2), round(position + period)
        if end > len(signal):
            break
        if gate[start]:
            signal[start:middle] = volume
            signal[middle:end] = -volume
        position += period
    return signal


def switched_square(pitches, volume=.45):
    phase = np.remainder(np.cumsum(pitches / FS) - pitches[0] / FS, 1.)
    return (volume * np.where(phase < .5, 1., -1.)).astype(np.float32)


def shaped_note(pitch, count, soft=False, attack=.005, release=.005):
    t = np.arange(count) / FS
    if soft:
        tone = (np.sin(2 * np.pi * pitch * t) + .18 * np.sin(4 * np.pi * pitch * t)) / 1.18
        active = count
    else:
        tone = np.where(np.sin(2 * np.pi * pitch * t) >= 0, 1., -1.)
        active = count - min(round(.025 * FS), count // 10)
    envelope = np.zeros(count)
    envelope[:active] = 1
    a, r = min(round(attack * FS), active // 2), min(round(release * FS), active // 2)
    if a:
        envelope[:a] = np.linspace(0, 1, a)
    if r:
        envelope[active-r:active] = np.linspace(1, 0, r)
    return tone * envelope


def arranged_audio(version, melody, chords, boundaries, bars):
    lead = np.zeros(len(melody), dtype=np.float32)
    for start, end in zip(boundaries[:-1], boundaries[1:]):
        pitch, count = melody[start], end - start
        if version == "chords":
            lead[start:end] = .65 * shaped_note(pitch, count)
        else:
            lead[start:end] = (.20 * shaped_note(pitch, count)
                               + .22 * shaped_note(pitch, count, True, .005, .04))
    if version == "chords":
        for start, end in zip(bars[:-1], bars[1:]):
            for pitch in chords[start]:
                lead[start:end] += .08 * shaped_note(pitch, end-start)
        return lead
    sides = np.zeros((len(lead), 2), dtype=np.float32)
    for start, end in zip(bars[:-1], bars[1:]):
        count = end-start
        for channel, detune in enumerate((.999, 1.001)):
            for pitch in chords[start]:
                sides[start:end, channel] += (.22 / 3) * shaped_note(pitch * detune, count, True, .04, .15)
        bass = .12 * shaped_note(chords[start, 0] / 4, count, True, .01, .10)
        sides[start:end] += bass[:, None]
    dry = sides + lead[:, None]
    signal = np.pad(dry, ((0, FS), (0, 0)))
    for delay, gain in ((.17, .16), (.29, .12), (.43, .08), (.61, .05)):
        offset = round(delay * FS)
        signal[offset:offset+len(dry)] += gain * dry[:, ::-1]
    peak = np.max(np.abs(signal))
    if peak > .95:
        signal *= .95 / peak
    return signal


def edge_fades(signal):
    """Fast 8 ms attack, 15 ms release for every saved/played version."""
    signal = signal.copy()
    for count, beginning in ((round(.008 * FS), True), (round(.015 * FS), False)):
        count = min(count, len(signal) // 2)
        ramp = np.linspace(0, 1, count, dtype=np.float32)
        if signal.ndim == 2:
            ramp = ramp[:, None]
        if beginning:
            signal[:count] *= ramp
        else:
            signal[-count:] *= ramp[::-1]
    return signal


def render(version="space", chord_share=None, chord_volume=.3):
    if version not in VERSIONS:
        raise ValueError(f"Unknown version: {version}")
    if chord_share is not None and (not np.isfinite(chord_share) or not 0 <= chord_share <= 1):
        raise ValueError("chord-share must be between 0 and 1")
    if not np.isfinite(chord_volume) or not 0 <= chord_volume <= 1:
        raise ValueError("chord-volume must be between 0 and 1")
    melody, chords, gate, boundaries, bars = score_arrays()
    share = (.5 if version == "switch" else .25) if chord_share is None else chord_share
    if version in ("space", "chords"):
        signal = arranged_audio(version, melody, chords, boundaries, bars)
    elif version == "summed":
        lead = cycle_square(melody, gate)
        chord_gate = np.ones_like(gate)
        accompaniment = sum(cycle_square(chords[:, i], chord_gate) for i in range(3)) / 3
        signal = (.45 / (1 + chord_volume)) * (lead + chord_volume * accompaniment)
    elif version in ("random", "packets"):
        packet = (4, 12) if version == "packets" else (1, 1)
        signal = cycle_square(melody, gate, .45, chords, share, packet)
    else:
        pair_position = np.arange(len(melody)) * 60 / FS
        pair_index = np.floor(pair_position).astype(np.int64)
        selected = (pair_position - pair_index) >= 1-share
        pitches = melody.copy()
        pitches[selected] = chords[np.flatnonzero(selected), pair_index[selected] % 3]
        signal = (cycle_square(pitches, gate, .45) if version == "full-cycles"
                  else switched_square(pitches))
    return edge_fades(signal)


def save_wav(path, signal):
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1 if signal.ndim == 1 else signal.shape[1])
        output.setsampwidth(2)
        output.setframerate(FS)
        output.writeframes((np.clip(signal, -1, 1) * 32767).astype("<i2").tobytes())


def play(signal, audio=None):
    # Nonblocking start + short polling avoids an uninterruptible native wait.
    if audio is None:
        import sounddevice as audio
    try:
        audio.play(signal, FS, blocking=False)
        import time
        while audio.get_stream().active:
            time.sleep(.05)
    except KeyboardInterrupt:
        print("\nPlayback interrupted. The complete WAV is already saved.")
        return False
    finally:
        audio.stop()
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", nargs="?", default="space", choices=[*VERSIONS, "all"],
                        help="Experiment to save and play (default: space); all plays the listening tour")
    parser.add_argument("--chord-share", type=float,
                        help="Time share for single-oscillator experiments (0-1)")
    parser.add_argument("--chord-volume", type=float, default=.3,
                        help="Chord-group amplitude relative to melody in summed (default .3)")
    args = parser.parse_args()
    if args.chord_share is not None and args.version in ("space", "chords", "summed"):
        parser.error("--chord-share applies to switch, less-chord, full-cycles, random and packets")
    try:
        for version in VERSIONS if args.version == "all" else [args.version]:
            print(f"Rendering {version}: {VERSIONS[version][1]}", flush=True)
            signal = render(version, args.chord_share, args.chord_volume)
            path = ROOT / VERSIONS[version][0]
            save_wav(path, signal)
            print(f"Saved {path.name}. Playing; press Ctrl-C to stop.", flush=True)
            if not play(signal):
                return 130
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")
    except ImportError:
        parser.exit(1, "Playback requires sounddevice. Run: python -m pip install -r requirements.txt\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
