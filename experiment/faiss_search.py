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

def encode_player(player):
    """
    Convert the player attributes into a numeric vector for FAISS.
    """
    # One-hot region
    region_vec = [1.0 if player["region"] == r else 0.0 for r in REGIONS]

    # Rank index
    rank_idx = float(RANKS.index(player["rank"]))

    # Build final vector
    vec = [
        player["skill_level"],
        player["latency_ms"],
        rank_idx,
        player["playtime_hours"],
    ] + region_vec

    return np.array(vec, dtype=np.float32)


def create_faiss_index(dim):
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)

    print("FAISS index size:", index.ntotal)
    return index


def search_faiss_index(index, query, num_neighbor=5):
    distances, indices = index.search(query, num_neighbor)
    print("\nNearest neighbors from CSV:")
    return distances, indices


if __name__=="__main__":
    # Get this generated from the work_loadgenerator
    playersfilename = "../input/player_attributes.csv"
    csv_players = read_player_attrs(playersfilename)

    vectors = np.array([encode_player(p) for p in csv_players], dtype=np.float32)
    dim = vectors.shape[1]

    print("Vector dimension:", dim)

    index = create_faiss_index(dim)

    query_player = {
        "player_id": 999,
        "skill_level": 88,
        "latency_ms": 26,
        "region": "NA",
        "rank": "Diamond",
        "playtime_hours": 410
    }

    query_vec = encode_player(query_player).reshape(1, -1)

    idxs, dists = search_faiss_index(index, query_vec)

    print("\nNearest neighbors from CSV:")
    for rank, (idx, dist) in enumerate(zip(idxs[0], dists[0])):
        p = csv_players[int(idx)]
        print(f"Top {rank+1}: player_id={p['player_id']}, distance={dist:.2f}")
