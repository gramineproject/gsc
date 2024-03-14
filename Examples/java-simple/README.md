# Simple Java application example

Java is one of the most popular programming languages in the world. By using the GSC tool, you can
deploy graminized containers with Java code. This is a trivial example on running a Java application
using GSC. For more information on Java, please visit https://www.oracle.com/java/.

## Notes

* Tested on:
  - Type: Azure Confidential Computing SGX Virtual Machine
  - Size: Standard DC1s v3 (1 vCPU, 8 GiB memory)
  - OS: Linux (Ubuntu 20.04)
  - OpenJDK 11

## Build and run graminized Docker image

1. Build Docker image:

```bash
$ docker build -t openjdk-11-java-simple .
```

2. Graminize the Docker image (this step can take some time!):

```bash
$ (cd ../.. && ./gsc build openjdk-11-java-simple \
    Examples/java-simple/java-simple.manifest \
    -c <PATH-TO-CONFIG-FILE>)
```

3. Sign the graminized Docker image:

```bash
$ (cd ../.. && ./gsc sign-image openjdk-11-java-simple \
    <PATH-TO-KEY-FILE> \
    -c <PATH-TO-CONFIG-FILE>)
```

4. Run graminized image:

```bash
$ docker run --rm --device=/dev/sgx_enclave \
    -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket \
    gsc-openjdk-11-java-simple
```
