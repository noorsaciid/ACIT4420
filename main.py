"""Run the sample fitness analyses."""

from fitness_analyzer.analyzer import Session, format_report
from fitness_analyzer.sample_data import all_scenarios


def analyze_scenario(name, profile, observations):
    """Analyse and print one scenario."""
    print("\n\n#### SCENARIO: %s ####" % name.upper())
    session = Session.from_generated(profile, observations)
    result = session.analyze()
    print(format_report(result))
    return result


def main():
    print("Smart Fitness Session Analyzer")
    print("Running %d sample scenarios (normal, unusual and invalid data)."
          % len(all_scenarios()))

    for name, (profile, observations) in all_scenarios().items():
        analyze_scenario(name, profile, observations)


if __name__ == "__main__":
    main()
