"""CSV readers and row-level validation for the fitness option."""

import csv
import re
from pathlib import Path

from .exceptions import InputFileError, InvalidIdentifierError, InvalidRecordError
from .models import FitnessObservation, Participant, Session

PROFILE_FIELDS = [
    "participant_id", "name", "baseline_heart_rate",
    "baseline_skin_response", "baseline_temperature",
]
SESSION_FIELDS = [
    "session_id", "participant_id", "timestamp", "heart_rate",
    "skin_response", "temperature", "activity_level", "signal_quality",
]
SESSION_ID_PATTERN = re.compile(r"^FIT-\d{4}-\d{3}$")
SIGNAL_THRESHOLD = 0.5


def _read_rows(path):
    try:
        handle = path.open("r", encoding="utf-8", newline="")
    except FileNotFoundError as error:
        raise InputFileError("input file not found: %s" % path) from error
    except PermissionError as error:
        raise InputFileError("permission denied reading: %s" % path) from error
    try:
        return csv.reader(handle, strict=True), handle
    except csv.Error as error:
        handle.close()
        raise InputFileError("CSV error in %s: %s" % (path, error)) from error


def _header(reader, path, expected):
    try:
        header = next(reader)
    except StopIteration as error:
        raise InputFileError("empty CSV file: %s" % path) from error
    if header != expected:
        raise InputFileError("unexpected header in %s" % path)


def _convert(value, field, converter, source, row_number):
    if value == "":
        raise InvalidRecordError(field, "required value is missing", source, row_number)
    try:
        return converter(value)
    except ValueError as error:
        raise InvalidRecordError(field, "cannot convert %r" % value, source, row_number) from error


def _identifier(value, field, pattern, source, row_number):
    if not pattern.fullmatch(value):
        raise InvalidIdentifierError(field, value, source, row_number)


def load_profiles(path):
    """Load participants and return ``(participants, rejected_rows)``."""
    path = Path(path)
    source = path.name
    participants = {}
    rejected = []
    reader, handle = _read_rows(path)
    try:
        _header(reader, path, PROFILE_FIELDS)
        for row_number, row in enumerate(reader, start=2):
            try:
                if len(row) != len(PROFILE_FIELDS):
                    raise InvalidRecordError("row", "expected %d fields, got %d" %
                                             (len(PROFILE_FIELDS), len(row)), source, row_number)
                values = dict(zip(PROFILE_FIELDS, row))
                _identifier(values["participant_id"], "participant_id",
                            Participant.ID_PATTERN, source, row_number)
                participant = Participant(
                    values["participant_id"], values["name"],
                    _convert(values["baseline_heart_rate"], "baseline_heart_rate", int, source, row_number),
                    _convert(values["baseline_skin_response"], "baseline_skin_response", float, source, row_number),
                    _convert(values["baseline_temperature"], "baseline_temperature", float, source, row_number),
                )
                if not values["name"]:
                    raise InvalidRecordError("name", "required value is missing", source, row_number)
                participants[participant.participant_id] = participant
            except (InvalidIdentifierError, InvalidRecordError, ValueError, KeyError) as error:
                if hasattr(error, "as_record"):
                    rejected.append(error.as_record())
                else:
                    rejected.append({"source": source, "row": row_number,
                                     "field": "profile", "reason": str(error)})
    except csv.Error as error:
        raise InputFileError("CSV error in %s: %s" % (path, error)) from error
    finally:
        handle.close()
    return participants, rejected


def load_sessions(path, participants, signal_threshold=SIGNAL_THRESHOLD):
    """Load accepted observations and group them into sessions."""
    path = Path(path)
    source = path.name
    sessions = {}
    rejected = []
    reader, handle = _read_rows(path)
    try:
        _header(reader, path, SESSION_FIELDS)
        for row_number, row in enumerate(reader, start=2):
            try:
                if len(row) != len(SESSION_FIELDS):
                    raise InvalidRecordError("row", "expected %d fields, got %d" %
                                             (len(SESSION_FIELDS), len(row)), source, row_number)
                values = dict(zip(SESSION_FIELDS, row))
                _identifier(values["session_id"], "session_id", SESSION_ID_PATTERN, source, row_number)
                _identifier(values["participant_id"], "participant_id",
                            Participant.ID_PATTERN, source, row_number)
                try:
                    participant = participants[values["participant_id"]]
                except KeyError as error:
                    raise InvalidRecordError("participant_id", "unknown participant %r" %
                                             values["participant_id"], source, row_number) from error
                session = sessions.setdefault(values["session_id"],
                                              Session(values["session_id"], participant, signal_threshold))
                observation = FitnessObservation(
                    _convert(values["timestamp"], "timestamp", int, source, row_number),
                    _convert(values["heart_rate"], "heart_rate", int, source, row_number),
                    _convert(values["skin_response"], "skin_response", float, source, row_number),
                    _convert(values["temperature"], "temperature", float, source, row_number),
                    _convert(values["activity_level"], "activity_level", float, source, row_number),
                    _convert(values["signal_quality"], "signal_quality", float, source, row_number),
                )
                issues = observation.validate()
                if issues:
                    raise InvalidRecordError("observation", "; ".join(issues), source, row_number)
                if observation.signal_quality < signal_threshold:
                    raise InvalidRecordError("signal_quality", "below usable threshold %.2f" %
                                             signal_threshold, source, row_number)
                session.add_observation(observation)
            except (InvalidIdentifierError, InvalidRecordError, ValueError, KeyError) as error:
                if hasattr(error, "as_record"):
                    rejected.append(error.as_record())
                else:
                    rejected.append({"source": source, "row": row_number,
                                     "field": "record", "reason": str(error)})
    except csv.Error as error:
        raise InputFileError("CSV error in %s: %s" % (path, error)) from error
    finally:
        handle.close()
    return list(sessions.values()), rejected