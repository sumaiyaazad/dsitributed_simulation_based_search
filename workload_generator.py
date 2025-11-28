import numpy as np
import csv
from scipy.stats import chi

REGIONS = ["NA", "EU", "AS", "SA", "AF", "OC"]

# Number of players to generate for the CSV
NUM_PLAYERS = 50000

# Degrees of freedom for chi distribution
SKILL_DF = 5
LATENCY_DF = 3

# Scale factors
SKILL_SCALE = 15
LATENCY_SCALE = 10
PLAYTIME_MEAN = 300
PLAYTIME_STD = 120


def compute_rank(skill):
    if skill > 95:
        return "Grandmaster"
    elif skill > 85:
        return "Master"
    elif skill > 70:
        return "Diamond"
    elif skill > 55:
        return "Gold"
    elif skill > 40:
        return "Silver"
    else:
        return "Bronze"


def generate_players(num_players: int = NUM_PLAYERS, seed: int | None = None):
    if seed is not None:
        np.random.seed(seed)

    players = []
    for player_id in range(1, num_players + 1):
        raw_skill = chi.rvs(SKILL_DF)
        skill_level = min(100, round(raw_skill * SKILL_SCALE))

        raw_latency = chi.rvs(LATENCY_DF)
        latency = max(5, round(raw_latency * LATENCY_SCALE))

        region = np.random.choice(REGIONS)
        rank = compute_rank(skill_level)

        playtime = max(0, int(np.random.normal(PLAYTIME_MEAN, PLAYTIME_STD)))

        players.append([
            player_id,
            skill_level,
            latency,
            region,
            rank,
            playtime,
        ])

    return players


def write_players_csv(players, output_file: str = "./input/player_attributes.csv"):
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["player_id", "skill_level", "latency_ms", "region", "rank", "playtime_hours"])
        writer.writerows(players)

    print(f"CSV file '{output_file}' generated with {len(players)} players.")


def generate_workload_seed_indices(
    players_csv: str,
    num_requests: int = 100000,
    hot_player_bias: float = 1.5,
    seed: int | None = None,
):
    """
    Generate a continuous stream of seed-player indices for benchmarking.

    - Players with higher playtime_hours appear more often (approx "more online").
    - hot_player_bias > 1.0 makes the distribution more skewed toward heavy players.
    - Returns a list of indices 0..N-1 (index into the CSV order).
    """
    import pandas as pd

    if seed is not None:
        np.random.seed(seed)

    df = pd.read_csv(players_csv)
    playtime = df["playtime_hours"].to_numpy(dtype=float)

    # Avoid zero weights
    playtime = playtime + 1.0

    # Apply bias
    weights = playtime ** hot_player_bias
    weights = weights / weights.sum()

    indices = np.arange(len(df))
    workload = np.random.choice(indices, size=num_requests, replace=True, p=weights)
    return workload.tolist()


if __name__ == "__main__":
    # 1) Generate CSV if needed
    players = generate_players()
    write_players_csv(players)

    # 2) Example workload usage
    workload = generate_workload_seed_indices("./input/player_attributes.csv",
                                              num_requests=50_000,
                                              hot_player_bias=1.5)
    print("Example workload:", workload[:20])

