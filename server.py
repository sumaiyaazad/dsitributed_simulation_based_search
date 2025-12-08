import numpy as np
import grpc
import random
import time
import threading
import os
from concurrent import futures
import threading
import time
import random

import messages_pb2
import messages_pb2_grpc

from common import search_faiss_index, create_faiss_index, read_player_attrs, encode_player

from common import REGIONS, RANKS 

server_id = 0
class PlayerService(messages_pb2_grpc.MatchmakerServiceServicer):
    def __init__(self, shard):
        super().__init__()
        self.shard = shard

    # ----------------------------
    # ANN Search
    # ----------------------------
    def RequestPlayers(self, request, context):
        query_vec = np.array(request.values, dtype=np.float32).reshape(1, -1)

        NUM_NEIGHBORS = 100
        dists, idxs = search_faiss_index(self.shard.index, query_vec, NUM_NEIGHBORS)

        chosen_ids = []
        MAX_RETURN = 10

        for idx in idxs[0]:
            idx = int(idx)

            if idx not in self.shard.online_indices:
                continue
            if idx in self.shard.busy_indices:
                continue
            if idx in self.shard.held_indices:
                continue

            pid = self.shard.all_player_ids[idx]
            chosen_ids.append(pid)

            if len(chosen_ids) >= MAX_RETURN:
                break

        return messages_pb2.PlayerList(playersIds=chosen_ids)

    # ----------------------------
    # Final Match Lock
    # ----------------------------
    def ConfirmToMatch(self, request, context):
        locked = 0
        with self.shard.lock:
            for pid in request.playersIds:
                idx = self.shard.id_to_index.get(pid)
                if idx is None:
                    continue

                self.shard.busy_indices.add(idx)
                self.shard.online_indices.discard(idx)
                self.shard.held_indices.discard(idx)

                locked += 1

        return messages_pb2.Status(isOK=True, message=f"Locked {locked} players")

    def HoldMatchPlayers(self, request, context):
        failed = []
        ok_to_hold = []

        with self.shard.lock:
            for pid in request.playersIds:
                idx = self.shard.id_to_index.get(pid)

                if idx is None:
                    failed.append(pid)
                    continue

                if idx in self.shard.busy_indices:
                    failed.append(pid)
                    continue
                if idx in self.shard.held_indices:
                    failed.append(pid)
                    continue

                ok_to_hold.append(idx)

            # If ANY player fails → coordinator can decide strategy
            if failed:
                return messages_pb2.HoldResponse(
                    success=False,
                    failedPlayers=failed
                )

            # Otherwise hold all
            for idx in ok_to_hold:
                self.shard.held_indices.add(idx)
                self.shard.online_indices.discard(idx)

        return messages_pb2.HoldResponse(success=True)

    def ReleaseMatchPlayers(self, request, context):
        released = 0

        with self.shard.lock:
            for pid in request.playersIds:
                idx = self.shard.id_to_index.get(pid)
                if idx is None:
                    continue

                if idx in self.shard.held_indices:
                    self.shard.held_indices.remove(idx)
                    self.shard.online_indices.add(idx)
                    released += 1

        return messages_pb2.Status(
            isOK=True,
            message=f"Released {released} players"
        )
