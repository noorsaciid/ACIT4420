"""Classes and functions for analysing fitness sessions."""

import statistics


VALID_RANGES = {
    "heart_rate": (35, 205),
    "skin_response": (0.0, 60.0),
    "temperature": (25.0, 42.0),
    "activity_level": (0.0, 1.0),
    "signal_quality": (0.0, 1.0),
}

PHYSIOLOGICAL_FIELDS = (
    "heart_rate",
    "skin_response",
    "temperature",
    "activity_level",
    "signal_quality",
)

DEFAULT_SIGNAL_THRESHOLD = 0.5

RESTING_MAX_ACTIVITY = 0.25
RESTING_MAX_HR_ELEVATION = 12
MODERATE_MAX_ACTIVITY = 0.67
MODERATE_MAX_HR_ELEVATION = 45

RECOVERY_MIN_START_ELEVATION = 15
RECOVERY_MIN_HR_DROP = 12
RECOVERY_MIN_ACTIVITY_DROP = 0.10

def is_real_number(value):
    """Return whether value is a usable number."""
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return value == value


def summarize(values):
    """Return count, average, minimum, and maximum for numeric values."""
    numbers = [v for v in values if is_real_number(v)]
    if not numbers:
        return {"count": 0, "average": None, "minimum": None, "maximum": None}
    return {
        "count": len(numbers),
        "average": round(statistics.mean(numbers), 2),
        "minimum": min(numbers),
        "maximum": max(numbers),
    }


def validate_raw_observation(raw):
    """Return validation issues for a raw observation dictionary."""
    if not isinstance(raw, dict):
        return ["observation is not a dictionary"]
    return FitnessObservation.from_raw(raw).validate()


def classify_intensity(mean_activity, hr_elevation):
    """Classify activity using movement and heart-rate elevation."""
    if mean_activity < RESTING_MAX_ACTIVITY and hr_elevation < RESTING_MAX_HR_ELEVATION:
        return "resting"
    if mean_activity < MODERATE_MAX_ACTIVITY and hr_elevation < MODERATE_MAX_HR_ELEVATION:
        return "moderate activity"
    return "high activity"


def detect_recovery(usable_observations, baseline_heart_rate):
    """Check whether heart rate and activity decline toward the end."""
    ordered = sorted(usable_observations, key=lambda obs: obs.timestamp)
    if len(ordered) < 6:
        return {
            "detected": False,
            "explanation": "Not enough usable windows to assess recovery.",
        }

    third = max(1, len(ordered) // 3)
    first, last = ordered[:third], ordered[-third:]

    first_hr = statistics.mean(obs.heart_rate for obs in first)
    last_hr = statistics.mean(obs.heart_rate for obs in last)
    first_activity = statistics.mean(obs.activity_level for obs in first)
    last_activity = statistics.mean(obs.activity_level for obs in last)

    hr_drop = first_hr - last_hr
    activity_drop = first_activity - last_activity
    start_elevation = first_hr - baseline_heart_rate

    detected = (
        start_elevation >= RECOVERY_MIN_START_ELEVATION
        and hr_drop >= RECOVERY_MIN_HR_DROP
        and activity_drop >= RECOVERY_MIN_ACTIVITY_DROP
    )

    if detected:
        explanation = (
            "Heart rate fell %.0f bpm and activity fell %.2f from the start of the "
            "session to the end, returning toward the personal baseline."
            % (hr_drop, activity_drop)
        )
    else:
        explanation = (
            "No clear decline near the end (heart-rate change %.0f bpm, "
            "activity change %.2f)." % (hr_drop, activity_drop)
        )

    return {
        "detected": detected,
        "explanation": explanation,
        "heart_rate_drop": round(hr_drop, 1),
        "activity_drop": round(activity_drop, 2),
        "start_elevation": round(start_elevation, 1),
        "end_elevation": round(last_hr - baseline_heart_rate, 1),
    }


def classify_session(usable_observations, total_windows, participant, recovery):
    """Return the session classification and explanation."""
    usable_count = len(usable_observations)

    if total_windows == 0 or usable_count < 3 or usable_count < total_windows / 2:
        return {
            "category": "insufficient data",
            "explanation": (
                "Only %d of %d windows were usable, which is too few to classify "
                "the session reliably." % (usable_count, total_windows)
            ),
        }

    mean_hr = statistics.mean(obs.heart_rate for obs in usable_observations)
    mean_activity = statistics.mean(obs.activity_level for obs in usable_observations)
    hr_elevation = mean_hr - participant.baseline_heart_rate

    if recovery["detected"]:
        return {
            "category": "recovering",
            "explanation": "Classified as recovering. " + recovery["explanation"],
            "mean_activity": round(mean_activity, 2),
            "heart_rate_elevation": round(hr_elevation, 1),
        }

    category = classify_intensity(mean_activity, hr_elevation)
    explanation = (
        "Average activity was %.2f and average heart rate was %.0f bpm "
        "(%+.0f bpm relative to the %d bpm baseline), which matches '%s'."
        % (
            mean_activity,
            mean_hr,
            hr_elevation,
            participant.baseline_heart_rate,
            category,
        )
    )
    return {
        "category": category,
        "explanation": explanation,
        "mean_activity": round(mean_activity, 2),
        "heart_rate_elevation": round(hr_elevation, 1),
    }


def compare_to_baseline(summaries, participant):
    """Compare session averages with participant baseline values."""
    comparison = {}
    baseline_by_field = {
        "heart_rate": participant.baseline_heart_rate,
        "skin_response": participant.baseline_skin_response,
        "temperature": participant.baseline_temperature,
    }

    for field, baseline in baseline_by_field.items():
        session_average = summaries.get(field, {}).get("average")
        if session_average is None:
            continue
        difference = session_average - baseline
        if difference > 0:
            direction = "above"
        elif difference < 0:
            direction = "below"
        else:
            direction = "equal to"
        comparison[field] = {
            "session_average": session_average,
            "baseline": round(baseline, 2),
            "difference": round(difference, 2),
            "direction": direction,
        }
    return comparison


def format_report(result):
    """Format an analysis result for the console."""
    lines = []
    lines.append("=" * 60)
    lines.append("SESSION REPORT - participant %s" % result["participant_id"])
    lines.append("=" * 60)

    lines.append(
        "Windows: %d total, %d usable, %d flagged"
        % (result["windows_total"], result["windows_usable"], result["windows_flagged"])
    )

    classification = result["classification"]
    lines.append("Classification: %s" % classification["category"].upper())
    lines.append("  %s" % classification["explanation"])

    recovery = result["recovery"]
    lines.append("Recovery detected: %s" % ("yes" if recovery["detected"] else "no"))
    lines.append("  %s" % recovery["explanation"])

    lines.append("-" * 60)
    lines.append("Summaries (usable windows only):")
    for field in PHYSIOLOGICAL_FIELDS:
        stats = result["summaries"][field]
        if stats["count"] == 0:
            lines.append("  %-15s no usable values" % field)
        else:
            lines.append(
                "  %-15s avg=%-7s min=%-7s max=%-7s (n=%d)"
                % (field, stats["average"], stats["minimum"], stats["maximum"], stats["count"])
            )

    if result["comparison"]:
        lines.append("-" * 60)
        lines.append("Comparison with personal baseline:")
        for field, info in result["comparison"].items():
            lines.append(
                "  %-15s %s vs baseline %s (%+.2f, %s baseline)"
                % (field, info["session_average"], info["baseline"], info["difference"], info["direction"])
            )

    if result["flagged_details"]:
        lines.append("-" * 60)
        lines.append("Flagged windows:")
        for item in result["flagged_details"]:
            lines.append("  timestamp %s: %s" % (item["timestamp"], "; ".join(item["reasons"])))

    lines.append("=" * 60)
    return "\n".join(lines)


class Participant:
    """A participant and their baseline measurements."""

    def __init__(
        self,
        participant_id,
        baseline_heart_rate,
        baseline_skin_response,
        baseline_temperature,
    ):
        if not isinstance(participant_id, str) or not participant_id.strip():
            raise ValueError("participant_id must be a non-empty string")
        self.participant_id = participant_id.strip()

        self._baseline_heart_rate = None
        self.baseline_heart_rate = baseline_heart_rate

        if not is_real_number(baseline_skin_response) or baseline_skin_response < 0:
            raise ValueError("baseline_skin_response must be a number >= 0")
        if not is_real_number(baseline_temperature):
            raise ValueError("baseline_temperature must be a number")
        self._baseline_skin_response = float(baseline_skin_response)
        self._baseline_temperature = float(baseline_temperature)

    @property
    def baseline_heart_rate(self):
        """Return the validated baseline heart rate."""
        return self._baseline_heart_rate

    @baseline_heart_rate.setter
    def baseline_heart_rate(self, value):
        if not is_real_number(value) or not (30 <= value <= 220):
            raise ValueError("baseline_heart_rate must be a plausible resting HR (30-220 bpm)")
        self._baseline_heart_rate = int(value)

    @property
    def baseline_skin_response(self):
        return self._baseline_skin_response

    @property
    def baseline_temperature(self):
        return self._baseline_temperature

    @classmethod
    def from_profile(cls, profile):
        """Build a participant from a profile dictionary."""
        if not isinstance(profile, dict):
            raise TypeError("profile must be a dictionary")
        required = (
            "participant_id",
            "baseline_heart_rate",
            "baseline_skin_response",
            "baseline_temperature",
        )
        missing = [key for key in required if key not in profile]
        if missing:
            raise KeyError("profile is missing required keys: " + ", ".join(missing))
        return cls(
            participant_id=profile["participant_id"],
            baseline_heart_rate=profile["baseline_heart_rate"],
            baseline_skin_response=profile["baseline_skin_response"],
            baseline_temperature=profile["baseline_temperature"],
        )

    def __repr__(self):
        return "Participant(%r, baseline_hr=%d)" % (
            self.participant_id,
            self._baseline_heart_rate,
        )


class Observation:
    """Base class for one sensor observation."""

    def __init__(self, timestamp, signal_quality):
        self.timestamp = timestamp
        self.signal_quality = signal_quality

    @staticmethod
    def in_range(value, low, high):
        """Return whether value is within an inclusive range."""
        return is_real_number(value) and low <= value <= high

    def validate(self):
        """Return validation issues for common fields."""
        issues = []
        if not isinstance(self.timestamp, int) or isinstance(self.timestamp, bool) or self.timestamp < 0:
            issues.append("timestamp must be an integer >= 0")
        if not self.in_range(self.signal_quality, *VALID_RANGES["signal_quality"]):
            issues.append("signal_quality missing or outside 0-1")
        return issues

    def is_usable(self, signal_threshold=DEFAULT_SIGNAL_THRESHOLD):
        """Return whether the observation is valid and reliable."""
        return not self.validate() and self.signal_quality >= signal_threshold


class FitnessObservation(Observation):
    """A sensor observation with fitness measurements."""

    def __init__(
        self,
        timestamp,
        heart_rate,
        skin_response,
        temperature,
        activity_level,
        signal_quality,
    ):
        super().__init__(timestamp, signal_quality)
        self.heart_rate = heart_rate
        self.skin_response = skin_response
        self.temperature = temperature
        self.activity_level = activity_level

    def validate(self):
        """Return validation issues for all observation fields."""
        issues = super().validate()
        for field in ("heart_rate", "skin_response", "temperature", "activity_level"):
            value = getattr(self, field)
            low, high = VALID_RANGES[field]
            if value is None:
                issues.append("%s is missing (None)" % field)
            elif not is_real_number(value):
                issues.append("%s is not a number" % field)
            elif not (low <= value <= high):
                issues.append(
                    "%s value %s is outside the valid range %s-%s" % (field, value, low, high)
                )
        return issues

    @classmethod
    def from_raw(cls, raw):
        """Build an observation from a raw dictionary."""
        return cls(
            timestamp=raw.get("timestamp"),
            heart_rate=raw.get("heart_rate"),
            skin_response=raw.get("skin_response"),
            temperature=raw.get("temperature"),
            activity_level=raw.get("activity_level"),
            signal_quality=raw.get("signal_quality"),
        )

    def __repr__(self):
        return "FitnessObservation(t=%s, hr=%s, activity=%s, signal=%s)" % (
            self.timestamp,
            self.heart_rate,
            self.activity_level,
            self.signal_quality,
        )


class Session:
    """A participant and their fitness observations."""

    def __init__(self, participant, signal_threshold=DEFAULT_SIGNAL_THRESHOLD):
        if not isinstance(participant, Participant):
            raise TypeError("session requires a Participant instance")
        self._participant = participant
        self._observations = []
        self.signal_threshold = signal_threshold

    @property
    def participant(self):
        return self._participant

    @property
    def observations(self):
        """Return the observations as a tuple."""
        return tuple(self._observations)

    def add_observation(self, observation):
        if not isinstance(observation, FitnessObservation):
            raise TypeError("only FitnessObservation instances can be added")
        self._observations.append(observation)

    @classmethod
    def from_generated(cls, profile, raw_observations, signal_threshold=DEFAULT_SIGNAL_THRESHOLD):
        """Build a session from generated data."""
        session = cls(Participant.from_profile(profile), signal_threshold)
        for raw in raw_observations:
            session.add_observation(FitnessObservation.from_raw(raw))
        return session

    def usable_observations(self):
        """Return observations that pass validation."""
        return [obs for obs in self._observations if obs.is_usable(self.signal_threshold)]

    def flagged_observations(self):
        """Return timestamps and reasons for flagged observations."""
        flagged = []
        for obs in self._observations:
            reasons = obs.validate()
            if not reasons and obs.signal_quality < self.signal_threshold:
                reasons = [
                    "signal_quality %s below usable threshold %s"
                    % (obs.signal_quality, self.signal_threshold)
                ]
            if reasons:
                flagged.append({"timestamp": obs.timestamp, "reasons": reasons})
        return flagged

    def summaries(self, usable=None):
        """Return summaries for usable observations."""
        if usable is None:
            usable = self.usable_observations()
        return {
            field: summarize([getattr(obs, field) for obs in usable])
            for field in PHYSIOLOGICAL_FIELDS
        }

    def analyze(self):
        """Return the complete analysis as a dictionary."""
        usable = self.usable_observations()
        summaries = self.summaries(usable)
        recovery = detect_recovery(usable, self._participant.baseline_heart_rate)
        classification = classify_session(
            usable, len(self._observations), self._participant, recovery
        )
        return {
            "participant_id": self._participant.participant_id,
            "windows_total": len(self._observations),
            "windows_usable": len(usable),
            "windows_flagged": len(self._observations) - len(usable),
            "baseline": {
                "heart_rate": self._participant.baseline_heart_rate,
                "skin_response": self._participant.baseline_skin_response,
                "temperature": self._participant.baseline_temperature,
            },
            "summaries": summaries,
            "comparison": compare_to_baseline(summaries, self._participant),
            "recovery": recovery,
            "classification": classification,
            "flagged_details": self.flagged_observations(),
        }

    def __repr__(self):
        return "Session(participant=%r, windows=%d)" % (
            self._participant.participant_id,
            len(self._observations),
        )
