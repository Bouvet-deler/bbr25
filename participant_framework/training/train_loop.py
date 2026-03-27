"""
Generic training loop for Bonanzha strategies.

Supports three training modes:
  - DQN: Neural network with experience replay
  - Tabular Q: Q-table with state discretization
  - Genetic: Evolutionary optimization of weight vectors

All training happens offline in the local simulator (no server needed).

Usage:
    python train.py --strategy dqn --episodes 50000
    python train.py --strategy tabular_q --episodes 30000
    python train.py --strategy genetic --episodes 200  (generations)
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from framework.simulator import BonanzhaEnv
from training.dqn_agent import DQNAgent, Transition


# ─────────────────────────────────────────────────────────────────────
#  DQN Training
# ─────────────────────────────────────────────────────────────────────

def train_dqn(
    episodes: int = 50_000,
    num_players: int = 4,
    save_dir: str = "models",
    resume: str | None = None,
    curriculum_interval: int = 5_000,
    eval_interval: int = 500,
    eval_episodes: int = 50,
):
    """Train a DQN agent using the offline simulator."""
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    agent = DQNAgent(
        action_dim=6,
        hidden=128,
        lr=3e-4,
        gamma=0.99,
        tau=0.005,
        eps_start=1.0,
        eps_end=0.05,
        eps_decay_steps=int(episodes * 0.6),
        buffer_capacity=200_000,
        batch_size=64,
    )

    if resume:
        agent.load(resume)
        print(f"Resumed from {resume} (eps={agent.eps:.3f}, steps={agent.steps})")

    env = BonanzhaEnv(num_players=num_players, opponent_policy=None)

    best_eval_score = -float("inf")
    episode_rewards = []
    episode_coins = []
    losses = []

    start_time = time.time()

    for ep in range(1, episodes + 1):
        obs, info = env.reset()
        legal = info["legal_actions"]
        total_reward = 0.0
        done = False

        while not done:
            action = agent.select_action(obs, legal)
            next_obs, reward, terminated, truncated, next_info = env.step(action)
            done = terminated or truncated
            next_legal = next_info.get("legal_actions", [0])

            agent.store(Transition(
                state=obs,
                action=action,
                reward=reward,
                next_state=next_obs,
                done=done,
                legal_actions=legal,
                next_legal_actions=next_legal,
            ))

            loss = agent.train_step()
            if loss > 0:
                losses.append(loss)
            agent.update_epsilon()

            obs = next_obs
            legal = next_legal
            total_reward += reward

        agent_coins = env.players[0].coins
        episode_rewards.append(total_reward)
        episode_coins.append(agent_coins)

        # Logging
        if ep % 100 == 0:
            avg_r = np.mean(episode_rewards[-100:])
            avg_c = np.mean(episode_coins[-100:])
            avg_l = np.mean(losses[-200:]) if losses else 0
            elapsed = time.time() - start_time
            eps_per_sec = ep / elapsed
            print(
                f"Ep {ep:>6d} | "
                f"R={avg_r:>6.2f} | "
                f"Coins={avg_c:>5.1f} | "
                f"Loss={avg_l:.4f} | "
                f"eps={agent.eps:.3f} | "
                f"{eps_per_sec:.0f} ep/s"
            )

        # Evaluation
        if ep % eval_interval == 0:
            eval_score = evaluate_agent(agent, num_players, eval_episodes)
            print(f"  >> Eval ({eval_episodes} games): avg coins = {eval_score:.2f}")
            if eval_score > best_eval_score:
                best_eval_score = eval_score
                agent.save(save_path / "best.pt")
                print(f"  >> New best model saved (coins={eval_score:.2f})")

        # Curriculum: upgrade opponent to latest best
        if ep % curriculum_interval == 0 and (save_path / "best.pt").exists():
            print(f"  >> Upgrading opponent policy to latest best model")
            opp_agent = DQNAgent(action_dim=6, hidden=128)
            opp_agent.load(save_path / "best.pt")
            env.opponent_policy = opp_agent.as_policy()

        # Periodic checkpoint
        if ep % 5000 == 0:
            agent.save(save_path / f"checkpoint_{ep}.pt")

    agent.save(save_path / "final.pt")
    print(f"\nTraining complete. Best eval: {best_eval_score:.2f} coins")
    print(f"Models saved in {save_path.resolve()}")


def evaluate_agent(agent: DQNAgent, num_players: int, num_episodes: int) -> float:
    """Run num_episodes with greedy policy, return average agent coins."""
    env = BonanzhaEnv(num_players=num_players, opponent_policy=None)
    coins = []
    for _ in range(num_episodes):
        obs, info = env.reset()
        legal = info["legal_actions"]
        done = False
        while not done:
            action = agent.select_action_greedy(obs, legal)
            obs, _, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            legal = info.get("legal_actions", [0])
        coins.append(env.players[0].coins)
    return float(np.mean(coins))


# ─────────────────────────────────────────────────────────────────────
#  Tabular Q-Learning Training
# ─────────────────────────────────────────────────────────────────────

def train_tabular_q(
    episodes: int = 30_000,
    num_players: int = 4,
    save_dir: str = "models",
):
    """Train a Tabular Q-Learning agent using the offline simulator."""
    from strategies.tabular_q_strategy import TabularQStrategy

    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    strategy = TabularQStrategy(model_path=str(save_path / "q_table.pkl"))
    strategy.epsilon = 1.0  # start with full exploration

    env = BonanzhaEnv(num_players=num_players, opponent_policy=None)

    best_eval = -float("inf")
    episode_coins = []
    start_time = time.time()

    eps_start = 1.0
    eps_end = 0.05
    eps_decay = (eps_start - eps_end) / (episodes * 0.7)
    strategy.epsilon = eps_start

    for ep in range(1, episodes + 1):
        obs, info = env.reset()
        legal = info["legal_actions"]
        phase = info["phase"]
        done = False

        while not done:
            action = strategy.select_action(obs, legal, phase)
            next_obs, reward, terminated, truncated, next_info = env.step(action)
            done = terminated or truncated
            next_legal = next_info.get("legal_actions", [0])
            next_phase = next_info.get("phase", 0)

            strategy.update_q(
                state=obs,
                action=action,
                reward=reward,
                next_state=next_obs,
                done=done,
                legal_actions=legal,
                next_legal_actions=next_legal,
                phase=phase,
                next_phase=next_phase,
            )

            obs = next_obs
            legal = next_legal
            phase = next_phase

        strategy.epsilon = max(eps_end, strategy.epsilon - eps_decay)
        episode_coins.append(env.players[0].coins)

        if ep % 100 == 0:
            avg_c = np.mean(episode_coins[-100:])
            elapsed = time.time() - start_time
            table_size = len(strategy.q_table)
            print(
                f"Ep {ep:>6d} | "
                f"Coins={avg_c:>5.1f} | "
                f"eps={strategy.epsilon:.3f} | "
                f"Q-table={table_size} states | "
                f"{ep/elapsed:.0f} ep/s"
            )

        if ep % 500 == 0:
            eval_score = evaluate_tabular(strategy, num_players, 50)
            print(f"  >> Eval: avg coins = {eval_score:.2f}")
            if eval_score > best_eval:
                best_eval = eval_score
                strategy.save()
                print(f"  >> New best Q-table saved ({len(strategy.q_table)} states)")

    strategy.save()
    print(f"\nTraining complete. Best eval: {best_eval:.2f} coins")
    print(f"Q-table size: {len(strategy.q_table)} states")


def evaluate_tabular(strategy, num_players: int, num_episodes: int) -> float:
    old_eps = strategy.epsilon
    strategy.epsilon = 0.0
    env = BonanzhaEnv(num_players=num_players, opponent_policy=None)
    coins = []
    for _ in range(num_episodes):
        obs, info = env.reset()
        legal = info["legal_actions"]
        phase = info["phase"]
        done = False
        while not done:
            action = strategy.select_action(obs, legal, phase)
            obs, _, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            legal = info.get("legal_actions", [0])
            phase = info.get("phase", 0)
        coins.append(env.players[0].coins)
    strategy.epsilon = old_eps
    return float(np.mean(coins))


# ─────────────────────────────────────────────────────────────────────
#  Genetic / Evolutionary Training
# ─────────────────────────────────────────────────────────────────────

def train_genetic(
    generations: int = 200,
    population_size: int = 50,
    num_players: int = 4,
    games_per_eval: int = 20,
    save_dir: str = "models",
):
    """Evolve a weight vector for the GeneticStrategy."""
    from strategies.genetic_strategy import GeneticStrategy

    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    # Determine number of features
    template = GeneticStrategy(model_path=str(save_path / "genetic_best.pkl"))
    num_features = template.num_features

    # Initialize population
    population = [GeneticStrategy.random_individual(num_features) for _ in range(population_size)]

    best_ever_fitness = -float("inf")
    start_time = time.time()

    for gen in range(1, generations + 1):
        # Evaluate each individual
        fitnesses = []
        for weights in population:
            fitness = evaluate_genetic_individual(weights, num_features, num_players, games_per_eval)
            fitnesses.append(fitness)

        # Stats
        best_idx = int(np.argmax(fitnesses))
        best_fitness = fitnesses[best_idx]
        avg_fitness = np.mean(fitnesses)

        elapsed = time.time() - start_time
        print(
            f"Gen {gen:>4d} | "
            f"Best={best_fitness:>5.1f} | "
            f"Avg={avg_fitness:>5.1f} | "
            f"{elapsed:.0f}s"
        )

        # Save best
        if best_fitness > best_ever_fitness:
            best_ever_fitness = best_fitness
            template.weights = population[best_idx].copy()
            template.save()
            print(f"  >> New best weights saved (fitness={best_fitness:.2f})")

        # Create next generation
        new_population = []
        # Elitism: keep top 10%
        elite_count = max(2, population_size // 10)
        sorted_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)
        for i in sorted_indices[:elite_count]:
            new_population.append(population[i].copy())

        # Fill rest with offspring
        while len(new_population) < population_size:
            parent1 = GeneticStrategy.tournament_select(population, fitnesses)
            parent2 = GeneticStrategy.tournament_select(population, fitnesses)
            child = GeneticStrategy.crossover(parent1, parent2)
            child = GeneticStrategy.mutate(child)
            new_population.append(child)

        population = new_population

    print(f"\nEvolution complete. Best fitness: {best_ever_fitness:.2f}")


def evaluate_genetic_individual(
    weights: np.ndarray, num_features: int, num_players: int, num_games: int
) -> float:
    """Evaluate a genetic individual by playing num_games in the simulator."""
    from strategies.genetic_strategy import GeneticStrategy

    strategy = GeneticStrategy.__new__(GeneticStrategy)
    strategy.num_features = num_features
    strategy.weights = weights
    strategy.model_path = Path("models/genetic_best.pkl")

    env = BonanzhaEnv(num_players=num_players, opponent_policy=None)
    total_coins = 0

    for _ in range(num_games):
        obs, info = env.reset()
        legal = info["legal_actions"]
        phase = info["phase"]
        done = False

        while not done:
            action = strategy.select_action(obs, legal, phase)
            obs, _, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            legal = info.get("legal_actions", [0])
            phase = info.get("phase", 0)

        total_coins += env.players[0].coins

    return total_coins / num_games


# ─────────────────────────────────────────────────────────────────────
#  CLI entry point (used by train.py)
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train a Bonanzha AI agent offline")
    parser.add_argument(
        "--strategy",
        choices=["dqn", "tabular_q", "genetic"],
        default="dqn",
        help="Which strategy to train",
    )
    parser.add_argument("--episodes", type=int, default=50_000, help="Training episodes (or generations for genetic)")
    parser.add_argument("--players", type=int, default=4, help="Number of players")
    parser.add_argument("--save-dir", type=str, default="models", help="Directory for saved models")
    parser.add_argument("--resume", type=str, default=None, help="Resume DQN from checkpoint")
    parser.add_argument("--population", type=int, default=50, help="Population size (genetic only)")
    args = parser.parse_args()

    if args.strategy == "dqn":
        train_dqn(
            episodes=args.episodes,
            num_players=args.players,
            save_dir=args.save_dir,
            resume=args.resume,
        )
    elif args.strategy == "tabular_q":
        train_tabular_q(
            episodes=args.episodes,
            num_players=args.players,
            save_dir=args.save_dir,
        )
    elif args.strategy == "genetic":
        train_genetic(
            generations=args.episodes,
            population_size=args.population,
            num_players=args.players,
            save_dir=args.save_dir,
        )


if __name__ == "__main__":
    main()
