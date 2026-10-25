"""Checks for the audio contracts that matter to the listening experiments."""

import contextlib
import io
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import wave

import numpy as np

import square_wave_lab as lab


class SynthesisTests(unittest.TestCase):
    def test_gallery_boundaries_and_wav_format(self):
        for version in lab.VERSIONS:
            with self.subTest(version=version):
                signal = lab.render(version)
                self.assertTrue(np.isfinite(signal).all())
                self.assertLessEqual(float(np.max(np.abs(signal))), 1)
                np.testing.assert_array_equal(signal[0], np.zeros_like(signal[0]))
                np.testing.assert_array_equal(signal[-1], np.zeros_like(signal[-1]))
                self.assertLessEqual(float(np.max(np.abs(signal[:20]))), .06)
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "test.wav"
                    lab.save_wav(path, signal)
                    with wave.open(str(path)) as recording:
                        self.assertEqual(recording.getnchannels(), 2 if version == "space" else 1)
                        self.assertEqual(recording.getframerate(), lab.FS)
                        self.assertEqual(recording.getsampwidth(), 2)
                        self.assertEqual(recording.getnframes(), (33 if version == "space" else 32) * lab.FS)

    def test_full_cycle_survives_midcycle_pitch_request(self):
        pitches = np.full(600, lab.FS / 100)
        pitches[30:] = lab.FS / 80
        signal = lab.cycle_square(pitches, np.ones(600, dtype=bool))
        np.testing.assert_array_equal(signal[:50], np.ones(50))
        np.testing.assert_array_equal(signal[50:100], -np.ones(50))
        np.testing.assert_array_equal(signal[100:140], np.ones(40))
        np.testing.assert_array_equal(signal[140:180], -np.ones(40))

    def test_random_is_repeatable_and_zero_share_is_melody(self):
        pitches = np.full(50000, 330.)
        chords = np.tile([262., 392., 523.], (len(pitches), 1))
        gate = np.ones(len(pitches), dtype=bool)
        a = lab.cycle_square(pitches, gate, chords=chords, packet=(4, 12))
        b = lab.cycle_square(pitches, gate, chords=chords, packet=(4, 12))
        np.testing.assert_array_equal(a, b)
        np.testing.assert_array_equal(lab.cycle_square(pitches, gate, chords=chords, share=0),
                                      lab.cycle_square(pitches, gate))

    def test_summed_has_real_additive_chord_gain(self):
        melody = lab.render("summed", chord_volume=0)
        a, b = lab.render("summed", chord_volume=.3), lab.render("summed", chord_volume=.6)
        np.testing.assert_allclose((1.3*a-melody)/.3, (1.6*b-melody)/.6, atol=1e-6)


class PlaybackTests(unittest.TestCase):
    def test_tour_saves_before_playing_and_ctrl_c_ends_tour(self):
        events = []
        with patch("sys.argv", ["square_wave_lab.py", "all"]), \
                patch.object(lab, "render", return_value=np.zeros(100)), \
                patch.object(lab, "save_wav", side_effect=lambda *args: events.append("save")), \
                patch.object(lab, "play", side_effect=lambda *args: events.append("play") or False), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lab.main(), 130)
        self.assertEqual(events, ["save", "play"])

    def test_ctrl_c_stops_device_and_exits_playback(self):
        audio = Mock()
        audio.get_stream.side_effect = KeyboardInterrupt
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(lab.play(np.zeros(100), audio))
        audio.play.assert_called_once()
        audio.stop.assert_called_once()

    def test_device_stops_on_success_and_on_error(self):
        audio = Mock()
        audio.get_stream.return_value.active = False
        self.assertTrue(lab.play(np.zeros(100), audio))
        audio.stop.assert_called_once()
        audio = Mock()
        audio.play.side_effect = RuntimeError("Device unavailable")
        with self.assertRaises(RuntimeError):
            lab.play(np.zeros(100), audio)
        audio.stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
