"""
Configuration for the Bonanzha AI Agent Framework.

Edit these settings to match your game server and preferences.
"""

# ── Server Connection ────────────────────────────────────────────────
SERVER_URL = "http://localhost:5201"   # Game server base URL

# ── Game Registration ────────────────────────────────────────────────
GAME_ID = "GAME1"     # Game name to join (ask the organizer which name to use)
MAX_PLAYERS = 4        # Number of players in the game

# ── Player Settings ──────────────────────────────────────────────────
PLAYER_NAME = "MyTeam"  # Your team name (shown on the scoreboard)

# ── Model Paths (for trained strategies) ─────────────────────────────
DQN_MODEL_PATH = "models/best.pt"
Q_TABLE_PATH = "models/q_table.pkl"
GENETIC_MODEL_PATH = "models/genetic_best.pkl"

# ── Polling / Timing ────────────────────────────────────────────────
POLL_INTERVAL = 0.3    # Seconds between state polls during gameplay
