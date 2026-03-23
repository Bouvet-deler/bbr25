"""
Offline training loop for the Bonanzha DQN agent.

Trains entirely in the local simulator (no server needed).
Supports curriculum learning: starts against random opponents, then
periodically promotes the best checkpoint as the opponent policy.

Usage:
    python train.py                        # default 50k episodes
    python train.py --episodes 100000      # more training
    python train.py --resume models/best.pt  # continue training
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from bonanzha_env import BonanzhaEnv
from dqn_agent import DQNAgent, Transition


def train(
    episodes: int = 50_000,
    num_players: int = 4,
    save_dir: str = "models",
    resume: str | None = None,
    curriculum_interval: int = 5_000,
    eval_interval: int = 500,
    eval_episodes: int = 50,
):
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

    # Opponent policy: start random, upgrade periodically
    opponent_policy = None  # None → random
    env = BonanzhaEnv(num_players=num_players, opponent_policy=opponent_policy)

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

        # ── Logging ──────────────────────────────────────────────
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

        # ── Evaluation ───────────────────────────────────────────
        if ep % eval_interval == 0:
            eval_score = evaluate(agent, num_players, eval_episodes)
            print(f"  >> Eval ({eval_episodes} games): avg coins = {eval_score:.2f}")
            if eval_score > best_eval_score:
                best_eval_score = eval_score
                agent.save(save_path / "best.pt")
                print(f"  >> New best model saved (coins={eval_score:.2f})")

        # ── Curriculum: upgrade opponents ────────────────────────
        if ep % curriculum_interval == 0 and (save_path / "best.pt").exists():
            print(f"  >> Upgrading opponent policy to latest best model")
            opp_agent = DQNAgent(action_dim=6, hidden=128)
            opp_agent.load(save_path / "best.pt")
            env.opponent_policy = opp_agent.as_policy()

        # ── Periodic checkpoint ──────────────────────────────────
        if ep % 5000 == 0:
            agent.save(save_path / f"checkpoint_{ep}.pt")

    # Final save
    agent.save(save_path / "final.pt")
    print(f"\nTraining complete. Best eval: {best_eval_score:.2f} coins")
    print(f"Models saved in {save_path.resolve()}")


def evaluate(agent: DQNAgent, num_players: int, num_episodes: int) -> float:
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


def main():
    parser = argparse.ArgumentParser(description="Train Bonanzha RL agent")
    parser.add_argument("--episodes", type=int, default=50_000)
    parser.add_argument("--players", type=int, default=4)
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--save-dir", type=str, default="models")
    parser.add_argument("--curriculum-interval", type=int, default=5_000)
    parser.add_argument("--eval-interval", type=int, default=500)
    parser.add_argument("--eval-episodes", type=int, default=50)
    args = parser.parse_args()

    train(
        episodes=args.episodes,
        num_players=args.players,
        save_dir=args.save_dir,
        resume=args.resume,
        curriculum_interval=args.curriculum_interval,
        eval_interval=args.eval_interval,
        eval_episodes=args.eval_episodes,
    )


if __name__ == "__main__":
    main()
