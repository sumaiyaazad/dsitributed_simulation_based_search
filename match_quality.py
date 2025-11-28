import statistics
import numpy as np
from common import WEIGHTS
from scipy.spatial.distance import pdist, squareform
from common import encode_player, read_player_attrs
import redis
import json
from z_score import qualify_match
import pandas as pd



def minmax_norm(vals):
    min_val = min(vals)
    max_val = max(vals)
    if max_val - min_val == 0:
        return [0.0 for _ in vals]
    return [(v - min_val) / (max_val - min_val) for v in vals]

def player_lookup(list_of_ids, players):
    match = []
    for id in list_of_ids:
        match.append(players[id])
    return match

if __name__ == "__main__":
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    players_csv = "./input/player_attributes.csv"

    players_df = pd.read_csv(players_csv, na_filter=False)
    pubsub = r.pubsub()
    pubsub.subscribe("matches")

    print("subscripted to coordinator")

    for message in pubsub.listen():
        if message["type"] == "message":
            msg = json.loads(message['data'])
            z_score, stds = qualify_match(msg, players_df)
            print(f"Match {msg} has z-score {z_score} with stds {stds}")
