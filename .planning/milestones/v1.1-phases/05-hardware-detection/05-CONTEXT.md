# Phase 05: Hardware Detection - Context

**Gathered:** 2026-05-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Detect user's GPU (model name + VRAM in GB), CPU core count, and total system RAM with cross-platform support (Linux/NVIDIA, macOS/Apple Silicon, CPU-only). Returns a structured hardware report used by Phase 6 (Recommendation Engine) to suggest optimal model + budget tier.

</domain>

<decisions>
## Implementation Decisions

### Detection Strategy
- **D-01:** Use `psutil` as primary detection library (lightweight ~50KB, cross-platform CPU/RAM detection). GPU detection uses CLI fallbacks: `nvidia-smi` on Linux, `system_profiler` on macOS.
- **D-02:** `psutil` is a new dependency — lightest possible detection path that still gives CPU/RAM reliably.
- **D-03:** CLI fallbacks for GPU: `nvidia-smi --query-gpu=name,memory.total --format=csv` on Linux; `system_profiler GPUMetalDataType` on macOS.

### Module Location
- **D-04:** Hardware detection lives in `src/budgetbench/utils/hardware.py` — single file alongside `types.py` and `exceptions.py`.
- **D-05:** Export a single public function: `detect_hardware() -> HardwareReport`.

### Data Structure
- **D-06:** TypedDict matching existing `types.py` pattern in `src/budgetbench/utils/types.py`.
- **D-07:** Fields: `gpu_model: Optional[str]`, `vram_gb: Optional[int]`, `cpu_model: str`, `cpu_cores: int`, `ram_gb: int`, `cpu_only: bool`.

### CPU-Only Detection
- **D-08:** Explicitly detect and flag CPU-only systems (no GPU). Set `gpu_model=None`, `vram_gb=None`, `cpu_only=True`.
- **D-09:** CPU-only systems still report `cpu_model`, `cpu_cores`, `ram_gb` from psutil.

### Edge Cases
- **D-10:** WSL2 / Docker with GPU passthrough: report the passthrough GPU if detectable via `nvidia-smi`, otherwise fall back to CPU-only detection.
- **D-11:** If `psutil` import fails (shouldn't happen — it's a required dep), fall back to pure CLI detection.
- **D-12:** If CLI commands fail (permission denied, not installed), log warning and return None for that field.

### Claude's Discretion
- Field naming conventions (already decided: TypedDict with Optional fields)
- Exact CLI command parsing (nvidia-smi output format, system_profiler output parsing)
- Error handling granularity (warning vs silent skip per field)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 5 goal and success criteria.
- `.planning/REQUIREMENTS.md` — PROF-01 (GPU model + VRAM), PROF-02 (CPU cores + RAM).
- `.planning/PROJECT.md` — Target hardware constraints (RTX 5060 Ti 16GB, M4/M5 Pro).

### Existing Code
- `src/budgetbench/utils/types.py` — TypedDict pattern to follow, BUDGET_TIERS constant.
- `src/budgetbench/utils/__init__.py` — Module init (currently empty).
- `src/budgetbench/core/exceptions.py` — Exception pattern to follow.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/budgetbench/utils/types.py` — `TypedDict` base class pattern, `Optional` imports.
- `src/budgetbench/core/exceptions.py` — Simple exception class pattern (single line body).

### Established Patterns
- TypedDict with `total=False` for optional fields (types.py pattern).
- No heavy dependencies — psutil is the lightest possible detection dep (~50KB).
- CLI fallbacks use `subprocess.run(..., capture_output=True, text=True)`.

### Integration Points
- `hardware.detect_hardware()` called by Phase 6 recommendation engine.
- `BUDGET_TIERS` from `utils/types.py` used by recommendation logic in Phase 6.

</code_context>

<specifics>
## Specific Ideas

- TypedDict name: `HardwareReport`
- Public API: single function `detect_hardware() -> HardwareReport`
- psutil: `psutil.cpu_count(logical=True)`, `psutil.virtual_memory().total`
- nvidia-smi query: `--query-gpu=name,memory.total --format=csv`
- macOS: `system_profiler GPUMetalDataType` returns GPU name and memory

</specifics>

<deferred>
## Deferred Ideas

- GPU compute capability detection (not needed for model recommendation)
- Multi-GPU support (single-GPU assumption for consumer hardware)
- Real-time thermal/throttling detection (out of scope for profiler)

</deferred>

---

*Phase: 05-hardware-detection*
*Context gathered: 2026-05-17*
