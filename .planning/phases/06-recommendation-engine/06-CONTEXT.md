# Phase 06: Recommendation Engine - Context

**Gathered:** 2026-05-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Take the HardwareReport from Phase 5 and match it to the optimal Qwen model + context budget tier based on VRAM vs model weights + KV-cache footprint. Returns a structured recommendation.

</domain>

<decisions>
## Implementation Decisions

### Model Registry
- **D-01:** Qwen model registry as a constant dict in `recommendation.py` with per-model VRAM estimates per tier.
- **D-02:** VRAM = weights (float16) + KV-cache (float16, context-length dependent).
- **D-03:** Model VRAM estimates:
  - Qwen2.5-Coder-1.5B: weights=3 GB, KV-cache per 1K tokens ~0.02 GB
  - Qwen2.5-Coder-3B: weights=6 GB, KV-cache per 1K tokens ~0.06 GB
  - Qwen2.5-Coder-7B: weights=14 GB, KV-cache per 1K tokens ~0.14 GB
  - Qwen2.5-Coder-14B: weights=28 GB, KV-cache per 1K tokens ~0.28 GB
  - Qwen2.5-Coder-32B: weights=64 GB, KV-cache per 1K tokens ~0.64 GB
  - Qwen3-Coder-30B-A3B: weights=3 GB (MoE active), KV-cache per 1K tokens ~0.04 GB

### Recommendation Logic
- **D-04:** Greedy approach: sort models by parameter size (largest first), pick the first model+tier where total_vram <= vram_gb * 0.9 (10% headroom).
- **D-05:** CPU-only systems: recommend smallest model (1.5B) with lowest budget tier (2K), with `vram_limited: true` flag.
- **D-06:** If no model fits even at 2K tier, recommend CPU-only inference with `cpu_only_rec: true`.

### Data Structure
- **D-07:** `RecommendationReport` TypedDict: `model_name`, `budget_tier`, `vram_needed_gb`, `vram_available_gb`, `vram_limited`, `cpu_only_rec`, `notes`.

### Module Location
- **D-08:** `src/budgetbench/utils/recommendation.py` — single file alongside hardware.py.
- **D-09:** Export two functions: `detect_best_model(report: HardwareReport) -> RecommendationReport`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 6 goal and success criteria.
- `.planning/REQUIREMENTS.md` — PROF-03.

### Existing Code
- `src/budgetbench/utils/hardware.py` — HardwareReport type and detect_hardware().
- `src/budgetbench/utils/types.py` — TypedDict pattern.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `HardwareReport` from hardware.py — input type for recommendation.
- `_run_cmd` pattern from hardware.py — not needed here (no CLI calls).

### Established Patterns
- TypedDict with `total=False` for optional fields.
- Module-level constants for model registry.
- Greedy largest-first selection with VRAM validation.

</code_context>

<specifics>
## Specific Ideas

- Model registry: `{model_name: {params_b, weights_gb, kv_per_1k_gb}}`
- KV-cache formula: `layers * 2 * head_dim * 2 * context_len * batch_size / (1024^3)`
- Budget tiers from `types.py`: `[2048, 4096, 8192, 16384, 32768]`
- 10% headroom for OS/GPU overhead
- Sort by weights_gb descending, pick first that fits

</specifics>

<deferred>
## Deferred Ideas

- GPU utilization monitoring (not needed for static recommendation)
- Dynamic KV-cache compression based on workload (Phase 7 or later)
- Multi-GPU recommendations (single-GPU assumption for consumer hardware)

</deferred>

---

*Phase: 06-recommendation-engine*
*Context gathered: 2026-05-17*
