"""
DQN (Deep Q-Network) strategy template.

Uses a neural network to estimate Q-values for each action, then picks
the action with the highest Q-value (masked to only legal actions).

This strategy extends ActionStrategy — you only need to implement
select_action() which maps (observation, legal_actions, phase) → action.

The DQN agent is trained offline using the simulator (see train.py).
Once trained, the model is loaded here for live play.

┌─────────────────────────────────────────────────────────────────┐
│  HOW TO USE THIS TEMPLATE                                       │
│                                                                 │
│  1. Train a model:  python train.py --strategy dqn              │
│  2. Play live:      python main.py --strategy dqn               │
│                                                                 │
│  The model file is saved to models/best.pt during training.     │
│  This strategy loads it automatically.                          │
│                                                                 │
│  THINGS TO EXPERIMENT WITH (marked with TODO below):            │
│  - Network architecture (deeper? wider? different activations?) │
│  - State encoding (override encode_state for custom features)   │
│  - Exploration rate during live play                            │
│  - Separate models for different phases                         │
│  - Reward shaping in the training loop                          │
└─────────────────────────────────────────────────────────────────┘
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np

from strategies.base_strategy import ActionStrategy


class DQNStrategy(ActionStrategy):
    """Strategy powered by a trained Deep Q-Network.

    Loads a pre-trained model and uses it to select actions greedily.
    """

    def __init__(self, model_path: str = "models/best.pt") -> None:
        super().__init__()
        self.model_path = Path(model_path)
        self.agent = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the trained DQN model."""
        from training.dqn_agent import DQNAgent

        # TODO: Experiment with different network sizes.
        # The default agent uses a DuelingQNetwork (defined in training/dqn_agent.py)
        # with hidden=128 for the shared backbone and the value/advantage heads.
        #
        # ── How to change the network architecture ───────────────────────────────
        # Option A (simplest): change the hidden size here:
        #   self.agent = DQNAgent(action_dim=6, hidden=256)
        #
        # Option B: modify DuelingQNetwork directly in training/dqn_agent.py
        #   (e.g. add more layers, change activations, add dropout)
        #
        # Option C: define a custom network and swap it in after creation:
        #   self.agent = DQNAgent(action_dim=6, hidden=128)
        #   self.agent.q_net = MyNetwork(STATE_SIZE, 6).to(self.agent.device)
        #   self.agent.target_net = MyNetwork(STATE_SIZE, 6).to(self.agent.device)
        #
        # Any architecture change requires retraining from scratch.
        self.agent = DQNAgent(action_dim=6, hidden=128)

        if self.model_path.exists():
            self.agent.load(self.model_path)
            self.agent.eps = 0.0  # pure exploitation — no random moves
            print(f"  [DQN] Loaded model from {self.model_path}")
        else:
            print(f"  [DQN] No model at {self.model_path} — using random actions")
            print(f"  [DQN] Train one first: python train.py --strategy dqn")
            self.agent.eps = 1.0  # fully random

    def select_action(
        self, observation: np.ndarray, legal_actions: List[int], phase: int
    ) -> int:
        """Select the best legal action using the trained Q-network.

        The DQN agent masks illegal actions with -inf before taking argmax,
        ensuring only legal moves are selected.
        """
        # TODO: Consider using a small epsilon (e.g. 0.05) during live play
        # to add some unpredictability. Pure greedy play can be exploited by
        # opponents who learn your patterns.
        return self.agent.select_action_greedy(observation, legal_actions)

    # TODO: Override encode_state() to experiment with custom features.
    # The default 75-element vector captures the basic game state, but you
    # could add features like:
    #   - Card counting (what's left in the deck for each type?)
    #   - Probability of drawing needed cards
    #   - Opponent behavior patterns
    #   - Trade history
    #
    # Example:
    #   def encode_state(self, game_state, player, phase_idx):
    #       base = super().encode_state(game_state, player, phase_idx)
    #       custom_features = np.array([...])
    #       return np.concatenate([base, custom_features])
    #
    # IMPORTANT: If you change the state size, you must also update the
    # DQN agent's state_dim and retrain the model!
