"""
BudgetBench Tradeoff Curve Generator
Reads aggregated CSV and produces a 2x2 panel figure.

Usage:
    python scripts/plot_tradeoffs.py --csv results/full_study_qwen2.5_14b_20260508.csv --model "qwen2.5:14b"
"""
import argparse
import os
import tempfile

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "budgetbench-matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", os.path.join(tempfile.gettempdir(), "budgetbench-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


BUDGET_TIERS = [2048, 4096, 8192, 16384, 32768]
BUDGET_LABELS = ["2K", "4K", "8K", "16K", "32K"]

STRATEGY_COLORS = {
    "truncation": "tab:blue",
    "summary": "tab:orange",
    "rag": "tab:green",
    "mem0": "tab:red",
    "letta": "tab:purple",
    "llmlingua": "tab:brown",
}
STRATEGY_MARKERS = {
    "truncation": "o",
    "summary": "s",
    "rag": "^",
    "mem0": "D",
    "letta": "v",
    "llmlingua": "P",
}


def plot_tradeoff_curves(df: pd.DataFrame, model: str, out_path: str) -> None:
    """Generate 2x2 panel tradeoff figure and save as PNG."""
    plt.rcParams.update({
        "font.size": 10,
        "font.family": "serif",
        "figure.dpi": 150,
        "axes.grid": True,
        "grid.alpha": 0.3,
    })

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey="row")
    tasks = [("swe", "SWE-bench Verified"), ("long", "LongBench v2")]

    model_df = df[df["model"] == model] if "model" in df.columns else df

    for col, (task_id, task_label) in enumerate(tasks):
        sub = model_df[model_df["task"] == task_id] if "task" in model_df.columns else model_df.iloc[0:0]
        strategies_in_data = sub["strategy"].unique() if not sub.empty else []

        for strategy in strategies_in_data:
            s_data = sub[sub["strategy"] == strategy].sort_values("budget")
            x = s_data["budget"].tolist()
            y_acc = s_data["accuracy"].tolist()
            if "violation_rate" in s_data:
                y_viol = s_data["violation_rate"].fillna(0).tolist()
            else:
                y_viol = [0] * len(x)

            color = STRATEGY_COLORS.get(strategy, None)
            marker = STRATEGY_MARKERS.get(strategy, "o")

            axes[0][col].plot(x, y_acc, label=strategy, color=color, marker=marker)
            axes[1][col].plot(x, y_viol, label=strategy, color=color, marker=marker)

        for row in range(2):
            axes[row][col].set_xscale("log", base=2)
            axes[row][col].set_xticks(BUDGET_TIERS)
            axes[row][col].set_xticklabels(BUDGET_LABELS)
            axes[row][col].set_xlim(1500, 40000)

        axes[0][col].set_title(f"{task_label}\nQuality vs Budget")
        axes[0][col].set_ylabel("Quality")
        axes[0][col].set_ylim(0, 1)
        axes[1][col].set_title(f"{task_label}\nViolation Rate vs Budget")
        axes[1][col].set_ylabel("Violation Rate")
        axes[1][col].set_xlabel("Context Budget (tokens)")
        axes[1][col].set_ylim(0, 1)

    handles, labels = axes[0][0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.02))

    fig.suptitle(f"BudgetBench Tradeoff Curves - {model}", fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    plt.close()
    print(f"Figure saved to: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate BudgetBench tradeoff curve figure")
    parser.add_argument("--csv", required=True, help="Path to aggregated results CSV")
    parser.add_argument("--model", required=True, help="Model name to plot (e.g. qwen2.5:14b)")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    model_slug = args.model.replace(":", "_").replace(".", "_")
    out_path = os.path.join("results", "figures", f"tradeoff_curves_{model_slug}.png")
    plot_tradeoff_curves(df, model=args.model, out_path=out_path)


if __name__ == "__main__":
    main()
