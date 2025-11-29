# benchmark_matchmaking.py
import time
from typing import Optional

import numpy as np
import pandas as pd
import faiss

from common import read_player_attrs, RANKS, encode_player
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
            continue

        queue.append(seed_idx)

        while len(queue) > 0:
            distinct = []
            seen = set()
            for idx in list(queue):
                if idx not in busy and idx not in seen:
                    distinct.append(idx)
                    seen.add(idx)
                if len(distinct) >= players_per_match:
                    break

            if len(distinct) < players_per_match:
                break

            chosen = distinct[:players_per_match]
            matches.append(chosen)

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




def evaluate_matches(matches, players_df: pd.DataFrame):
    """
    Compute some basic quality metrics per strategy.

    Metrics:
    - num_matches
    - avg_skill_std:         average std-dev of skill_level within a match
    - avg_rank_std:          average std-dev of rank index within a match
    - avg_latency_std:       average std-dev of latency_ms within a match
    - avg_regions_per_match: average number of distinct regions in a match
    - avg_playtime_std:      average std-dev of playtime_hours within a match
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


    csv_players = read_player_attrs(players_csv)
    players_df = pd.read_csv(players_csv)
    num_players = len(csv_players)

    workload = generate_workload_seed_indices(
        players_csv,
        num_requests=100_000,
        hot_player_bias=1.5,
        seed=42,
    )


    target_matches = 3000
    players_per_match = 10


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


    vectors_unweighted = np.array(
        [encode_player(p) for p in csv_players],
        dtype=np.float32,
    )
    dim_unweighted = vectors_unweighted.shape[1]
    index_unweighted = faiss.IndexFlatL2(dim_unweighted)
    index_unweighted.add(vectors_unweighted)
    print("\nUnweighted FAISS index size:", index_unweighted.ntotal)

    start = time.perf_counter()
    faiss_unweighted_matches = form_matches_weighted(
        workload_seed_indices=workload,
        vectors=vectors_unweighted,
        index=index_unweighted,
        players_per_match=players_per_match,
        k=50,
        max_matches=target_matches,
    )
    faiss_unweighted_time = time.perf_counter() - start

    faiss_unweighted_metrics = evaluate_matches(faiss_unweighted_matches, players_df)
    print_metrics("FAISS (unweighted)", faiss_unweighted_metrics, faiss_unweighted_time)


    vectors_weighted = np.array(
        [encode_player_weighted(p) for p in csv_players],
        dtype=np.float32,
    )
    index_weighted = create_weighted_index(vectors_weighted)

    start = time.perf_counter()
    faiss_weighted_matches = form_matches_weighted(
        workload_seed_indices=workload,
        vectors=vectors_weighted,
        index=index_weighted,
        players_per_match=players_per_match,
        k=50,
        max_matches=target_matches,
    )
    faiss_weighted_time = time.perf_counter() - start

    faiss_weighted_metrics = evaluate_matches(faiss_weighted_matches, players_df)
    print_metrics("FAISS (weighted)", faiss_weighted_metrics, faiss_weighted_time)
