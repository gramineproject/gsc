# Download and build Gramine directory

gramine_dir="gramine"
if [ -d "$gramine_dir" ]; then
    echo "\n\n ***** '$gramine_dir' directory exists, proceeding to image generation ***** \n\n"
else
    chmod u+x gramine_build.sh
    ./gramine_build.sh
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

# Remove Gramine directory

rm -rf gramine/
