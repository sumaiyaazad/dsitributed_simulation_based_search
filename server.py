import csv
import numpy as np
import grpc
import faiss
import random
import time
import threading
from dataclasses import dataclass
from concurrent import futures

import messages_pb2
import messages_pb2_grpc

REGIONS = ["NA", "EU", "AS", "SA", "AF", "OC"]
RANKS = ["Bronze", "Silver", "Gold", "Diamond", "Master", "Grandmaster"]
server_id = 0

index = None

# In-memory key-value storage
@dataclass
class service:
    players = {}
    lock = threading.Lock()

# this function will proc between 1 and 5 times a second to simulate player logins
def run_player_simulation():
    print("Starting player simulation thread...")
    while True:
        num_logins_this_second = random.randint(1, 5)

        # randomly select players to add to 'online_players' struct
        with service.lock:
            for _ in range(num_logins_this_second):
                player_id = random.choice(list(service.players.keys()))
                service.players[player_id]["is_online"] = True
                print(f"Player {service.players[player_id]['player_id']} logged in.")

                player_id = random.choice(list(service.players.keys()))
                service.players[player_id]["is_online"] = False
                print(f"Player {service.players[player_id]['player_id']} logged out.")

        time.sleep(1)
        
def map_server_id_to_region(server_id):
	if server_id == 0:
		return "NA"
	elif server_id == 1:
		return "EU"
	elif server_id == 2:
		return "AS"
	elif server_id == 3:
		return "SA"
	elif server_id == 4:
		return "AF"
	elif server_id == 5:
		return "OC"
	else:	
		return "UNKNOWN"

def read_player_attrs(filename):
    players = []
    with open(filename, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["region"] != map_server_id_to_region(server_id):
                continue
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
