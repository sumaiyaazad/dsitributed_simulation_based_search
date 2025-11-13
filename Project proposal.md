# Tab 1

### Project: High Performance Distributed Key-Value Store for the similarity-based indexes

### Members:

Shreeda Ghatpande  
Jacob Hopkins  
Sumaiya Azad  
Fariba Amiri

### Introduction:

We plan to build a **high-performance distributed key-value store** that supports **similarity-based indexing and querying**, using high-dimensional **embedding vectors** as keys rather than traditional hash or string keys. The system is intended to support applications such as image retrieval, recommendation systems, and natural language understanding where data is often queried by similarity instead of exact match.

At a high level, our system will allow users to insert (vector, value) pairs and later retrieve the **top-K most similar vectors** to a given query. Unlike existing key-value stores that rely on exact key matching, our design will integrate **approximate nearest neighbor (ANN) search algorithms** (like FAISS or HNSW) and support **distributed computation and storage** across multiple nodes. The architecture includes a client, a coordinator for routing and metadata, and multiple data nodes responsible for local vector indexing and storage.

This project explores the intersection of **distributed systems** and **machine learning infrastructure**, with a focus on optimizing query performance, scalability, and fault tolerance for high-dimensional data.

The central question we aim to answer is:  
**Can a distributed key-value store be effectively designed to support similarity-based search with high performance and scalability, without compromising accuracy?**

We plan to measure and evaluate the system based on:

* **Query latency**: Time taken to return top-K similar vectors.  
* **Recall**: Accuracy of similarity search across distributed nodes.  
* **Scalability**: How well performance holds as the number of vectors and nodes increases.  
* **Load balancing efficiency**: How evenly queries and data are distributed.  
* **Fan-out cost**: Network and compute overhead when querying across multiple shards.

Our key hypotheses are:

* **Vector-aware sharding** (e.g., clustering-based partitioning) will significantly improve similarity recall and reduce fan-out compared to hash-based sharding.  
* **Hybrid routing strategies** can limit the number of shards queried while preserving accuracy.  
* A distributed ANN index can scale horizontally with minimal degradation in query latency, given proper coordination and data distribution.

To carry out this project and test our hypotheses, we will follow these main steps:

* Define the system architecture: client, coordinator, and server nodes.  
* Choose the appropriate technologies (e.g., gRPC, FAISS, LMDB, Python/Go).  
* Set up the basic distributed framework using gRPC for RPC communication.  
  Core Functionality  
* Implement the put(vector, value) and query(vector, top\_k) API.  
* Integrate a local ANN index (e.g., FAISS) in each server node.  
* Develop the coordinator to manage metadata and route queries intelligently.

3\. Sharding & Indexing

* Implement both **hash-based** and **clustering-based sharding**.  
* Experiment with clustering algorithms (K-Means, IVF) to partition vector space.  
* Build routing logic to direct queries to relevant shards.

4\.  Evaluation & Measurement

* Load the system with real-world or synthetic embeddings.  
* Benchmark:  
  * Query latency (with increasing data and shards)  
  * Recall (accuracy of returned vectors)  
  * Load distribution and fan-out cost  
* Compare hash-based vs. vector-aware sharding strategies.

5\. Optimization & Fault Tolerance

* Implement replication and failure recovery mechanisms.  
* Add support for rebalancing shards when data distribution shifts.  
* Explore approximate global routing to reduce fan-out.

### 

### These are the points and details discussed till date for this project.

### 

### System Architecture:

 Client

* Interacts with the system via a gRPC.  
* Can **put(vector, value)** pairs or **query for similar vectors**.  
* Does not need to know the internal architecture.

  Coordinator (this logic can be embedded into the client itself)

* Knows the topology of the cluster (which node stores what).  
* Handles:  
  * **Metadata management** (which partition has which data).  
  * **Query routing** (where to send query vectors).  
  * **Replication coordination**.

Server Nodes (Data Nodes)

* Each maintains a **local ANN index** (e.g., HNSW, FAISS).  
* Responsible for:  
  * Ingesting data.  
  * Performing local similarity search.  
  * Syncing replicated data if enabled.

* Local databases (e.g., FISS, LMDB) for storing key-value pairs.

### Sharding Challenges:

1\. Non-Uniform Similarity Distribution

* Vectors are not uniformly distributed in space.  
* A simple hash-based sharding (like consistent hashing) breaks locality and makes similarity search across shards ineffective.

**Cons:** Similar vectors may be stored on different shards → degraded recall and increased cross-shard communication.

2\. Cross-Shard Querying (Fan-out Problem)

* To ensure high recall, the query must be **broadcast** to multiple shards.  
* Fan-out increases:  
  * **Latency**: Aggregating results from all shards.  
  * **Cost**: Network and compute usage.

**Trade-off:** Accuracy vs. scalability.

3\. Shard Imbalance

* Vector data often exhibits **clustered** patterns (e.g., due to natural groupings in embeddings).  
* Sharding based on clustering can lead to:  
  * **Hotspots** on some shards (load imbalance).  
  * Hard to rebalance shards dynamically due to large vector volumes.

4\. Index Partitioning

* Most vector search libraries (e.g., Faiss, ScaNN, HNSWlib) are designed for **single-node** or in-memory use.  
* Distributed sharding needs:  
  * Synchronized indexes across shards.  
  * Complexity in distributed ANN structures.

5\. Insert/Delete/Update Complexity

* Updating vector data means updating the similarity index.  
* In a sharded system:  
  * Need to find the right shard (often based on vector locality or hash).  
  * Might require **re-sharding** as distribution shifts.

### Some solutions we would like to explore:

1. Vector-Aware Sharding (Clustering-Based)  
* Use K-means, product quantization, or tree-based partitioning (e.g., IVF, ANNOY) to group similar vectors.  
* Assign clusters to shards.  
* Route queries to the top-N closest clusters.  
  **Pros:** Improves query accuracy and limits fan-out.  
  **Cons:** Hard to dynamically balance load. Re-clustering is expensive.  
2. Hybrid Indexing  
* Combine local ANN search within a shard with a global routing index (e.g., coarse quantizer or tree).  
3. Approximate Routing  
* Instead of querying all shards, use a lightweight approximate global index to select top-K shards likely to have relevant vectors.  
4. Dynamic Re-Sharding & Load Balancing  
* Monitor shard loads and periodically reassign vector clusters.  
* Use vector hashing schemes (like LSH) for more dynamic, approximate partitioning.  
5. Hierarchical Sharding  
* Combine coarse global sharding (based on vector locality) with fine-grained local indexing.

### **Scalability & Fault Tolerance**

* **Scalability**

  * Add more worker nodes to store more vectors.  
  * Load balancing through a coordinator or consistent hashing.

* **Fault Tolerance**  
  * Data replication.  
  * Coordinator failure recovery via leader election (e.g., Raft).  
  * Background rebalancing when nodes join/leave.

### Tools & Technologies

* **Programming Language**: Python or Go  
* **Libraries**: FAISS / ScaNN for ANN indexing  
* **RPC Framework**: gRPC  
* **Storage**: LMDB

# Matchmaking proposal

Group members: Andy Herbert, u1398830

Project: Matchmaking Simulator

In multiplayer video games, matchmaking is a task performed by servers which attempt to create matches between players, based on criteria such as relative skill or network latency. This project would seek to build a simulated matchmaking environment in a distributed systems manner, with an environment consisting of different clients with simulated distances away from matchmaking servers. The matchmaking servers would at minimum attempt to create matches of clients with the lowest latency, and upon meeting a certain number of clients (depending on the test environment), tell the clients to connect to a game server, which could operate virtualized on the matchmaking machine, or on a separate but nearby machine. The game server would instruct clients to perform a single shard workload, such as PA1 (or perhaps multi-sharded, where the matchmaking servers act as the data servers, and the game servers shard across the matchmaking servers). Upon completing the workload, the clients reconnect to the matchmaking server where they would be matched up as long as the matchmaking server is running.

In addition to implementing a matchmaking environment, this project would also consist of a research oriented component, to identify existing architectures of distributed systems related to this simulation, such as clients connecting to lowest latency servers, algorithms for determining fair matches, or even models which abstract servers and clients. Initially, the hypothesis of this project would be to explore the effectiveness of implementing a matchmaking system, but there may be a more concrete hypothesis to test after analyzing existing research.

Steps: 1\. Find, read up on potential relevant research. 2\. Revise the hypothesis to focus more based on relevant research. 3\. Implement a client and matchmaking server (attempt to use Go, but if a more object oriented approach is warranted, implement the matchmaking side outside of Go, while the game server/client would remain unmodified from PA1). 4\. Deploy and test on Cloudlab. 5\. Analyze results and repeat testing if warranted.

Work problem ideas:

matchmaking based: matches made with clients

* **Matchmaking simulation**: YCSB-like workload. Clients initially connect to coordinator, coordinator performs matchmaking. Clients connect to one game server (match). Objective is to rank clients by skill level, with a high amount of certainty (skill level and certainty explained below)  
  * Matches consist of rounds: clients in a match will send a (weighted per client) randomly generated value, and the server will respond with a score based on how off the client's score was to the median score, and how off the score was to neighboring scores. This score is added each round. Scores start at 0 and are compared based on the last received rpc data per client.  
  * The match ends when a client has exceeded a maximal score. match servers send the scores to the coordinator, and clients request a new match.  
  * A match consists of one or more servers and multiple clients, operating independently of other matches.  
  * To matchmake, the coordinator stores a skill level for each client: a rolling average of their workload's total; and additionally, a certainty value, which is used to dictate how close a client actually is to their skill. Each client starts with 500/1000 skill and 0 certainty.  
    * After completing a workload and receiving the result, the result is applied to the client's skill level (rolling average over the last 5 matches). The certainty is calculated as a percentage indicating deviation from the previous skill levels: 100% certainty means all the previous matches and current match in the rolling average were equal, 0% means the average deviation resulted in a change of 250 skill (which is 1/4 the total possible skill)  
      * the total averages and the certainty scale can be adjusted to meet the criteria, of perhaps an average of 85% certainty across clients. Coordinator will complete the experiment if the criteria is met and maintained for a certain amount of time.  
      * Certainty can be used to determine how much of a difference in skill level to apply, similar to an epsilon value in some ML training models  
  * Latency: latency can be factored into the change in skill level, with the idea being to give high latency clients the benefit of the doubt (high latency, less change in skill)  
  * Can integrate server farm components for more fine matchmaking  
* **Cheat detection:** YCSB workload, identical to PA1, except some clients will cheat by choosing specific keys to insert values into, instead of randomly or evenly distributed across shards. Servers report to a coordinator a log of transactions, and with mathematical probability the coordinator will attempt to determine the cheating clients. If a cheater is detected with high probability, coordinator instructs servers to reject and disconnect that client. At the end of the workload, final score is determined based on how many cheaters were removed vs how many stayed, and how many false positives there were.  
  * There is an interesting yt video I began watching about mathematically identifying cheaters. This is based on server side anticheat systems, which would communicate to matchmaking servers in games to reject cheaters from being matchmade (or matchmaking cheaters)  
    * Variation: matchmaking with cheaters. Each client is given a cheating score which is the probability they're a cheater. Rather than outright rejecting cheaters, clients are instead matchmade with similar cheat scores, the idea being cheaters end up getting matched with other cheaters and fair clients matched with other fair clients. Additional metrics like skill and latency can also play into this.  
* **Server farm/FAH simulation:** Workload consists of some complex mathematical operations, such as matrix operations. Clients connect to a coordinator, advertising their capabilities (ie what basic math operations can the client perform). Servers also connect to the coordinator, advertising what capabilities it is requesting. This is similar to something like Folding At Home, which allows anyone to use their own computer to assist with complex medical simulations.  
  * Coordinator calculates a similarity value, which indicates how much of a match a server is to a client. This value can be multiplied by total potential clients, if it is preferred to connect multiple clients instead of pairing one server to one client.  
  * If the similarity value meets a minimum, coordinator indicates to client(s) and server to connect to each other and commence workload. Server then communicates to clients based on its own workload, tracking which clients to use for certain RPCs.  
  * Upon completion, server and clients connect back to coordinator. Servers report to coordinator the results of the operation.  
  * Failover: if a client disconnects from a server, the server reports to the coordinator to request a new client, while performing the missing client's workload on the next best client. Upon the new client connecting, the next workload for that client is sent to it.  
  * Capabilities: can be determined by physical hardware, latency, or even simulated. Ideally, would be a set of operations/tasks which one machine can perform well in.  
    * Perhaps use machines with GPUs with this

Distributed workloads:

* **FAH/server farm flipped:** Same as server farm idea except clients have workloads for servers to execute.  
  * Coordinator instructs client to connect to specific servers for certain tasks (based on the server's capabilities, load, latency, etc.)  
  * servers process in parallel workloads from different clients, all independent per workload.  
  * If a server shuts down, clients request new workload to coordinator  
* **P2P farm:** remove the abstraction between server/client. Each peer advertises its own capabilities, and seeds other peers. Each peer determines other peers to connect to and send workloads to. Peers receive workloads and ideally process it (but have the potential to act maliciously?)  
  * cheat detection can be applied to this as well

