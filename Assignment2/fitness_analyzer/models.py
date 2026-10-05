"""Domain classes carried forward from Assignment 1."""

import re


VALID_RANGES = {
    "heart_rate": (35, 205),
    "skin_response": (0.0, 60.0),
    "temperature": (25.0, 42.0),
    "activity_level": (0.0, 1.0),
    "signal_quality": (0.0, 1.0),
}

PHYSIOLOGICAL_FIELDS = (
    "heart_rate", "skin_response", "temperature", "activity_level", "signal_quality"
)

DEFAULT_SIGNAL_THRESHOLD = 0.5


def is_real_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return value == value


class Participant:
    """A participant and their personal reference measurements."""

    ID_PATTERN = re.compile(r"^P\d{3}$")

    def __init__(self, participant_id, name, baseline_heart_rate,
                 baseline_skin_response, baseline_temperature):
        if not isinstance(participant_id, str) or not self.ID_PATTERN.fullmatch(participant_id):
            raise ValueError("participant_id must match P followed by three digits")
        self.participant_id = participant_id
        self.name = name
        self._baseline_heart_rate = None
        self.baseline_heart_rate = baseline_heart_rate
        if not is_real_number(baseline_skin_response) or baseline_skin_response < 0:
            raise ValueError("baseline_skin_response must be a non-negative number")
        if not is_real_number(baseline_temperature) or not 25 <= baseline_temperature <= 42:
            raise ValueError("baseline_temperature must be between 25 and 42")
        self._baseline_skin_response = float(baseline_skin_response)
        self._baseline_temperature = float(baseline_temperature)

    @property
    def baseline_heart_rate(self):
        return self._baseline_heart_rate

    @baseline_heart_rate.setter
    def baseline_heart_rate(self, value):
        if not is_real_number(value) or not 30 <= value <= 220:
            raise ValueError("baseline_heart_rate must be between 30 and 220")
        self._baseline_heart_rate = int(value)

    @property
    def baseline_skin_response(self):
        return self._baseline_skin_response

    @property
    def baseline_temperature(self):
        return self._baseline_temperature


class Observation:
    """Base class for one sensor observation."""

    def __init__(self, timestamp, signal_quality):
        self.timestamp = timestamp
        self.signal_quality = signal_quality

    @staticmethod
    def in_range(value, low, high):
        return is_real_number(value) and low <= value <= high

    def validate(self):
        issues = []
        if not isinstance(self.timestamp, int) or isinstance(self.timestamp, bool) or self.timestamp < 0:
            issues.append("timestamp must be a non-negative integer")
        if not self.in_range(self.signal_quality, *VALID_RANGES["signal_quality"]):
            issues.append("signal_quality must be between 0 and 1")
        return issues

    def is_usable(self, signal_threshold=DEFAULT_SIGNAL_THRESHOLD):
        return not self.validate() and self.signal_quality >= signal_threshold


class FitnessObservation(Observation):
    """One fitness sensor window."""

    def __init__(self, timestamp, heart_rate, skin_response, temperature,
                 activity_level, signal_quality):
        super().__init__(timestamp, signal_quality)
        self.heart_rate = heart_rate
        self.skin_response = skin_response
        self.temperature = temperature
        self.activity_level = activity_level

    def validate(self):
        issues = super().validate()
        for field in ("heart_rate", "skin_response", "temperature", "activity_level"):
            value = getattr(self, field)
            low, high = VALID_RANGES[field]
            if not is_real_number(value):
                issues.append("%s must be a number" % field)
            elif not low <= value <= high:
                issues.append("%s must be between %s and %s" % (field, low, high))
        return issues


class Session:
    """A participant and all accepted observations for one session."""

    def __init__(self, session_id, participant, signal_threshold=DEFAULT_SIGNAL_THRESHOLD):
        if not isinstance(participant, Participant):
            raise TypeError("session requires a Participant")
        self.session_id = session_id
        self._participant = participant
        self._observations = []
        self.signal_threshold = signal_threshold

    @property
    def participant(self):
        return self._participant

    @property
    def observations(self):
        return tuple(self._observations)

    def add_observation(self, observation):
        if not isinstance(observation, FitnessObservation):
            raise TypeError("only FitnessObservation instances can be added")
        self._observations.append(observation)