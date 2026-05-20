# Phase 05: Hardware Detection - Summary

**Executed:** 2026-05-17
**Status:** Complete

## What was implemented

### `src/budgetbench/utils/hardware.py`
- Single-file hardware detection module with `detect_hardware() -> HardwareReport`
- Cross-platform GPU detection:
  - Linux: `nvidia-smi --query-gpu=name,memory.total`
  - macOS: `system_profiler SPDisplaysDataType` (Chipset Model)
  - Windows: PowerShell WMI `Win32_VideoController`
- Apple Silicon unified memory: VRAM = total RAM (correct for M-series)
- CPU/RAM via `psutil` (cross-platform, lightweight ~50KB)
- CPU-only flag when no GPU is detected

### `pyproject.toml`
- Project initialized with hatchling build backend
- `psutil>=5.9.0` as the only dependency
- CLI entry point `budgetbench = "budgetbench.cli:main"` scaffolded

### `tests/test_hardware.py`
- 17 tests covering all detection paths
- Mock-based tests for Linux/Windows GPU detection
- macOS-specific tests for Apple Silicon detection
- CPU-only flag verification
- All 17 tests passing

## Verification

- `detect_hardware()` returns correct report on M4 Pro:
  - GPU: Apple M4 Pro, 64 GB VRAM (unified memory)
  - CPU: Apple M4 Pro, 14 cores
  - RAM: 64 GB
  - cpu_only: false

## Success Criteria Met

1. **PROF-01:** GPU model + VRAM detection works on macOS (Apple M4 Pro, 64 GB)
2. **PROF-02:** CPU core count (14) and RAM (64 GB) returned accurately
3. **Fallback paths:** nvidia-smi (Linux), system_profiler (macOS), PowerShell (Windows) all implemented

## Files Created

- `src/budgetbench/utils/hardware.py` — hardware detection module
- `pyproject.toml` — project configuration
- `tests/test_hardware.py` — 17 test cases
