import numpy as np
import grpc
import random
import time
import threading
import os
from concurrent import futures
import threading
import time
import random

import messages_pb2
import messages_pb2_grpc

from common import search_faiss_index, create_faiss_index, read_player_attrs, encode_player

REGIONS = ["NA", "EU", "AS", "SA", "AF", "OC"]
RANKS = ["Bronze", "Silver", "Gold", "Diamond", "Master", "Grandmaster"]
server_id = 0

class PlayerService(messages_pb2_grpc.MatchmakerServiceServicer):
    def __init__(self, shard):
        super().__init__()
        self.shard = shard

    def RequestPlayers(self, request, context):
        # request.values: 1D list of floats
        query_vec = np.array(request.values, dtype=np.float32).reshape(1, -1)
        print("Server received query vector with shape", query_vec.shape)

        # Ask FAISS for a large-ish number of neighbors to allow for filtering
        NUM_NEIGHBORS = 100
        dists, idxs = search_faiss_index(self.shard.index, query_vec, num_neighbor=NUM_NEIGHBORS)

        chosen_ids = []
        MAX_RETURN = 10  # how many we give back to the coordinator

        for idx in idxs[0]:
            idx = int(idx)
            # skip if not online
            if idx not in self.shard.online_indices:
                continue
            # skip if in a match
            if idx in self.shard.busy_indices:
                continue
            # accept this player
            pid = int(self.shard.all_player_ids[idx])
            chosen_ids.append(pid)
            if len(chosen_ids) >= MAX_RETURN:
                break

        print("Nearest eligible neighbor player_ids:", chosen_ids)
        return messages_pb2.PlayerList(playersIds=chosen_ids)
    
    def ConfirmToMatch(self, request, context):
        """
        Coordinator calls this AFTER deciding a match, to lock those players
        so they cannot be reused for another match.
        """
        locked = 0
        for pid in request.playersIds:
            idx = self.shard.id_to_index.get(pid)
            if idx is None:
                continue
            # mark busy
            self.shard.busy_indices.add(idx)
            # ensure they are no longer considered online
            if idx in self.shard.online_indices:
                self.shard.online_indices.discard(idx)
            locked += 1

        print(f"Locked {locked} players as busy for a match.")
        return messages_pb2.Status(isOK=True)

class ServerShard:
    def __init__(self, zone_name, datafile, port_no=50051, online_fraction=0.5):
       self.port_no = port_no
       self.server_id = server_id
       self._datafile = datafile
       self.online_players = set() #set containing player_ids of online players
       self.busy_players = set()   #set containing player_ids of busy players
       self.offline_players = set() #set containing player_ids of offline players, should be inverse of online_players
       self.lock = threading.Lock()
       self.index = None

       # All players in this region
       self.all_players = []        # list of dicts
       self.all_player_ids = []     # list[int]
       self.id_to_index = {}        # player_id -> global index in all_players

       # Online and busy sets (indices into all_players)
       self.online_indices = set()  # eligible to be matched
       self.busy_indices = set()    # currently in a match

    
    def _load_data(self):
        csv_players = read_player_attrs(self._datafile)
        csv_players = [p for p in csv_players if p["region"] == self.map_server_id_to_region(self.server_id)]
        # randomly assign some players as online 1 in 10 chance
        for p in csv_players:
            n = random.randint(1, 10)
            if n == 1:
                self.online_players.add(p["player_id"])
            else:
                self.offline_players.add(p["player_id"])
        vectors = np.array([encode_player(p) for p in csv_players], dtype=np.float32)
        self.index = create_faiss_index(vectors)
    
    # this function will proc between 1 and 5 times a second to simulate player logins
    def run_player_simulation(self):
        print("Starting player simulation thread...")
        while True:
            num_logins_this_second = random.randint(1, 5)

            # randomly select players to add to 'online_players' struct
            with self.lock:
                for _ in range(num_logins_this_second):
                    choice = random.choice(list(self.offline_players))
                    if choice in self.busy_players:
                        continue
                    self.online_players.add(choice)
                    self.offline_players.remove(choice)
                    print(f"Player {choice} logged in.")

                    choice = random.choice(list(self.online_players))
                    if choice in self.busy_players:
                        continue
                    self.offline_players.add(choice)
                    self.online_players.remove(choice)
                    print(f"Player {choice} logged out.")

            time.sleep(1)

    def map_server_id_to_region(self, server_id):
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

        # 4. Choose a random subset as "online"
        num_online = max(1, int(num_total * self.online_fraction))
        chosen_indices = np.random.choice(num_total, size=num_online, replace=False)
        self.online_indices = set(int(i) for i in chosen_indices)
        self.busy_indices = set()

        print(
            f"[{self.zone_name}] total players={num_total}, "
            f"online={len(self.online_indices)}, port={self.port_no}"
        )

    def _online_fluctuation_loop(self, interval_secs=5, change_fraction=0.05):
        """
        Periodically flip a fraction of players between online and offline.
        Busy players are never flipped.
        """
        n = len(self.all_players)
        if n == 0:
            return
        
        while True:
            time.sleep(interval_secs)

            # current online indices
            current_online = list(self.online_indices)

            # offline candidates = all - online - busy
            all_indices = set(range(n))
            offline_candidates = list(all_indices - self.online_indices - self.busy_indices)

            if not current_online and not offline_candidates:
                continue

            # how many to flip in each direction
            num_flip_offline = 0
            if current_online:
                num_flip_offline = min(
                    max(1, int(change_fraction * len(current_online))),
                    len(current_online),
                )

            num_flip_online = 0
            if offline_candidates:
                num_flip_online = min(
                    max(1, int(change_fraction * len(offline_candidates))),
                    len(offline_candidates),
                )

            # Online -> offline (but never touch busy)
            if num_flip_offline > 0:
                for idx in random.sample(current_online, num_flip_offline):
                    if idx in self.busy_indices:
                        continue
                    self.online_indices.discard(idx)

            # Offline -> online
            if num_flip_online > 0:
                for idx in random.sample(offline_candidates, num_flip_online):
                    self.online_indices.add(idx)

            print(
                f"[{self.zone_name}] reshuffle: online={len(self.online_indices)}, "
                f"busy={len(self.busy_indices)}"
            )

    def serve(self):
        self._load_data()
        assert self.index is not None

        _server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        # pass shared players dict and lock into the servicer
        messages_pb2_grpc.add_MatchmakerServiceServicer_to_server(PlayerService(self.index, self.offline_players, self.online_players, self.busy_players, self.lock), _server)
        _server.add_insecure_port(f"[::]:{self.port_no}")
        t = threading.Thread(target=self.run_player_simulation, daemon=True)
        t.start()
        _server.start()
        print(f"Server for zone {self.zone_name} started on port {self.port_no}")

        # start background reshuffle of online players
        t = threading.Thread(target=self._online_fluctuation_loop, daemon=True)
        t.start()

        _server.wait_for_termination()

if __name__ == "__main__":
    server_id = int(os.environ.get("SERVER_ID", 0))
    shard = ServerShard(server_id, "input/player_attributes.csv", 50051)
    shard.serve()