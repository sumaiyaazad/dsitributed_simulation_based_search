from server import Server
import messages_pb2
import messages_pb2_grpc

class GameServerService(messages_pb2_grpc.GameServerServicer):
	pass

# a GameServer hosts multiple clients, to perform some workload across the clients.
# This file can be run directly to host a game server, or the class used to store
# info about a game server without running it.
class GameServer(Server):
	pass
	#requests = []