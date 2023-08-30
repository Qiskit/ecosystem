"""Docstring."""
import math
from typing import Union


class Impl:
    """Demo impl."""

    def __init__(self):
        """Demo impl."""
        self.pow = 2

    def run(self, number: Union[int, float]) -> Union[int, float]:
        """Run method."""
        from collections import Hashable

        return math.pow(number, self.pow)

    def __repr__(self):
        return f"Impl(pow: {self.pow})"
