"""
Genetic / Evolutionary strategy template.

Instead of learning through trial-and-error updates (like Q-learning or DQN),
this approach EVOLVES a set of weights that score each possible action.
A population of weight vectors is maintained, and the best performers
are combined (crossover) and mutated to create the next generation.

This template is a SKELETON — search for TODO to find the parts you
need to implement.

Training: Run `python train.py --strategy genetic --episodes 200`
          (episodes here means generations, each evaluating the full population)
Playing:  Run `python main.py --strategy genetic` (loads models/genetic_best.pkl)

Key concepts:
  - Each "individual" is a weight vector that scores actions
  - For each legal action, compute: score = weights · features(state, action)
  - Pick the action with the highest score
  - Evolve weights using tournament selection, crossover, and mutation

Trade-offs vs DQN / Q-learning:
  + No gradient computation needed
  + Easy to parallelize (evaluate many individuals)
  + Works well with small, hand-crafted feature sets
  + Can find good solutions with very few generations
  - Doesn't use individual game experiences (less sample efficient)
  - Requires careful feature engineering
  - Population size trades off coverage vs computation
"""
from __future__ import annotations

import pickle
import random
from pathlib import Path
from typing import List

import numpy as np

from strategies.base_strategy import ActionStrategy


class GeneticStrategy(ActionStrategy):
    """Strategy using evolved weights for action scoring."""

    def __init__(self, model_path: str = "models/genetic_best.pkl") -> None:
        super().__init__()
        self.model_path = Path(model_path)

        # TODO: Set the number of features your scoring function uses.
        # This should match the output size of extract_features().
        self.num_features = 10

        # Weight vector: one weight per feature
        self.weights = np.zeros(self.num_features, dtype=np.float32)

        self._load()

    def _load(self) -> None:
        if self.model_path.exists():
            with open(self.model_path, "rb") as f:
                self.weights = pickle.load(f)
            print(f"  [Genetic] Loaded weights from {self.model_path}")
        else:
            print(f"  [Genetic] No weights at {self.model_path} — using zeros")

    def save(self) -> None:
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump(self.weights, f)

    # ── Feature Extraction ───────────────────────────────────────────

    def extract_features(
        self, observation: np.ndarray, action: int, phase: int
    ) -> np.ndarray:
        """Extract features for a (state, action) pair.

        TODO: This is the KEY method to implement! Design features that
        capture why an action is good or bad.

        The score for each action will be: dot(weights, features).
        Good features should be:
          - Informative: different values for good vs bad situations
          - Normalized: roughly in [0, 1] range
          - Relevant: capture what matters for the current phase

        Example features to consider:
          - Does this action plant on a matching field? (0 or 1)
          - How many cards are on the target field? (normalized)
          - Will harvesting this field earn coins? (normalized value)
          - How close is the field to the next threshold? (0-1)
          - Is this the last round? (0 or 1)
          - How many cards of this type remain in the deck? (estimated)
          - Would this trade give us a useful card? (0 or 1)

        Parameters
        ----------
        observation : np.ndarray
            The 75-element state vector.
        action : int
            The action to evaluate.
        phase : int
            Current phase (0-3).

        Returns
        -------
        np.ndarray
            Feature vector of length self.num_features.
        """
        features = np.zeros(self.num_features, dtype=np.float32)

        # TODO: Implement your feature extraction here!
        # Below are placeholder features — replace with your own.

        # Feature 0: bias term (always 1)
        features[0] = 1.0

        # Feature 1: current phase
        features[1] = phase / 3.0

        # Feature 2: is "skip" action? (action 2 in optional, action 0 in trading)
        features[2] = 1.0 if (phase == 1 and action == 2) or (phase == 2 and action == 0) else 0.0

        # Feature 3: deck fullness
        features[3] = observation[47]  # deck size normalized

        # Feature 4: own coins
        features[4] = observation[49]

        # Feature 5: field 0 count
        features[5] = observation[8]

        # Feature 6: field 1 count
        features[6] = observation[19]

        # Feature 7: is last round?
        features[7] = observation[73]

        # Feature 8-9: reserved for your features
        # TODO: Add more meaningful features!
        # features[8] = ...
        # features[9] = ...

        return features

    # ── Action Selection ─────────────────────────────────────────────

    def select_action(
        self, observation: np.ndarray, legal_actions: List[int], phase: int
    ) -> int:
        """Score each legal action and pick the best one."""
        best_action = legal_actions[0]
        best_score = float("-inf")

        for action in legal_actions:
            features = self.extract_features(observation, action, phase)
            score = np.dot(self.weights, features)
            if score > best_score:
                best_score = score
                best_action = action

        return best_action

    # ── Evolution Helpers (used by train.py) ─────────────────────────

    @staticmethod
    def random_individual(num_features: int) -> np.ndarray:
        """Create a random weight vector."""
        return np.random.randn(num_features).astype(np.float32) * 0.5

    @staticmethod
    def mutate(weights: np.ndarray, mutation_rate: float = 0.1, mutation_strength: float = 0.3) -> np.ndarray:
        """Mutate a weight vector with Gaussian noise.

        TODO: Experiment with different mutation strategies:
          - Adaptive mutation rate (decrease over generations)
          - Per-weight mutation rates
          - Cauchy distribution instead of Gaussian (fatter tails)
        """
        child = weights.copy()
        for i in range(len(child)):
            if random.random() < mutation_rate:
                child[i] += np.random.randn() * mutation_strength
        return child

    @staticmethod
    def crossover(parent1: np.ndarray, parent2: np.ndarray) -> np.ndarray:
        """Create offspring by combining two parents.

        TODO: Try different crossover strategies:
          - Uniform crossover (randomly pick each weight from either parent)
          - Blend crossover (average of parents with noise)
          - Single-point crossover (split at a random point)
        """
        # Default: uniform crossover
        mask = np.random.random(len(parent1)) > 0.5
        child = np.where(mask, parent1, parent2)
        return child.astype(np.float32)

    @staticmethod
    def tournament_select(population: list, fitnesses: list, tournament_size: int = 3) -> np.ndarray:
        """Select an individual via tournament selection.

        Pick tournament_size random individuals, return the best one.
        """
        indices = random.sample(range(len(population)), min(tournament_size, len(population)))
        best_idx = max(indices, key=lambda i: fitnesses[i])
        return population[best_idx].copy()
