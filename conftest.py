"""Pytest configuration: ensure the project root is on sys.path."""
import sys
import os

# Add project root to sys.path so 'src' package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
