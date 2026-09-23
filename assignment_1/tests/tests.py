import contextlib
import io
import unittest

from fitness_analyzer.analyzer import (
    Participant,
    Observation,
    FitnessObservation,
    Session,
    is_real_number,
    summarize,
    validate_raw_observation,
    classify_intensity,
    detect_recovery,
    compare_to_baseline,
)
from fitness_analyzer import sample_data
import main


class TestStandaloneFunctions(unittest.TestCase):
    def test_is_real_number_rejects_bool_and_none(self):
        self.assertTrue(is_real_number(3))
        self.assertTrue(is_real_number(3.5))
        self.assertFalse(is_real_number(True))
        self.assertFalse(is_real_number(None))
        self.assertFalse(is_real_number("5"))

    def test_summarize_normal(self):
        result = summarize([10, 20, 30])
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["average"], 20.0)
        self.assertEqual(result["minimum"], 10)
        self.assertEqual(result["maximum"], 30)

    def test_summarize_ignores_non_numbers(self):
        result = summarize([10, None, "x", 30, True])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["minimum"], 10)
        self.assertEqual(result["maximum"], 30)

    def test_summarize_empty(self):
        result = summarize([None, None])
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["average"])

    def test_validate_raw_observation_flags_problems(self):
        bad = {"timestamp": 0, "heart_rate": None, "skin_response": 2.0,
               "temperature": 32.5, "activity_level": -0.3, "signal_quality": 0.9}
        issues = validate_raw_observation(bad)
        self.assertTrue(any("heart_rate" in i for i in issues))
        self.assertTrue(any("activity_level" in i for i in issues))

    def test_classify_intensity_boundaries(self):
        self.assertEqual(classify_intensity(0.10, 2), "resting")
        self.assertEqual(classify_intensity(0.50, 28), "moderate activity")
        self.assertEqual(classify_intensity(0.80, 58), "high activity")


class TestParticipantEncapsulation(unittest.TestCase):
    def test_valid_participant(self):
        p = Participant("P1", 65, 2.0, 32.5)
        self.assertEqual(p.baseline_heart_rate, 65)

    def test_property_rejects_impossible_baseline(self):
        with self.assertRaises(ValueError):
            Participant("P1", 500, 2.0, 32.5)
        p = Participant("P1", 65, 2.0, 32.5)
        with self.assertRaises(ValueError):
            p.baseline_heart_rate = 5

    def test_from_profile_classmethod(self):
        profile = {"participant_id": "P9", "baseline_heart_rate": 70,
                   "baseline_skin_response": 1.5, "baseline_temperature": 32.0}
        p = Participant.from_profile(profile)
        self.assertEqual(p.participant_id, "P9")
        self.assertEqual(p.baseline_heart_rate, 70)

    def test_from_profile_rejects_missing_keys(self):
        with self.assertRaises(KeyError):
            Participant.from_profile({"participant_id": "P1"})
        with self.assertRaises(TypeError):
            Participant.from_profile("not a dict")


class TestObservationInheritance(unittest.TestCase):
    def test_subclass_relationship(self):
        obs = FitnessObservation(0, 70, 2.0, 32.5, 0.2, 0.9)
        self.assertIsInstance(obs, Observation)

    def test_override_adds_physiological_checks(self):
        base = Observation(0, 0.9)
        self.assertEqual(base.validate(), [])
        obs = FitnessObservation(0, None, 2.0, 32.5, 0.2, 0.9)
        issues = obs.validate()
        self.assertTrue(any("heart_rate" in i for i in issues))

    def test_is_usable_respects_signal_threshold(self):
        good = FitnessObservation(0, 70, 2.0, 32.5, 0.2, 0.9)
        weak = FitnessObservation(1, 70, 2.0, 32.5, 0.2, 0.3)
        self.assertTrue(good.is_usable())
        self.assertFalse(weak.is_usable())

    def test_impossible_values_rejected(self):
        obs = FitnessObservation(0, 260, 2.0, 32.5, -0.3, 0.9)
        issues = obs.validate()
        self.assertTrue(any("heart_rate" in i for i in issues))
        self.assertTrue(any("activity_level" in i for i in issues))


class TestSessionComposition(unittest.TestCase):
    def test_session_owns_participant_and_observations(self):
        profile, observations = sample_data.load_generated("resting")
        session = Session.from_generated(profile, observations)
        self.assertIsInstance(session.participant, Participant)
        self.assertEqual(len(session.observations), len(observations))

    def test_usable_and_flagged_partition_all_windows(self):
        profile, observations = sample_data.load_handcrafted_invalid()
        session = Session.from_generated(profile, observations)
        usable = len(session.usable_observations())
        flagged = len(session.flagged_observations())
        self.assertEqual(usable + flagged, len(session.observations))

    def test_add_observation_type_checked(self):
        p = Participant("P1", 65, 2.0, 32.5)
        session = Session(p)
        with self.assertRaises(TypeError):
            session.add_observation({"not": "an observation"})


class TestStructuredResult(unittest.TestCase):
    def test_result_is_dict_with_required_keys(self):
        profile, observations = sample_data.load_generated("moderate_activity")
        result = Session.from_generated(profile, observations).analyze()
        self.assertIsInstance(result, dict)
        for key in (
            "participant_id", "windows_total", "windows_usable", "windows_flagged",
            "summaries", "comparison", "recovery", "classification", "flagged_details",
        ):
            self.assertIn(key, result)

    def test_summaries_have_avg_min_max(self):
        profile, observations = sample_data.load_generated("high_activity")
        result = Session.from_generated(profile, observations).analyze()
        hr = result["summaries"]["heart_rate"]
        self.assertGreater(hr["count"], 0)
        self.assertLessEqual(hr["minimum"], hr["average"])
        self.assertLessEqual(hr["average"], hr["maximum"])


class TestClassificationScenarios(unittest.TestCase):
    def test_generated_scenarios_classify_as_expected(self):
        for name in sample_data.GENERATED_SCENARIOS:
            profile, observations = sample_data.load_generated(name)
            result = Session.from_generated(profile, observations).analyze()
            self.assertEqual(
                result["classification"]["category"],
                sample_data.EXPECTED_CATEGORY[name],
                msg="scenario %s misclassified as %s"
                    % (name, result["classification"]["category"]),
            )

    def test_generated_scenarios_robust_across_seeds(self):
        from fitness_analyzer.data_generator import generate_fitness_data
        checks = {
            "resting": "resting",
            "moderate_activity": "moderate activity",
            "high_activity": "high activity",
            "recovery": "recovering",
            "poor_quality": "insufficient data",
        }
        for scenario, expected in checks.items():
            for seed in (1, 3, 5, 7, 42, 99, 123):
                profile, observations = generate_fitness_data(
                    "P001", scenario, seed, 12)
                result = Session.from_generated(profile, observations).analyze()
                self.assertEqual(
                    result["classification"]["category"], expected,
                    msg="%s seed=%d -> %s"
                        % (scenario, seed, result["classification"]["category"]),
                )

    def test_recovery_detected_for_recovery_only(self):
        profile, observations = sample_data.load_generated("recovery")
        recovery = Session.from_generated(profile, observations).analyze()["recovery"]
        self.assertTrue(recovery["detected"])

        profile, observations = sample_data.load_generated("high_activity")
        recovery = Session.from_generated(profile, observations).analyze()["recovery"]
        self.assertFalse(recovery["detected"])

    def test_empty_session_is_insufficient(self):
        profile, observations = sample_data.load_empty()
        result = Session.from_generated(profile, observations).analyze()
        self.assertEqual(result["classification"]["category"], "insufficient data")
        self.assertEqual(result["windows_usable"], 0)


class TestReportingAndComparison(unittest.TestCase):
    def test_compare_to_baseline_direction_words(self):
        summaries = {
            "heart_rate": {"average": 120},
            "skin_response": {"average": 2.0},
            "temperature": {"average": 31.0},
        }
        participant = Participant("P1", 60, 2.0, 32.0)
        comparison = compare_to_baseline(summaries, participant)
        self.assertEqual(comparison["heart_rate"]["direction"], "above")
        self.assertEqual(comparison["skin_response"]["direction"], "equal to")
        self.assertEqual(comparison["temperature"]["direction"], "below")

    def test_compare_skips_fields_without_data(self):
        summaries = {
            "heart_rate": {"average": None},
            "skin_response": {"average": 2.0},
            "temperature": {"average": 32.0},
        }
        participant = Participant("P1", 60, 2.0, 32.0)
        comparison = compare_to_baseline(summaries, participant)
        self.assertNotIn("heart_rate", comparison)

    def test_main_runs_without_error(self):
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                main.main()
        except Exception as exc:
            self.fail("main.main() raised: %r" % exc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
