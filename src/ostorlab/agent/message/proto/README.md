It important to build the file from the proto folder to maintain the package structure. A onliner to build all protos
in the v3 filder:
```shell
find v3 -name '*.proto' | xargs -I {} protoc --python_out=. {}
```

For the case where a protobuf message from outside the v3 directory, is used in one of the message of v3.
The following points should be considered:

1. The package name should start from the root of the project:
```
package ostorlab.agent.messsage.proto.common.x509;
```

2.Compile the external proto normaly, from the proto directory:

```shell
find common -name '*.proto' | xargs -I {} protoc --python_out=. {}
```

3. Import the message as follows:
```
import "ostorlab/agent/message/proto/common/x509/x509.proto";
    ....
repeated ostorlab.agent.messsage.proto.common.x509.X509Cert cert_chain = 4;
```
