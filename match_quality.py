import statistics
import numpy as np
from common import WEIGHTS
from scipy.spatial.distance import pdist, squareform
from common import encode_player, read_player_attrs
import redis
import json


region_map = {
    "NA": 0,
    "EU": 1,
    "AS": 2,
    "SA": 3,
    "AF": 4,
    "OC": 5
}

graph = {
    0: [0, 1, 2, 1, 2, 3],
    1: [1, 0, 1, 2, 1, 2],
    2: [2, 1, 0, 3, 2, 1],
    3: [1, 2, 3, 0, 1, 2],
    4: [2, 1, 2, 1, 0, 1],
    5: [3, 2, 1, 2, 1, 0]
}

rank_to_value = {
    "Bronze": 1,
    "Silver": 2,
    "Gold": 3, 
    "Diamond": 4,
    "Master": 5,
    "Grandmaster": 6
}

def qualify_match(list_of_players):
    # collect in Python lists
    skills = []
    latencies = []
    playtimes = []
    ranks = []
    regions = []

    for p in list_of_players:
        skills.append(p["skill_level"])
        latencies.append(p["latency_ms"])
        playtimes.append(p["playtime_hours"])
        ranks.append(rank_to_value[p["rank"]])
        regions.append(p["region"])

    z_scores = z_score(skills, latencies, playtimes, ranks, average_region(regions))
    obj_z_scores = z_scores.sum(axis=1)
    print("Z-scores per player:", obj_z_scores)


def z_score(skills, latencies, playtimes, ranks, regions):
    
    skill_std = statistics.stdev(skills)
    latency_std = statistics.stdev(latencies)
    playtime_std = statistics.stdev(playtimes)
    rank_std = statistics.stdev(ranks)
    region_std = statistics.stdev(regions)

    print("Standard deviations:", skill_std, latency_std, playtime_std, rank_std, region_std)

    avg_skill = statistics.mean(skills)
    avg_latency = statistics.mean(latencies)
    avg_playtime = statistics.mean(playtimes)
    avg_rank = statistics.mean(ranks)
    avg_region = statistics.mean(ranks)

    z_scores = []
    for i in range(len(skills)):
        z_skill = (skills[i] - avg_skill) / skill_std if skill_std > 0 else 0
        z_latency = (latencies[i] - avg_latency) / latency_std if latency_std > 0 else 0
        z_playtime = (playtimes[i] - avg_playtime) / playtime_std if playtime_std > 0 else 0
        z_rank = (ranks[i] - avg_rank) / rank_std if rank_std > 0 else 0
        z_region = (regions[i] - avg_region) / region_std if region_std > 0 else 0
        z_scores.append((z_skill, z_latency, z_playtime, z_rank, z_region))

    W = np.array([
        WEIGHTS["skill"],
        WEIGHTS["latency"],
        WEIGHTS["playtime"],
        WEIGHTS["rank"],
        WEIGHTS["region"]
    ], dtype=np.float32)

    zW = z_scores * W
    return zW

def average_region(regions):
    avg_dist = []
    for r1 in regions:
        lengths = 0
        for r2 in regions:
            lengths = lengths + dist(r1, r2)
        avg_dist.append(lengths/(len(regions) - 1))
    return avg_dist

def dist(r1, r2):
    return graph[region_map[r1]][region_map[r2]]    

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
    players = read_player_attrs("input/player_attributes.csv")
    pubsub = r.pubsub()
    pubsub.subscribe("matches")

    print("subscripted to coordinator")

    for message in pubsub.listen():
        if message["type"] == "message":
            msg = json.loads(message['data'])
            list_of_players = player_lookup(msg, players)
            qualify_match(list_of_players=list_of_players)
