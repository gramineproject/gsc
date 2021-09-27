FROM ubuntu:18.04

RUN apt-get update \
    && env DEBIAN_FRONTEND=noninteractive apt-get install -y wget \
    build-essential \
    gnupg2 \
    libcurl3-gnutls \
    python3

# Installing DCAP libraries

RUN echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu bionic main' \
    > /etc/apt/sources.list.d/intel-sgx.list \
    && wget https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key \
    && apt-key add intel-sgx-deb.key

RUN apt-get update \
    && apt-get install -y libsgx-urts \
    libsgx-dcap-ql \
    libsgx-quote-ex

# Build environment of this Dockerfile should point to the root of Gramine directory

RUN mkdir -p /ra-tls-secret-prov

COPY CI-Examples/ra-tls-secret-prov /ra-tls-secret-prov

WORKDIR /ra-tls-secret-prov

ENV PATH = "${PATH}:/ra-tls-secret-prov"

ENTRYPOINT ["/ra-tls-secret-prov/secret_prov_min_client"]
