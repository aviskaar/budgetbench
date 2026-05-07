"""Root conftest.py — adds src/ to sys.path so that budgetbench is importable
without requiring a package installation step."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
