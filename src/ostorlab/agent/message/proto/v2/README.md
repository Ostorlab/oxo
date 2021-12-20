# Protbuf & Message Serialization

## Compilation

To compile protobuf file to python, use command:

```shell
$cd ostorlab
$protoc -I. --python_out=. scan_engine/proto/scan/file.proto
```

## Rules

* A selector is the file path plus file name, for instance the selector '/scan/android/file' corresponds to
  proto/scan/android/file.proto

* The message class in the protobuf file must match the file name

* Protobuf definition MUST NOT use ENUM and nested messages

* Compiled protobuf files MUST be committed

* If new folder is created, it must be a python package
  (add '\_\_init\_\_.py' file)
