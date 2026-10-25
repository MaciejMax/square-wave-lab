"""Rebuild the listening examples and their beginner-friendly diagrams."""

from html import escape
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np

from square_wave_lab import VERSIONS, render, save_wav


COLORS = ("#2563eb", "#c46510", "#9154c8", "#148260")
INK = "#182a43"
LABELS = ("Melody: E4", "Chord note 1: C4", "Chord note 2: E4", "Chord note 3: G4")


def text(x, y, value, size=18, color=INK, bold=False):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{700 if bold else 400}">{escape(value)}</text>')


def rect(x, y, w, h, color, radius=5, opacity=1):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
            f'fill="{color}" opacity="{opacity}"/>')


def document(height, title, description, content):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" '
            f'viewBox="0 0 1000 {height}" role="img" aria-labelledby="title description">'
            f'<title id="title">{escape(title)}</title><desc id="description">{escape(description)}</desc>'
            '<g font-family="Segoe UI, Arial, sans-serif">'
            + rect(0, 0, 1000, height, "#f1f5fa", 0) + ''.join(content) + '</g></svg>')


def four_parts():
    content = [text(32, 42, "One tune + three chord notes = four parts", 28, bold=True),
               text(32, 76, "At the beginning, the tune plays E while the chord is C + E + G."),
               text(42, 116, "THE MELODY", 16, bold=True),
               text(350, 116, "THE CHORD: THREE NOTES TOGETHER", 16, bold=True)]
    boxes = ((40, 250, "E4", "The tune", 0), (350, 175, "C4", "Chord note 1", 1),
             (555, 175, "E4", "Chord note 2", 2), (760, 175, "G4", "Chord note 3", 3))
    for x, width, note, label, index in boxes:
        content += [rect(x, 132, width, 100, COLORS[index]),
                    text(x+18, 174, note, 32, "white", True),
                    text(x+18, 210, label, 17, "white")]
    content += [text(310, 190, "+", 30),
                text(40, 270, "E appears twice here: once in the tune, and once as part of the chord.", 18)]
    return document(300, "Meet the four parts", "Blue melody E4 plus three chord notes: orange C4, purple E4, green G4.", content)


def intervals(version):
    """Illustrative schedules: one active lane at a time in shared modes."""
    if version in ("space", "chords", "summed"):
        return [(i, 0., 1.) for i in range(4)]
    result, position = [], 0.
    if version == "packets":
        # Show all four players in this short teaching example.
        for lane, duration in [(0, .14), (1, .08), (0, .20), (3, .06),
                               (0, .16), (2, .09), (0, .17), (1, .10)]:
            result.append((lane, position, position + duration))
            position += duration
        return result
    if version == "switch":
        for i in range(24):
            lane = 0 if i % 2 == 0 else (i // 2) % 3 + 1
            result.append((lane, i/24, (i+1)/24))
    elif version in ("less-chord", "full-cycles"):
        # Full cycles wait a little longer or shorter for a safe wave boundary.
        for i in range(9):
            split = .75 if version == "less-chord" else (.72, .79, .74)[i % 3]
            result += [(0, i/9, (i+split)/9), ((i % 3)+1, (i+split)/9, (i+1)/9)]
    else:
        rng = np.random.default_rng(42)
        while position < 1:
            lane = int(rng.choice(4, p=[.65, .12, .12, .11]))
            duration = float(rng.uniform(.012, .026))
            result.append((lane, position, min(1., position+duration)))
            position += duration
    return result


def journey():
    cards = [
        ("space", "Start here: SPACE", "Give the four parts softer sounds, then add bass and echoes.",
         "All parts play together. Echoes make the sound feel wider."),
        ("chords", "1. CHORDS: everyone plays", "Four square-wave sounds at once. A plain, loud starting point.",
         "Four filled rows = four notes sounding together."),
        ("switch", "2. SWITCH: take turns", "One generator: tune, chord note, tune, next chord note...",
         "The tune gets 50% of the time. The repeating pattern can buzz."),
        ("less-chord", "3. LESS CHORD: more time for the tune", "Keep taking turns, but shorten the chord notes' turns.",
         "The tune gets 75% of the time; the whole chord shares 25%."),
        ("full-cycles", "4. FULL CYCLES: finish each wave", "Same idea, but wait for the whole high/low wave before switching.",
         "A turn can move a little to avoid cutting a wave in half."),
        ("random", "5. RANDOM: draw after every wave", "Pick the next part by chance. No repeating turn order.",
         "Lots of tiny, uneven turns can sound like crackling."),
        ("packets", "6. PACKETS: stay a little longer", "Draw a part, let it play 4-12 complete waves, then draw again.",
         "Longer turns give the ear more time to recognize each note."),
        ("summed", "7. SUMMED: four generators", "Give each part its own square-wave generator. Add their sounds.",
         "Everyone plays together again, with a quieter chord behind the tune."),
    ]
    content = [text(32, 43, "Who is playing right now?", 30, bold=True),
               text(32, 76, "Read left to right. Colored = playing. Blank = waiting."),
               text(32, 105, "Same four parts in every example; extra bass and echoes in Space.", 17)]
    for card_index, (version, title, subtitle, footer) in enumerate(cards):
        y = 130 + card_index * 315
        content += [rect(16, y, 968, 300, "white", 12), text(36, y+35, title, 24, bold=True),
                    text(36, y+64, subtitle, 17)]
        for lane, label in enumerate(LABELS):
            yy = y+85+lane*29
            content += [text(36, yy+18, label, 17, COLORS[lane], True),
                        rect(230, yy, 715, 23, "#edf1f6", 3)]
        for lane, start, end in intervals(version):
            opacity = .55 if version == "summed" and lane else 1.
            width = max(1, (end-start)*715 - (1 if version not in ("space", "chords", "summed") else 0))
            content.append(rect(230+start*715, y+85+lane*29, width, 23, COLORS[lane], 2, opacity))
        content += [text(230, y+224, "TIME", 13),
                    f'<path d="M280 {y+220} H940 l-8 -4 m8 4 l-8 4" fill="none" stroke="#64748b"/>',
                    text(36, y+253, footer, 17)]
        if version == "full-cycles":
            # Two complete periods, with a shared rising edge between them.
            content += [text(36, y+282, "One complete wave:", 15),
                        '<path d="M230 %d v-12 h35 v24 h35 v-24 h25 v24 h25" stroke="#2563eb" fill="none" stroke-width="2"/>' % (y+277),
                        text(370, y+282, "Change note at the next rising edge.", 15)]
        elif version == "space":
            content += [text(36, y+282, "Also playing: a low bass. Echoes repeat the sound softly on the left and right.", 15)]
        elif version == "summed":
            content += [text(36, y+282, "Paler chord strips mean lower volume, not less playing time.", 15)]
    content.append(text(32, 130+315*8+15, "Illustrated rules, not measured waveforms. Row colors identify parts, not loudness (except where noted).", 15))
    return document(130+315*8+40, "Eight ways to play four parts", "Eight timelines contrast simultaneous parts, regular turns, complete cycles, random turns, and longer random packets.", content)


def main():
    for version, (filename, _) in VERSIONS.items():
        save_wav(ROOT / filename, render(version))
        print(f"Built {filename}", flush=True)
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "four_parts.svg").write_text(four_parts(), encoding="utf-8")
    (docs / "listening_journey.svg").write_text(journey(), encoding="utf-8")


if __name__ == "__main__":
    main()
