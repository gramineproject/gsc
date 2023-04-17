.. program:: gsc

=============================================
:program:`gsc` -- Gramine Shielded Containers
=============================================

Synopsis
========

:command:`gsc` *COMMAND* [*OPTIONS*] ...

Description
===========

Docker containers are widely used to deploy applications in the cloud. Using
Gramine Shielded Containers (GSC) we provide the infrastructure to deploy Docker
containers protected by Intel SGX enclaves using the Gramine Library OS.

The :program:`gsc` tool transforms a Docker image into a new image
(called ``gsc-<image-name>``) which includes the Gramine Library OS, manifest
files, Intel SGX related information, and executes the application inside an
Intel SGX enclave using the Gramine Library OS. It follows the common Docker
approach to first build an image and subsequently run a container of an image.
At first a Docker image has to be graminized via the :command:`gsc build`
command. When the graminized image should run within an Intel SGX enclave, the
image has to be signed via a :command:`gsc sign-image` command. Subsequently,
the image can be run using :command:`docker run`.

**NOTE**: As part of the :command:`gsc build` step, GSC generates the manifest
file with a list of trusted files (files with integrity protection). This list
contains hashes of *all* files present in the original Docker image. Therefore,
GSC's manifest creation capability depends on packaging of the original Docker
image: if the original Docker image is bloated (contains unnecessary files),
then the generated manifest will also be bloated. Though this doesn't worsen
security guarantees of Gramine/GSC, it may affect startup performance. Please
exercise care in pulling in only the dependencies truly required for your Docker
image.

Prerequisites
=============

The installation descriptions of prerequisites are for Ubuntu 18.04 and may
differ when using a different Ubuntu version or Linux distribution.

Software packages
-----------------

Please install the ``docker.io``, ``python3``, ``python3-pip`` packages. In
addition, install the Docker client, Jinja2, TOML, and YAML python packages via
pip. GSC requires Python 3.6 or later.

.. code-block:: sh

   sudo apt-get install docker.io python3 python3-pip
   pip3 install docker jinja2 tomli tomli-w pyyaml
   pip3 install toml  # for compatibility with Gramine v1.3 or lower

SGX software stack
------------------

To run with Intel SGX, please install the corresponding software stack as
described in https://gramine.readthedocs.io/en/stable/devel/building.html.

Host configuration
------------------

To create Docker images, the user must have access to Docker daemon.

.. warning::
    Please use this step with caution. By granting the user access to the Docker
    group, the user may acquire root privileges via :command:`docker run`.

.. code-block:: sh

   sudo adduser $USER docker

Create a configuration file called :file:`config.yaml` or specify a different
configuration file via :program:`gsc` option. Please see the documentation on
configuration options below and use the :file:`config.yaml.template` as
reference.

Command line arguments
======================

.. option:: --help

   Display usage.

.. program:: gsc-build

:command:`gsc build` -- build graminized image
-----------------------------------------------

Builds an unsigned graminized Docker image of an application image called
``gsc-<IMAGE-NAME>-unsigned`` by compiling Gramine or relying on a prebuilt
Gramine image.

:command:`gsc build` [*OPTIONS*] <*IMAGE-NAME*> <*APP.MANIFEST*>

.. option:: -b <buildtype>, --buildtype <buildtype>

   Use <buildtype> value ``release``, ``debug`` or ``debugoptimized`` to
   compile Gramine in the corresponding mode. Default: ``release``.

..
  TODO: Drop `-d` option with GSC v1.6 release

.. option:: -d, --debug

   Compile Gramine with debug flags and debug output.

   .. deprecated:: 1.5
      Use :option:`--buildtype`.

.. option:: -L

   Compile Gramine with Linux PAL in addition to Linux-SGX PAL. If configured
   to use a prebuilt Gramine image, the image has to support this option.

.. option:: --insecure-args

   Allow untrusted arguments to be specified at :command:`docker run`. Otherwise
   any arguments specified during :command:`docker run` are ignored.

.. option:: --no-cache

   Disable Docker's caches during :command:`gsc build`. This builds the
   unsigned graminized image from scratch.

.. option:: --rm

   Remove intermediate Docker images created by :command:`gsc build`, if the
   image build is successful.

.. option:: --build-arg

   Set build-time variables during :command:`gsc build` (same as `docker build
   --build-arg`).

.. option:: -c

   Specify configuration file. Default: :file:`config.yaml`.

.. option:: IMAGE-NAME

   Name of the application Docker image.

.. option:: APP.MANIFEST

   Manifest file (Gramine configuration).

.. program:: gsc-sign-image

:command:`gsc sign-image` -- signs a graminized image
------------------------------------------------------

Signs the enclave of an unsigned graminized Docker image and creates a new
Docker image called ``gsc-<IMAGE-NAME>``. :command:`gsc sign-image` always
removes intermediate Docker images, if successful or not, to ensure the removal
of the signing key in them.

:command:`gsc sign-image` [*OPTIONS*] <*IMAGE-NAME*> <*KEY-FILE*>

.. option:: -c

   Specify configuration file. Default: :file:`config.yaml`

.. option:: -p

   Provide passphrase for the enclave signing key (if applicable)

.. option:: --remove-gramine-deps

   Remove Gramine dependencies that are not needed at runtime. This may have
   a negative side effect of removing even those dependencies that are actually
   needed by the original application. Use with care!

.. option:: IMAGE-NAME

   Name of the application Docker image

.. option:: KEY-FILE

   Used to sign the Intel SGX enclave

.. program:: gsc-build-gramine

:command:`gsc build-gramine` -- build Gramine-only Docker image
-----------------------------------------------------------------

Builds a base Docker image including the Gramine sources and compiled runtime.
This base image can be used as input for :command:`gsc build` via configuration
parameter `Gramine.Image`.

:command:`gsc build-gramine` [*OPTIONS*] <*IMAGE-NAME*>

.. option:: -b <buildtype>, --buildtype <buildtype>

   Use <buildtype> value ``release``, ``debug`` or ``debugoptimized`` to
   compile Gramine in the corresponding mode. Default: ``release``.

..
  TODO: Drop `-d` option with GSC v1.6 release

.. option:: -d, --debug

   Compile Gramine with debug flags and debug output.

   .. deprecated:: 1.5
      Use :option:`--buildtype`.

.. option:: -L

   Compile Gramine with Linux PAL in addition to Linux-SGX PAL. Allows
   :command:`gsc build` commands to include the Linux PAL using :option:`-L
   <gsc-build -L>`.

.. option:: --no-cache

   Disable Docker's caches during :command:`gsc build-gramine`. This builds the
   unsigned graminized image from scratch.

.. option:: --rm

   Remove intermediate Docker images created by :command:`gsc build-gramine`,
   if the image build is successful.

.. option:: --build-arg

   Set build-time variables during :command:`gsc build-gramine` (same as
   `docker build --build-arg`).

.. option:: -c

   Specify configuration file. Default: :file:`config.yaml`

.. option:: -f

   Stop after Dockerfile is created and do not build the Docker image.

.. option:: IMAGE-NAME

   Name of the resulting Gramine Docker image

.. program:: gsc-info-image

:command:`gsc info-image` -- retrieve information about graminized Docker image
--------------------------------------------------------------------------------

Retrieves Intel SGX relevant information about the graminized Docker image such
as the ``MRENCLAVE`` and ``MRSIGNER`` measurements for each application in the
Docker image.

Synopsis:

:command:`gsc info-image` <*IMAGE-NAME*>

.. option:: IMAGE-NAME

   Name of the graminized Docker image

Using Gramine's trusted command line arguments
----------------------------------------------

Most executables aren't designed to run with attacker-controlled arguments.
Allowing an attacker to control executable arguments can break the security of
the resulting enclave.

:command:`gsc build` uses the existing Docker image's entrypoint and cmd fields
to identify the trusted arguments. These arguments are stored in
:file:`trusted_argv`. This file is only generated when :option:`--insecure-args
<gsc-build --insecure-args>` is *not* specified. As a result any arguments
specified during :command:`docker run` are ignored.

To be able to provide arguments at runtime, the image build has to enable this
via the option :option:`--insecure-args <gsc-build --insecure-args>`.

Stages of building graminized SGX Docker images
------------------------------------------------

The build process of a graminized Docker image from image ``<image-name>``
follows three main stages and produces an image named ``gsc-<image-name>``.
:command:`gsc build-gramine` performs only the first stage,
:command:`gsc build` performs the first two stages, and finally
:command:`gsc sign-image` performs the last stage.

#. **Building Gramine.** The first stage builds Gramine from sources based on
   the provided configuration (see :file:`config.yaml`) which includes the
   distribution (e.g., Ubuntu 18.04), Gramine repository, and the Intel SGX
   driver details. This stage can be skipped if :command:`gsc build` uses a
   pre-built Gramine Docker image.

#. **Graminizing the application image.** The second stage copies the important
   Gramine artifacts (e.g., the runtime and signer tool) from the first stage
   (or if the first stage was skipped, it pulls a prebuilt Docker image defined
   via the configuration file).  It then prepares image-specific variables such
   as the executable path and the library path, and scans the entire image to
   generate a list of trusted files.  GSC excludes files and paths starting with
   :file:`/boot`, :file:`/dev`, :file:`.dockerenv`, :file:`.dockerinit`,
   :file:`/etc/mtab`, :file:`/etc/rc`, :file:`/proc`, :file:`/sys`, and
   :file:`/var`, since checksums are required which either don't exist or may
   vary across different deployment machines. GSC combines these variables and
   list of trusted files into a new manifest file. In a last step the entrypoint
   is changed to launch the :file:`apploader.sh` script which generates an Intel
   SGX token (only if needed, on non-FLC platforms) and starts the
   :program:`gramine-sgx` loader. Note that the generated image
   (``gsc-<image-name>-unsigned``) cannot successfully load an Intel SGX
   enclave, since essential files and the signature of the enclave are still
   missing (see next stage).

#. **Signing the Intel SGX enclave.** The third stage uses Gramine's signer
   tool to generate SIGSTRUCT files for SGX enclave initialization. This tool
   also generates an SGX-specific manifest file.  The required signing key is
   provided by the user via the :command:`gsc sign-image` command and copied
   into this Docker build stage. The generated image is called
   ``gsc-<image-name>`` and includes all necessary files to start an Intel SGX
   enclave.

In the future we plan to provide prebuilt Gramine images for popular
cloud-provider offerings.

Generating a signed graminized Docker image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The last stage combines the graminized Docker image with the signed enclave and
manifest files. Therefore it copies the SIGSTRUCT files and the SGX-specific
manifest file from the previous stage into the graminized Docker image from the
second stage.

Configuration
=============

GSC is configured via a configuration file called :file:`config.yaml` or
specified as a :program:`gsc` option. A template configuration file is provided
in :file:`config.yaml.template`.

.. describe:: Distro

   Defines Linux distribution to be used to build Gramine in. This distro should
   match the distro underlying the application's Docker image; otherwise the
   results may be unpredictable. Currently supported distros are Ubuntu 18.04,
   Ubuntu 20.04, Ubuntu 21.04, Debian 10, Debian 11 and CentOS 8. Default value
   is ``ubuntu:18.04``.

.. describe:: Registry

   Defines the registry and repository where the Linux distribution
   image is located. Only needed if the image in `Distro` requires to
   be prepended with this information.

.. describe:: Gramine.Repository

   Source repository of Gramine. Default value:
   `https://github.com/gramineproject/gramine.git
   <https://github.com/gramineproject/gramine.git>`__.

.. describe:: Gramine.Branch

   Use this release/branch of the repository. Default value: ``v1.4``.

.. describe:: Gramine.Image

   Builds graminized Docker image based on a prebuilt Gramine Docker image.
   These images are prepared via :command:`gsc build-gramine` and will be
   provided for popular cloud-provider environments. `Gramine.Repository` and
   `Gramine.Branch` are ignored in case `Gramine.Image` is specified.

.. describe:: SGXDriver.Repository

   Source repository of the Intel SGX driver. Default value: ""
   (in-kernel driver).

.. describe:: SGXDriver.Branch

   Use this branch of the repository. Default value: ""
   (in-kernel driver).

Run graminized Docker images
=============================

Execute :command:`docker run` command via Docker CLI and provide gsgx and
isgx/sgx devices and the PSW/AESM socket. Additional Docker options and
executable arguments may be supplied to the :command:`docker run` command.

.. warning::
   Forwarding devices to a container lowers security of the host. GSC should
   never be used as a sandbox for applications (i.e. it only shields the app
   from the host but not vice versa).

.. program:: docker

:command:`docker run` [*OPTIONS*] gsc-<*IMAGE-NAME*> [<*ARGUMENTS*>]

.. option:: OPTIONS

   :command:`docker run` options. Common options include ``-it`` (interactive
   with terminal), ``-d`` (detached), ``--device`` (forward device). Please see
   `Docker manual <https://docs.docker.com/engine/reference/commandline/run/>`__
   for details.

.. option:: IMAGE-NAME

   Name of original image (without GSC build).

.. option:: ARGUMENTS

   Arguments to be supplied to the executable launching inside the Docker
   container and Gramine. Such arguments may only be provided when
   :option:`--insecure-args <gsc-build --insecure-args>` was specified during
   :command:`gsc build`.


Execute with Linux PAL instead of Linux-SGX PAL
-----------------------------------------------

When specifying :option:`-L <gsc-build -L>`  during GSC :command:`gsc build`,
you may select the Linux PAL at Docker run time instead of the Linux-SGX PAL by
specifying the environment variable :envvar:`GSC_PAL` as an option to the
:command:`docker run` command. When using the Linux PAL, it is not necessary to
sign the image via a :command:`gsc sign-image` command.

.. envvar:: GSC_PAL

   This environment variable specifies the pal loader.

GSC requires a custom seccomp profile while running with Linux PAL, which has to be
specified at Docker run time. There are two options:

#. Pass `unconfined` to run the container without the default seccomp profile.
   This option is generally considered insecure, since this results in containers
   running with unrestricted system calls (all system calls are allowed which
   increases the attack surface of the Linux Kernel).

#. Pass the custom seccomp profile
   https://github.com/gramineproject/gramine/blob/master/scripts/docker_seccomp.json.

   With this option, Docker containers restrict themselves to a rather narrow set
   of allowed system calls, keeping the attack surface of the Linux kernel small.
   All the necessary capabilities required for GSC to function are still enabled.

.. code-block:: sh

   docker run ... --env GSC_PAL=Linux --security-opt seccomp=<profile> gsc-<image-name> ...

Example
=======

.. warning::
   Example below relies on insecure arguments to be able to run Python with
   arbitrary arguments. This is not intended for production environments.

The example below shows how to graminize the public Docker image of Python3.
This example assumes that all prerequisites are installed and configured.

#. Create a configuration file:

   .. code-block:: sh

      cp config.yaml.template config.yaml
      # Manually adopt config.yaml to the installed Intel SGX driver and desired
      # Gramine repository/version.

#. Generate the signing key (if you don't already have a key):

   .. code-block:: sh

      openssl genrsa -3 -out enclave-key.pem 3072

#. Pull public Python image from Dockerhub:

   .. code-block:: sh

      docker pull python

#. Graminize the Python image using :command:`gsc build`:

   .. code-block:: sh

      ./gsc build --insecure-args python test/generic.manifest

#. Sign the graminized Docker image using :command:`gsc sign-image`:

   .. code-block:: sh

      ./gsc sign-image python enclave-key.pem

#. Retrieve SGX-related information from graminized image using :command:`gsc info-image`:

   .. code-block:: sh

      ./gsc info-image gsc-python

#. Test the graminized Docker image (change ``--device=/dev/sgx_enclave`` to
   your version of the Intel SGX driver if needed):

   .. code-block:: sh

      docker run --device=/dev/sgx_enclave \
         -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket \
         gsc-python -c 'print("HelloWorld!")'

#. You can also start a Bash interactive session in the graminized Docker
   image (useful for debugging):

   .. code-block:: sh

      docker run --device=/dev/sgx_enclave \
         -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket \
         -it --entrypoint /bin/bash gsc-python

Limitations
===========

This document focuses on the most important limitations of GSC. `Issue #13
<https://github.com/gramineproject/gsc/issues/13>`__ provides the complete list
of known limitations and serves as a discussion board for workarounds.

Operating System dependency
---------------------------

GSC relies on Gramine to execute Linux applications inside Intel SGX enclaves and
the installation of prerequisites depends on package manager and package
repositories. Docker images based on Ubuntu and CentOS are supported by GSC.
GSC can simply be extended to support other distributions by
providing a set of templates for this distribution in :file:`templates/`.

Trusted data in Docker volumes
------------------------------

Data mounted as Docker volumes at runtime is not included in the general search
for trusted files during the image build. As a result, Gramine denies access to
these files, since they are neither allowed nor trusted files. This will likely
break applications using files stored in Docker volumes.

Workaround
^^^^^^^^^^

Trusted files can be added to image-specific manifest file (first argument to
:command:`gsc build` command) at build time. This workaround does not allow
these files to change between build and run, or over multiple runs. This only
provides integrity for files and not confidentiality.

Allowing dynamic file contents via Gramine protected files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Docker volumes can include Gramine protected files. As a result Gramine can
open these protected files without knowing the exact contents as long as the
protected file was configured in the manifest. The complete and secure use of
protected files may require additional steps.

Integration of Docker Secrets
-----------------------------

Docker Secrets are automatically pulled by Docker and the results are stored
either in environment variables or mounted as files. GSC is currently unaware of
such files and hence, cannot mark them trusted. Similar to trusted data, these
files may be added to the manifest.

Access to files in excluded paths
---------------------------------

The manifest generation excludes all files and paths starting with :file:`/boot`
, :file:`/dev`, :file:`.dockerenv`, :file:`.dockerinit`, :file:`/etc/mtab`,
:file:`/etc/rc`, :file:`/proc`, :file:`/sys`, and :file:`/var` from the list of
trusted files. If your application relies on some files in these directories,
you must manually add them to the manifest::

   sgx.trusted_files = [ "file:file1", "file:file2" ]
   or
   sgx.allowed_files = [ "file:file3", "file:file4" ]

Issues with hostname and DNS
----------------------------

If your application queries the hostname or DNS information, you must manually
add the following option to the manifest::

    sys.enable_extra_runtime_domain_names_conf = true

For more information on this option, refer to
https://gramine.readthedocs.io/en/stable/manifest-syntax.html#domain-names-configuration.
