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
RUN wget https://packages.microsoft.com/ubuntu/18.04/prod/pool/main/a/az-dcap-client/az-dcap-client_1.10_amd64.deb \
 && dpkg -i az-dcap-client_1.10_amd64.deb

# Installing DCAP Quote Verification Library
RUN echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu bionic main' \
    > /etc/apt/sources.list.d/intel-sgx.list \
    && wget https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key \
    && apt-key add intel-sgx-deb.key

RUN apt-get update && apt-get install -y libsgx-dcap-quote-verify

WORKDIR /ra-tls-secret-prov

COPY gramine/CI-Examples/ra-tls-secret-prov/certs ./certs
COPY gramine/CI-Examples/ra-tls-secret-prov/files ./files

COPY gramine/CI-Examples/ra-tls-secret-prov/secret_prov_server_dcap /usr/local/bin

RUN mkdir libs

COPY gramine/meson_build_output/lib/x86_64-linux-gnu/libsecret_prov_verify_dcap.so libs
COPY gramine/meson_build_output/lib/x86_64-linux-gnu/libsgx_util.so libs
COPY gramine/meson_build_output/lib/x86_64-linux-gnu/libmbedcrypto_gramine.so.* libs
COPY gramine/meson_build_output/lib/x86_64-linux-gnu/libmbedtls_gramine.so.* libs
COPY gramine/meson_build_output/lib/x86_64-linux-gnu/libmbedx509_gramine.so.* libs

ENV LD_LIBRARY_PATH = "${LD_LIBRARY_PATH}:/ra-tls-secret-prov/libs"

ENTRYPOINT ["secret_prov_server_dcap"]
