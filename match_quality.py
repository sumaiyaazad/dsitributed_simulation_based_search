import statistics
import numpy as np
from common import WEIGHTS
from scipy.spatial.distance import pdist, squareform

graph = {
    "NA": ["EU", "SA"],
    "EU": ["NA", "AS"],
    "AS": ["EU", "OC"],
    "SA": ["NA", "AF"],
    "AF": ["SA", "OC"],
    "OC": ["AS", "AF"]
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

    z_scores = z_score(skills, latencies, playtimes, ranks)
    obj_z_scores = z_scores.sum(axis=1)
    print("Z-scores per player:", obj_z_scores)


def z_score(skills, latencies, playtimes, ranks):
    
    skill_std = statistics.stdev(skills)
    latency_std = statistics.stdev(latencies)
    playtime_std = statistics.stdev(playtimes)
    rank_std = statistics.stdev(ranks)

    print("Standard deviations:", skill_std, latency_std, playtime_std, rank_std)

    avg_skill = statistics.mean(skills)
    avg_latency = statistics.mean(latencies)
    avg_playtime = statistics.mean(playtimes)
    avg_rank = statistics.mean(ranks)

    z_scores = []
    for i in range(len(skills)):
        z_skill = (skills[i] - avg_skill) / skill_std if skill_std > 0 else 0
        z_latency = (latencies[i] - avg_latency) / latency_std if latency_std > 0 else 0
        z_playtime = (playtimes[i] - avg_playtime) / playtime_std if playtime_std > 0 else 0
        z_rank = (ranks[i] - avg_rank) / rank_std if rank_std > 0 else 0
        z_scores.append((z_skill, z_latency, z_playtime, z_rank))

    W = np.array([
        WEIGHTS["skill"],
        WEIGHTS["latency"],
        WEIGHTS["playtime"],
        WEIGHTS["rank"]
    ], dtype=np.float32)

    zW = z_scores * W
    return zW

def minmax_norm(vals):
    min_val = min(vals)
    max_val = max(vals)
    if max_val - min_val == 0:
        return [0.0 for _ in vals]
    return [(v - min_val) / (max_val - min_val) for v in vals]