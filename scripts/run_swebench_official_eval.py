"""
Run the official SWE-bench containerized evaluation harness on exported predictions.

Primary source:
https://github.com/SWE-bench/SWE-bench/blob/main/docs/guides/evaluation.md
"""
import argparse
import os
import shutil
import subprocess
import sys
from typing import List


def build_command(
    predictions_path: str,
    dataset_name: str,
    run_id: str,
    max_workers: int,
    instance_ids: List[str],
    cache_level: str,
    clean: bool,
    modal: bool,
    parallelism: int,
) -> List[str]:
    command = [
        sys.executable,
        "-m",
        "swebench.harness.run_evaluation",
        "--dataset_name",
        dataset_name,
        "--predictions_path",
        predictions_path,
        "--max_workers",
        str(max_workers),
        "--run_id",
        run_id,
    ]
    if instance_ids:
        command.extend(["--instance_ids", *instance_ids])
    if cache_level:
        command.extend(["--cache_level", cache_level])
    if clean:
        command.extend(["--clean", "True"])
    if modal:
        command.extend(["--modal", "true", "--parallelism", str(parallelism)])
    return command


def ensure_prereqs() -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("docker is required for official SWE-bench evaluation")
    try:
        import swebench  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "swebench is not installed. Install the official package first, e.g. `pip install -e /path/to/SWE-bench`."
        ) from exc


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run official SWE-bench evaluation on exported BudgetBench predictions"
    )
    parser.add_argument("--predictions", required=True, help="Official-format SWE-bench predictions JSONL")
    parser.add_argument("--dataset-name", default="princeton-nlp/SWE-bench_Verified", help="Dataset name for official harness")
    parser.add_argument("--run-id", required=True, help="Official SWE-bench run identifier")
    parser.add_argument("--max-workers", type=int, default=2, help="Official harness max_workers")
    parser.add_argument("--instance-ids", nargs="*", default=[], help="Optional subset of instance IDs")
    parser.add_argument("--cache-level", default="env", help="Docker cache level: none/base/env/instance")
    parser.add_argument("--clean", action="store_true", help="Request official harness cleanup after run")
    parser.add_argument("--modal", action="store_true", help="Use official Modal execution path instead of local Docker")
    parser.add_argument("--parallelism", type=int, default=10, help="Modal parallelism when --modal is set")
    args = parser.parse_args()

    ensure_prereqs()
    command = build_command(
        predictions_path=args.predictions,
        dataset_name=args.dataset_name,
        run_id=args.run_id,
        max_workers=args.max_workers,
        instance_ids=args.instance_ids,
        cache_level=args.cache_level,
        clean=args.clean,
        modal=args.modal,
        parallelism=args.parallelism,
    )
    print("Running:", " ".join(command))
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
