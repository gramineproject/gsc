# Download and build Gramine directory. We need it to build and copy ra-tls-secret-prov files and
# relevant libraries into the server and client Dockerfiles.

if [ -d "gramine" ]; then
    echo "***** gramine directory exists, proceeding to image generation *****"
else
    bash ./gramine_build.sh
fi

# Include Meson build output directory in $PATH
export PATH="$PWD/gramine/meson_build_output/bin:$PATH"

# Include Meson build output Python dir in $PYTHONPATH, needed by gramine-sgx-get-token
export PYTHONPATH="$(find $PWD/gramine/meson_build_output/lib -type d -path '*/site-packages'):${PYTHONPATH}"

# Include Meson build output packages dir in $PKG_CONFIG_PATH, contains mbedTLS and util libs
export PKG_CONFIG_PATH="$(find $PWD/gramine/meson_build_output/lib -type d -path '*/pkgconfig'):${PKG_CONFIG_PATH}"

# Create Server image

cd gramine/CI-Examples/ra-tls-secret-prov
make clean && make dcap
cd ../../../
docker build -f aks-secret-prov-server.dockerfile -t aks-secret-prov-server-img .

# Create Client image

cd gramine/CI-Examples/ra-tls-secret-prov
make clean && make secret_prov_min_client
cd ../../../
docker build -f aks-secret-prov-client.dockerfile -t aks-secret-prov-client-img .

rm -rf gramine/
