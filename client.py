import grpc
import numpy as np

import messages_pb2
import messages_pb2_grpc
from common import encode_player, read_player_attrs
from match_quality import qualify_match

def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = messages_pb2_grpc.MatchmakerServiceStub(channel)
        query_player = {
                "player_id": 999,
                "skill_level": 90,
                "latency_ms": 100,
                "region": "NA",
                "rank": "Silver",
                "playtime_hours": 400
            }

        query_vec = encode_player(query_player).reshape(1, -1)

        vec = encode_player(query_player)
        request = messages_pb2.Player(values=vec.tolist())

        response = stub.RequestPlayers(request)
        players = read_player_attrs("input/player_attributes.csv")
        match = [query_player]
        for p in response.playersIds:
            match.append(players[p])
        
        result = qualify_match(match)

        # PlayerList has playersIds, not values
        print("Client received IDs:", list(response.playersIds))


if __name__ == "__main__":
    run()
