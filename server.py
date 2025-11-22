import numpy as np
import grpc
from concurrent import futures

import messages_pb2
import messages_pb2_grpc

from common import search_faiss_index, create_faiss_index, read_player_attrs, encode_player

REGIONS = ["NA", "EU", "AS", "SA", "AF", "OC"]
RANKS = ["Bronze", "Silver", "Gold", "Diamond", "Master", "Grandmaster"]

class PlayerService(messages_pb2_grpc.MatchmakerServiceServicer):

    def __init__(self, index):
        super().__init__()
        self.index = index

    def RequestPlayers(self, request, context):
        print("Server received:", list(request.values))
        dists, idxs = search_faiss_index(self.index)
        response = messages_pb2.PlayerList(playersIds=idxs)
        return response

class ServerShard:
    def __init__(self, zone_name, datafile, port_no=50051):
       self.port_no = port_no
       self.zone_name = zone_name
       self._datafile = datafile
       self.index = None
    
    def _load_data(self):
        csv_players = read_player_attrs(self._datafile)
        vectors = np.array([encode_player(p) for p in csv_players], dtype=np.float32)
        self.index = create_faiss_index(vectors)

    def serve(self):
        self._load_data()
        assert self.index is not None
        _server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        messages_pb2_grpc.add_VectorServiceServicer_to_server(PlayerService(self.index), _server)
        _server.add_insecure_port(f"[::]:{self.port_no}")
        _server.start()
        print("Server started on port 50051")
        _server.wait_for_termination()

if __name__ == "__main__":
    shard = ServerShard("CA", "../input/player_attributes.csv", 50051)
    shard.serve()