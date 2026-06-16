"""CLI entry point for BudgetBench.

Usage:
    budgetbench profile           # print hardware report + recommendation
    budgetbench profile --json    # same output as JSON
"""

import argparse
import json
import sys

from .profile import profile as _profile


def _format_report(data: dict) -> str:
    """Format a profile report as human-readable text."""
    hw = data["hardware"]
    rec = data["recommendation"]

    lines = [
        "BudgetBench Hardware Profile",
        "=" * 30,
        f"GPU:      {hw.get('gpu_model') or 'CPU-only'}",
        f"VRAM:     {hw.get('vram_gb', 'N/A')} GB",
        f"CPU:      {hw.get('cpu_model', 'Unknown')} ({hw.get('cpu_cores', '?')} cores)",
        f"RAM:      {hw.get('ram_gb', 'N/A')} GB",
        "",
        f"Recommendation: {rec.get('model_name', 'N/A')} @ {rec.get('budget_tier', '?')} tier",
        f"VRAM needed:  {rec.get('vram_needed_gb', 'N/A')} GB / {rec.get('vram_available_gb', 'N/A')} GB",
    ]

    if rec.get("notes"):
        lines.append(f"Note: {rec['notes']}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="budgetbench",
        description="BudgetBench — hardware profiler and benchmark runner",
    )
    sub = parser.add_subparsers(dest="command")

    profile_parser = sub.add_parser(
        "profile",
        help="Print hardware report with model+tier recommendation",
    )
    profile_parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output as JSON instead of formatted text",
    )

    args = parser.parse_args()

    if args.command == "profile":
        data = _profile()
        if args.as_json:
            print(json.dumps(data, indent=2, default=str))
        else:
            print(_format_report(data))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
