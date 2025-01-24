# OpenVINO benchmark

For additional information on supported models, how to install, run and optimize
OpenVINO, please see
https://github.com/gramineproject/examples/blob/master/openvino/README.md.

Currently tested distro is Ubuntu 24.04.

## Building graminized Docker image

1. Build Docker image:
```bash
docker build --tag ubuntu24.04-openvino --file ubuntu24.04-openvino.dockerfile .
```

2. Graminize the Docker image using `gsc build`:
```bash
cd ../..
./gsc build --insecure-args ubuntu24.04-openvino \
    Examples/openvino/ubuntu24.04-openvino.manifest
```

3. Sign the graminized Docker image using `gsc sign-image`:
```bash
./gsc sign-image ubuntu24.04-openvino enclave-key.pem
```

## Running the benchmark in GSC

### Throughput runs

- For benchmarking:
```bash
docker run --cpuset-cpus="0-35,72-107" --cpuset-mems=0 \
    --device /dev/sgx_enclave \
    gsc-ubuntu24.04-openvino -i <image files> \
    -m /model/<public | intel>/<model_dir>/<INT8 | FP16 | FP32>/<model_xml_file> \
    -d CPU -b 1 -t 20 -nstreams 72 -nthreads 72 -nireq 72 -hint none
```

- For a quick test:
```bash
docker run --rm --device /dev/sgx_enclave gsc-ubuntu24.04-openvino \
    -m /model/public/resnet-50-tf/FP16/resnet-50-tf.xml \
    -d CPU -b 1 -t 20 -nstreams 2 -nthreads 2 -nireq 2 -hint none
```

### Latency runs

- For benchmarking:
```bash
docker run --cpuset-cpus="0-35,72-107" --cpuset-mems="0" \
    --device /dev/sgx_enclave \
    gsc-ubuntu24.04-openvino -i <image files> \
    -m /model/<public | intel>/<model_dir>/<INT8 | FP16 | FP32>/<model_xml_file> \
    -d CPU -b 1 -t 20 -api sync -hint none
```

- For a quick test:
```bash
docker run --rm --device /dev/sgx_enclave gsc-ubuntu24.04-openvino \
    -m /model/public/resnet-50-tf/FP16/resnet-50-tf.xml \
    -d CPU -b 1 -t 20 -api sync -hint none
```

## Running the benchmark natively

To run the benchmark in a native Docker container (outside Gramine), run the above commands with the following modifications:
- remove `--device=/dev/sgx_enclave`,
- replace `gsc-ubuntu24.04-openvino` with `ubuntu24.04-openvino`.

## Notes

The above `docker run` commands are for a 36-core system. Please check
https://github.com/gramineproject/examples/blob/master/openvino/README.md for an
overview of options to achieve optimal performance on different systems.
