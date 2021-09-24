# Gramine Attestation Inside AKS cluster

This guide demonstrates how Gramine DCAP attestation quote can be generated and verified from
within an AKS cluster. Here, we provide an end-to-end example to help Cloud Solution Providers
integrate Gramine’s RA-TLS attestation and secret provisioning feature with a confidential compute
cluster managed by Azure Kubernetes Service. The necessary reference wrappers that will enable
Gramine to use AKS components such as the AESMD and quote provider libraries are contributed.
A microservice deployment is also provided for the RA-TLS verifier module that can be readily
deployed to the AKS cluster.

## Preparing client and server images

This demonstration is created for ``gramine/CI-Examples/ra-tls-secret-prov`` sample.
In order to create the below two images, user needs to download core [Gramine repository](https://github.com/gramineproject/gramine).

### Creating server image

1. Prepare server certificate:
    - Create server certificate signed by your trusted root CA. Ensure "Common Name"
      field in the server certificate corresponds to `<AKS-DNS-NAME>` used in step 5.
    - Put trusted root CA certificate, server certificate, and server key in
      `gramine/CI-Examples/ra-tls-secret-prov/certs` directory with existing naming convention.

2. Make sure Gramine is built with `meson setup ... -Ddcap=enabled`.

3. Create base ra-tls-secret-prov server image:

    ```sh
    $ cd gramine/CI-Examples/ra-tls-secret-prov
    $ make clean && make dcap
    $ cd gramine
    $ docker build -t <aks-secret-prov-server-img> \
        -f <path-to-gsc>/examples/aks-attestation/aks-secret-prov-server.dockerfile .
    ```

4. Push resulting image to Docker Hub or your preferred registry:

    ```sh
    $ docker tag <aks-secret-prov-server-img> \
        <dockerhubusername>/<aks-secret-prov-server-img>
    $ docker push <dockerhubusername>/<aks-secret-prov-server-img>
    ```

5. Deploy `<aks-secret-prov-server-img>` in AKS confidential compute cluster:
    - Reference deployment file:
        `gsc/examples/aks-attestation/aks-secret-prov-server-deployment.yaml`

NOTE:  Server can be deployed at a non-confidential compute node as well. However, in that case
       QVE-based dcap verification will fail.

### Creating client image

1. Make sure Gramine is built with `meson setup ... -Ddcap=enabled`.

2. Create base ra-tls-secret-prov min client image:

    ```sh
    $ cd gramine/CI-Examples/ra-tls-secret-prov
    $ make clean && make secret_prov_min_client
    $ cd gramine
    $ docker build -t <base-secret-prov-client-img> \
        -f <path-to-gsc>/examples/aks-attestation/aks-secret-prov-client.dockerfile .
    ```

3. Prepare client to connect with remote ra-tls-secret-prov server hosted inside AKS cluster:
    - Provide server dns name `<AKS-DNS-NAME>` as `loader.env.SECRET_PROVISION_SERVERS` value
      inside `gsc/examples/aks-attestation/aks-secret-prov-client.manifest` file.

4. Create gsc image for ra-tls-secret-prov min client:

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

NOTE: We recommend deploying gsc images on Ubuntu with Linux kernel version 5.11 or higher.

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
