"""
Run the official LongMemEval evaluation script on exported BudgetBench hypotheses.

Primary source:
https://github.com/xiaowu0162/longmemeval
"""
import argparse
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List


def build_command(
    evaluation_script: str,
    judge_model: str,
    hypothesis_file: str,
    data_file: str,
) -> List[str]:
    return [
        "python3",
        evaluation_script,
        judge_model,
        hypothesis_file,
        data_file,
    ]


def ensure_prereqs(
    repo_dir: str,
    api_key_env: str,
) -> None:
    evaluation_script = Path(repo_dir) / "src" / "evaluation" / "evaluate_qa.py"
    if not evaluation_script.exists():
        raise RuntimeError(
            f"Official LongMemEval evaluation script not found at {evaluation_script}. "
            "Clone the official repository first."
        )
    if not os.environ.get(api_key_env):
        raise RuntimeError(
            f"{api_key_env} is required by the official LongMemEval evaluation script wrapper"
        )


def maybe_prepare_patched_eval_script(
    repo_dir: str,
    openai_base_url: str | None,
    metric_model_override: str | None,
) -> str:
    evaluation_script = Path(repo_dir) / "src" / "evaluation" / "evaluate_qa.py"
    if not openai_base_url and not metric_model_override:
        return str(evaluation_script)

    source = evaluation_script.read_text(encoding="utf-8")
    if openai_base_url:
        source = source.replace(
            "        openai_api_base = None\n",
            '        openai_api_base = os.getenv("OPENAI_API_BASE")\n',
        )
    if metric_model_override:
        source = source.replace(
            "    metric_model, metric_model_source = model_zoo[metric_model_short]\n",
            '    metric_model, metric_model_source = model_zoo[metric_model_short]\n'
            '    metric_model = os.getenv("LONGMEMEVAL_METRIC_MODEL_OVERRIDE", metric_model)\n',
        )

    patched_dir = Path(tempfile.mkdtemp(prefix="longmemeval_eval_patch_"))
    patched_script = patched_dir / "evaluate_qa.py"
    patched_script.write_text(source, encoding="utf-8")
    return str(patched_script)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run official LongMemEval evaluation on exported BudgetBench hypotheses"
    )
    parser.add_argument("--repo-dir", required=True, help="Path to cloned official LongMemEval repository")
    parser.add_argument("--judge-model", default="gpt-4o", help="Judge model name for evaluate_qa.py")
    parser.add_argument(
        "--metric-model-override",
        default=None,
        help="Override the actual OpenAI-compatible model ID sent by the evaluator, e.g. openai/gpt-4o-mini for OpenRouter",
    )
    parser.add_argument(
        "--openai-base-url",
        default=None,
        help="OpenAI-compatible base URL override, e.g. https://openrouter.ai/api/v1",
    )
    parser.add_argument(
        "--api-key-env",
        default="OPENAI_API_KEY",
        help="Environment variable containing the API key for the judge endpoint",
    )
    parser.add_argument("--hypotheses", required=True, help="Official-format hypothesis JSONL")
    parser.add_argument("--data-file", required=True, help="LongMemEval data JSON used for evaluation")
    args = parser.parse_args()

    ensure_prereqs(args.repo_dir, api_key_env=args.api_key_env)
    evaluation_script = maybe_prepare_patched_eval_script(
        repo_dir=args.repo_dir,
        openai_base_url=args.openai_base_url,
        metric_model_override=args.metric_model_override,
    )
    command = build_command(
        evaluation_script=evaluation_script,
        judge_model=args.judge_model,
        hypothesis_file=args.hypotheses,
        data_file=args.data_file,
    )
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = env[args.api_key_env]
    if args.openai_base_url:
        env["OPENAI_API_BASE"] = args.openai_base_url
    if args.metric_model_override:
        env["LONGMEMEVAL_METRIC_MODEL_OVERRIDE"] = args.metric_model_override
    print("Running:", " ".join(command))
    subprocess.run(command, cwd=os.path.dirname(evaluation_script), env=env, check=True)


if __name__ == "__main__":
    main()
