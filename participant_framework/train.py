"""
Training entry point: train an agent offline using the simulator.

To get started:
  1. Uncomment the training method you want to use below.
  2. Adjust the episode count (more = better, but slower).
  3. Run:  python train.py

Models are saved to the models/ directory.
"""
from training.train_loop import train_dqn, train_tabular_q, train_genetic

# ══════════════════════════════════════════════════════
#  CHOOSE YOUR TRAINING METHOD
#  Uncomment the approach you want to train.
# ══════════════════════════════════════════════════════
def main():
    train_dqn(episodes=50_000)
    # train_tabular_q(episodes=30_000)
    # train_genetic(generations=200, population_size=50)
# ══════════════════════════════════════════════════════


if __name__ == "__main__":
    main()
