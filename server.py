import csv
import numpy as np
import grpc
import faiss
from concurrent import futures

import messages_pb2
import messages_pb2_grpc

REGIONS = ["NA", "EU", "AS", "SA", "AF", "OC"]
RANKS = ["Bronze", "Silver", "Gold", "Diamond", "Master", "Grandmaster"]

index = None

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

def create_faiss_index(vectors):
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)

    print("FAISS index size:", index.ntotal)
    return index

def search_faiss_index(index, query, num_neighbor=5):
    distances, indices = index.search(query, num_neighbor)
    print("\nNearest neighbors from CSV:")
    return distances, indices

class VectorService(messages_pb2_grpc.VectorServiceServicer):
    def RequestPlayers(self, request, context):
        print("Server received:", list(request.values))
        dists, idxs = search_faiss_index(index)
        response = messages_pb2.PlayerList(playersIds=idxs)
        return response


def statup():
    playersfilename = "../input/player_attributes.csv"
    csv_players = read_player_attrs(playersfilename)
    vectors = np.array([encode_player(p) for p in csv_players], dtype=np.float32)
    index = create_faiss_index(vectors)
    
    return index 

def serve():
    index = statup()
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messages_pb2_grpc.add_VectorServiceServicer_to_server(VectorService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Server started on port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
