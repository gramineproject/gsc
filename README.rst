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

.. highlight:: sh

Docker containers are widely used to deploy applications in the cloud. Using
Gramine Shielded Containers (GSC) we provide the infrastructure to deploy Docker
containers protected by Intel SGX enclaves using the Gramine Library OS.

The GSC tool transforms a Docker image into a new image which includes the
Gramine Library OS, manifest files, Intel SGX related information, and executes
the application inside an Intel SGX enclave using the Gramine Library OS. It
follows the common Docker approach to first build an image and subsequently run
a container of an image.  At first a Docker image has to be graminized via the
``gsc build`` command. When the graminized image should run within an Intel SGX
enclave, the image has to be signed via a ``gsc sign-image`` command.
Subsequently, the image can be run using ``docker run``.

Gramine and GSC documentation
=============================

The official Gramine Library OS documentation can be found at
https://gramine.readthedocs.io.

The official GSC documentation can be found at
https://gramine-gsc.readthedocs.io.

How to contribute?
==================

We welcome contributions through GitHub pull requests. Please keep in mind that
they are governed by `the same rules as the main project
<https://gramine.readthedocs.io/en/latest/devel/contributing.html>`_.

Getting help
============

For any questions, please send an email to support@gramine-project.io
(`public archive <https://groups.google.com/forum/#!forum/gramine-support>`__).

For bug reports, post an issue on our GitHub repository:
https://github.com/gramineproject/gsc/issues.
