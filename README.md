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
smart-fitness-session-analyzer/
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

## Run with uv

Install `uv` if it is not already installed. From PowerShell, move into the
project directory and create the environment from `pyproject.toml`:

```powershell
cd smart-fitness-session-analyzer
uv sync
```

Run the application:

```powershell
uv run main.py
```

Run the test suite:

```powershell
uv run python -m unittest discover -s tests
```

The test suite covers the required classes, inheritance, composition,
encapsulation, validation, scenarios, structured results, and reporting.
