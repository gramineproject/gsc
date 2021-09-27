FROM ubuntu:18.04

RUN apt-get update \
    && env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    gnupg2 \
    libcurl3-gnutls \
    libcurl4-openssl-dev \
    python3 \
    wget

# Installing Azure DCAP Quote Provider Library (az-dcap-client).
# Here, the version of az-dcap-client should be in sync with the az-dcap-client
# version used for quote generation. User can replace the below package with the
# latest package.

RUN wget https://github.com/microsoft/Azure-DCAP-Client/releases/download/1.8/az-dcap-client_1.8_amd64_18.04.deb \
    && dpkg -i az-dcap-client_1.8_amd64_18.04.deb

# Installing DCAP Quote Verification Library
RUN echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu bionic main' \
    > /etc/apt/sources.list.d/intel-sgx.list \
    && wget https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key \
    && apt-key add intel-sgx-deb.key

RUN apt-get update && apt-get install -y libsgx-dcap-quote-verify

# Build environment of this Dockerfile should point to the root of Gramine directory

RUN mkdir -p /ra-tls-secret-prov

COPY CI-Examples/ra-tls-secret-prov /ra-tls-secret-prov

RUN mkdir -p /ra-tls-secret-prov/libs

COPY build/Pal/src/host/Linux-SGX/tools/ra-tls/libsecret_prov_verify_dcap.so /ra-tls-secret-prov/libs
COPY build/Pal/src/host/Linux-SGX/tools/common/libsgx_util.so /ra-tls-secret-prov/libs
COPY build/subprojects/mbedtls-mbedtls-2.26.0/libmbedcrypto_gramine.so.6 /ra-tls-secret-prov/libs
COPY build/subprojects/mbedtls-mbedtls-2.26.0/libmbedtls_gramine.so.13 /ra-tls-secret-prov/libs
COPY build/subprojects/mbedtls-mbedtls-2.26.0/libmbedx509_gramine.so.1 /ra-tls-secret-prov/libs

ENV LD_LIBRARY_PATH = "${LD_LIBRARY_PATH}:/ra-tls-secret-prov/libs"

WORKDIR /ra-tls-secret-prov

ENTRYPOINT ["/ra-tls-secret-prov/secret_prov_server_dcap"]
