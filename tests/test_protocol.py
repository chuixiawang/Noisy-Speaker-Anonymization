import tempfile
import unittest
from pathlib import Path

from casr.protocol import select_protocol


class ProtocolTests(unittest.TestCase):
    def test_protocol_builds_900_positive_and_negative_trials(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            speaker_lines = []
            for speaker_index in range(20):
                speaker = f"{speaker_index + 1}"
                gender = "M" if speaker_index < 10 else "F"
                speaker_lines.append(f"{speaker} | {gender} | test-clean | 1 | speaker-{speaker}\n")
                chapter = root / "test-clean" / speaker / "1"
                chapter.mkdir(parents=True)
                transcript_lines = []
                for utterance_index in range(10):
                    utterance_id = f"{speaker}-1-{utterance_index:04d}"
                    (chapter / f"{utterance_id}.flac").touch()
                    transcript_lines.append(f"{utterance_id} TEST UTTERANCE\n")
                (chapter / f"{speaker}-1.trans.txt").write_text("".join(transcript_lines))
            (root / "SPEAKERS.TXT").write_text("".join(speaker_lines))

            protocol = select_protocol(root, seed=2026)

        self.assertEqual(protocol["n_positive_trials"], 900)
        self.assertEqual(protocol["n_negative_trials"], 900)
        self.assertEqual(sum(len(rows) for rows in protocol["utterances"].values()), 200)


if __name__ == "__main__":
    unittest.main()
