# Download and build Gramine directory

if [ -d "gramine" ]; then
    echo "***** gramine directory exists, proceeding to image generation *****"
else
    bash ./gramine_build.sh
fi

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
