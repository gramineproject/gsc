# NGINX

Currently tested distros are `ubuntu 18.04` and `ubuntu 20.04`.

## Building graminized Docker image

1. Build Docker image:
```bash
docker build -t nginx .
```

2. Graminize the Docker image using `gsc build`:
```bash
cd ../..
./gsc build --insecure-args nginx test/generic.manifest
```

3. Sign the graminized Docker image using `gsc sign-image`:
```bash
./gsc sign-image nginx enclave-key.pem
```

## Running NGINX server in GSC

### Start NGINX server

```bash
docker run --device=/dev/sgx_enclave --rm -it --privileged --network host --shm-size=4g --name nginx_g nginx:latest
```
To access the nginx server, go to `ip_address:8002`.