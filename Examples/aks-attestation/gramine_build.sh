# This script assumes that in-kernel driver is installed on the host system.
# Please refer to https://gramine.readthedocs.io/en/latest/devel/building.html#install-the-intel-sgx-driver
# for more details.

# Install Gramine dependencies
sudo apt-get install -y \
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

sudo python3 -B -m pip install 'toml>=0.10' 'meson>=0.55'

# Download Gramine
git clone https://github.com/gramineproject/gramine.git --depth=1
cd gramine
mkdir -p meson_build_output

# Generate signing key
openssl genrsa -3 -out Pal/src/host/Linux-SGX/signer/enclave-key.pem 3072

# Install DCAP dependencies
echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu bionic main' | \
    sudo tee /etc/apt/sources.list.d/intel-sgx.list
wget https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key
sudo apt-key add intel-sgx-deb.key
sudo apt-get install --no-install-recommends -y libsgx-urts libsgx-dcap-quote-verify-dev

# Build Gramine with DCAP enabled mode (assuming in-kernel driver)
meson setup build/ --prefix="$PWD/meson_build_output" --buildtype=release -Ddirect=enabled \
  -Dsgx=enabled -Ddcap=enabled
ninja -C build/
ninja -C build/ install

# Copy dummy server certificate with Common Name as "<AKS-DNS-NAME.*.cloudapp.azure.com>
cd ../
cp -r certs/ gramine/CI-Examples/ra-tls-secret-prov/
