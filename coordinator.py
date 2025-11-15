import queue
from server import Server
from concurrent import futures
import messages_pb2
import messages_pb2_grpc

#rpc functions for client communication
class ClientCoordinator(messages_pb2_grpc.CoordinatorClientServicer):
	#def Login(self, request, context):
		#return messages_pb2.PutResponse(success=False, message=f"RPC not implemented.")


#The Coordinator is a server which consists of two rpc servers:
#one client-facing and one server-facing.
class Coordinator(Server):
	#the queue of clients looking to join a game server
	player_queue = queue.Queue()

	#list of open game servers
	open_game_servers = []

	#list of game servers running matches
	busy_game_servers = []

