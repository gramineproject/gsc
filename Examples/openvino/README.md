# OpenVINO benchmark

For additional information on supported models, how to install, run and optimize
OpenVINO, please see
https://github.com/gramineproject/examples/blob/master/openvino/README.md.

Currently tested distro is Ubuntu 20.04.

## Building graminized Docker image

1. Build Docker image:
```bash
docker build --tag ubuntu20.04-openvino --file ubuntu20.04-openvino.dockerfile .
```

2. Graminize the Docker image using `gsc build`:
```bash
cd ../..
./gsc build --insecure-args \
    --manifest Examples/openvino/ubuntu20.04-openvino.manifest \
    ubuntu20.04-openvino
```

3. Sign the graminized Docker image using `gsc sign-image`:
```bash
./gsc sign-image --key enclave-key.pem ubuntu20.04-openvino
```

## Running the benchmark in GSC

### Throughput runs

- For benchmarking:
```bash
$ docker run --cpuset-cpus="0-35,72-107" --cpuset-mems=0 \
    --device /dev/sgx_enclave \
    gsc-ubuntu20.04-openvino -i <image files> \
    -m model/<public | intel>/<model_dir>/<INT8 | FP16 | FP32>/<model_xml_file> \
    -d CPU -b 1 -t 20 -nstreams 72 -nthreads 72 -nireq 72
```

- For a quick test:
```bash
$ docker run --rm --device /dev/sgx_enclave gsc-ubuntu20.04-openvino \
    -m model/public/resnet-50-tf/FP16/resnet-50-tf.xml \
    -d CPU -b 1 -t 20 -nstreams 2 -nthreads 2 -nireq 2
```

### Latency runs

- For benchmarking:
```bash
$ docker run --cpuset-cpus="0-35,72-107" --cpuset-mems="0" \
    --device /dev/sgx_enclave \
    gsc-ubuntu20.04-openvino -i <image files> \
    -m model/<public | intel>/<model_dir>/<INT8 | FP16 | FP32>/<model_xml_file> \
    -d CPU -b 1 -t 20 -api sync
```

- For a quick test:
```bash
$ docker run --rm --device /dev/sgx_enclave gsc-ubuntu20.04-openvino \
    -m model/public/resnet-50-tf/FP16/resnet-50-tf.xml \
    -d CPU -b 1 -t 20 -api sync
```

## Running the benchmark natively

To run the benchmark in a native Docker container (outside Gramine), run the
above commands with the following modifications:
- remove `--device=/dev/sgx_enclave`,
- replace `gsc-ubuntu20.04-openvino` with `ubuntu20.04-openvino`.

## Notes

The above `docker run` commands are for a 36-core system. Please check
https://github.com/gramineproject/examples/blob/master/openvino/README.md for an
overview of options to achieve optimal performance on different systems.
