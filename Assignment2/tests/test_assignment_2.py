import csv
import tempfile
import unittest
from pathlib import Path

from fitness_analyzer.analysis import analyze_session
from fitness_analyzer.csv_loader import load_profiles, load_sessions
from fitness_analyzer.exceptions import InputFileError
from fitness_analyzer.models import FitnessObservation


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Assignment_II_Pack" / "data" / "option_a_fitness"


class TestOfficialFitnessFiles(unittest.TestCase):
    def test_valid_file_produces_five_sessions(self):
        participants, profile_rejections = load_profiles(DATA / "participants.csv")
        sessions, rejections = load_sessions(DATA / "fitness_sessions.csv", participants)
        self.assertEqual(set(participants), {"P001", "P002", "P003"})
        self.assertEqual(len(profile_rejections), 0)
        self.assertEqual(len(sessions), 5)
        self.assertEqual(sum(len(session.observations) for session in sessions), 24)
        self.assertEqual(len(rejections), 5)

    def test_analysis_keeps_assignment_one_categories(self):
        participants, _ = load_profiles(DATA / "participants.csv")
        sessions, _ = load_sessions(DATA / "fitness_sessions.csv", participants)
        categories = [analyze_session(session)["classification"]["category"] for session in sessions]
        self.assertEqual(categories, [
            "resting", "moderate activity", "high activity", "recovering", "insufficient data",
        ])

    def test_invalid_file_continues_and_records_context(self):
        participants, _ = load_profiles(DATA / "participants.csv")
        sessions, rejected = load_sessions(DATA / "fitness_sessions_invalid.csv", participants)
        self.assertEqual({session.session_id for session in sessions}, {"FIT-2026-101", "FIT-2026-102"})
        self.assertEqual(len(rejected), 10)
        self.assertTrue(all(item["source"] == "fitness_sessions_invalid.csv" for item in rejected))
        self.assertTrue(any(item["field"] == "session_id" for item in rejected))


class TestValidationBoundaries(unittest.TestCase):
    def test_inclusive_measurement_boundaries_are_valid(self):
        observation = FitnessObservation(0, 35, 0, 25, 0, 0.5)
        self.assertEqual(observation.validate(), [])
        self.assertTrue(observation.is_usable())

    def test_invalid_identifier_and_missing_file_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profiles.csv"
            path.write_text(
                "participant_id,name,baseline_heart_rate,baseline_skin_response,baseline_temperature\n"
                "P01,Amina,68,1.2,32.4\n", encoding="utf-8")
            participants, rejected = load_profiles(path)
            self.assertEqual(participants, {})
            self.assertEqual(rejected[0]["field"], "participant_id")
        with self.assertRaises(InputFileError):
            load_profiles(Path("does-not-exist.csv"))


class TestOutputContract(unittest.TestCase):
    def test_official_headers_are_not_changed(self):
        with (DATA / "fitness_sessions.csv").open(encoding="utf-8", newline="") as handle:
            self.assertEqual(next(csv.reader(handle)), [
                "session_id", "participant_id", "timestamp", "heart_rate",
                "skin_response", "temperature", "activity_level", "signal_quality",
            ])


if __name__ == "__main__":
    unittest.main(verbosity=2)