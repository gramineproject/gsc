FROM ubuntu:18.04

# Install prerequisites
RUN apt-get update && \
    env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    git \
    gnupg \
    numactl \
    python3 \
    python3-pip \
    wget

RUN curl -o GPG-PUB-KEY-INTEL-OPENVINO-2021 \
    "https://apt.repos.intel.com/openvino/2021/GPG-PUB-KEY-INTEL-OPENVINO-2021" && \
    apt-key add GPG-PUB-KEY-INTEL-OPENVINO-2021 && \
    echo "deb https://apt.repos.intel.com/openvino/2021 all main" \
    | tee - a /etc/apt/sources.list.d/intel-openvino-2021.list && \
    apt-get update && apt-get install -y --no-install-recommends "intel-openvino-dev-ubuntu18-2021.4.582" && \
    rm -rf /var/lib/apt/lists/*

# Workaround for a failure due to update in major release of Protobuf from 3.20.1 to 4.21.0
# see details at https://developers.google.com/protocol-buffers/docs/news/2022-05-06#python-updates
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# Build apps
RUN cd /opt/intel/openvino_2021.4.582/inference_engine/samples/cpp && \
    ./build_samples.sh

# Download models benchmark app
RUN cd /opt/intel/openvino_2021.4.582/deployment_tools/open_model_zoo/tools/downloader && \
    pip3 install -r ./requirements.in && \
    cd /opt/intel/openvino_2021.4.582/deployment_tools/model_optimizer && \
    python3 -m pip install --upgrade pip setuptools && \
    pip3 install -r requirements.txt && \
    cd /opt/intel/openvino_2021.4.582/deployment_tools/open_model_zoo/tools/downloader && \
    for model_name in resnet-50-tf \
                      bert-large-uncased-whole-word-masking-squad-0001 \
                      bert-large-uncased-whole-word-masking-squad-int8-0001 \
                      brain-tumor-segmentation-0001 \
                      brain-tumor-segmentation-0002 \
                      ssd_mobilenet_v1_coco; \
    do \
        python3 ./downloader.py --name $model_name -o /model; \
        python3 ./converter.py --mo /opt/intel/openvino_2021.4.582/deployment_tools/model_optimizer/mo.py --name $model_name -d /model -o /model; \
    done

ENV LD_LIBRARY_PATH=/opt/intel/openvino_2021.4.582/deployment_tools/inference_engine/external/tbb/lib:/opt/intel/openvino_2021.4.582/deployment_tools/inference_engine/lib/intel64:/opt/intel/openvino_2021.4.582/deployment_tools/ngraph/lib:$LD_LIBRARY_PATH

RUN echo "source /opt/intel/openvino_2021.4.582/bin/setupvars.sh" > /root/.bashrc

ENTRYPOINT ["/root/inference_engine_cpp_samples_build/intel64/Release/benchmark_app"]
