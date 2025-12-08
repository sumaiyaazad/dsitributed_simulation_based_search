# weighted_faiss_search.py
import numpy as np
import faiss

from common import REGIONS, RANKS, read_player_attrs

# Weighting priorities: rank > skill > latency
WEIGHTS = {
    "rank": 10.0,        # highest weight 
    "skill": 5.0,
    "latency": 2.0,
    "playtime": 0.5,     # minor
    "region": 0.2        # very small influence
}


def encode_player_weighted(p):
    """Create a weighted vector for FAISS matchmaking."""
    rank_idx = RANKS.index(p["rank"])

    region_vec = np.array(
        [1.0 if p["region"] == r else 0.0 for r in REGIONS],
        dtype=np.float32
    ) * WEIGHTS["region"]

    vec = np.array([
        rank_idx * WEIGHTS["rank"],
        p["skill_level"] * WEIGHTS["skill"],
        p["latency_ms"] * WEIGHTS["latency"],
        p["playtime_hours"] * WEIGHTS["playtime"],
    ], dtype=np.float32)

    return np.concatenate([vec, region_vec]).astype(np.float32)


def create_weighted_index(vectors: np.ndarray) -> faiss.IndexFlatL2:
    assert vectors.ndim == 2
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)
    print("\nWeighted FAISS index size:", index.ntotal)
    return index


def form_matches_weighted(
    workload_seed_indices,
    vectors: np.ndarray,
    index: faiss.IndexFlatL2,
    players_per_match: int = 10,
    k: int = 50,
    max_matches: int | None = None,
):
    """
    Form matches using weighted FAISS, driven by a seed-player workload.

    - workload_seed_indices: list[int] of indices into `vectors` (who requests a match).
    - Each time a seed appears, if they are not busy, we FAISS-search around them
      and form a match of size `players_per_match` (seed + closest neighbors).
    - A player can only be in one match (busy set).
    """
    n = vectors.shape[0]
    busy = set()
    matches = []

    for seed_idx in workload_seed_indices:
        if seed_idx < 0 or seed_idx >= n:
            continue

        if seed_idx in busy:
            # Player already matched, ignore this request
            continue

        query_vec = vectors[seed_idx:seed_idx + 1]
        distances, indices = index.search(query_vec, k)

        # Flatten neighbor list and filter out busy players
        neighbors = [int(i) for i in indices[0] if i not in busy]

        if len(neighbors) < players_per_match:
            # Not enough available neighbors now, skip this seed
            continue

        chosen = neighbors[:players_per_match]
        matches.append(chosen)

        for pid in chosen:
            busy.add(pid)

        if max_matches is not None and len(matches) >= max_matches:
            break

    return matches


if __name__ == "__main__":
    # Simple local test: build matches once from CSV
    playersfilename = "./input/player_attributes.csv"
    csv_players = read_player_attrs(playersfilename)

    vectors = np.array([encode_player_weighted(p) for p in csv_players], dtype=np.float32)
    index = create_weighted_index(vectors)

    # Trivial "workload": everyone once, in order
    workload = list(range(len(csv_players)))

    matches = form_matches_weighted(workload, vectors, index, players_per_match=10, k=50)

    for m_i, match in enumerate(matches, 1):
        print(f"\n=== MATCH {m_i} ===")
        for idx in match:
            print(csv_players[idx])
