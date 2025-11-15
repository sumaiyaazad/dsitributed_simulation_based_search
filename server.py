import grpc
from concurrent import futures
import messages_pb2
import messages_pb2_grpc
import ipaddress

# In-memory key-value storage
store = {}

#base class for key-value rpcs
class KeyValueStoreServicer(messages_pb2_grpc.KeyValueStoreServicer):
	def Put(self, request, context):
		store[request.key] = request.value
		return messages_pb2.PutResponse(success=True, message=f"Stored key '{request.key}'")

	def Get(self, request, context):
		value = store.get(request.key, "")
		return messages_pb2.GetResponse(found=request.key in store, value=value)

	def Delete(self, request, context):
		if request.key in store:
			del store[request.key]
			return messages_pb2.DeleteResponse(success=True, message="Deleted successfully")
		return messages_pb2.DeleteResponse(success=False, message="Key not found")

#a (by default) key-value server
class Server():
	#specify an ip to listen on, or the ip which the server is located in
	ip: ipaddress.IPv4Address

	#the port to listen on
	port: int

	#the actual server object listening
	__server: grpc.server

	#sets up the appropriate RPC class 
	def setup_rpcs(self):
		messages_pb2_grpc.add_KeyValueStoreServicer_to_server(KeyValueStoreServicer(), self.__server)

	#starts listening on the specified port
	def serve(self, port: int = 50051) -> None:
		self.port = port
		self.__server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
		self.__server.add_insecure_port(f"[::]:{port}")
		print(f"✅ gRPC server running on port {port}")
		self.__server.start()
		self.__server.wait_for_termination()

if __name__ == "__main__":
	Server().serve()
