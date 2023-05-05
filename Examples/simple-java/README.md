# Simple java application example

Java is one of the most popular programming languages in the world. By using the GSC tool, you can
deploy containers with code that will increase the security level. For more information on Java,
please visit https://www.oracle.com/pl/java/.

## Disclaimer

* This generated confidential computing image is for non-production usage.

* Tested on:
  - Type: Azure Confidential Computing SGX Virtual Machine
  - OS: Linux (Ubuntu 20.04)
  - Size: Standard DC1s v3 (1 vCPU, 8 GiB memory)
  - OpenJDK 11

## Build and run graminized Docker image

1. Enter to simple-java directory:

```sh
$ cd gsc/Examples/gramine-simple-java/
```

2. Build a Docker image:

```sh
$ docker build -t gramine-simple-java .
```

3. Go back under the gsc/... directory:

```sh
$ cd ../..
```

4. Graminize the Docker image using gsc build (this step can take some time!):

```sh
$ ./gsc build gramine-simple-java Examples/gramine-simple-java/gramine-simple-java.manifest \
        -c Examples/gramine-simple-java/config.yaml
```

5. Sign graminized Docker image using gsc sign-image:

```sh
$ ./gsc sign-image gramine-simple-java enclave-key.pem \
        -c Examples/gramine-simple-java/config.yaml
```

6. Run graminized image. The first parameter is responsible for adding a host device to
the container, and this is the driver for SGX. The second parameter is used to bind mount
a volume in the form of an ASEM service, which provides key provisioning and remote attestation:

```sh
$ docker run --rm --device=/dev/sgx_enclave \
        -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket gsc-gramine-simple-java
```
