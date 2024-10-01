Examples and Tests for GSC
==========================

This folder includes sample images and test cases for GSC:

-  Hello-World (print "Hello World!" using echo)
-  Bash (run bash command line)

Each sample consists of two files ``<distro>-<image-name>.dockerfile`` and
``<distro>-<image-name>.manifest`` where ``<distro>`` specifies the underlying
Linux distribution and ``<image-name>`` specifies the test case.

``.dockerfile`` describes the basic image and its application. It builds the
Docker image by installing required software packages, configuring the
application and changing the Docker entrypoint to start the application.

``.manifest`` describes the specific Gramine manifest changes required to run
this application reliably. For instance, this includes the memory size and the
number of threads. In some cases this file might be empty (default values are
used then).

Building sample images
----------------------

The example below shows how to graminize the sample Docker image of Bash. The
below commands assume that you already created the GSC configuration file
(`config.yaml`); for details on this file see the GSC documentation.

.. code-block:: sh

   cd ..

   docker build --tag ubuntu20.04-bash --file test/ubuntu20.04-bash.dockerfile .

   ./gsc build --insecure-args ubuntu20.04-bash test/ubuntu20.04-bash.manifest
   ./gsc sign-image ubuntu20.04-bash enclave-key.pem
   ./gsc info-image gsc-ubuntu20.04-bash

Test the graminized Docker image (change ``--device=/dev/sgx_enclave`` to your
version of the Intel SGX driver if needed):

.. code-block:: sh

   docker run --device=/dev/sgx_enclave \
      -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket \
      gsc-ubuntu20.04-bash -c ls

Building for Gramine-TDX
------------------------

Note that we need at least Ubuntu 22.04.

.. code-block:: sh

   docker build --tag ubuntu22.04-hello-world --file test/ubuntu22.04-hello-world.dockerfile .

   ./gsc build --buildtype debug ubuntu22.04-hello-world test/ubuntu22.04-hello-world.manifest
   ./gsc sign-image ubuntu22.04-hello-world enclave-key.pem

   docker run --env GRAMINE_MODE=vm --security-opt seccomp=unconfined \
       --shm-size 4G --env GRAMINE_CPU_NUM=1 \
       --device=/dev/vhost-vsock:/dev/vhost-vsock \
       --device=/dev/kvm:/dev/kvm --group-add `getent group kvm | cut -d: -f3` \
       gsc-ubuntu22.04-hello-world
   # or to peek into the image
   docker run -it --entrypoint /bin/bash gsc-ubuntu22.04-hello-world

Note that in ``docker run``, we must specify the following:

- ``--shm-size 4G`` -- our QEMU/KVM uses ``/dev/shm`` for virtio-fs shared
  memory. However, Docker containers start with 64MB by default. Thus, we need
  to explicitly specify the shared memory limit. ``4G`` is just an example; this
  limit depends on the app running inside Gramine-TDX.
- ``--env GRAMINE_CPU_NUM=1`` -- this instructs QEMU to spawn a Gramine-TDX VM
  with 1 vCPU. Modify this to have more vCPUs.
