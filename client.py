import grpc
import numpy as np

import messages_pb2
import messages_pb2_grpc
from common import encode_player, read_player_attrs
from match_quality import qualify_match
import redis
import time
import json

import grpc
import numpy as np
import json
import time
import redis

import messages_pb2
import messages_pb2_grpc

from common import encode_player

def run():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)

    with grpc.insecure_channel("localhost:50051") as channel:
        stub = messages_pb2_grpc.MatchmakerServiceStub(channel)

        # ------------------------------------------------
        # Create a synthetic test player and encode vector
        # ------------------------------------------------
        query_player = {
            "player_id": 999,
            "skill_level": 90,
            "latency_ms": 100,
            "region": "NA",
            "rank": "Silver",
            "playtime_hours": 400
        }

        vec = encode_player(query_player)

        request = messages_pb2.VectorRequest(values=vec.tolist())

        response = stub.RequestPlayers(request)
        candidate_ids = list(response.playersIds)

        print("Client received candidate IDs:", candidate_ids)

        if not candidate_ids:
            print("No candidates found.")
            publish_abort(r, time.time())
            return

        print("Attempting to HOLD players:", candidate_ids)

        hold_req = messages_pb2.HoldRequest(playersIds=candidate_ids)
        hold_res = stub.HoldMatchPlayers(hold_req)

        if not hold_res.success:
            print("Hold failed — players:", hold_res.failedPlayers)
            publish_abort(r, time.time())
            return

        print("Players successfully held.")
        print("Confirming match...")

        confirm_req = messages_pb2.PlayerList(playersIds=candidate_ids)
        confirm_res = stub.ConfirmToMatch(confirm_req)

        if not confirm_res.isOK:
            print("Confirm failed — releasing players.")
            release_req = messages_pb2.ReleaseRequest(playersIds=candidate_ids)
            stub.ReleaseMatchPlayers(release_req)
            publish_abort(r, time.time())
            return

        print("Match confirmed:", candidate_ids)

        publish_match(candidate_ids, r, time.time())



def publish_match(list_of_players, r, timestamp):
    msg = {
        "message_type": "match",
        "player_ids": list_of_players,
        "timestamp": timestamp
    }
    json_msg = json.dumps(msg)
    r.publish("matches", json_msg)
    print(f"Published MATCH: {json_msg}")


def publish_abort(r, timestamp):
    msg = {
        "message_type": "abort",
        "timestamp": timestamp
    }
    json_msg = json.dumps(msg)
    r.publish("matches", json_msg)
    print(f"Published ABORT: {json_msg}")


if __name__ == "__main__":
    run()
