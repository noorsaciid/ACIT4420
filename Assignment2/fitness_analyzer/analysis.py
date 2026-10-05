"""Analysis functions I implemented and now reused and extended from Assignment 1."""

import statistics

from .models import PHYSIOLOGICAL_FIELDS

RESTING_MAX_ACTIVITY = 0.25
RESTING_MAX_HR_ELEVATION = 12
MODERATE_MAX_ACTIVITY = 0.67
MODERATE_MAX_HR_ELEVATION = 45


def summarize(values):
    numbers = [value for value in values if isinstance(value, (int, float))]
    if not numbers:
        return {"count": 0, "average": None, "minimum": None, "maximum": None}
    return {"count": len(numbers), "average": round(statistics.mean(numbers), 2),
            "minimum": min(numbers), "maximum": max(numbers)}


def classify_intensity(mean_activity, hr_elevation):
    if mean_activity < RESTING_MAX_ACTIVITY and hr_elevation < RESTING_MAX_HR_ELEVATION:
        return "resting"
    if mean_activity < MODERATE_MAX_ACTIVITY and hr_elevation < MODERATE_MAX_HR_ELEVATION:
        return "moderate activity"
    return "high activity"


def detect_recovery(observations, baseline_heart_rate):
    ordered = sorted(observations, key=lambda observation: observation.timestamp)
    if len(ordered) < 6:
        return {"detected": False, "explanation": "Not enough usable windows to assess recovery."}
    third = max(1, len(ordered) // 3)
    first, last = ordered[:third], ordered[-third:]
    first_hr = statistics.mean(item.heart_rate for item in first)
    last_hr = statistics.mean(item.heart_rate for item in last)
    first_activity = statistics.mean(item.activity_level for item in first)
    last_activity = statistics.mean(item.activity_level for item in last)
    hr_drop = first_hr - last_hr
    activity_drop = first_activity - last_activity
    detected = first_hr - baseline_heart_rate >= 15 and hr_drop >= 12 and activity_drop >= 0.10
    explanation = ("Heart rate fell %.0f bpm and activity fell %.2f."
                   if detected else
                   "No clear decline near the end (heart-rate change %.0f bpm, activity change %.2f).") % (
                       hr_drop, activity_drop)
    return {"detected": detected, "explanation": explanation,
            "heart_rate_drop": round(hr_drop, 1), "activity_drop": round(activity_drop, 2)}


def analyze_session(session):
    usable = [item for item in session.observations if item.is_usable(session.signal_threshold)]
    summaries = {field: summarize([getattr(item, field) for item in usable])
                 for field in PHYSIOLOGICAL_FIELDS}
    recovery = detect_recovery(usable, session.participant.baseline_heart_rate)
    if len(usable) < 3 or len(usable) < len(session.observations) / 2:
        classification = {"category": "insufficient data",
                          "explanation": "Only %d of %d accepted windows were usable."
                          % (len(usable), len(session.observations))}
    else:
        mean_hr = statistics.mean(item.heart_rate for item in usable)
        mean_activity = statistics.mean(item.activity_level for item in usable)
        elevation = mean_hr - session.participant.baseline_heart_rate
        category = "recovering" if recovery["detected"] else classify_intensity(mean_activity, elevation)
        classification = {"category": category,
                          "explanation": "Average activity %.2f and heart rate %.0f bpm (%+.0f bpm from baseline)."
                          % (mean_activity, mean_hr, elevation)}
    comparison = {}
    baselines = {"heart_rate": session.participant.baseline_heart_rate,
                 "skin_response": session.participant.baseline_skin_response,
                 "temperature": session.participant.baseline_temperature}
    for field, baseline in baselines.items():
        average = summaries[field]["average"]
        if average is not None:
            comparison[field] = {"average": average, "baseline": baseline,
                                 "difference": round(average - baseline, 2)}
    return {"session_id": session.session_id,
            "participant_id": session.participant.participant_id,
            "windows_total": len(session.observations),
            "windows_usable": len(usable),
            "windows_flagged": len(session.observations) - len(usable),
            "summaries": summaries, "comparison": comparison,
            "recovery": recovery, "classification": classification}


def format_report(result):
    lines = ["SESSION REPORT - %s (%s)" % (result["session_id"], result["participant_id"]),
             "Windows: %d total, %d usable, %d flagged" %
             (result["windows_total"], result["windows_usable"], result["windows_flagged"]),
             "Classification: %s" % result["classification"]["category"].upper(),
             result["classification"]["explanation"],
             "Recovery detected: %s" % ("yes" if result["recovery"]["detected"] else "no"),
             result["recovery"]["explanation"], "Summaries:"]
    for field, values in result["summaries"].items():
        lines.append("  %s: average=%s minimum=%s maximum=%s count=%d" %
                     (field, values["average"], values["minimum"], values["maximum"], values["count"]))
    return "\n".join(lines)