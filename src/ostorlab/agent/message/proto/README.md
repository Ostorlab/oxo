It is important to build the file from the src folder to maintain the package structure. A onliner to build all protos
in the `src` folder:
```shell
find -path '*/proto/v3/*' -name '*.proto' | xargs -I {} protoc --python_out=. {}
find -path '*/proto/common/*' -name '*.proto' | xargs -I {} protoc --python_out=. {}
```
