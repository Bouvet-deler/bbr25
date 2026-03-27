"""
Smoke tests for the Bonanzha AI Agent Framework.

Verifies that the simulator, strategies, and training loop all work
without needing a live server. Run with:

    python test_smoke.py

All tests should print OK. If any print FAIL, something is broken.
"""
from __future__ import annotations

import sys
import traceback


def run_test(name: str, fn):
    try:
        fn()
        print(f"  OK  {name}")
        return True
    except Exception as e:
        print(f"  FAIL {name}")
        traceback.print_exc()
        return False


# ─────────────────────────────────────────────────────────────────────
#  Framework core
# ─────────────────────────────────────────────────────────────────────

def test_card_config():
    from framework.card_config import CARD_TYPES, TOTAL_CARDS, harvest_value, next_threshold
    assert TOTAL_CARDS == 104
    assert len(CARD_TYPES) == 8
    assert harvest_value("Uranuceps", 5) == 4
    assert harvest_value("Uranuceps", 1) == 0
    assert next_threshold("Uranuceps", 3) == 4


def test_state_encoder_size():
    from framework.simulator import BonanzhaEnv
    from framework.state_encoder import STATE_SIZE
    env = BonanzhaEnv(num_players=4)
    obs, _ = env.reset()
    assert obs.shape == (STATE_SIZE,), f"Expected ({STATE_SIZE},), got {obs.shape}"
    assert obs.dtype.name == "float32"


def test_simulator_runs_full_game():
    """Play a complete game with random actions and verify it terminates."""
    import random
    from framework.simulator import BonanzhaEnv

    env = BonanzhaEnv(num_players=4)
    obs, info = env.reset()
    steps = 0
    done = False

    while not done and steps < 10_000:
        legal = info["legal_actions"]
        assert len(legal) > 0, "No legal actions available"
        action = random.choice(legal)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        steps += 1

    assert done, f"Game did not terminate in {steps} steps"
    assert steps < 10_000, "Game took too many steps"


def test_simulator_obs_bounds():
    """All observation values should be in [-1, 1]."""
    import random
    import numpy as np
    from framework.simulator import BonanzhaEnv

    env = BonanzhaEnv(num_players=2)
    obs, info = env.reset()

    for _ in range(200):
        legal = info["legal_actions"]
        obs, _, done, _, info = env.step(random.choice(legal))
        assert np.all(obs >= -1.0) and np.all(obs <= 1.0), \
            f"Observation out of [-1,1] bounds: min={obs.min():.3f}, max={obs.max():.3f}"
        if done:
            break


# ─────────────────────────────────────────────────────────────────────
#  Strategies (offline: no server)
# ─────────────────────────────────────────────────────────────────────

def test_random_strategy_in_simulator():
    """RandomStrategy selects valid actions in the simulator."""
    import random as rnd
    import numpy as np
    from framework.simulator import BonanzhaEnv
    from strategies.random_strategy import RandomStrategy

    strategy = RandomStrategy()
    env = BonanzhaEnv(num_players=4)
    obs, info = env.reset()
    done = False
    steps = 0

    while not done and steps < 5_000:
        legal = info["legal_actions"]
        phase = info["phase"]
        action = strategy.select_action(obs, legal, phase)
        assert action in legal, f"RandomStrategy chose illegal action {action}, legal={legal}"
        obs, _, done, _, info = env.step(action)
        steps += 1


def test_tabular_q_strategy_in_simulator():
    """TabularQStrategy runs without errors (no model file needed)."""
    import random
    from framework.simulator import BonanzhaEnv
    from strategies.tabular_q_strategy import TabularQStrategy

    strategy = TabularQStrategy(model_path="models/_test_q.pkl")
    strategy.epsilon = 1.0  # fully random to avoid needing a trained model

    env = BonanzhaEnv(num_players=4)
    obs, info = env.reset()
    done = False
    steps = 0

    while not done and steps < 5_000:
        legal = info["legal_actions"]
        phase = info["phase"]
        action = strategy.select_action(obs, legal, phase)
        assert action in legal, f"TabularQStrategy chose illegal action {action}"
        obs, _, done, _, info = env.step(action)
        steps += 1


def test_genetic_strategy_in_simulator():
    """GeneticStrategy runs without errors (no model file needed)."""
    from framework.simulator import BonanzhaEnv
    from strategies.genetic_strategy import GeneticStrategy

    strategy = GeneticStrategy(model_path="models/_test_genetic.pkl")
    # Default zero weights, still produces valid actions

    env = BonanzhaEnv(num_players=4)
    obs, info = env.reset()
    done = False
    steps = 0

    while not done and steps < 5_000:
        legal = info["legal_actions"]
        phase = info["phase"]
        action = strategy.select_action(obs, legal, phase)
        assert action in legal, f"GeneticStrategy chose illegal action {action}"
        obs, _, done, _, info = env.step(action)
        steps += 1


# ─────────────────────────────────────────────────────────────────────
#  Training infrastructure
# ─────────────────────────────────────────────────────────────────────

def test_dqn_agent_action_selection():
    """DQNAgent selects only legal actions."""
    import numpy as np
    from training.dqn_agent import DQNAgent
    from framework.state_encoder import STATE_SIZE

    agent = DQNAgent(action_dim=6)
    state = np.random.randn(STATE_SIZE).astype("float32")
    legal = [0, 2, 4]

    for _ in range(20):
        action = agent.select_action(state, legal)
        assert action in legal, f"DQNAgent chose illegal action {action}"
        action = agent.select_action_greedy(state, legal)
        assert action in legal, f"DQNAgent greedy chose illegal action {action}"


def test_dqn_training_loop():
    """DQN training runs without error for a small number of episodes."""
    from training.train_loop import train_dqn
    # eval_interval set very high so no evaluation pass happens
    train_dqn(episodes=5, save_dir="models/_smoke_test", eval_interval=10_000)


def test_tabular_q_training_loop():
    from training.train_loop import train_tabular_q
    train_tabular_q(episodes=5, save_dir="models/_smoke_test")


# ─────────────────────────────────────────────────────────────────────
#  Run all tests
# ─────────────────────────────────────────────────────────────────────

def main():
    tests = [
        ("card config values",              test_card_config),
        ("state encoder produces 75 floats", test_state_encoder_size),
        ("simulator runs a full game",       test_simulator_runs_full_game),
        ("observation in [-1, 1] bounds",    test_simulator_obs_bounds),
        ("RandomStrategy picks legal actions",   test_random_strategy_in_simulator),
        ("TabularQStrategy runs (untrained)",    test_tabular_q_strategy_in_simulator),
        ("GeneticStrategy runs (untrained)",     test_genetic_strategy_in_simulator),
        ("DQNAgent action masking",          test_dqn_agent_action_selection),
        ("DQN training loop (5 episodes)",   test_dqn_training_loop),
        ("Tabular Q training loop (5 eps)",  test_tabular_q_training_loop),
    ]

    print("Running smoke tests...\n")
    results = [run_test(name, fn) for name, fn in tests]
    print()

    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} passed")

    # Clean up test artifacts
    import shutil
    import pathlib
    smoke_dir = pathlib.Path("models/_smoke_test")
    if smoke_dir.exists():
        shutil.rmtree(smoke_dir)

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
