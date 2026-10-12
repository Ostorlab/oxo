Generate the `*_pb2.py` files from the `.proto` definitions.

Install the generator (use `grpc_tools.protoc`, not a system `protoc`):

```shell
pip install "protobuf==6.33.6" grpcio-tools
```

Build all protos (run from `src`):

```shell
cd src
find -path '*/proto/v3/*' -name '*.proto' | xargs -I {} python -m grpc_tools.protoc --proto_path=. --python_out=. {}
find -path '*/proto/common/*' -name '*.proto' | xargs -I {} python -m grpc_tools.protoc --proto_path=. --python_out=. {}
```
