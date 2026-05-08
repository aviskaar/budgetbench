# A budget-tiered benchmark for local agent memory

**Bottom line: the idea survives the scan, but barely, and only with sharp scoping.** No existing benchmark does what is proposed — fix the model, sweep an *active* token budget across deployment-realistic tiers (4k/8k/16k), plug in arbitrary memory strategies through a standardized interface, and measure long-horizon agent task quality. However, two very recent (Feb–Apr 2026) method papers — **BudgetMem** and especially **ContextBudget/BACM-RL** — already use this exact evaluation pattern *internally* to motivate their own techniques. The defensible move is to ship the **community benchmark and harness** that those methods should have been evaluated against, scoped to the **local-LLM regime** they ignore, with a **swappable strategy interface** none of them provide. The window is narrow: at least eight memory-agent benchmarks have appeared in the last six months. A 1-month, deterministic-grader-only paper targeting an arXiv preprint plus a NeurIPS 2026 Datasets & Benchmarks submission is realistic on the available hardware. A 3-month version can add an MoE model and a continuous Pareto-frontier formulation.

The rest of this report walks through the eight required sections in order.

## 1. Exact-competitor check

No benchmark whose **primary contribution** is "fix the model, vary active context budget at standardized tiers, plug in any memory strategy, measure long-horizon agent quality" currently exists. The two closest artifacts are method papers, not benchmarks:

**ContextBudget / BACM-RL** (Wu et al., Zhejiang/Alibaba, arXiv:2604.01664, April 2026) is the sharpest threat. It explicitly sweeps **4k/8k/16k token budgets** on long-horizon **web-browsing** and compositional multi-objective QA, plotting quality, peak context, and dependent-cost across (budget × complexity) cells. But it is a single RL-trained policy compared to fixed baselines (MEM1, Summary Agent, Search-R1), not a third-party plug-in framework, and it targets cloud-scale Qwen models, not local deployment. **Overlap on framing: ~70%. Overlap on artifact: ~20%.**

**BudgetMem** (Zhang et al., arXiv:2602.06025, Feb 2026; project at viktoraxelsen.github.io/BudgetMem) proposes a learned router across Low/Mid/High module budget tiers along three axes (implementation/reasoning/capacity). It calls itself a "unified testbed" and reports accuracy–cost frontiers — but evaluates on **LoCoMo, LongMemEval, HotpotQA only** (QA/dialogue, no agents), uses module-level tiers rather than raw token budgets, and is not designed for third-party strategy submission. A separate paper of the same name (Alla et al., arXiv:2511.04919, Nov 2025) on selective memory policies adds naming-collision risk.

Other near-misses include **Context-Folding/FoldGRPO** (Sun et al., arXiv:2510.11967, ICLR submission), which compares same-budget memory strategies on SWE-bench Verified and BrowseComp-Plus but at a single 32K budget point; **Memex(RL)** (arXiv:2603.04257), an indexed-memory RL method with internal budget constraints; **MEMORYARENA** (arXiv:2602.16313), a memory-agent-environment loop benchmark without a budget axis; and a small industry blog post by Sandelin (Mar 2026) running a memory-on/off A/B test on a coding workflow. **None of these provide the conjunction of fixed token-budget tiers + swappable strategy interface + long-horizon agent tasks + local-model focus.**

## 2. Adjacent-benchmark check

The adjacent benchmarks fall cleanly into three groups, none of which cover the proposed combination.

**Long-context model evaluation (no agents, no swappable memory):** LongBench and LongBench v2 (ACL 2024/2025) measure passive long-context QA; LongBench v2 deserves attention as a substrate because its **MCQ-only design gives bulletproof deterministic grading**. RULER (NVIDIA, COLM 2024) is the cleanest *length-as-axis* benchmark (4K–128K) but tests raw model context capacity, not memory strategies. HELMET (Princeton, ICLR 2025) similarly sweeps controllable lengths across seven application categories but evaluates LCLMs, not memory strategies. BABILong (NeurIPS 2024) sweeps haystack length 0K–10M for reasoning-in-haystack, again with strategies as model architectures rather than pluggable components. ∞Bench/InfiniteBench evaluates 100K+ token capacity at fixed length. NIAH variants are largely saturated.

**Agent benchmarks (no memory-strategy or budget axis):** AgentBench (ICLR 2024), τ-bench / τ²-bench / τ³-bench (Sierra), SWE-bench Verified, WebArena/VisualWebArena, AppWorld, OfficeBench all provide long-horizon agentic substrate but report end-to-end success without ablating memory strategy or budget. They are excellent **task pools to draw from**, not competitors.

**Memory benchmarks (no budget tier axis):** **MemoryAgentBench** (Hu et al., arXiv:2507.05257, accepted ICLR 2026) is the closest in *intent* — it explicitly evaluates pluggable memory paradigms (long-context FIFO, BM25, dense retrieval, RAPTOR/GraphRAG, MemGPT, Self-RAG) across four competencies (accurate retrieval, test-time learning, long-range understanding, conflict resolution). But it varies *input* length (up to 4M tokens), not the agent's *active budget*, and its tasks are QA-shaped, not long-horizon agentic. **MemBench** (Tan et al., ACL 2025 Findings) reports an MQI metric weighting accuracy + efficiency + capacity, but the cost dimension is latency-based, not token-budget-tier-based. LoCoMo (Snap, 2024) and **LongMemEval** (Wu et al., 2024) are the de facto chat-memory eval substrates used by Mem0, A-Mem, Zep, MemoryBank, BudgetMem, and LightMem — they give cross-comparable numbers but enforce no protocol. AMA-Bench (Feb 2026), MemTrack, GoodAI LTM, EMemBench, Mem2ActBench, MemoryRewardBench are all 2025–2026 entrants in adjacent niches; **none make active context budget the primary independent variable**.

The pattern across the adjacent literature is clear: **everyone agrees memory matters and budget matters, but no one has standardized the joint evaluation.**

## 3. Recent workshop and preprint check

The space exploded in late 2025 and early 2026. Concrete signals:

- **MemAgents Workshop @ ICLR 2026** (Rio de Janeiro, April 2026) explicitly covers agent memory architectures, "context management (chunking/summarization)," and long-context utilization. Submission deadline Feb 13, 2026 — already passed for the original CFP.
- **NeurIPS 2025 Expo Workshop** "AI Assistants in the Wild: Agents, Adaptation, and Memory-Augmented Deployment" thematically aligns with edge/local memory but has no associated benchmark.
- **ICLR 2026 Recursive Self-Improvement Workshop** accepted "SimpleMem" and "Learning to Continually Learn via Meta-learning Agentic Memory Designs" — confirming the workshop appetite.
- **No ACL 2026, NeurIPS 2025, or LMSys leaderboard** explicitly formalizes a context-budget-vs-quality axis. Galileo Agent Leaderboard v2 reports cost/session as a side metric without sweeping budgets.
- **HuggingFace Daily Papers** featured an "Agent-Memory-Paper-List" (Dec 2025) and a Mem0 "State of AI Agent Memory 2026" report; the ecosystem is consolidating around LoCoMo and LongMemEval as default evaluation surfaces.
- The unifying term **"context engineering"** (Karpathy 2024; Anthropic 2025; survey arXiv:2507.13334) is now the dominant framing — a benchmark in this name space arrives into a receptive but rapidly saturating audience.

The risk is real: **roughly one new memory or memory-budget benchmark has appeared per month since October 2025.** Acting in the next 1–3 months and emphasizing the *local + fixed-token-tier + agent-task triple* is essential.

## 4. Method-paper check (baseline candidates)

The strongest baseline set, balancing coverage, reproducibility, and local-hardware viability, is six methods covering all required families:

1. **Truncation + sliding-window** (LangChain `ConversationBufferWindowMemory`) as the no-management floor.
2. **Summary-buffer** (LangChain `ConversationSummaryBufferMemory`) as the rolling-summary baseline used by virtually every applied paper.
3. **Vanilla RAG over an episodic store** plus a **selective/agentic-RAG variant** (CRAG-style) covering the dominant retrieval paradigm.
4. **MemGPT/Letta** (Packer et al., arXiv:2310.08560; Letta on GitHub) as the canonical hierarchical OS-style memory baseline.
5. **Mem0** (Chhikara et al., arXiv:2504.19413) or **A-Mem** (Xu et al., NeurIPS 2025, arXiv:2502.12110) as the 2024–2025-generation production hierarchical/graph memory.
6. **LLMLingua-2** (Jiang et al., arXiv:2403.12968) as the prompt-compression baseline — uniquely valuable because it has a **continuous compression-ratio knob (2×–20×)** that produces smooth budget/quality curves.

Optional 7th slot: the **Generative Agents** memory architecture (Park et al., UIST 2023) — recency × importance × relevance retrieval with reflection — adds a different retrieval-scoring axis and is pure-prompting.

**Methods to explicitly exclude as baselines** (cite as comparators only): AutoCompressor, ICAE, and Gist tokens all require fine-tuned-checkpoint-specific base models and cannot be applied to arbitrary local LLMs. LongMem requires a residual side-network on a frozen backbone in a dated fairseq stack. Self-RAG specifically requires its fine-tuned Llama-2 critic model. Voyager is Minecraft-coupled. Anthropic's context editing + memory tool is **Claude-API-only** (`context-management-2025-06-27` beta). FoldGRPO and AgentFold require RL fine-tuning of the policy — only manual-folding ablations are tractable. Zep/Graphiti requires Neo4j infrastructure that complicates a minimalist harness.

## 5. Automatic grading feasibility

Grading is the make-or-break risk for this paper. The verdict by task type:

**Long-horizon coding — well-established (low risk).** SWE-bench Verified provides deterministic Docker-based pytest grading on 500 real GitHub issues; local 32B coders (Skywork-SWE-32B, SWE-Dev-32B based on Qwen2.5-Coder-32B) score 36–47%, leaving plenty of dynamic range to show context-budget effects. **LongCodeBench / LongSWE-Bench** (arXiv:2505.07897) already demonstrates Qwen2.5-14B dropping from 70.2% → 40% as context grows, validating the hypothesis cheaply. Use mini-SWE-agent as the harness (lower token overhead than OpenHands, standard for open models).

**Multi-turn tool-use chains — established but subtle (low–medium risk).** **τ²-bench** (Sierra) provides deterministic state-comparison grading with the `pass^k` reliability metric; it runs locally via LiteLLM and Qwen3-30B-A3B baselines around 58–67% on airline give clean dynamic range. **BFCL v3/v4** adds AST-based deterministic checking on multi-turn-and-multi-step tool calls. The variance source is the user-simulator LLM in τ-bench — pin it (a fixed local 70B or a frozen API call) and report version, which is standard 2026 practice. **Avoid ToolBench's LLM-as-judge mode.**

**Multi-doc synthesis with distractors — partially established (medium risk for free-form, low for MCQ).** **LongBench v2** (Bai et al., ACL 2025) is the most reviewer-defensible choice: 503 four-way MCQ items at 8K–2M tokens, exact-match grading, deliberately chosen by its authors to avoid F1/ROUGE noise. Pair with **MuSiQue-Ans** (EM/F1 with anti-shortcut filtering) for the harder long-form regime. LongBench v1 multi-doc QA tasks are drop-in via lm-evaluation-harness.

**Hard rule for this paper: deterministic graders only.** No LLM-as-judge. This rules out a few attractive task pools (some long-form summarization, ToolBench win-rate) but is essential for peer-review credibility on a *benchmark paper*.

## 6. Novelty verdict

**The idea is genuinely open at the level of a community benchmark, but partially preempted at the level of evaluation pattern.** Anyone reviewing this work will know ContextBudget/BACM-RL and will ask the differentiation question first. Three answers must survive that question:

The first defensible distinction is **scope of contribution**: ContextBudget and BudgetMem are method papers that invented their own ad-hoc evaluation harness; this benchmark is the standardization those methods need, with a third-party plug-in interface for memory strategies and a public leaderboard. The second is **local-LLM regime**: every adjacent benchmark leads with frontier proprietary models and treats constrained context as a temporary inconvenience; this benchmark treats it as the deployment reality on consumer hardware (8B–32B quantized), where context is genuinely scarce and the strategy choice matters most. The third is **task breadth across long-horizon agentic work**: ContextBudget covers web + QA only; this benchmark unifies SWE-style coding (deterministic pytest), tool-use chains (state-comparison), and multi-doc synthesis (MCQ) under one budget protocol.

**Sharpest novelty claim that survives the scan:** *"The first standardized benchmark that fixes a local LLM, sweeps active context budgets across deployment-realistic tiers (2k/4k/8k/16k/32k), and reports the Pareto frontier of quality vs. budget for swappable memory strategies on long-horizon agent tasks (SWE-bench Verified, τ²-bench, LongBench v2/MuSiQue), with a plug-in API and reference baselines."*

**Required framing pivots:** lead with **"local agents"** as the binding constraint and the **"swappable strategy interface"** as the contribution. Do *not* claim novelty on "varying context budget" alone (RULER, BABILong, HELMET, ContextBudget all do this for some setting) and do not claim novelty on "comparing memory strategies" alone (MemoryAgentBench, MemBench do this without budget tiers). The novelty is the **conjunction**, not any single axis.

**Workshop and competition risks:** MemAgents@ICLR 2026 has already run (Feb deadline). NeurIPS 2026 Datasets & Benchmarks track is the natural primary target. No Kaggle, DrivenData, LMSys, or HuggingFace leaderboard currently formalizes this axis — this is a real opening for a community leaderboard launched alongside the paper.

## 7. Scoping for the constraints

**Hardware reality check.** The "RTX 5060 16GB" almost certainly refers to the **RTX 5060 Ti 16GB** (GB206, 4608 CUDA, 448 GB/s, 180W) — the vanilla 5060 ships only with 8GB and the mobile 5060 has no 16GB SKU. This matters because GPU memory bandwidth caps long-context tok/s. Verify before committing.

The realistic model lineup, given verified KV-cache math (Qwen2.5-14B at 32K consumes ~6 GB KV in FP16, ~1.5 GB at Q4) and community/MLX measurements:

| Model | Quant | RTX 5060 Ti 16GB | M4 Pro 64GB | M5 Pro 48GB |
|---|---|---|---|---|
| Llama-3.1-8B | Q4_K_M | 32K @ ~60 tok/s | 32K @ ~30 tok/s | 32K–64K @ ~40 tok/s |
| **Qwen2.5/3-14B** | Q4_K_M | **32K @ ~32 tok/s (sweet spot)** | 32K–64K @ ~18 tok/s | 64K @ ~22 tok/s |
| **Qwen2.5/3-32B** | Q4_K_M | Does not fit | **32K @ 12–18 tok/s** | **32K–65K @ ~15 tok/s** |
| **Qwen3-Coder-30B-A3B** (MoE) | Q4 | Marginal at 4K | **32K–64K @ 30–60 tok/s** | **64K+ @ 40–70 tok/s** |
| Llama-3.3-70B | Q4_K_M | No | Marginal, not recommended | No (48GB tight) |

**Drop 70B from scope** — it's a different paper. **Cap context sweeps at 32K** because (a) all three machines handle 32K cleanly at 14B, (b) all three target models natively support 32K, and (c) it gives a clean 4× log-spaced sweep at 2K/4K/8K/16K/32K. Use **Q8 KV-cache quantization** for the long-context runs to stretch the 5060 Ti.

**Inference stacks:** llama.cpp (or vLLM with W4A16/AWQ on Blackwell) on the 5060 Ti, **MLX on Macs** (20–50% faster than llama.cpp on Apple Silicon, especially M5 which uses Neural Accelerators for 4× prefill speedup over M4). Pin one stack per platform and report KV-quant settings.

**Minimum viable benchmark for a 1-month paper:** 3 models × 5 budget tiers × 3 task families × ~500 total task instances × 6 strategies. Compute budget estimate: with combined ~5M generated tokens/day across the three machines and a benchmark cost around ~37M tokens (SWE-bench dominates), the suite fits comfortably in two weeks of wall-clock, leaving time for re-runs, sensitivity studies, and writing.

**Cheap pilot to validate the core hypothesis before building the full harness:** run truncation, summary-buffer, and vanilla RAG on Qwen2.5-14B at 4K/8K/16K on **20 SWE-bench Verified instances** and **50 LongBench v2 multi-doc items**. If quality differences exceed ~10 absolute points across strategies at the 4K tier and curves are non-monotonic across budgets (some strategy crosses another), the hypothesis is alive and the full benchmark is worth building. This pilot takes 2–3 days.

## 8. Final paper plan

**Title (sharpened):** *"How small can your context get? A budget-tiered benchmark for memory strategies in local LLM agents"* — alternative shorter form: *"BudgetBench: standardized context-budget tradeoff curves for local agent memory."*

**Crisp scientific question:** *Holding the local LLM and task fixed, which memory-management strategy dominates at each active-context-budget tier, and how does the dominance frontier shift with task type, dependency depth, and evidence dispersion?*

**Precise novelty claim:** the first benchmark that (a) treats active context budget as a primary controlled axis at standardized tiers (2K–32K), (b) provides a swappable third-party strategy interface, (c) covers long-horizon coding + tool-use + multi-doc synthesis with deterministic graders, and (d) targets the local-LLM deployment regime where the tradeoff actually bites. Defended against ContextBudget (method, not benchmark; web+QA only; cloud-scale), BudgetMem (method, not benchmark; QA/dialogue only; module-tier rather than token-tier), and MemoryAgentBench (no budget axis; QA-shaped tasks).

**Concrete benchmark design.** Three task families with deterministic graders: **(1)** SWE-bench Verified 100-instance stratified subset with mini-SWE-agent harness, max 30 turns, % Resolved metric; tagged by repo size and dependency depth. **(2)** τ²-bench retail + airline full sets (~200 tasks), `pass^k` with k=4 and a pinned user-simulator; tagged by required tool-call count and policy-document length. **(3)** LongBench v2 multi-doc QA filtered to 8K–32K range (~80 items) plus MuSiQue-Ans 1K dev items; tagged by evidence dispersion (number of supporting paragraphs) and recall-vs-recognition demand (free-form vs. MCQ).

**Active-budget protocol.** A budget enforcer wraps every LLM call, measures pre-call context tokens, raises a violation if it exceeds the tier ceiling, and the strategy must respond. Five tiers at 2K, 4K, 8K, 16K, 32K. Report quality, mean used budget, peak budget, violation rate, and tokens-per-task-resolved as the cost metric. Open-source the harness as a Python package with a `MemoryStrategy` ABC.

**Baseline strategies (six required, optional seventh).** Truncation + sliding-window; summary-buffer; vanilla RAG over an episodic FAISS store with bge-small embeddings; MemGPT/Letta; Mem0 (or A-Mem); LLMLingua-2 with a swept compression ratio. Optional: Generative Agents recency × importance × relevance retrieval.

**Hardware-feasible matrix.** Primary: Qwen2.5-14B-Instruct Q4_K_M on the 5060 Ti as the workhorse and Qwen2.5-32B-Instruct Q4_K_M on the M4 Pro as the larger anchor. Secondary: Qwen3-Coder-30B-A3B MoE on the M5 Pro for the MoE-vs-dense axis (this is currently the strongest local agent-coding model). Optional small reference: Llama-3.1-8B Q4 on the 5060 Ti for the speed lower bound.

**1-month plan with weekly milestones.** Week 1: implement the harness, the `MemoryStrategy` ABC, the budget enforcer, and three of six baselines (truncation, summary-buffer, vanilla RAG); run the cheap pilot on 20 SWE + 50 LongBench v2 items at three budgets to validate the hypothesis. Week 2: implement the remaining baselines (MemGPT/Letta, Mem0, LLMLingua-2); finalize task suites and tags; first full sweep on Qwen2.5-14B across all three tasks. Week 3: full sweep on the 32B model and Qwen3-Coder-30B-A3B; sensitivity studies (KV-quant, embedder choice, simulator pin). Week 4: writing, figure polish, harness documentation, arXiv preprint. **Stretch goals (3-month version):** add a continuous λ-weighted Pareto-frontier formulation alongside discrete tiers; add the MoE-vs-dense ablation as a first-class result; add WebArena lite as a fourth task family; add a public leaderboard with strategy submissions.

**Risks and mitigations.** *Risk 1: ContextBudget reviewer asks "what's new?"* Mitigation: lead with the third-party swappable interface and local-LLM scope; explicitly reference and frame ContextBudget-style methods as users of the benchmark. *Risk 2: SWE-bench full evaluation blows the compute budget.* Mitigation: 100-instance stratified subset, mini-SWE-agent, turn cap at 30. *Risk 3: τ²-bench user-simulator non-determinism contaminates results.* Mitigation: pinned simulator with temperature 0; report `pass^k` with k≥4; document simulator version. *Risk 4: KV cache OOM on 5060 Ti above 14B Q4 at 32K.* Mitigation: Q8 KV-cache quantization; route 64K stretch-goal runs to Macs only. *Risk 5: another budget benchmark scoops the work in the next 60 days.* Mitigation: post arXiv preprint within 30 days, even if D&B submission is later; emphasize the swappable-interface contribution which is mechanically the hardest piece to replicate quickly.

**Suggested target venues, in priority order.** **(1) arXiv preprint within 30 days** — non-negotiable given field velocity. **(2) NeurIPS 2026 Datasets & Benchmarks track** (typical deadline late May/early June 2026) — the natural home; benchmark papers with deterministic graders, plug-in interfaces, and cross-strategy results fit the track exactly. **(3) ICLR 2027 main track or D&B** as fallback if NeurIPS doesn't land. **(4) Workshop alternatives**: NeurIPS 2026 workshop on agents/memory (likely call), an ICLR 2027 follow-up to MemAgents, or the EMNLP 2026 industry track if a local-deployment angle is emphasized. **(5) Open-source release timing**: harness public at preprint time, leaderboard live at venue acceptance.

## Conclusion

The proposed benchmark sits in a fast-moving field where the *evaluation pattern* — sweep token budget, compare memory strategies — has been independently invented several times in the last six months, but always inside method papers and never as a community standard. The opening is real but narrow: ship a deterministic-grader-only, swappable-interface, local-LLM-focused harness with a hypothesis-validating pilot inside 30 days, and the work has a defensible novelty claim against every existing artifact. Wait three months without an arXiv preprint and the most likely outcome is that ContextBudget v2 or a NeurIPS-2026-deadline competitor occupies this space first. The hardware on hand is sufficient for the scoped 8B–32B regime; the deterministic grading infrastructure for all three task families exists off the shelf; the six baseline implementations are mostly pip-installable. The remaining work is the harness, the protocol document, and the experiments. **Build the pilot this week.**