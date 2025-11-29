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

def qualify_match(match, players_df):

    m = np.array(match, dtype=int)
    # Pre-extract columns as numpy arrays for fast indexing
    skill_arr = players_df["skill_level"].to_numpy()
    latency_arr = players_df["latency_ms"].to_numpy()
    region_arr = players_df["region"].to_numpy()
    rank_arr = players_df["rank"].to_numpy()
    playtime_arr = players_df["playtime_hours"].to_numpy()

    m = np.array(match, dtype=int)

    skills = skill_arr[m]
    lats = latency_arr[m]
    ranks = rank_arr[m]
    playtimes = playtime_arr[m]
    regions = region_arr[m]
    num_ranks = []
    for r in ranks:
        num_ranks.append(rank_to_value[r])


    zw, stds = match_z_score(skills, lats, playtimes, num_ranks, average_region(regions))
    player_z_scores = np.abs(zw).sum(axis=1)
    attribute_scores = np.abs(zw).mean(axis=0)
    score = float(player_z_scores.mean()) if len(player_z_scores) > 0 else 0.0,
    return  score, attribute_scores, stds

def match_z_score(skills, latencies, playtimes, ranks, regions):
    
    skill_std = np.std(skills)
    latency_std = np.std(latencies)
    playtime_std = np.std(playtimes)
    rank_std = np.std(ranks)
    region_std = np.std(regions)

    avg_skill = np.mean(skills)
    avg_latency = np.mean(latencies)
    avg_playtime = np.mean(playtimes)
    avg_rank = np.mean(ranks)
    avg_region = np.mean(ranks)

    z_scores = []
    for i in range(len(skills)):
        z_skill = z_score(skills[i], avg_skill, skill_std)
        z_latency = z_score(latencies[i], avg_latency, latency_std)
        z_playtime = z_score(playtimes[i], avg_playtime, playtime_std)
        z_rank = z_score(ranks[i], avg_rank, rank_std)
        z_region = z_score(regions[i], avg_region, region_std)
        z_scores.append((z_skill, z_latency, z_playtime, z_rank, z_region))

    z_scores = np.array(z_scores, dtype=np.float32)

    W = np.array([
        WEIGHTS["skill"],
        WEIGHTS["latency"],
        WEIGHTS["playtime"],
        WEIGHTS["rank"],
        WEIGHTS["region"]
    ], dtype=np.float32)

    zW = z_scores * W
    return zW, np.array([skill_std, latency_std, playtime_std, rank_std, region_std])

def z_score(val, mean, std):
    if std == 0:
        return 0.0
    return (val - mean) / std