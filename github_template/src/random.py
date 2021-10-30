"""Docstring."""
import math
from typing import Union


class Random:
    """Demo random."""

    def __init__(self):
        """Demo random."""
        self.pow = 2

    def run(self, number: Union[int, float]) -> Union[int, float]:
        """Run method."""
        from collections import Hashable

        return math.pow(number, self.pow)

    def __repr__(self):
        return f"Random(pow: {self.pow})"
