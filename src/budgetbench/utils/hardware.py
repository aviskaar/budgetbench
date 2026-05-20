"""Hardware detection for the BudgetBench profiler.

Detects GPU (model + VRAM), CPU cores, and system RAM with
cross-platform support (Linux/NVIDIA, macOS/Apple Silicon, CPU-only).
"""

import platform
import subprocess
import logging
from typing import Optional

import psutil

from .types import TypedDict

logger = logging.getLogger(__name__)


class HardwareReport(TypedDict, total=False):
    """Structured hardware report for the recommendation engine."""
    gpu_model: Optional[str]
    vram_gb: Optional[int]
    cpu_model: str
    cpu_cores: int
    ram_gb: int
    cpu_only: bool


def _run_cmd(cmd: list[str]) -> str | None:
    """Run a CLI command and return stdout, or None on failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return None


def _detect_gpu_linux() -> tuple[Optional[str], Optional[int]]:
    """Detect GPU via nvidia-smi on Linux."""
    output = _run_cmd(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"])
    if output:
        first_line = output.split("\n")[0].strip()
        parts = [p.strip() for p in first_line.split(",")]
        if len(parts) >= 2:
            gpu_name = parts[0]
            try:
                vram_mb = int(parts[1].replace(" MiB", "").strip())
                return gpu_name, max(1, vram_mb // 1024)
            except ValueError:
                return gpu_name, None
    return None, None


def _detect_gpu_macos() -> tuple[Optional[str], Optional[int]]:
    """Detect GPU via system_profiler on macOS.

    Apple Silicon uses unified memory, so VRAM equals total RAM.
    """
    output = _run_cmd(["system_profiler", "SPDisplaysDataType"])
    if output:
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("Chipset Model:"):
                gpu_name = line.split(":", 1)[1].strip()
                # Apple Silicon: unified memory, so VRAM ~= total RAM
                ram_gb = psutil.virtual_memory().total // (1024 ** 3)
                return gpu_name, ram_gb
    return None, None


def _detect_gpu_windows() -> tuple[Optional[str], Optional[int]]:
    """Detect GPU via WMI on Windows."""
    try:
        import ctypes  # noqa: F811

        # Use ADAPTERINFO via Windows API — too complex, fall back to PowerShell
        pass
    except ImportError:
        pass
    output = _run_cmd([
        "powershell", "-Command",
        "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM | Format-List"
    ])
    if output:
        gpu_name = None
        vram_mb = None
        for line in output.splitlines():
            if "Name" in line:
                gpu_name = line.split(":", 1)[1].strip()
            elif "AdapterRAM" in line:
                try:
                    vram_mb = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
        if gpu_name:
            if vram_mb:
                return gpu_name, max(1, vram_mb // (1024 ** 3))
            return gpu_name, None
    return None, None


def _detect_cpu_model() -> str:
    """Detect CPU model string cross-platform."""
    # Linux
    output = _run_cmd(["lscpu"])
    if output:
        for line in output.splitlines():
            if "Model name:" in line:
                return line.split(":", 1)[1].strip()

    # macOS
    output = _run_cmd(["sysctl", "-n", "machdep.cpu.brand_string"])
    if output and output.strip():
        return output.strip()

    # Windows
    output = _run_cmd([
        "powershell", "-Command",
        "Get-CimInstance Win32_Processor | Select-Object Name | Format-Value"
    ])
    if output and output.strip():
        return output.strip()

    return "Unknown"


def detect_hardware() -> HardwareReport:
    """Detect user's hardware configuration.

    Returns a HardwareReport with GPU model/VRAM, CPU model/cores,
    and system RAM. CPU-only systems get gpu_model=None, vram_gb=None,
    cpu_only=True.

    Detection priority:
    - GPU: platform-specific CLI (nvidia-smi / system_profiler / PowerShell)
    - CPU/RAM: psutil (cross-platform)
    """
    report: HardwareReport = {}

    # GPU detection
    system = platform.system()
    gpu_model = None
    vram_gb = None

    if system == "Linux":
        gpu_model, vram_gb = _detect_gpu_linux()
    elif system == "Darwin":
        gpu_model, vram_gb = _detect_gpu_macos()
    elif system == "Windows":
        gpu_model, vram_gb = _detect_gpu_windows()
    else:
        logger.warning("Unsupported platform %s, skipping GPU detection", system)

    cpu_only = gpu_model is None
    if cpu_only:
        logger.info("No GPU detected — running in CPU-only mode")

    # CPU and RAM via psutil
    try:
        cpu_cores = psutil.cpu_count(logical=True) or 1
    except (AttributeError, OSError):
        cpu_cores = 1

    try:
        ram_total = psutil.virtual_memory().total
        ram_gb = max(1, ram_total // (1024 ** 3))
    except (AttributeError, OSError):
        ram_gb = 1

    cpu_model = _detect_cpu_model()

    report["gpu_model"] = gpu_model
    report["vram_gb"] = vram_gb
    report["cpu_model"] = cpu_model
    report["cpu_cores"] = cpu_cores
    report["ram_gb"] = ram_gb
    report["cpu_only"] = cpu_only

    return report
