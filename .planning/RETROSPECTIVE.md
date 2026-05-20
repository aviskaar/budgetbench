# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.1 — Hardware Profiler

**Shipped:** 2026-05-20
**Phases:** 3 | **Plans:** 5 | **Sessions:** multiple

### What Was Built
- Cross-platform hardware detection module (GPU, CPU, RAM) with fallbacks for Linux/macOS/Windows
- Recommendation engine with greedy largest-first selection and VRAM headroom calculation
- `budgetbench profile` CLI command with human-readable and JSON output modes
- 416 lines of Python, 37 tests passing

### What Worked
- Single-file module design for hardware.py kept the detection logic simple and testable
- psutil for CPU/RAM detection is cross-platform with no compilation needed
- Greedy largest-first algorithm for model selection is simple and correct
- All 5 PROF requirements satisfied with no gaps

### What Was Inefficient
- Phase 05 missing VERIFICATION.md — documentation gap caught during audit
- Some SUMMARY.md files had inconsistent frontmatter format (requires vs provides vs requirements fields)

### Patterns Established
- Hardware detection: psutil primary, CLI fallbacks per platform
- Apple Silicon: VRAM = total RAM (unified memory architecture)
- Recommendation: 10% headroom buffer on VRAM calculations
- MoE models: use active parameter count (3 GB) not total parameters (30 GB) for weight estimation

### Key Lessons
1. Always write VERIFICATION.md during execute-phase — it saves audit time
2. SUMMARY.md frontmatter should use consistent field names (requirements vs requires vs provides)
3. 416 LOC with 37 tests is a healthy ratio for utility modules

### Cost Observations
- Model mix: Mix of opus/sonnet for code review and integration verification
- Notable: Integration checker agent caught no issues — clean cross-phase wiring

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 4 | 13 | Core benchmark harness built |
| v1.1 | 3 | 5 | Hardware profiler with full audit pipeline |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 52+ | Strategy, harness, metrics, tasks | psutil (1 dep) |
| v1.1 | 37 | Hardware, recommendation, profile | None (psutil already added) |

### Top Lessons (Verified Across Milestones)
1. Write VERIFICATION.md during execute-phase, not after
2. SUMMARY.md frontmatter consistency reduces audit friction
3. Integration checker catches wiring issues early — keep using it
