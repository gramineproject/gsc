# This script assumes that in-kernel driver is installed on the host system.
# Please refer https://gramine.readthedocs.io/en/latest/building.html#id2 for more details.

# install Gramine dependencies

apt-get install -y \
        autoconf \
        bison \
        build-essential \
        coreutils \
        curl \
        gawk \
        git \
        libcurl4-openssl-dev \
        libprotobuf-c-dev \
        linux-headers-generic \
        ninja-build \
        pkg-config \
        protobuf-c-compiler \
        python3 \
        python3-pip \
        python3-protobuf \
        wget

python3 -B -m pip install 'toml>=0.10' 'meson>=0.55'

# Download Gramine

git clone https://github.com/gramineproject/gramine.git

# Generate Signing Key

cd gramine/Pal/src/host/Linux-SGX/signer/
openssl genrsa -3 -out enclave-key.pem 3072

# Build Gramine with DCAP enabled mode (assuming in-kernel driver)

cd ../../../../../
meson setup build/ --buildtype=release -Ddirect=enabled -Dsgx=enabled -Ddcap=enabled
ninja -C build/
sudo ninja -C build/ install

# Copy dummy server certificate with Common Name as "<AKS-DNS-NAME.*.cloudapp.azure.com>
cd CI-Examples/ra-tls-secret-prov
mv certs certs_orig
cp -r ../../../certs  ./
