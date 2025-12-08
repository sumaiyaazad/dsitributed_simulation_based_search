import statistics
from time import time
import numpy as np
from common import WEIGHTS
from scipy.spatial.distance import pdist, squareform
from common import encode_player, read_player_attrs
import redis
import json
from z_score import qualify_match
import pandas as pd
import threading



class stats():
    def __init__(self):
        self.lock = threading.Lock()
        self.commits = 0
        self.aborts = 0
        self.z_scores = []
        self.timestart = time.time()

    def add_commit(self):
        with self.lock:
            self.commits += 1
    def add_abort(self):
        with self.lock:
            self.aborts += 1
    def add_z_score(self, z):
        with self.lock:
            self.z_scores.append(z)
    def get_stats(self):
        with self.lock:
            elapsed = time.time() - self.timestart
            return {
                "commits": self.commits,
                "aborts": self.aborts,
                "elapsed_seconds": elapsed,
                "commit_rate_per_sec": self.commits / elapsed if elapsed > 0 else 0,
                "abort_rate_per_sec": self.aborts / elapsed if elapsed > 0 else 0
            }
 

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
    stats = stats(lock=None)

    for message in pubsub.listen():
        if message["type"] == "message":
            msg = json.loads(message['data'])
            if msg["message_type"] == "match":
                z_score, stds = qualify_match(msg["player_ids"], players_df)
                stats.add_z_score(z_score)
                stats.add_commit()
                print(f"Match {msg} has z-score {z_score} with stds {stds}")
            elif msg["message_type"] == "abort":
                stats.add_abort()
                print(f"Match {msg} was aborted.")
