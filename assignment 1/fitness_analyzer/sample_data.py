"""Sample scenarios used by the program and tests."""

from .data_generator import generate_fitness_data


GENERATED_SCENARIOS = {
    "resting": {"scenario": "resting", "seed": 7, "windows": 12},
    "moderate_activity": {"scenario": "moderate_activity", "seed": 3, "windows": 12},
    "high_activity": {"scenario": "high_activity", "seed": 5, "windows": 12},
    "recovery": {"scenario": "recovery", "seed": 42, "windows": 12},
    "poor_quality": {"scenario": "poor_quality", "seed": 1, "windows": 12},
}

EXPECTED_CATEGORY = {
    "resting": "resting",
    "moderate_activity": "moderate activity",
    "high_activity": "high activity",
    "recovery": "recovering",
    "poor_quality": "insufficient data",
    "empty": "insufficient data",
    "handcrafted_invalid": "insufficient data",
}


def load_generated(name, participant_id="P001"):
    """Return data for a generated scenario."""
    config = GENERATED_SCENARIOS[name]
    return generate_fitness_data(
        participant_id=participant_id,
        scenario=config["scenario"],
        seed=config["seed"],
        number_of_windows=config["windows"],
    )


def load_empty(participant_id="P900"):
    """Return a session with no observations."""
    profile = {
        "participant_id": participant_id,
        "baseline_heart_rate": 64,
        "baseline_skin_response": 1.8,
        "baseline_temperature": 32.4,
    }
    return profile, []


def load_handcrafted_invalid(participant_id="P901"):
    """Return a session containing invalid observations."""
    profile = {
        "participant_id": participant_id,
        "baseline_heart_rate": 66,
        "baseline_skin_response": 2.0,
        "baseline_temperature": 32.5,
    }
    observations = [
        {"timestamp": 0, "heart_rate": 70, "skin_response": 2.1,
         "temperature": 32.6, "activity_level": 0.12, "signal_quality": 0.95},
        {"timestamp": 1, "heart_rate": None, "skin_response": 2.0,
         "temperature": 32.5, "activity_level": 0.15, "signal_quality": 0.90},
        {"timestamp": 2, "heart_rate": 260, "skin_response": 2.2,
         "temperature": 32.7, "activity_level": 0.20, "signal_quality": 0.91},
        {"timestamp": 3, "heart_rate": 72, "skin_response": 2.1,
         "temperature": 32.6, "activity_level": -0.30, "signal_quality": 0.88},
        {"timestamp": 4, "heart_rate": 71, "skin_response": None,
         "temperature": 32.5, "activity_level": 0.14, "signal_quality": 0.92},
        {"timestamp": 5, "heart_rate": 69, "skin_response": 2.0,
         "temperature": 32.4, "activity_level": 0.13, "signal_quality": 0.20},
    ]
    return profile, observations


def all_scenarios():
    """Return all scenarios in display order."""
    scenarios = {}
    for name in GENERATED_SCENARIOS:
        scenarios[name] = load_generated(name)
    scenarios["empty"] = load_empty()
    scenarios["handcrafted_invalid"] = load_handcrafted_invalid()
    return scenarios
