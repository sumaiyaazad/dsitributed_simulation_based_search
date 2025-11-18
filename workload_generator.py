import numpy as np
import csv
from scipy.stats import chi

# Number of players to generate
NUM_PLAYERS = 50000

# Degrees of freedom for chi distribution
SKILL_DF = 5
LATENCY_DF = 3

# Regions to pick from
REGIONS = ["NA", "EU", "AS", "SA", "AF", "OC"]

# Scale factors
SKILL_SCALE = 15
LATENCY_SCALE = 10
PLAYTIME_MEAN = 300
PLAYTIME_STD = 120

def compute_rank(skill):
    if skill > 95:
        return "Grandmaster"
    elif skill > 85:
        return "Master"
    elif skill > 70:
        return "Diamond"
    elif skill > 55:
        return "Gold"
    elif skill > 40:
        return "Silver"
    else:
        return "Bronze"


players = []

for player_id in range(1, NUM_PLAYERS + 1):

    # Generate skill using SciPy chi distribution
    raw_skill = chi.rvs(SKILL_DF)
    skill_level = min(100, round(raw_skill * SKILL_SCALE))

    # Generate latency using SciPy chi distribution
    raw_latency = chi.rvs(LATENCY_DF)
    latency = max(5, round(raw_latency * LATENCY_SCALE))

    # Choose player region
    region = np.random.choice(REGIONS)

    # Compute rank from skill
    rank = compute_rank(skill_level)

    # Generate playtime from normal distribution
    playtime = max(0, int(np.random.normal(PLAYTIME_MEAN, PLAYTIME_STD)))

    players.append([
        player_id, skill_level, latency, region, rank, playtime
    ])

# Write CSV
output_file = "./input/player_attributes.csv"

with open(output_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["player_id", "skill_level", "latency_ms", "region", "rank", "playtime_hours"])
    writer.writerows(players)

print(f"CSV file '{output_file}' generated with {NUM_PLAYERS} players.")
