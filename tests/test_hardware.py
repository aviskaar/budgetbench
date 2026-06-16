"""Tests for hardware detection module."""

from unittest.mock import patch, MagicMock

import pytest

from budgetbench.utils.hardware import (
     detect_hardware,
     _detect_gpu_linux,
     _detect_gpu_macos,
     _detect_gpu_windows,
     _detect_cpu_model,
     _run_cmd,
)


class TestRunCmd:
     def test_success_returns_stdout(self):
         result = MagicMock(returncode=0, stdout="hello\n", stderr="")
         with patch("budgetbench.utils.hardware.subprocess.run", return_value=result):
             assert _run_cmd(["echo", "hello"]) == "hello"

     def test_nonzero_returncode_returns_none(self):
         result = MagicMock(returncode=1, stdout="", stderr="err")
         with patch("budgetbench.utils.hardware.subprocess.run", return_value=result):
             assert _run_cmd(["false"]) is None

     def test_timeout_returns_none(self):
         import subprocess as sp
         with patch("budgetbench.utils.hardware.subprocess.run",
                     side_effect=sp.TimeoutExpired(cmd=["sleep"], timeout=10)):
             assert _run_cmd(["sleep", "999"]) is None

     def test_oserror_returns_none(self):
         with patch("budgetbench.utils.hardware.subprocess.run",
                     side_effect=FileNotFoundError("not found")):
             assert _run_cmd(["nonexistent_cmd"]) is None


class TestGPUDetectionLinux:
     def test_nvidia_detects_gpu_and_vram(self):
          # nvidia-smi --format=csv uses comma separator
         output = "NVIDIA GeForce RTX 5060 Ti, 16384 MiB"
         with patch("budgetbench.utils.hardware._run_cmd", return_value=output):
             model, vram = _detect_gpu_linux()
         assert model == "NVIDIA GeForce RTX 5060 Ti"
         assert vram == 16

     def test_nvidia_no_memory_field(self):
          # nvidia-smi CSV format always has comma, even with single field
         output = "NVIDIA GeForce RTX 4090,"
         with patch("budgetbench.utils.hardware._run_cmd", return_value=output):
             model, vram = _detect_gpu_linux()
         assert model == "NVIDIA GeForce RTX 4090"
         assert vram is None

     def test_nvidia_command_fails_returns_none(self):
         with patch("budgetbench.utils.hardware._run_cmd", return_value=None):
             model, vram = _detect_gpu_linux()
         assert model is None
         assert vram is None


class TestGPUDetectionMacOS:
     def test_apple_silicon_detects_gpu_and_unified_memory(self):
         output = """Graphics/Displays:

     Apple M4 Pro:

       Chipset Model: Apple M4 Pro
       Type: GPU
       Total Number of Cores: 20"""
         with patch("budgetbench.utils.hardware._run_cmd", return_value=output):
             with patch("psutil.virtual_memory", return_value=MagicMock(total=64 * 1024**3)):
                 model, vram = _detect_gpu_macos()
         assert model == "Apple M4 Pro"
         assert vram == 64

     def test_no_chipset_line_returns_none(self):
         with patch("budgetbench.utils.hardware._run_cmd", return_value="nothing here"):
             model, vram = _detect_gpu_macos()
         assert model is None
         assert vram is None


class TestGPUDetectionWindows:
     def test_wmi_detects_gpu_and_vram(self):
         output = "Name: NVIDIA GeForce RTX 5060 Ti\n\nAdapterRAM: 17179869184"
         with patch("budgetbench.utils.hardware._run_cmd", return_value=output):
             model, vram = _detect_gpu_windows()
         assert model == "NVIDIA GeForce RTX 5060 Ti"
          # 17179869184 bytes = 16384 MB = 16 GB
         assert vram == 16

     def test_wmi_no_adapter_ram(self):
         output = "Name: Intel Iris Xe"
         with patch("budgetbench.utils.hardware._run_cmd", return_value=output):
             model, vram = _detect_gpu_windows()
         assert model == "Intel Iris Xe"
         assert vram is None


class TestCPUModel:
     def test_linux_cpu_model(self):
         output = "Model name: Intel Core i7-13700K"
         with patch("budgetbench.utils.hardware._run_cmd", return_value=output):
             assert _detect_cpu_model() == "Intel Core i7-13700K"

     def test_macos_cpu_model(self):
          # lscpu returns None on macOS, sysctl returns the CPU string
         with patch("budgetbench.utils.hardware._run_cmd", side_effect=[None, "Apple M4 Pro"]):
             assert _detect_cpu_model() == "Apple M4 Pro"

     def test_fallback_unknown(self):
         with patch("budgetbench.utils.hardware._run_cmd", return_value=None):
             assert _detect_cpu_model() == "Unknown"


class TestDetectHardware:
     def test_returns_all_fields_macos(self):
          # On macOS, _detect_gpu_macos is called
         with patch("budgetbench.utils.hardware._detect_gpu_macos", return_value=("Apple M4 Pro", 64)):
             with patch("budgetbench.utils.hardware._detect_cpu_model", return_value="Apple M4 Pro"):
                 with patch("psutil.cpu_count", return_value=14):
                     with patch("psutil.virtual_memory", return_value=MagicMock(total=64 * 1024**3)):
                         report = detect_hardware()
         assert report["gpu_model"] == "Apple M4 Pro"
         assert report["vram_gb"] == 64
         assert report["cpu_model"] == "Apple M4 Pro"
         assert report["cpu_cores"] == 14
         assert report["ram_gb"] == 64
         assert report["cpu_only"] is False

     def test_cpu_only_flag_when_no_gpu(self):
         with patch("budgetbench.utils.hardware._detect_gpu_macos", return_value=(None, None)):
             with patch("budgetbench.utils.hardware._detect_cpu_model", return_value="Test CPU"):
                 with patch("psutil.cpu_count", return_value=4):
                     with patch("psutil.virtual_memory", return_value=MagicMock(total=8 * 1024**3)):
                         report = detect_hardware()
         assert report["cpu_only"] is True
         assert report["gpu_model"] is None
         assert report["vram_gb"] is None
         assert report["cpu_model"] == "Test CPU"
         assert report["ram_gb"] == 8

     def test_returns_typed_dict(self):
         with patch("budgetbench.utils.hardware._detect_gpu_macos", return_value=("Test GPU", 8)):
             with patch("budgetbench.utils.hardware._detect_cpu_model", return_value="Test CPU"):
                 with patch("psutil.cpu_count", return_value=2):
                     with patch("psutil.virtual_memory", return_value=MagicMock(total=4 * 1024**3)):
                         report = detect_hardware()
         assert isinstance(report, dict)
