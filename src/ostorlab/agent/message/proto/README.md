Generate the `*_pb2.py` modules and their `*_pb2.pyi` stubs from the `.proto` definitions.

Install the pinned protobuf runtime and the gRPC codegen tool:

```shell
pip install "protobuf==6.33.6" "grpcio-tools==1.78.0"
```

Build all protos. Run from `src` so the generated modules land inside the `ostorlab` package tree:

```shell
cd src
find -path '*/proto/v3/*' -name '*.proto' | xargs -I {} python -m grpc_tools.protoc --proto_path=. --python_out=. {}
find -path '*/proto/common/*' -name '*.proto' | xargs -I {} python -m grpc_tools.protoc --proto_path=. --python_out=. {}
```

The `*_pb2.pyi` type stubs are committed too. Still inside `src` (from the build step above), regenerate them with the pinned stub toolchain:

```shell
pip install -r ../typing_requirements.txt
python ../tools/generate_proto_stubs.py
```
