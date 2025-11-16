from scipy.stats import chi2
import random
import time

#simulates a queue of players arriving according to a Poisson process
def playerQueue():
    players_per_second = 10
    while True:
        dt = random.expovariate(players_per_second)
        time.sleep(dt)

#generates player with random attributes
def generate_player():
    from attributes import attributes
    import random

    skill = generate_skill()
    region = random.choice(['West', 'East', 'Central'])
    latency = random.randint(20, 200)  # in milliseconds

    return attributes(skill, region, latency)

#generates a skill value based on a chi-squared distribution
def generate_skill():
    d = 15
    a = 100
    sample = a * chi2.rvs(df=d, size =1)
    return sample[0]

