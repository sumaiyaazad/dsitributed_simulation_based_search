import statistics
import numpy as np
from common import WEIGHTS

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
    skills = np.array([])
    latencys = np.array([])
    playtimes = np.array([])
    ranks = np.array([])
    regions = np.array([])
    for p in list_of_players:
        #skill
        skills.append(p["skill_level"])
        latencys.append(p["latency_ms"])
        playtimes.append(p["playtime_hours"])
        ranks.append(rank_to_value[p["rank"]])
        regions.append(p["region"])

    i = len(list_of_players)
    normalized_skill = (skills - min(skills)) / (max(skills) - min(skills))
    normalized_latency = (latencys - min(latencys)) / (max(latencys) - min(latencys))
    normalized_playtime = (playtimes - min(playtimes)) / (max(playtimes) - min(playtimes))
    normalized_ranks = (ranks - min(ranks)) / (max(ranks) - min(ranks))

    weighted_superscore = normalized_skill * WEIGHTS["skill"] + normalized_latency * WEIGHTS["latency"] + normalized_playtime * WEIGHTS["playtime"] + normalized_ranks * WEIGHTS["rank"]
    return weighted_superscore
    