#!/usr/bin/env python3
"""Entry point: run full Hormuz–Philippine urea scenario pipeline."""

from pathlib import Path

# Ensure src is on path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.runner import run_pipeline


if __name__ == "__main__":
    run_pipeline()
