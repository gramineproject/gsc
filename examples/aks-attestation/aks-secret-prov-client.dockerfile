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

WORKDIR /ra-tls-secret-prov

COPY gramine/CI-Examples/ra-tls-secret-prov/certs ./certs

COPY gramine/CI-Examples/ra-tls-secret-prov/secret_prov_min_client /usr/local/bin

RUN mkdir libs

COPY gramine/build/Pal/src/host/Linux-SGX/tools/ra-tls/libsecret_prov_attest.so libs
COPY gramine/build/subprojects/mbedtls-mbedtls-2.26.0/libmbedcrypto_gramine.so.6 libs
COPY gramine/build/subprojects/mbedtls-mbedtls-2.26.0/libmbedtls_gramine.so.13 libs
COPY gramine/build/subprojects/mbedtls-mbedtls-2.26.0/libmbedx509_gramine.so.1 libs

ENV LD_LIBRARY_PATH = "${LD_LIBRARY_PATH}:/ra-tls-secret-prov/libs"

ENTRYPOINT ["secret_prov_min_client"]
