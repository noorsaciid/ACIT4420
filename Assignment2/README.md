# Smart Fitness Session Analyzer

This is the Assignment 2 continuation of the Assignment 1 fitness analyzer. It
reads participant profiles and fitness-session CSV files, validates every row,
continues after rejected records, analyzes accepted sessions, and writes stable
reports.

## Run with uv

From this directory:

```powershell
uv sync
uv run python main.py --profiles Assignment_II_Pack/data/option_a_fitness/participants.csv --sessions Assignment_II_Pack/data/option_a_fitness/fitness_sessions.csv --invalid-sessions Assignment_II_Pack/data/option_a_fitness/fitness_sessions_invalid.csv --output output
```

The default command arguments point to the supplied fitness files, so this is
also enough:

```powershell
uv run python main.py
```

Run tests with:

```powershell
uv run python -m unittest discover -s tests -v
```

The output directory contains `analysis_summary.csv`, `analysis_report.txt`,
and `rejected_records.txt`. The program overwrites these files on each run.