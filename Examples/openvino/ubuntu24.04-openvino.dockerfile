FROM openvino/ubuntu24_dev:2024.6.0

USER root

RUN for model_name in resnet-50-tf \
                      bert-large-uncased-whole-word-masking-squad-0001 \
                      ssd_mobilenet_v1_coco \
                      brain-tumor-segmentation-0002 \
                      bert-large-uncased-whole-word-masking-squad-int8-0001; do \
        omz_downloader --name $model_name -o model && \
        omz_converter --name $model_name -d model -o model; \
    done

ENTRYPOINT ["/opt/intel/openvino/samples/cpp/samples_bin/samples_bin/benchmark_app"]
