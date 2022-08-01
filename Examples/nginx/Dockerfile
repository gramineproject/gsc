FROM ubuntu:20.04

RUN apt-get update && \
    env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    numactl \
    wget \
    curl \
    build-essential \ 
    apache2-utils \ 
    libssl-dev \ 
    libcurl4-openssl-dev \
    libprotobuf-c-dev \
    protobuf-c-compiler \
    python3-pip \ 
    python3-protobuf \
    meson \
    pkg-config \
    cmake \
    libpcre3 \ 
    libpcre3-dev \
    zlib1g \
    zlib1g-dev \
    libssl-dev \
    make

RUN git clone https://github.com/gramineproject/gramine.git /home/gramine 
RUN cd /home/gramine \
    && curl -fsSLo /usr/share/keyrings/gramine-keyring.gpg https://packages.gramineproject.io/gramine-keyring.gpg \
    && echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/gramine-keyring.gpg] https://packages.gramineproject.io/ stable main' | tee /etc/apt/sources.list.d/gramine.list \
    && apt-get update \
    && apt-get install gramine -y \
    && cd /home/gramine/CI-Examples/nginx/ \
    && mkdir -p "$HOME"/.config/gramine/ \
    && openssl genrsa -3 -out "$HOME"/.config/gramine/enclave-key.pem 3072 \
    && sed -i 's/worker_processes 4/worker_processes 1/' nginx-gramine.conf.template \
    && sed -i 's/sgx.thread_num = 4/sgx.thread_num = 1/' nginx.manifest.template \
    && make

COPY start_nginx.sh /home/gramine/CI-Examples/nginx/

WORKDIR /home/gramine/CI-Examples/nginx/
RUN chmod +x /home/gramine/CI-Examples/nginx/start_nginx.sh

ENTRYPOINT ["bash","start_nginx.sh"]
