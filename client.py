#!/usr/bin/env python3
import grpc
import kvstore_pb2
import kvstore_pb2_grpc

def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)

        print("Sending Put request...")
        put_response = stub.Put(kvstore_pb2.PutRequest(key="foo", value="bar"))
        print("Put:", put_response.message)

        print("Sending Get request...")
        get_response = stub.Get(kvstore_pb2.GetRequest(key="foo"))
        if get_response.found:
            print("Get: Found value =", get_response.value)
        else:
            print("Get: Key not found")

        print("Sending Delete request...")
        del_response = stub.Delete(kvstore_pb2.DeleteRequest(key="foo"))
        print("Delete:", del_response.message)

if __name__ == "__main__":
    run()
