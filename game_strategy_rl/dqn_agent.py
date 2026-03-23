"""
DQN Agent with masked action selection for Bonanzha.

Features:
- Dueling DQN architecture (value + advantage streams)
- Legal-action masking (illegal actions get -inf before softmax/argmax)
- Prioritised experience replay (proportional)
- Soft target-network updates
- Epsilon-greedy exploration with decay
"""
from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from state_encoder import STATE_SIZE


# ── Network ──────────────────────────────────────────────────────────

class DuelingQNetwork(nn.Module):
    """Dueling DQN: splits into value and advantage streams."""

    def __init__(self, state_dim: int, action_dim: int, hidden: int = 128):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
        )
        self.value_head = nn.Sequential(
            nn.Linear(hidden, hidden // 2),
            nn.ReLU(),
            nn.Linear(hidden // 2, 1),
        )
        self.advantage_head = nn.Sequential(
            nn.Linear(hidden, hidden // 2),
            nn.ReLU(),
            nn.Linear(hidden // 2, action_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        shared = self.shared(x)
        value = self.value_head(shared)                # (B, 1)
        advantage = self.advantage_head(shared)        # (B, A)
        # Combine: Q = V + (A - mean(A))
        q = value + advantage - advantage.mean(dim=-1, keepdim=True)
        return q


# ── Replay buffer ────────────────────────────────────────────────────

@dataclass
class Transition:
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    legal_actions: List[int]
    next_legal_actions: List[int]


class PrioritisedReplayBuffer:
    """Simple proportional prioritised replay."""

    def __init__(self, capacity: int = 100_000, alpha: float = 0.6):
        self.capacity = capacity
        self.alpha = alpha
        self.buffer: List[Optional[Transition]] = []
        self.priorities = np.zeros(capacity, dtype=np.float64)
        self.pos = 0
        self.size = 0

    def push(self, transition: Transition):
        max_prio = self.priorities[:self.size].max() if self.size > 0 else 1.0
        if self.size < self.capacity:
            self.buffer.append(transition)
        else:
            self.buffer[self.pos] = transition
        self.priorities[self.pos] = max_prio
        self.pos = (self.pos + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size: int, beta: float = 0.4):
        prios = self.priorities[:self.size] ** self.alpha
        probs = prios / prios.sum()
        indices = np.random.choice(self.size, batch_size, p=probs, replace=False)
        weights = (self.size * probs[indices]) ** (-beta)
        weights /= weights.max()
        batch = [self.buffer[i] for i in indices]
        return batch, indices, torch.FloatTensor(weights)

    def update_priorities(self, indices, td_errors):
        for idx, td in zip(indices, td_errors):
            self.priorities[idx] = abs(td) + 1e-6

    def __len__(self):
        return self.size


# ── Agent ────────────────────────────────────────────────────────────

class DQNAgent:
    """DQN agent with masked action selection."""

    def __init__(
        self,
        action_dim: int = 6,
        hidden: int = 128,
        lr: float = 1e-3,
        gamma: float = 0.99,
        tau: float = 0.005,
        eps_start: float = 1.0,
        eps_end: float = 0.05,
        eps_decay_steps: int = 30_000,
        buffer_capacity: int = 100_000,
        batch_size: int = 64,
        device: str | None = None,
    ):
        self.action_dim = action_dim
        self.gamma = gamma
        self.tau = tau
        self.batch_size = batch_size

        self.eps = eps_start
        self.eps_end = eps_end
        self.eps_decay = (eps_start - eps_end) / eps_decay_steps

        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        self.q_net = DuelingQNetwork(STATE_SIZE, action_dim, hidden).to(self.device)
        self.target_net = DuelingQNetwork(STATE_SIZE, action_dim, hidden).to(self.device)
        self.target_net.load_state_dict(self.q_net.state_dict())

        self.optimizer = optim.Adam(self.q_net.parameters(), lr=lr)
        self.buffer = PrioritisedReplayBuffer(buffer_capacity)

        self.steps = 0

    # ── Action selection ─────────────────────────────────────────────

    def select_action(self, state: np.ndarray, legal_actions: List[int]) -> int:
        """Epsilon-greedy with legal-action masking."""
        if random.random() < self.eps:
            return random.choice(legal_actions)

        with torch.no_grad():
            s = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.q_net(s).squeeze(0)
            # Mask illegal actions
            mask = torch.full((self.action_dim,), float("-inf"), device=self.device)
            for a in legal_actions:
                mask[a] = 0.0
            masked_q = q_values + mask
            return int(masked_q.argmax().item())

    def select_action_greedy(self, state: np.ndarray, legal_actions: List[int]) -> int:
        """Purely greedy (no exploration)."""
        with torch.no_grad():
            s = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.q_net(s).squeeze(0)
            mask = torch.full((self.action_dim,), float("-inf"), device=self.device)
            for a in legal_actions:
                mask[a] = 0.0
            masked_q = q_values + mask
            return int(masked_q.argmax().item())

    # ── Experience management ────────────────────────────────────────

    def store(self, transition: Transition):
        self.buffer.push(transition)

    def update_epsilon(self):
        self.eps = max(self.eps_end, self.eps - self.eps_decay)
        self.steps += 1

    # ── Training ─────────────────────────────────────────────────────

    def train_step(self) -> float:
        """Sample a batch and do one gradient step. Returns loss."""
        if len(self.buffer) < self.batch_size:
            return 0.0

        beta = min(1.0, 0.4 + (1.0 - 0.4) * self.steps / 50_000)
        batch, indices, weights = self.buffer.sample(self.batch_size, beta)
        weights = weights.to(self.device)

        states = torch.FloatTensor(np.array([t.state for t in batch])).to(self.device)
        actions = torch.LongTensor([t.action for t in batch]).to(self.device)
        rewards = torch.FloatTensor([t.reward for t in batch]).to(self.device)
        next_states = torch.FloatTensor(np.array([t.next_state for t in batch])).to(self.device)
        dones = torch.FloatTensor([float(t.done) for t in batch]).to(self.device)

        # Current Q
        q_values = self.q_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # Double DQN: use q_net to select actions, target_net to evaluate
        with torch.no_grad():
            next_q_all = self.q_net(next_states)
            next_q_target = self.target_net(next_states)

            # Mask illegal actions in next state
            for i, t in enumerate(batch):
                mask = torch.full((self.action_dim,), float("-inf"), device=self.device)
                for a in t.next_legal_actions:
                    mask[a] = 0.0
                next_q_all[i] += mask

            best_actions = next_q_all.argmax(dim=1)
            next_q = next_q_target.gather(1, best_actions.unsqueeze(1)).squeeze(1)
            target = rewards + self.gamma * next_q * (1.0 - dones)

        td_errors = (q_values - target).detach().cpu().numpy()
        self.buffer.update_priorities(indices, td_errors)

        loss = (weights * F.smooth_l1_loss(q_values, target, reduction="none")).mean()
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.q_net.parameters(), 10.0)
        self.optimizer.step()

        # Soft update target
        for tp, sp in zip(self.target_net.parameters(), self.q_net.parameters()):
            tp.data.copy_(self.tau * sp.data + (1.0 - self.tau) * tp.data)

        return loss.item()

    # ── Persistence ──────────────────────────────────────────────────

    def save(self, path: str | Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "q_net": self.q_net.state_dict(),
            "target_net": self.target_net.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "eps": self.eps,
            "steps": self.steps,
        }, path)

    def load(self, path: str | Path):
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        self.q_net.load_state_dict(checkpoint["q_net"])
        self.target_net.load_state_dict(checkpoint["target_net"])
        self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.eps = checkpoint.get("eps", self.eps_end)
        self.steps = checkpoint.get("steps", 0)

    # ── For use as opponent policy callback ──────────────────────────

    def as_policy(self):
        """Return a callable ``(obs, legal_actions, phase) -> action`` for
        use as the opponent_policy in BonanzhaEnv."""
        def policy(obs, legal_actions, phase):
            return self.select_action_greedy(obs, legal_actions)
        return policy
