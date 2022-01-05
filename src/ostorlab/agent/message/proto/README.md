It important to build the file from the proto folder to maintain the package structure. A onliner to build all protos
in the v3 filder:
```shell
find v3 -name '*.proto' | xargs -I {} protoc --python_out=. {}
```
