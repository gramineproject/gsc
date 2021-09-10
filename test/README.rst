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

The example below shows how to graminize the sample Docker image of Bash.

.. code-block:: sh

   cd ..

   docker build --tag ubuntu18.04-bash --file test/ubuntu18.04-bash.dockerfile .

   ./gsc build --insecure-args ubuntu18.04-bash test/ubuntu18.04-bash.manifest
   ./gsc sign-image ubuntu18.04-bash enclave-key.pem
   ./gsc info-image gsc-ubuntu18.04-bash

Test the graminized Docker image (change ``--device=/dev/sgx_enclave`` to your
version of the Intel SGX driver if needed):

.. code-block:: sh

   docker run --device=/dev/sgx_enclave \
      -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket \
      gsc-ubuntu18.04-bash -c ls
