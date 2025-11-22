import grpc
import numpy as np

import messages_pb2
import messages_pb2_grpc


from common import encode_player

def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = messages_pb2_grpc.MatchmakerServiceStub(channel)
        query_player = {
                "player_id": 999,
                "skill_level": 88,
                "latency_ms": 26,
                "region": "NA",
                "rank": "Diamond",
                "playtime_hours": 410
            }

        query_vec = encode_player(query_player).reshape(1, -1)

        request = messages_pb2.Player(values = query_vec) 

        response = stub.RequestPlayers(request)

        print("Client received:", list(response.values))


if __name__ == "__main__":
    run()
