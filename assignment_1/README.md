# Smart Fitness Session Analyzer

**Course:** ACIT4420 - Programming Assignment I  
**Option:** A - Smart Fitness Session Analyzer  
**Student:** Saciid Noor  
**Student number:** 394097

## Overview

This program analyses simulated wearable-device measurements from fitness
sessions. It validates observations, calculates summaries, compares results
with a participant baseline, classifies the session, detects recovery, and
prints a readable console report.

The project uses Python's standard library only. Dependencies and the Python
environment are managed with `uv`.

## Project Structure

```text
assignment_1/
|-- fitness_analyzer/
|   |-- analyzer.py          # Classes and analysis functions
|   |-- data_generator.py    # Supplied data generator
|   |-- sample_data.py       # Reproducible test scenarios
|   `-- __init__.py
|-- tests/
|   `-- tests.py             # Unit tests
|-- docs/
|   `-- DATA_DESCRIPTION.md  # Data-field description
|-- main.py                  # Program entry point
|-- pyproject.toml           # uv project configuration
|-- uv.lock                 # Locked environment
|-- requirements.txt        # Standard-library dependency note
`-- .gitignore
```

## OOP Design

- `Participant` stores participant identity and baseline measurements.
- `Observation` is the base class for sensor observations.
- `FitnessObservation` inherits from `Observation` and overrides `validate()`
  with fitness-specific checks.
- `Session` composes one `Participant` with a list of
  `FitnessObservation` objects.
- `Participant._baseline_heart_rate` is protected by a validating property.
- `Participant.from_profile`, `FitnessObservation.from_raw`, and
  `Session.from_generated` are class methods.
- `Observation.in_range` is a static method.

Standalone functions handle number checks, summaries, validation, intensity,
recovery, baseline comparison, classification, and report formatting.

## Validation and Scenarios

Observations with missing, non-numeric, impossible, or low-quality values are
flagged and excluded from summaries. Valid ranges include:

- Heart rate: 35-205 bpm
- Skin response: 0-60
- Temperature: 25-42 C
- Activity level: 0-1
- Signal quality: 0-1, with at least 0.50 required for use

The program runs seven scenarios:

- Resting
- Moderate activity
- High activity
- Recovery
- Poor-quality data
- Empty session
- Handcrafted invalid data

`Session.analyze()` returns the structured result as a dictionary, and
`format_report()` produces the console report.

## Installation and Running

The required standard Python workflow is:

```bash
git clone https://github.com/noorsaciid/ACIT4420.git
cd ACIT4420
cd assignment_1
python3 main.py
```

On Windows, if the command is `python` rather than `python3`, use:

```powershell
cd assignment_1
python main.py
```

The tests can be run with:

```powershell
cd assignment_1
python tests/tests.py
```

The project also supports `uv`. Install `uv`, then run from the repository
the `assignment_1` directory:

```powershell
cd assignment_1
uv sync
uv run main.py
uv run python -m unittest discover -s tests
```

## Example Output

```text
SESSION REPORT - participant P001
Windows: 12 total, 12 usable, 0 flagged
Classification: HIGH ACTIVITY
Recovery detected: no
```

## Known Limitations

- Classification uses fixed thresholds calibrated for the supplied generator.
- Recovery compares the first and last thirds of a session.
- The program analyses one session at a time and does not store results.

The test suite covers the required classes, inheritance, composition,
encapsulation, validation, scenarios, structured results, and reporting.
