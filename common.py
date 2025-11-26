# common.py
import numpy as np
import csv
import faiss

REGIONS = ["NA", "EU", "AS", "SA", "AF", "OC"]
RANKS = ["Bronze", "Silver", "Gold", "Diamond", "Master", "Grandmaster"]

def read_player_attrs(filename):
    players = []
    with open(filename, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["player_id"] = int(row["player_id"])
            row["skill_level"] = float(row["skill_level"])
            row["latency_ms"] = float(row["latency_ms"])
            row["playtime_hours"] = float(row["playtime_hours"])
            players.append(row)

    print(f"Loaded {len(players)} players from CSV.")
    return players


def encode_player(player):
    """
    Convert the player attributes into a numeric vector for FAISS.
    Unweighted encoding – used e.g. by simple baselines / server.
    """
    region_vec = [1.0 if player["region"] == r else 0.0 for r in REGIONS]
    rank_idx = float(RANKS.index(player["rank"]))

    vec = [
        player["skill_level"],
        player["latency_ms"],
        rank_idx,
        player["playtime_hours"],
    ] + region_vec

    return np.array(vec, dtype=np.float32)


def create_faiss_index(vectors: np.ndarray) -> faiss.IndexFlatL2:
    """
    Build a simple L2 FAISS index over the given vectors.
    """
    assert vectors.ndim == 2
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)
    print("FAISS index size:", index.ntotal)
    return index


def search_faiss_index(index, query: np.ndarray, num_neighbors: int = 5):
    """
    Query FAISS index with a (1, d) query vector.
    """
    distances, indices = index.search(query, num_neighbors)
    return distances, indices
