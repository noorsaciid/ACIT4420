# Smart Fitness Session Analyzer

**Course:** ACIT4420 — Programming Assignment I (Object-Oriented Python)
**Selected option:** Option A — Smart Fitness Session Analyzer

**Student name:** Saciid Noor
**Student number:** 394097

---

## 1. Short description

A fitness centre receives simulated measurements from wearable devices worn
during training sessions. This program turns those raw measurements into an
interpretable report. It:

- organises a **participant** and their personal **baseline** reference values;
- groups individual **observation windows** into a **session**;
- **validates** each window and rejects or flags missing, impossible or
  low-quality values;
- computes **summaries** (average, minimum, maximum) for every measurement;
- **compares** the session with the participant's personal baseline;
- **classifies** the session as *resting*, *moderate activity*, *high activity*,
  *recovering* or *insufficient data*;
- **detects recovery** by checking whether heart rate and activity decline
  toward the end of the session; and
- prints a **readable console report** for each of several scenarios.

Only the Python standard library is used (`statistics` and `unittest`).

---

## 2. Repository structure

```
smart-fitness-session-analyzer/
|-- README.md            <- this file
|-- main.py              <- entry point: runs every scenario and prints reports
|-- analyzer.py          <- the object model + standalone functions (the solution)
|-- sample_data.py       <- reproducible sample datasets (5 generated + 2 handcrafted)
|-- tests.py             <- unittest suite
|-- pyproject.toml       <- project metadata and uv configuration
|-- uv.lock              <- reproducible uv lockfile
|-- data_generator.py    <- instructor-supplied data generator (unmodified)
`-- DATA_DESCRIPTION.md   <- instructor-supplied data description
```

The solution is split into a small `analyzer.py` module so that `main.py` stays
a thin entry point and the same classes can be imported by `tests.py`. The
project uses `uv` to manage its environment and has no third-party packages.

---

## 3. Class design and responsibilities

| Class | Responsibility |
|---|---|
| `Participant` | Holds a participant's id and their personal baseline heart rate, skin response and temperature. Guarantees the baseline heart rate is always plausible. |
| `Observation` | Base class for **any** single sensor observation window. Knows only the concerns common to every sensor: an ordered `timestamp` and a `signal_quality`, and how to validate them. |
| `FitnessObservation` | Subclass of `Observation` that adds the physiological fields (`heart_rate`, `skin_response`, `temperature`, `activity_level`) and extends validation to them. |
| `Session` | A single training session. **Owns** one `Participant` and a list of `FitnessObservation` objects, and drives the whole analysis (usable/flagged windows, summaries, comparison, recovery, classification, and the final structured result). |

Standalone functions in `analyzer.py` keep the calculations, validation and
presentation reusable and testable on their own: `is_real_number`, `summarize`,
`validate_raw_observation`, `classify_intensity`, `detect_recovery`,
`classify_session`, `compare_to_baseline` and `format_report`.

---

## 4. Where the OOP concepts are demonstrated

- **Composition** — `Session` *has-a* `Participant` and *has-a* list of
  `FitnessObservation` objects (`Session._participant`, `Session._observations`).
  The session owns these objects and their lifetime is tied to it. This is the
  required clear example of composition.
- **Encapsulation** — `Participant.baseline_heart_rate` is stored in the
  protected attribute `_baseline_heart_rate` and exposed through a **property**
  whose setter validates the value, so an implausible baseline can never be
  stored. `Session` similarly protects `_participant` and `_observations` and
  exposes read-only properties.
- **Inheritance** — `FitnessObservation` inherits from `Observation`, reusing the
  common timestamp / signal-quality handling.
- **Method overriding** — `FitnessObservation.validate()` overrides
  `Observation.validate()`, calling `super().validate()` first and then adding
  the physiological range checks. Because `Observation.is_usable()` calls
  `self.validate()`, the correct (subclass) validation runs polymorphically.
- **Class methods** — `Participant.from_profile`, `FitnessObservation.from_raw`
  and `Session.from_generated` are alternative constructors that build objects
  from the raw dictionaries returned by the data generator.
- **Static method** — `Observation.in_range` is a pure range-check helper that
  needs no instance state and is shared by the base class and its subclass.

---

## 5. Assumptions and classification rules

### Validity of an observation

A window is **usable** only if every field is present and within range **and**
its `signal_quality` is at least **0.50**. The accepted ranges (from
`DATA_DESCRIPTION.md`) are:

| Field | Valid range |
|---|---|
| `heart_rate` | 35–205 bpm |
| `skin_response` | ≥ 0 (values above 60 rejected as impossible) |
| `temperature` | 25–42 °C |
| `activity_level` | 0–1 |
| `signal_quality` | 0–1 (and ≥ 0.50 to be *usable*) |

Missing (`None`), non-numeric or out-of-range values cause the window to be
flagged and excluded from all summaries. Booleans are not accepted as numbers.

### Heart-rate elevation

Intensity is judged from **heart-rate elevation**, defined as the session's
average heart rate minus the participant's personal baseline, so the same
absolute heart rate is interpreted relative to the individual.

### Classification rules (evaluated in this order)

1. **insufficient data** — fewer than 3 usable windows, or fewer than half
   (below 50%) of the windows usable. A session with at least half of its
   windows usable is classified normally.
2. **recovering** — the session started clearly elevated (first-third average at
   least 15 bpm above baseline) **and** both heart rate (≥ 12 bpm) and activity
   (≥ 0.10) fell from the first third to the last third. Checked before the
   intensity labels because an averaged recovering session can look "moderate".
3. **resting** — average activity < 0.25 **and** heart-rate elevation < 12 bpm.
4. **moderate activity** — average activity < 0.67 **and** heart-rate
   elevation < 45 bpm.
5. **high activity** — anything above the moderate thresholds.

These thresholds were calibrated against the supplied `data_generator.py` and
verified to hold across many random seeds (see `tests.py`).

---

## 6. Installation and running instructions

Install `uv`, then run these commands from the project directory:

```bash
uv sync
uv run main.py
```

Run the test suite with:

```bash
uv run tests.py
```

---

## 7. Example output

Running `uv run main.py` produces a report for each of the seven scenarios.
Two representative reports are shown below.

```
#### SCENARIO: HIGH_ACTIVITY ####
============================================================
SESSION REPORT - participant P001
============================================================
Windows: 12 total, 12 usable, 0 flagged
Classification: HIGH ACTIVITY
  Average activity was 0.80 and average heart rate was 137 bpm (+60 bpm relative to the 77 bpm baseline), which matches 'high activity'.
Recovery detected: no
  No clear decline near the end (heart-rate change 5 bpm, activity change -0.05).
------------------------------------------------------------
Summaries (usable windows only):
  heart_rate      avg=137.25  min=117     max=153     (n=12)
  skin_response   avg=2.11    min=1.71    max=2.29    (n=12)
  temperature     avg=32.62   min=32.38   max=32.93   (n=12)
  activity_level  avg=0.8     min=0.71    max=0.93    (n=12)
  signal_quality  avg=0.89    min=0.82    max=0.98    (n=12)
------------------------------------------------------------
Comparison with personal baseline:
  heart_rate      137.25 vs baseline 77 (+60.25, above baseline)
  skin_response   2.11 vs baseline 1.38 (+0.73, above baseline)
  temperature     32.62 vs baseline 32.11 (+0.51, above baseline)
============================================================

#### SCENARIO: POOR_QUALITY ####
============================================================
SESSION REPORT - participant P001
============================================================
Windows: 12 total, 0 usable, 12 flagged
Classification: INSUFFICIENT DATA
  Only 0 of 12 windows were usable, which is too few to classify the session reliably.
Recovery detected: no
  Not enough usable windows to assess recovery.
------------------------------------------------------------
Summaries (usable windows only):
  heart_rate      no usable values
  ...
------------------------------------------------------------
Flagged windows:
  timestamp 0: heart_rate is missing (None)
  timestamp 1: heart_rate value 265 is outside the valid range 35-205
  timestamp 2: activity_level value -0.2 is outside the valid range 0.0-1.0
  timestamp 3: skin_response is missing (None)
  ...
============================================================
```

The seven scenarios exercised by `main.py` are: **resting**, **moderate
activity**, **high activity**, **recovery** (unusual), **poor-quality/invalid
sensor data**, an **empty** session, and a **hand-crafted invalid** dataset that
covers every kind of data-quality problem in one place.

---

## 8. Known limitations

- Classification uses fixed, hand-tuned thresholds rather than learned values
  (the assignment forbids machine learning), so unusual real data far outside
  the generator's ranges might sit near a boundary.
- Recovery detection compares the first third of a session with the last third;
  a session that recovers and then rises again would not be reported as
  recovering.
- Summaries are simple averages, minimums and maximums; no smoothing or
  outlier handling beyond the validity checks is applied.
- The program analyses one session at a time; it does not persist results or
  aggregate across multiple sessions.
