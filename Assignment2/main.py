"""Command-line entry point for the Assignment 2 fitness analyzer."""

import argparse
from pathlib import Path

from fitness_analyzer.analysis import analyze_session
from fitness_analyzer.csv_loader import load_profiles, load_sessions
from fitness_analyzer.exceptions import InputFileError
from fitness_analyzer.reports import write_outputs


def main():
    parser = argparse.ArgumentParser(description="Analyze CSV fitness sessions")
    parser.add_argument("--profiles", type=Path,
                        default=Path("Assignment_II_Pack/data/option_a_fitness/participants.csv"))
    parser.add_argument("--sessions", type=Path,
                        default=Path("Assignment_II_Pack/data/option_a_fitness/fitness_sessions.csv"))
    parser.add_argument("--invalid-sessions", type=Path,
                        default=Path("Assignment_II_Pack/data/option_a_fitness/fitness_sessions_invalid.csv"))
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()
    try:
        participants, profile_rejections = load_profiles(args.profiles)
        valid_sessions, valid_rejections = load_sessions(args.sessions, participants)
        invalid_sessions, invalid_rejections = load_sessions(args.invalid_sessions, participants)
    except InputFileError as error:
        parser.error(str(error))
    sessions = valid_sessions + invalid_sessions
    results = [analyze_session(session) for session in sessions]
    files = write_outputs(results, profile_rejections + valid_rejections + invalid_rejections, args.output)
    print("Processed %d sessions; accepted %d observations; rejected %d rows." % (
        len(results), sum(result["windows_usable"] for result in results),
        len(profile_rejections) + len(valid_rejections) + len(invalid_rejections)))
    print("Created: %s" % ", ".join(str(path) for path in files))


if __name__ == "__main__":
    main()