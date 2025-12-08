#!/bin/bash

source .venv/bin/activate
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. messages.proto
