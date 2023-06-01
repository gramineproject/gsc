# Java Spring Boot example

Spring Boot is a popular framework for building Java-based web applications. By using the GSC tool,
you can deploy Spring Boot web applications inside a graminized Docker container, such that the app
runs inside the SGX enclave. For more information on Spring Boot, please visit https://spring.io/.

## Notes

* This generated image is for non-production usage.

* Tested on:
  - Type: Azure Confidential Computing SGX Virtual Machine
  - Size: Standard DC1s v3 (1 vCPU, 8 GiB memory)
  - OS: Linux (Ubuntu 20.04)

* Install the OpenJDK 11 package so that Gradle can consume the files:

    ```bash
    $ sudo apt-get install openjdk-11-jdk
    ```

* Follow the installation guide at https://gradle.org/install/ to install Gradle v7.6.

## Build and run graminized Docker image

1. Build a project using Gradle:

```bash
$ (cd spring-boot-web-service/; gradle build)
```

2. Build Docker image:

```bash
$ docker build -t openjdk-11-java-spring-boot .
```

3. Clean up files that will be no longer used:

```bash
$ (cd spring-boot-web-service/; gradle clean)
```

4. Graminize the Docker image (this step can take some time!):

```bash
$ (cd ../..; ./gsc build openjdk-11-java-spring-boot \
    Examples/java-spring-boot/java-spring-boot.manifest \
    -c <PATH-TO-CONFIG-FILE>)
```

5. Sign the graminized Docker image:

```bash
$ (cd ../..; ./gsc sign-image openjdk-11-java-spring-boot \
    <PATH-TO-KEY-FILE> \
    -c <PATH-TO-CONFIG-FILE>)
```

6. Run graminized image (the application may take a while to load):

      * On the default port set to 8080:

        ```bash
        $ docker run --rm --device=/dev/sgx_enclave \
            -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket \
            -p 8080:8080 \
            -d gsc-openjdk-11-java-spring-boot
        ```

      * On a customized port using an environment variable, e.g. 9080:

        ```bash
        $ docker run --rm --device=/dev/sgx_enclave \
            -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket \
            -e SERVER_PORT=9080 \
            -p 9080:9080 \
            -d gsc-openjdk-11-java-spring-boot
        ```


7. Once you have the graminized container up and running, verify its correctness by calling
the following command below. The result should be the following text - "Hello from Graminized Spring
Boot application":

```bash
$ wget -q localhost:<port>
$ cat index.html
```

8. To stop the graminized container with Spring-Boot application, run the command:

```sh
$ docker stop <containerID>
```
