# Phase 05: Hardware Detection - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-17
**Phase:** 05-hardware-detection
**Areas discussed:** Detection library strategy, module location, CPU-only detection, data structure, edge cases

---

## Detection Library Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| torch / metal (Python APIs) | Most accurate VRAM/model info but adds torch as a dependency (~2GB full, ~100MB cpu-only) | |
| CLI fallbacks (nvidia-smi, system_profiler) | Zero new Python deps, lighter but platform-specific shell commands | |
| psutil + CLI fallbacks | psutil for CPU/RAM (light dep, ~50KB) + CLI fallbacks for GPU | ✓ |

**User's choice:** psutil + CLI fallbacks
**Notes:** psutil is the lightest possible detection path that still gives CPU/RAM reliably. GPU detection delegated to platform CLI tools.

## Module Location

| Option | Description | Selected |
|--------|-------------|----------|
| src/budgetbench/utils/hardware.py | Single file alongside types.py and exceptions.py | ✓ |
| src/budgetbench/profiler/ package | Separate module for future extensibility | |

**User's choice:** src/budgetbench/utils/hardware.py
**Notes:** Keep it simple, matches existing codebase structure.

## CPU-Only Detection

| Option | Description | Selected |
|--------|-------------|----------|
| Report CPU model + RAM when no GPU | Return None/0 for GPU fields, set cpu_only=True | ✓ |
| Skip GPU fields entirely | Just report what psutil gives | |

**User's choice:** Report CPU model + RAM when no GPU
**Notes:** CPU-only systems should still get full CPU/RAM report with cpu_only flag.

## Data Structure

| Option | Description | Selected |
|--------|-------------|----------|
| TypedDict (matches types.py pattern) | TypedDict with optional fields | ✓ |
| dataclass with __repr__ | dataclass with named fields | |
| Plain dict | Plain dict, no import overhead | |

**User's choice:** TypedDict matching types.py pattern
**Notes:** Consistent with existing codebase conventions.

## Edge Cases

| Option | Description | Selected |
|--------|-------------|----------|
| Report CPU model + RAM when no GPU | WSL2/Docker passthrough detection | ✓ |
| Skip GPU fields entirely | Just report psutil data | |

**User's choice:** Report CPU model + RAM when no GPU
**Notes:** WSL2/Docker with GPU passthrough should report passthrough GPU if detectable via nvidia-smi.

---

## Claude's Discretion

- Field naming conventions (TypedDict with Optional fields)
- Exact CLI command parsing (nvidia-smi output format, system_profiler output parsing)
- Error handling granularity (warning vs silent skip per field)

## Deferred Ideas

- GPU compute capability detection (not needed for model recommendation)
- Multi-GPU support (single-GPU assumption for consumer hardware)
- Real-time thermal/throttling detection (out of scope for profiler)
