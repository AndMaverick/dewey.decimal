"""Dewey.Decimal: decision-ready text statistics. One spec (spec/SPEC.md), three implementations that print byte-identical output."""
from .core import analyse, to_json

__version__ = "1.0.0"
__all__ = ["analyse", "to_json", "__version__"]
