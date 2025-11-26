import time
from typing import Optional

import numpy as np
import pandas as pd

from common import read_player_attrs, RANKS
from workload_generator import generate_workload_seed_indices
from weighted_faiss_search import (
    encode_player_weighted,
    create_weighted_index,
    form_matches_weighted,
)


def form_matches_fifo(
    workload_seed_indices,
    num_players: int,
    players_per_match: int = 10,
    max_matches: Optional[int] = None,
):
    """
    FIFO baseline:
    - We maintain a queue of "waiting" players.
    - When there are >= players_per_match distinct non-busy players in the queue,
      we pop the first players_per_match and form a match.
    - A player can only appear in one match (busy set).
    """
    from collections import deque

    busy = set()
    queue = deque()
    matches = []

    for seed_idx in workload_seed_indices:
        if seed_idx < 0 or seed_idx >= num_players:
            continue

        if seed_idx in busy:
            # Already matched, ignore this arrival
            continue

        # Add to queue
        queue.append(seed_idx)

        # Try to form a match while possible
        while len(queue) > 0:
            # Count distinct non-busy players in queue
            distinct = []
            seen = set()
            for idx in list(queue):
                if idx not in busy and idx not in seen:
                    distinct.append(idx)
                    seen.add(idx)
                if len(distinct) >= players_per_match:
                    break

            if len(distinct) < players_per_match:
                # Not enough distinct players yet
                break

            chosen = distinct[:players_per_match]
            matches.append(chosen)

            # Remove chosen from queue and mark busy
            new_queue = deque()
            chosen_set = set(chosen)
            while queue:
                x = queue.popleft()
                if x not in chosen_set:
                    new_queue.append(x)
            queue = new_queue

            for pid in chosen:
                busy.add(pid)

            if max_matches is not None and len(matches) >= max_matches:
                return matches

    return matches


# ---------- Helper: evaluation ----------

def evaluate_matches(matches, players_df: pd.DataFrame):
    """
    Compute some basic quality metrics per strategy.

    Metrics:
    - num_matches
    - avg_skill_std:       average std-dev of skill_level within a match
    - avg_rank_std:        average std-dev of rank index within a match
    - avg_latency_std:     average std-dev of latency_ms within a match
    - avg_regions_per_match: average number of distinct regions in a match
    - avg_playtime_std:    average std-dev of playtime_hours within a match
    """
    if not matches:
        return {
            "num_matches": 0,
            "avg_skill_std": None,
            "avg_rank_std": None,
            "avg_latency_std": None,
            "avg_regions_per_match": None,
            "avg_playtime_std": None,
        }

    skill_stds = []
    rank_stds = []
    latency_stds = []
    regions_per_match = []
    playtime_stds = []

    # Pre-extract columns as numpy arrays for fast indexing
    skill_arr = players_df["skill_level"].to_numpy()
    latency_arr = players_df["latency_ms"].to_numpy()
    region_arr = players_df["region"].to_numpy()
    rank_arr = players_df["rank"].to_numpy()
    playtime_arr = players_df["playtime_hours"].to_numpy()

    for match in matches:
        m = np.array(match, dtype=int)

        skills = skill_arr[m]
        lats = latency_arr[m]
        regs = region_arr[m]
        ranks = rank_arr[m]
        playtimes = playtime_arr[m]

        # Map rank labels to numeric indices 0..len(RANKS)-1
        rank_idxs = np.array([RANKS.index(r) for r in ranks], dtype=float)

        skill_stds.append(np.std(skills))
        rank_stds.append(np.std(rank_idxs))
        latency_stds.append(np.std(lats))
        regions_per_match.append(len(set(regs)))
        playtime_stds.append(np.std(playtimes))

    metrics = {
        "num_matches": len(matches),
        "avg_skill_std": float(np.mean(skill_stds)),
        "avg_rank_std": float(np.mean(rank_stds)),
        "avg_latency_std": float(np.mean(latency_stds)),
        "avg_regions_per_match": float(np.mean(regions_per_match)),
        "avg_playtime_std": float(np.mean(playtime_stds)),
    }
    return metrics


def print_metrics(label, metrics, elapsed):
    print(f"\n=== {label} ===")
    print(f"Runtime (s):               {elapsed:.4f}")
    print(f"Num matches:               {metrics['num_matches']}")
    print(f"Avg skill std in match:    {metrics['avg_skill_std']}")
    print(f"Avg rank std in match:     {metrics.get('avg_rank_std')}")
    print(f"Avg latency std in match:  {metrics['avg_latency_std']}")
    print(f"Avg regions per match:     {metrics['avg_regions_per_match']}")
    print(f"Avg playtime std in match: {metrics.get('avg_playtime_std')}")


if __name__ == "__main__":
    players_csv = "./input/player_attributes.csv"

    # Load players as list + DataFrame
    csv_players = read_player_attrs(players_csv)
    players_df = pd.read_csv(players_csv)
    num_players = len(csv_players)

    # Generate workload (this is the "continuous queue" driving the system)
    workload = generate_workload_seed_indices(
        players_csv,
        num_requests=100_000,   # how long your simulation runs
        hot_player_bias=1.5,
        seed=42,
    )

    # How many matches we *aim* to build before stopping in each strategy
    target_matches = 3000
    players_per_match = 10

    # --------- 1) FIFO baseline ---------
    start = time.perf_counter()
    fifo_matches = form_matches_fifo(
        workload,
        num_players=num_players,
        players_per_match=players_per_match,
        max_matches=target_matches,
    )
    fifo_time = time.perf_counter() - start

    fifo_metrics = evaluate_matches(fifo_matches, players_df)
    print_metrics("FIFO baseline", fifo_metrics, fifo_time)

    # --------- 2) Weighted FAISS ---------
    # Build weighted vectors and index
    vectors = np.array(
        [encode_player_weighted(p) for p in csv_players],
        dtype=np.float32,
    )
    index = create_weighted_index(vectors)

    start = time.perf_counter()
    faiss_matches = form_matches_weighted(
        workload_seed_indices=workload,
        vectors=vectors,
        index=index,
        players_per_match=players_per_match,
        k=50,
        max_matches=target_matches,
    )
    faiss_time = time.perf_counter() - start

    faiss_metrics = evaluate_matches(faiss_matches, players_df)
    print_metrics("Weighted FAISS", faiss_metrics, faiss_time)
