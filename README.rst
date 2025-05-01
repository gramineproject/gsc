*********************************
Gramine Shielded Containers (GSC)
*********************************

.. image:: https://readthedocs.org/projects/gramine-gsc/badge/?version=latest
   :target: http://gramine-gsc.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. This is not |~|, because that is in rst_prolog in conf.py, which GitHub cannot parse.
   GitHub doesn't appear to use it correctly anyway...
.. |nbsp| unicode:: 0xa0
   :trim:

Docker containers are widely used to deploy applications in the cloud. Using
Gramine Shielded Containers (GSC) we provide the infrastructure to deploy Docker
containers protected by Intel SGX enclaves using the Gramine Library OS.

The GSC tool transforms a Docker image into a new image which includes the
Gramine Library OS, manifest files, Intel SGX related information, and executes
the application inside an Intel SGX enclave using the Gramine Library OS. It
follows the common Docker approach to first build an image and subsequently run
this image inside of a container. At first a Docker image has to be graminized
via the ``gsc build`` command. When the graminized image should run within an
Intel SGX enclave, the image has to be signed via a ``gsc sign-image`` command.
Subsequently, the image can be run using ``docker run``.

**NOTE**: As part of the ``gsc build`` step, GSC generates the manifest file
with a list of trusted files (files with integrity protection). This list
contains hashes of *all* files present in the original Docker image. Therefore,
GSC's manifest creation capability depends on packaging of the original Docker
image: if the original Docker image is bloated (contains unnecessary files),
then the generated manifest will also be bloated. Though this doesn't worsen
security guarantees of Gramine/GSC, it may affect startup performance. Please
exercise care in pulling in only the dependencies truly required for your Docker
image.

Gramine and GSC documentation
=============================

The official Gramine Library OS documentation can be found at
https://gramine.readthedocs.io.

The official GSC documentation can be found at
https://gramine.readthedocs.io/projects/gsc.

How to contribute?
==================

We welcome contributions through GitHub pull requests. Please keep in mind that
they are governed by `the same rules as the main project
<https://gramine.readthedocs.io/en/latest/devel/contributing.html>`_.

Getting help
============

For any questions, please send an email to users@gramineproject.io
(`public archive <https://groups.google.com/g/gramine-users>`__).

For bug reports, post an issue on our GitHub repository:
https://github.com/gramineproject/gsc/issues.
