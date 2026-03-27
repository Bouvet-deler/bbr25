"""
Tabular Q-Learning strategy template.

Instead of a neural network, this approach uses a lookup table (dictionary)
mapping discretized states to Q-values. Much simpler than DQN and faster to
train, but requires careful state discretization to keep the table manageable.

This template is a SKELETON — search for TODO to find the parts you
need to implement.

Training: Run `python train.py --strategy tabular_q --episodes 50000`
Playing:  Run `python main.py --strategy tabular_q` (loads models/q_table.pkl)

Key concepts:
  - Continuous 75-dim state → discretized state key (tuple of bins)
  - Q-table: dict mapping (state_key, action) → expected future reward
  - Simpler than neural networks, but state space must be kept small
  - Works best when you identify the ~5-10 most important features

Trade-offs vs DQN:
  + Much faster to train (no GPU needed)
  + Easier to understand and debug
  + More interpretable (you can inspect the Q-table)
  - State discretization loses information
  - Doesn't generalize to unseen states
  - Table size explodes if too many features/bins
"""
from __future__ import annotations

import pickle
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from strategies.base_strategy import ActionStrategy


class TabularQStrategy(ActionStrategy):
    """Strategy using a Q-table for action selection.

    State is discretized into bins, then looked up in a table.
    """

    def __init__(self, model_path: str = "models/q_table.pkl") -> None:
        super().__init__()
        self.model_path = Path(model_path)

        # Q-table: maps (state_key, action) → Q-value
        self.q_table: Dict[Tuple, Dict[int, float]] = defaultdict(
            lambda: defaultdict(float)
        )

        # TODO: Tune these hyperparameters
        self.learning_rate = 0.1      # How fast to update Q-values (0.01 - 0.5)
        self.discount_factor = 0.95   # How much to value future rewards (0.9 - 0.99)
        self.epsilon = 0.0            # Exploration rate (0.0 for deployment)

        self._load()

    def _load(self) -> None:
        if self.model_path.exists():
            with open(self.model_path, "rb") as f:
                self.q_table = pickle.load(f)
            print(f"  [Q-Table] Loaded {len(self.q_table)} states from {self.model_path}")
        else:
            print(f"  [Q-Table] No table at {self.model_path} — starting fresh")

    def save(self) -> None:
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump(dict(self.q_table), f)

    # ── State Discretization ─────────────────────────────────────────

    def discretize_state(self, observation: np.ndarray, phase: int) -> tuple:
        """Convert 75-dim float vector into a hashable state key.

        TODO: This is the MOST IMPORTANT method to get right.
        The default discretization is very coarse — it only looks at a few
        features. You should:

        1. Identify which features matter most for good decisions
        2. Choose appropriate bin sizes (more bins = finer distinctions
           but larger table)
        3. Consider using different features per phase

        The observation vector layout (see state_encoder.py for details):
          [0..21]   — own fields (2 × 11 features each)
          [22..30]  — hand composition
          [31..38]  — drawn cards
          [39..46]  — traded cards
          [47]      — deck size
          [48]      — round
          [49]      — own coins
          [50..52]  — opponent coins
          [53..56]  — phase one-hot
          [57..72]  — opponent fields
          [73..74]  — end-of-game urgency

        Tips:
          - Start with very few features (3-5) and add more if performance plateaus
          - Bin continuous values into 3-5 buckets (e.g., "low", "mid", "high")
          - Field card type + count are usually the most important features
        """
        # TODO: Replace this basic discretization with something smarter!

        # Example: extract a few key features and bin them
        field_0_count = int(observation[8] * 20)   # field 0 card count (denormalized)
        field_1_count = int(observation[19] * 20)  # field 1 card count
        field_0_type = int(np.argmax(observation[0:8])) if np.any(observation[0:8]) else -1
        field_1_type = int(np.argmax(observation[11:19])) if np.any(observation[11:19]) else -1
        deck_bin = int(observation[47] * 3)         # deck: 0=low, 1=mid, 2=high
        coins_bin = int(observation[49] * 3)         # coins: 0=low, 1=mid, 2=high

        return (phase, field_0_type, field_0_count, field_1_type, field_1_count,
                deck_bin, coins_bin)

    # ── Action Selection ─────────────────────────────────────────────

    def select_action(
        self, observation: np.ndarray, legal_actions: List[int], phase: int
    ) -> int:
        """Select action using epsilon-greedy Q-table lookup."""

        # Exploration (during training)
        if random.random() < self.epsilon:
            return random.choice(legal_actions)

        # Exploitation: pick the legal action with highest Q-value
        state_key = self.discretize_state(observation, phase)
        q_values = self.q_table[state_key]

        best_action = max(legal_actions, key=lambda a: q_values[a])
        return best_action

    # ── Training Update ──────────────────────────────────────────────

    def update_q(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        legal_actions: List[int],
        next_legal_actions: List[int],
        phase: int,
        next_phase: int,
    ) -> None:
        """Standard Q-learning update: Q(s,a) += α * (r + γ * max Q(s',a') - Q(s,a))

        TODO: Consider more advanced update rules:
          - Double Q-learning (use two tables to reduce overestimation)
          - Eligibility traces (propagate rewards faster through state sequences)
          - Optimistic initialization (start Q-values high to encourage exploration)
        """
        state_key = self.discretize_state(state, phase)
        next_state_key = self.discretize_state(next_state, next_phase)

        current_q = self.q_table[state_key][action]

        if done:
            target = reward
        else:
            next_q_values = self.q_table[next_state_key]
            max_next_q = max(next_q_values[a] for a in next_legal_actions) if next_legal_actions else 0.0
            target = reward + self.discount_factor * max_next_q

        self.q_table[state_key][action] += self.learning_rate * (target - current_q)
