# Gramine Attestation Inside AKS cluster

This guide demonstrates how Gramine DCAP attestation quote can be generated and verified from
within an AKS cluster. Here, we provide an end-to-end example to help Cloud Solution Providers
integrate Gramine’s RA-TLS attestation and secret provisioning feature with a confidential compute
cluster managed by Azure Kubernetes Service. This guide contains necessary reference wrappers that
enable Gramine to use AKS components such as AESMD and DCAP quote provider libraries. This guide
also describes a microservice deployment for the RA-TLS verifier (server) that can be readily
deployed to the AKS cluster.

## Preparing client and server images

This demonstration is based on the `ra-tls-secret-prov` example from
https://github.com/gramineproject/gramine/tree/master/CI-Examples/ra-tls-secret-prov. Familiarity
with this example is highly recommended before proceeding further. The sample contains client and
server applications, where by default server is running on localhost:4433. In the example, the
client sends its SGX quote to the server for verification. After successful quote verification, the
server sends a secret to the client. To run these client and server applications inside the AKS
cluster, user needs to prepare two docker images, one for the client and one for the server. In our
AKS attestation example, the server will no longer run on localhost, instead it will run in a Docker
container inside the AKS cluster. The server container should be assigned a DNS name
(e.g., `<AKS-DNS-NAME>`) to be accessible from the outside of the container. The client will send
requests to this DNS name. Therefore, for demonstration we updated the example certificates from
https://github.com/gramineproject/gramine/tree/master/CI-Examples/ra-tls-secret-prov/certs by
replacing the "Common Name" field in the server certificate (i.e., `server2-sha256.crt`) from
`localhost` to `<AKS-DNS-NAME.*.cloudapp.azure.com>`.

In order to create base client and server images for the AKS environment, user can execute the
`base-image-generation-script.sh` script. Since both client and server applications will
run inside containers in the AKS cluster, and the client application will send its SGX quote to the
server for verification, therefore the user needs to graminize the client application. Hence, the
following two steps create a native Docker server image and a graminized GSC client image for the
AKS cluster.

Note: This example is Ubuntu-specific (tested version is Ubuntu 18.04).

### Creating server image

1. The `base-image-generation-script.sh` script will create the native Docker server image with the
   name `aks-secret-prov-server-img:latest`.

2. Push the server image to Docker Hub or your preferred registry:

    ```sh
    $ docker tag aks-secret-prov-server-img:latest \
        <dockerhubusername>/aks-secret-prov-server-img:latest
    $ docker push <dockerhubusername>/aks-secret-prov-server-img:latest
    ```

3. Deploy `aks-secret-prov-server-img:latest` in the AKS confidential compute cluster:
    - Reference deployment file:
        `aks-secret-prov-server-deployment.yaml`

### Creating client image

1. The `base-image-generation-script.sh` script will create the native Docker client image with the
   name `aks-secret-prov-client-img:latest`.

2. Create the GSC client image:

    ```sh
    $ cd gsc
    $ cp config.yaml.template config.yaml
    $ openssl genrsa -3 -out enclave-key.pem 3072
    $ ./gsc build aks-secret-prov-client-img:latest \
        examples/aks-attestation/aks-secret-prov-client.manifest
    $ ./gsc sign-image aks-secret-prov-client-img:latest enclave-key.pem
    ```

5. Push resulting image to Docker Hub or your preferred registry:

    ```sh
    $ docker tag gsc-aks-secret-prov-client-img:latest \
        <dockerhubusername>/gsc-aks-secret-prov-client-img:latest
    $ docker push <dockerhubusername>/gsc-aks-secret-prov-client-img:latest
    ```

6. Deploy `gsc-aks-secret-prov-client-img:latest` in AKS confidential compute cluster:
    - Reference deployment file:
        `aks-secret-prov-client-deployment.yaml`

Note: We tested this example with DCAP driver 1.11 specified in the GSC configuration file.

## Deploying client and server images in AKS Confidential Compute cluster

AKS confidential compute cluster can be created using the following
[link](https://docs.microsoft.com/en-us/azure/confidential-computing/confidential-enclave-nodes-aks-get-started).

Gramine performs out-of-proc mode DCAP quote generation. Out-of-proc mode quote generation requires
aesmd service. To fulfill this requirement, AKS provides the
[sgxquotehelper daemonset](https://docs.microsoft.com/en-us/azure/confidential-computing/confidential-nodes-aks-addon#out-of-proc-attestation-for-confidential-workloads)
(can be enabled by `--enable-sgxquotehelper` during cluster creation). This feature exposes aesmd
service for the container node. The service will internally connect with az-dcap-client to fetch the
platform collateral required for quote generation. In this demo, the
`aks-secret-prov-client-deployment.yaml` uses aesmd service exposed by AKS with the help of the
sgxquotehelper plugin.

In our example, the client will generate the SGX quote that will be embedded inside the RA-TLS
certificate. On receiving the quote, the server will internally verify it using the
libsgx-dcap-quote-verify library via the az-dcap-client library.

### Deployment

```sh
$ kubectl apply -f aks-secret-prov-server-deployment.yaml
```

Once the server container is in running state, start the client container as shown below:

```sh
$ kubectl apply -f aks-secret-prov-client-deployment.yaml
```

At this stage, a successful RA-TLS verification will be completed, and the secrets will be
provisioned from the server to the client.

## Checking SGX quote generation and verification

Verify the client job is completed:

```sh
$ kubectl get pods
```

Receive logs to verify the secret has been provisioned to the client:

```sh
$ kubectl logs -l app=gsc-ra-tls-secret-prov-client --tail=50
```

Expected output:

`--- Received secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'`

Delete both client and server containers:

```sh
$ kubectl delete -f aks-secret-prov-server-deployment.yaml
$ kubectl delete -f aks-secret-prov-client-deployment.yaml
```
