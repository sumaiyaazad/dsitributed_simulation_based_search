import statistics
import numpy as np
from common import WEIGHTS
from scipy.spatial.distance import pdist, squareform
from common import encode_player, read_player_attrs
import redis
import json
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
            list_of_players = player_lookup(msg, players_df)
            # qualify_match(list_of_players=list_of_players)
