import numpy as np
import grpc
from concurrent import futures

import messages_pb2
import messages_pb2_grpc

from common import search_faiss_index, create_faiss_index, read_player_attrs, encode_player

REGIONS = ["NA", "EU", "AS", "SA", "AF", "OC"]
RANKS = ["Bronze", "Silver", "Gold", "Diamond", "Master", "Grandmaster"]

class PlayerService(messages_pb2_grpc.MatchmakerServiceServicer):

    def __init__(self, index, online_player_ids):
        super().__init__()
        self.index = index
        # list where position i corresponds to row i in FAISS
        self.online_player_ids = online_player_ids

    def RequestPlayers(self, request, context):
        # request.values is the query vector from the client
        query_vec = np.array(request.values, dtype=np.float32).reshape(1, -1)
        print("Server received query vector with shape", query_vec.shape)

        # ask FAISS for nearest neighbors among ONLINE players
        dists, idxs = search_faiss_index(self.index, query_vec, num_neighbor=10)
        # idxs is shape (1, k), translate row indices -> actual player_ids
        neighbor_ids = [int(self.online_player_ids[i]) for i in idxs[0]]
        print("Nearest neighbor player_ids:", neighbor_ids)

        response = messages_pb2.PlayerList(playersIds=neighbor_ids)
        return response

class ServerShard:
    def __init__(self, zone_name, datafile, port_no=50051, online_fraction=0.5):
       self.port_no = port_no
       self.zone_name = zone_name
       self._datafile = datafile
       self.online_fraction = online_fraction

       self.index = None
       self.players = []           # list of dicts (ONLINE only)
       self.online_player_ids = [] # list of ints
       self.id_to_index = {}       # player_id -> row index in FAISS
    
    def _load_data(self):
        # 1. Read all players from CSV
        all_players = read_player_attrs(self._datafile)

        # 2. If zone_name is a geographic region, restrict to that region
        if self.zone_name in REGIONS:
            shard_players = [p for p in all_players if p["region"] == self.zone_name]
        else:
            # fallback: shard has all players
            shard_players = all_players

        num_total = len(shard_players)
        if num_total == 0:
            raise RuntimeError(f"No players found for shard region {self.zone_name}")

        # 3. Randomly sample a subset as "online"
        num_online = max(1, int(num_total * self.online_fraction))
        chosen_indices = np.random.choice(num_total, size=num_online, replace=False)

        self.players = [shard_players[i] for i in chosen_indices]
        self.online_player_ids = [p["player_id"] for p in self.players]
        self.id_to_index = {pid: idx for idx, pid in enumerate(self.online_player_ids)}

        # 4. Build FAISS index over only these ONLINE players
        vectors = np.array([encode_player(p) for p in self.players], dtype=np.float32)
        self.index = create_faiss_index(vectors)

        print(
            f"[{self.zone_name}] total players={num_total}, "
            f"online={len(self.players)}, port={self.port_no}"
        )

    def serve(self):
        self._load_data()
        assert self.index is not None
        _server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        messages_pb2_grpc.add_MatchmakerServiceServicer_to_server(
            PlayerService(self.index, self.online_player_ids), _server
        )        
        _server.add_insecure_port(f"[::]:{self.port_no}")
        _server.start()
        print(f"Server for zone {self.zone_name} started on port {self.port_no}")
        _server.wait_for_termination()

if __name__ == "__main__":
    shard = ServerShard("NA", "./input/player_attributes.csv", 50051, online_fraction=0.5)
    shard.serve()