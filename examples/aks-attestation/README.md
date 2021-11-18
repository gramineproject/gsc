# Gramine Attestation Inside AKS cluster

This guide demonstrates how Gramine DCAP attestation quote can be generated and verified from
within an AKS cluster. Here, we provide an end-to-end example to help Cloud Solution Providers
integrate Gramine’s RA-TLS attestation and secret provisioning feature with a confidential compute
cluster managed by Azure Kubernetes Service. The necessary reference wrappers that will enable
Gramine to use AKS components such as the AESMD and quote provider libraries are contributed.
A microservice deployment is also provided for the RA-TLS verifier module that can be readily
deployed to the AKS cluster.

## Preparing client and server images

This demonstration is based on ra-tls-secret-prov sample from
``gramine/CI-Examples/ra-tls-secret-prov``. Familiarity with this sample is highly recommended
before proceeding further.  The sample contains client and server applications, where by-default
server is running on localhost:4433. Here, the client sends its SGX quote to the server for
verification. After successful quote verification, the server sends a secret to the client. To run
these client and server applications inside AKS cluster, user needs to prepare two docker images,
each for client and server application. Since, now the server will no longer run on localhost,
instead it will run as part of a container inside AKS cluster, the server container should be
assigned a dns name (e.g., `<AKS-DNS-NAME>`) for outside container visibility. The client will send
requests to this dns name. Therefore, for demonstration we updated
``gramine/CI-Examples/ra-tls-secret-prov/certs`` directory certificates by replacing "Common Name"
field in the server certificate (i.e., `server2-sha256.crt`) from `localhost` to
`<AKS-DNS-NAME.*.cloudapp.azure.com>`.

In order to create base client and server images for AKS environment, user can execute
base-image-generation-script.sh script (with sudo). Since, both client and server applications will
run inside containers in AKS cluster, and the client wants to send its SGX quote to the server for
verification, therefore the user needs to graminize the client application, so that it can leverage
SGX capabilities from within a container. Hence, the following two steps create base server image
and gsc-client image for AKS cluster.

### Creating server image

1. The base-image-generation-script.sh script will create server image with the name
   aks-secret-prov-server-img:latest.

2. Push server image to Docker Hub or your preferred registry:

    ```sh
    $ docker tag <aks-secret-prov-server-img> \
        <dockerhubusername>/<aks-secret-prov-server-img>
    $ docker push <dockerhubusername>/<aks-secret-prov-server-img>
    ```

3. Deploy `<aks-secret-prov-server-img>` in AKS confidential compute cluster:
    - Reference deployment file:
        `gsc/examples/aks-attestation/aks-secret-prov-server-deployment.yaml`

### Creating client image

1. The base-image-generation-script.sh script will create client image with the name
   aks-secret-prov-client-img:latest.

2. Create GSC image for ra-tls-secret-prov min client:

    ```sh
    $ cd gsc
    $ openssl genrsa -3 -out enclave-key.pem 3072
    $ ./gsc build <base-secret-prov-client-img> \
        examples/aks-attestation/aks-secret-prov-client.manifest
    $ ./gsc sign-image <base-secret-prov-client-img> enclave-key.pem
    ```

5. Push resulting image to Docker Hub or your preferred registry:

    ```sh
    $ docker tag <gsc-base-secret-prov-client-img> \
        <dockerhubusername>/<aks-gsc-secret-prov-client-img>
    $ docker push <dockerhubusername>/<aks-gsc-secret-prov-client-img>
    ```

6. Deploy `<aks-gsc-secret-prov-client-img>` in AKS confidential compute cluster:
    - Reference deployment file:
        `gsc/examples/aks-attestation/aks-secret-prov-client-deployment.yaml`

**NOTE**: We recommend deploying GSC images on Ubuntu with Linux kernel version 5.11 or higher.

## Deploying client and server images inside AKS Confidential Compute cluster

AKS confidential compute cluster can be created using following
[link](https://docs.microsoft.com/en-us/azure/confidential-computing/confidential-nodes-aks-get-started).

Gramine performs out-of-proc mode DCAP quote generation. Out-of-proc mode quote generation requires aesmd
service. To fulfill this requirement, AKS provides
[sgxquotehelper daemonset](https://docs.microsoft.com/en-us/azure/confidential-computing/confidential-nodes-out-of-proc-attestation).
This feature exposes aesmd service for the container node. The service will internally connect with
az-dcap-client to fetch the platform collateral required for quote generation. In this demo, the
``aks-secret-prov-client-deployment.yaml`` uses aesmd service exposed by AKS with the help of
sgxquotehelper plugin.

In the ra-tls-secret-prov example, the client will generate out-of-proc mode sgx quote that will be
embedded inside RA-TLS certificate. On receiving the quote, the server will internally verify it
using libsgx-dcap-quote-verify library via az-dcap-client library. Here,
``aks-secret-prov-server-deployment.yaml`` will deploy a ra-tls-secret-prov server container inside
 AKS cluster.

### Deployment

```sh
$ kubectl apply -f aks-secret-prov-server-deployment.yaml
```

Once the server container is in running state, start the client container as shown below:

```sh
$ kubectl apply -f aks-secret-prov-client-deployment.yaml
```

At this stage, a successful RA-TLS verification would be completed, and the secrets have been
provisioned from the server to the client container.

## Checking SGX quote generation and verification

Verify the client job is completed:

```sh
$ kubectl get pods
```

Receive logs to verify the secret has been provisioned to the client:

```sh
$ kubectl logs -l app=gsc-ra-tls-secret-prov-client --tail=50
```

### Expected Output

`--- Received secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'`

Delete both client and server containers

```sh
$ kubectl delete -f aks-secret-prov-server-deployment.yaml
$ kubectl delete -f aks-secret-prov-client-deployment.yaml
```
