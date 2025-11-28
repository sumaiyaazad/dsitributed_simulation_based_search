import numpy as np
import grpc
import random
import time
import threading
import os
from concurrent import futures

import messages_pb2
import messages_pb2_grpc

from common import search_faiss_index, create_faiss_index, read_player_attrs, encode_player

REGIONS = ["NA", "EU", "AS", "SA", "AF", "OC"]
RANKS = ["Bronze", "Silver", "Gold", "Diamond", "Master", "Grandmaster"]
server_id = 0

class PlayerService(messages_pb2_grpc.MatchmakerServiceServicer):

    def __init__(self, index, online_players, offline_players, busy_players, lock):
        super().__init__()
        self.index = index
        self.online_players = online_players   #set of online player_ids
        self.busy_players = busy_players       #set of busy player_ids
        self.offline_players = offline_players #set of offline player_ids
        self.lock = lock

    def RequestPlayers(self, request, context):
        print("Server received:", list(request.values))

        query = np.ascontiguousarray([list(request.values)], dtype=np.float32)
        #grab 30 nearest neighbors since many will be offline or busy
        dists, idxs = search_faiss_index(self.index, query, 30)
        ids = [int(x) for x in idxs.flatten().tolist() if int(x) >= 0]

        # filter neighbors by online status to make sure they are available
        result = []
        with self.lock:
            for pid in ids:
                if pid not in self.busy_players:
                    result.append(pid)
                    self.busy_players.add(pid)  #mark player as busy
                if len(result) >= 10:
                    break

        return messages_pb2.PlayerList(playersIds=result)
    
    def ConfirmToMatch(self, request, context):
        print("Server received confirmation for player ID:", request.playerId)
        with self.lock:
            if request.playerId in self.busy_players:
                #for now make the player go offline when match is found
                self.busy_players.remove(request.playerId)
                # self.offline_players.add(request.playerId)
                # self.online_players.remove(request.playerId)
        return messages_pb2.Confirmation(status="Confirmed")

class ServerShard:
    def __init__(self, server_id, datafile, port_no=50051):
       self.port_no = port_no
       self.server_id = server_id
       self._datafile = datafile
       self.online_players = set() #set containing player_ids of online players
       self.busy_players = set()   #set containing player_ids of busy players
       self.offline_players = set() #set containing player_ids of offline players, should be inverse of online_players
       self.lock = threading.Lock()
       self.index = None
    
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
        print("Server started on port 50051")
        _server.wait_for_termination()

if __name__ == "__main__":
    server_id = int(os.environ.get("SERVER_ID", 0))
    shard = ServerShard(server_id, "input/player_attributes.csv", 50051)
    shard.serve()