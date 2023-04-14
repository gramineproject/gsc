# Simple java application as GSC

## Disclaimer
* This generated confidential computing image is for non-production usage.

* Tested on:</br>
  - Type: Azure Confidential Computing(Virtual Machine)</br>
  - OS: Linux(ubuntu 20.04)</br>
  - Size: Standard DC1s v3(1vcpu, 8 GiB memory )</br>
  - OpenJDK11
## Software requirements
1. Follow https://github.com/gramineproject/gsc to find a reference to the documentation to install Gramine and GSC, which are necessary to run this example 

## Build and run graminized Docker image
1.  Enter the directory with gramine-simple-java:
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
4. If you don't already have a signing key, then generate one using the following command presented below. If you have generated the key according to the instructions described in https://gramine.readthedocs.io/en/stable/quickstart.html, then you don't need to execute this command, instead, you need to indicate the correct path to it when signing the image:
```sh
$ openssl genrsa -3 -out enclave-key.pem 3072
```
5. Graminize the Docker image using gsc build (this step can take some time!):
```sh
$ ./gsc build   gramine-simple-java  Examples/gramine-simple-java/gramine-simple-java.manifest  -c Examples/gramine-simple-java/config.yaml
```
6. Sign graminized Docker image using gsc sign-image:
```sh
$ ./gsc sign-image gramine-simple-java  enclave-key.pem -c Examples/gramine-simple-java/config.yaml
``` 
7. Run graminized image. The first parameter is responsible for adding a host device to the container, and this is the driver for SGX. The second parameter is used to bind mount a volume in the form of an ASEM service, which provides key provisioning and remote attestation:
```sh
$ docker run --rm --device=/dev/sgx_enclave -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket gsc-gramine-simple-java
```