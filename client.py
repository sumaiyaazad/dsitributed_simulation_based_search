import grpc
import numpy as np

import messages_pb2
import messages_pb2_grpc
from common import encode_player, read_player_attrs
from match_quality import qualify_match
import redis
import time
import json

def run():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)

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
        result = publish_match(list(response.playersIds), r)
        print(result)

        # PlayerList has playersIds, not values
        print("Client received IDs:", list(response.playersIds))

def publish_match(list_of_players, r):
    
    msg = json.dumps(list_of_players)
    r.publish("matches", msg)
    print(f"Published: {msg}")


if __name__ == "__main__":
    run()
