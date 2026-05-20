---
phase: 06-recommendation-engine
plan: 06
type: execute
wave: 1
depends_on: ["05-02"]
files_modified: [src/budgetbench/utils/recommendation.py, tests/test_recommendation.py]
autonomous: true
requirements: [PROF-03]
---

<objective>
Build the recommendation engine that matches detected hardware to the optimal Qwen model + context budget tier based on VRAM vs model weights + KV-cache footprint.

Purpose: Give users a `detect_best_model()` function that returns a structured recommendation for their hardware.
Output: `recommendation.py` module + test suite.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/phases/06-recommendation-engine/06-CONTEXT.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Implement Recommendation Engine</name>
  <files>src/budgetbench/utils/recommendation.py</files>
  <action>
    Implement the recommendation engine module:
    - Define `RecommendationReport` TypedDict with fields: model_name, budget_tier, vram_needed_gb, vram_available_gb, vram_limited, cpu_only_rec, notes.
    - Define `MODEL_REGISTRY` constant dict with VRAM estimates for all 6 Qwen Coder models (params_b, weights_gb, kv_per_1k_gb, moe).
    - Implement `_total_vram(model, tier_tokens)` — calculates weights (float16) + KV-cache (float16, tier-dependent).
    - Implement `detect_best_model(report: HardwareReport) -> RecommendationReport` using greedy largest-first:
      - Sort models by parameter size descending.
      - For each model, try tiers from largest to smallest.
      - Pick first model+tier where total_vram <= vram_gb * 0.9 (10% headroom).
      - CPU-only or VRAM < 4 GB: recommend Qwen2.5-Coder-1.5B at 2K tier with cpu_only_rec flag.
      - Fallback if no model fits: recommend 1.5B at 2K with "No model fits" note.
  </action>
  <verify>
    <automated>python -c "from budgetbench.utils.recommendation import detect_best_model, MODEL_REGISTRY; print(len(MODEL_REGISTRY), 'models registered')"</automated>
  </verify>
  <done>Recommendation engine module is implemented with model registry and detection logic.</done>
</task>

<task type="auto">
  <name>Task 2: Write Test Suite</name>
  <files>tests/test_recommendation.py</files>
  <action>
    Write comprehensive tests for the recommendation engine:
    - `TestTotalVram`: test KV-cache calculation for 1.5B/2K, 32B/32K, 30B-A3B/32K.
    - `TestDetectBestModel`: test high VRAM (64GB → 30B-A3B), 16GB, 8GB, 48GB, 128GB (32B), CPU-only, low VRAM (<4GB), fallback when no model fits, dict subclass verification.
  </action>
  <verify>
    <automated>python -m pytest tests/test_recommendation.py -v</automated>
  </verify>
  <done>All 12 tests pass covering all hot paths.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries
| Boundary | Description |
|----------|-------------|
| Hardware detection → Recommendation | Trusted internal module, no external input |

## STRIDE Threat Register
| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-06-06-01 | Injection | None | n/a | No external input — pure computation on detected hardware data. |
</threat_model>

<verification>
1. All tests pass: `python -m pytest tests/test_recommendation.py -v`
2. `detect_best_model()` returns correct recommendations for all success criteria scenarios (8GB, 16GB, 48GB+, CPU-only).
3. `RecommendationReport` is a dict subclass with all required fields.
</verification>

<success_criteria>
1. Given 8 GB VRAM, the recommender selects a model + tier that fits within VRAM constraints (weights + KV-cache).
2. Given 16 GB VRAM, the recommender selects a higher-tier model or larger context budget than for 8 GB.
3. Given 48+ GB RAM (M4/M5 Pro), the recommender suggests the highest viable model + 32K tier.
4. CPU-only systems receive a conservative recommendation with explicit VRAM limitation notice.
</success_criteria>

<output>
After completion, create `.planning/phases/06-recommendation-engine/06-SUMMARY.md`
</output>
