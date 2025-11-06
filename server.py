import grpc
from concurrent import futures
import kvstore_pb2
import kvstore_pb2_grpc

# In-memory key-value storage
store = {}

class KeyValueStoreServicer(kvstore_pb2_grpc.KeyValueStoreServicer):
    def Put(self, request, context):
        store[request.key] = request.value
        return kvstore_pb2.PutResponse(success=True, message=f"Stored key '{request.key}'")

    def Get(self, request, context):
        value = store.get(request.key, "")
        return kvstore_pb2.GetResponse(found=request.key in store, value=value)

    def Delete(self, request, context):
        if request.key in store:
            del store[request.key]
            return kvstore_pb2.DeleteResponse(success=True, message="Deleted successfully")
        return kvstore_pb2.DeleteResponse(success=False, message="Key not found")

def serve(port: int = 50051) -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvstore_pb2_grpc.add_KeyValueStoreServicer_to_server(KeyValueStoreServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    print(f"✅ gRPC server running on port {port}")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
