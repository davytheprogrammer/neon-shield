#!/usr/bin/env python3
"""
Root-level entry-point shim for MITM-INTERCEPT.
Delegates to src/cli/main.py so the project root can be on sys.path.
"""
import sys
import os

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cli.main import main

if __name__ == "__main__":
    main()
