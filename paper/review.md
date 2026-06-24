> **Verdict: Borderline.** The protocol idea is useful and the paper is unusually honest, but the current evidence still reads as artifact validation rather than a publishable benchmark study. Acceptance depends on venue: plausible for a workshop/tool paper, weak for a Datasets & Benchmarks track without hardened tokenizer accounting, official graders, and stronger empirical evidence.

# 1. Summary

The paper introduces **BudgetBench**, a protocol for comparing memory strategies for local LLM agents under fixed per-call context budgets. It implements truncation, summarization, RAG, lean retrieval, checkpointing, and full-context diagnostics across several pilot tasks. The key result is not a strategy ranking, but evidence that the harness can expose budget-compliance failures and underpowered quality comparisons that full-context evaluation hides.

# 2. Contributions

The strongest actual contribution is the measurement framing: active context budget is treated as the independent variable, and budget violations are logged as first-class outcomes. The strategy interface and raw-log orientation are also useful.

The contribution framing is now mostly appropriate. It no longer oversells equivalence or benchmark maturity. However, the paper still sometimes leans on “benchmark” language while repeatedly admitting the study is a pilot, the tokenizer is approximate, latency is single-run, and public-memory scoring is not official. The novelty is a practical conjunction, not a new method.

# 3. Methodology

The protocol is described clearly enough to reproduce the main qwen2.5:1.5b run, and the command transcript is stronger than typical. The reset-per-item design is defensible for controlled comparisons, but it limits claims about memory systems that depend on persistent state.

The largest methodological problem is token accounting. The paper now reports that Qwen tokenization would mark many tiktoken-compliant truncation prompts over budget. That is an excellent disclosure, but it also undermines the central “fixed active budget” manipulation. If the served model tokenizer disagrees materially with the enforcement tokenizer, violation rates are only compliance-with-proxy metrics.

Ablations are still thin. The current baselines test broad strategy families, but the paper does not isolate retrieval chunking, embedding choice, summary quality, or prompt formatting effects.

# 4. Experiments

Baselines are reasonable as scaffold baselines, but not yet strong enough for a benchmark claim. The absence of LLMLingua-2, Mem0, Letta/MemGPT, or an official LongMemEval judge limits the paper’s ability to speak to current memory systems.

Datasets are a mixed bag. LongBench v2 is a useful deterministic substrate; SWE-bench is only a proxy scaffold; synthetic memory is diagnostic; LongMemEval uses an approximate scorer. The main LongBench table now includes bootstrap CIs, which helps, but the intervals overlap heavily and support no ranking. The full-context slice is honest: no detectable difference is not equivalence.

Compute and serving details are reasonably disclosed. Latency remains weak: single-run, warmup-uncontrolled values are presented as diagnostics, not stable estimates. That demotion is correct, but it also removes latency as a claim-bearing result.

# 5. Limitations

The authors acknowledge most major limitations: pilot scale, small model, proxy SWE scoring, approximate LongMemEval scoring, tokenizer mismatch, local alias provenance, and single-run latency.

The missed limitation is that the tokenizer audit is not merely a nuisance; it may invalidate apparent budget compliance for the central LongBench truncation rows under the served model’s actual tokenizer. Another underplayed limitation is that qwen2.5:1.5b may be too weak for strategy effects to generalize. The transfer probes mostly show fragility rather than robustness.

# 6. Related Work

The related work is current and mostly fair. The core concurrent claims are backed by recent budgeted-memory and long-context papers, and the paper now contrasts itself with them in the right way: as a local, fixed-budget protocol with swappable strategies and operational metrics.

The paper should still add or discuss newer/adjacent memory benchmarks that sharpen the “agent memory” positioning: LongMemEval-V2, MemoryArena, LoCoMo, and similar long-term memory benchmarks. These works emphasize environment experience, interdependent multi-session tasks, and very long-term conversational memory, which are closer to the paper’s intended future direction than the current pilot.

# 7. Verdict

**Borderline.** The artifact idea is real: fixed active-budget sweeps plus explicit violation logging is useful for local-agent evaluation. The paper is also unusually transparent, which makes it more trustworthy than many pilot benchmark papers. But the empirical study is not yet strong enough to justify more than a protocol/tooling contribution: token enforcement is approximate and materially different from the served tokenizer, latency is not benchmark-quality, SWE is degenerate, and LongMemEval scoring is unofficial. For acceptance, I would want at least one hardened claim-bearing slice with model-specific tokenization, official or validated grading, repeated latency measurements, and enough items to support a clear paired comparison.
