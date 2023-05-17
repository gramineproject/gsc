# Simple Java application example

Java is one of the most popular programming languages in the world. By using the GSC tool, you can
deploy graminized containers with Java code. This is a trivial example on running
a Java application using GSC. For more information on Java, please visit
https://www.oracle.com/pl/java/.

## Disclaimer

* This generated image is for non-production usage.

* Tested on:
  - Type: Azure Confidential Computing SGX Virtual Machine
  - OS: Linux (Ubuntu 20.04)
  - Size: Standard DC1s v3 (1 vCPU, 8 GiB memory)
  - OpenJDK 11

## Build and run graminized Docker image

1. Navigate to the `java-simple/` directory:

```bash
$ cd gsc/Examples/java-simple/
```

2. Build a Docker image:

```bash
$ docker build -t java-simple .
```

3. Navigate to the `gsc/` directory:

```bash
$ cd ../..
```

1. Graminize the Docker image (this step can take some time!):

```bash
$ ./gsc build java-simple Examples/java-simple/java-simple.manifest \
        -c <PATH-TO-CONFIG-FILE>
```

1. Sign graminized Docker image using:

```bash
$ ./gsc sign-image java-simple <PATH-TO-KEY-FILE> \
        -c <PATH-TO-CONFIG-FILE>
```

6. Run graminized image: 

```bash
$ docker run --rm --device=/dev/sgx_enclave \
        -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket gsc-java-simple
```
