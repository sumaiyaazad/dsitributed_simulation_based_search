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
            # Convert numeric fields
            row["player_id"] = int(row["player_id"])
            row["skill_level"] = float(row["skill_level"])
            row["latency_ms"] = float(row["latency_ms"])
            row["playtime_hours"] = float(row["playtime_hours"])
            # region and rank remain strings
            players.append(row)

    print(f"Loaded {len(players)} players from CSV.")
    return players

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


def create_faiss_index(dim):
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)

    print("FAISS index size:", index.ntotal)
    return index


def form_matches(vectors, index, k=20, players_per_match=10):
    """
    Forms FAISS-weighted matches of size 10.
    Uses the closest players according to weighted vector.
    """
    unmatched = set(range(vectors.size()[0]))
    matches = []

    while len(unmatched) >= players_per_match:

        # Anchor: take the first unmatched player
        anchor_idx = next(iter(unmatched))

        # Query FAISS for the closest candidates
        query_vec = vectors[anchor_idx:anchor_idx+1]
        distances, indices = index.search(query_vec, k)

        # Filter out players already matched
        candidates = [i for i in indices[0] if i in unmatched]

        # Keep only 10
        if len(candidates) >= players_per_match:
            chosen = candidates[:players_per_match]
            matches.append(chosen)

            # Remove matched players
            for c in chosen:
                unmatched.remove(c)
        else:
            # Not enough candidates — relax and just match top available
            chosen = list(unmatched)[:players_per_match]
            matches.append(chosen)
            for c in chosen:
                unmatched.remove(c)

    return matches


if __name__=="__main__":
    # Get this generated from the work_loadgenerator
    playersfilename = "../input/player_attributes.csv"
    csv_players = read_player_attrs(playersfilename)

    vectors = np.array([encode_player_weighted  (p) for p in csv_players], dtype=np.float32)
    dim = vectors.shape[1]

    print("Vector dimension:", dim)

    index = create_faiss_index(dim)

    matches = form_matches(vectors, index)

    # Display results
    for m_i, match in enumerate(matches, 1):
        print(f"\n=== MATCH {m_i} ===")
        for idx in match:
            print(csv_players[idx])
