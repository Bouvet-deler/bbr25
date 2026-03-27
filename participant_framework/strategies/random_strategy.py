"""
Random strategy — the absolute baseline.

Picks a random legal action every time. This is the bar your strategy
must beat. Useful for testing that everything works end-to-end.

Expected performance: ~1-3 coins per game.
"""
import random
from typing import List

import numpy as np

from strategies.base_strategy import ActionStrategy


class RandomStrategy(ActionStrategy):
    """Picks a random legal action. The simplest possible agent."""

    def select_action(
        self, observation: np.ndarray, legal_actions: List[int], phase: int
    ) -> int:
        return random.choice(legal_actions)
