from pathlib import Path

from scripts.run_longmemeval_official_eval import (
    build_command,
    maybe_prepare_patched_eval_script,
)


def test_build_command_resolves_input_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    command = build_command(
        evaluation_script="/tmp/evaluate_qa.py",
        judge_model="gpt-4o",
        hypothesis_file="results/hypotheses.jsonl",
        data_file="data/longmemeval_oracle.json",
    )

    assert command == [
        "python3",
        "/tmp/evaluate_qa.py",
        "gpt-4o",
        str(tmp_path / "results/hypotheses.jsonl"),
        str(tmp_path / "data/longmemeval_oracle.json"),
    ]


def test_patched_evaluator_is_quiet_and_uses_overrides(tmp_path):
    source_dir = tmp_path / "src/evaluation"
    source_dir.mkdir(parents=True)
    source = source_dir / "evaluate_qa.py"
    source.write_text(
        "verbose = True\n"
        "for entry in tqdm(hypotheses):\n"
        "        openai_api_base = None\n"
        "    metric_model, metric_model_source = model_zoo[metric_model_short]\n",
        encoding="utf-8",
    )

    patched = Path(
        maybe_prepare_patched_eval_script(
            repo_dir=str(tmp_path),
            openai_base_url="https://openrouter.ai/api/v1",
            metric_model_override="openai/gpt-4o",
        )
    ).read_text(encoding="utf-8")

    assert "verbose = False" in patched
    assert "for entry in hypotheses:" in patched
    assert 'openai_api_base = os.getenv("OPENAI_API_BASE")' in patched
    assert 'metric_model = os.getenv("LONGMEMEVAL_METRIC_MODEL_OVERRIDE", metric_model)' in patched
