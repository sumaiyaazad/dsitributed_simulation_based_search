Teams Members :

Fariba Amiri
Sumaiya Azad
Shreeda Ghatpande
Jacob Hopkins
Andy Herbert

Current Status
We now have a basic working implementation of the FAISS-powered distributed matchmaking server. The core logic is functioning and is producing initial match results as expected. We are facing some problems with double spending. We are still working on finalizing the redis cache coordination and  this will stimulate the dame played for the players.
What’s Working /Not Working 
●	The fixed ruleset for local-zone matchmaking is operating reliably, including fallback to neighboring zones or geographic clusters when the local zone is insufficient.
●	We identified that not distinguishing between “online” and “busy” players was causing inflated or incorrect matches.
●	We are now implementing a busy-player tracking mechanism using Redis caches, inspired by the 2PL + PC model, to better coordinate player availability across the distributed system.
●	We have started using standard deviation based quantization for the metrics we track, improving how players are grouped before FAISS retrieval.
Next Steps
●	Generate a full set of metrics and test several combinations we outlined earlier to evaluate match quality and match thresholding.
●	Conduct deeper testing and validation of both the code and the underlying concepts, including concurrency scenarios and fallback logic.
●	Continue refining shard load balancing, busy-player coordination, and quantization thresholds.
Team Contributions:-
Jacob Hopkins :  Generating servers and shard data based on zone and quantizing the player attributes.
Fariba Amiri : Creating and implementing online player concept and proper randomization of shards.
Sumaiya Azad: Working on workload generator and redis cache for player busy concept
Andy Herbert: Quantizing the good match and generating player attributes weighted encoding for match quality
Shreeda Ghatpande: Designing and integrating all implementations to get the working POC along with helping in the added 2pl + pc testing and implementation . 
