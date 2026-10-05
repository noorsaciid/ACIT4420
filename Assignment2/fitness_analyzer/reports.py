"""Stable output files for processed results and rejected rows."""

import csv
from pathlib import Path

from .analysis import format_report


def write_outputs(results, rejected, output_directory):
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    summary_path = output_directory / "analysis_summary.csv"
    report_path = output_directory / "analysis_report.txt"
    rejected_path = output_directory / "rejected_records.txt"
    fields = ["session_id", "participant_id", "windows_total", "windows_usable",
              "windows_flagged", "classification", "recovery_detected"]
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow({
                "session_id": result["session_id"],
                "participant_id": result["participant_id"],
                "windows_total": result["windows_total"],
                "windows_usable": result["windows_usable"],
                "windows_flagged": result["windows_flagged"],
                "classification": result["classification"]["category"],
                "recovery_detected": result["recovery"]["detected"],
            })
    with report_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n\n".join(format_report(result) for result in results))
        handle.write("\n")
    with rejected_path.open("w", encoding="utf-8", newline="") as handle:
        if rejected:
            for item in rejected:
                handle.write("%s, row %s, %s: %s\n" %
                             (item["source"], item["row"], item["field"], item["reason"]))
        else:
            handle.write("No rejected records.\n")
    return summary_path, report_path, rejected_path