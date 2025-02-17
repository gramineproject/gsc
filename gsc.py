#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (C) 2020-2021 Intel Corp.
#                         Anjo Vahldiek-Oberwagner <anjo.lucas.vahldiek-oberwagner@intel.com>
#                         Dmitrii Kuvaiskii <dmitrii.kuvaiskii@intel.com>

import argparse
import hashlib
import os
import pathlib
import re
import shutil
import struct
import sys
import tempfile
import uuid

import docker  # pylint: disable=import-error
import jinja2
import shlex
import tomli   # pylint: disable=import-error
import tomli_w # pylint: disable=import-error
import yaml    # pylint: disable=import-error

class DistroRetrievalError(Exception):
    def __init__(self, *args):
        super().__init__(('Could not automatically detect the OS distro of the supplied Docker '
                         'image. Please specify OS distro manually in the configuration file.'),
                         *args)

def test_trueish(value):
    if not value:
        return False
    value = value.casefold()
    if value in ('false', 'off', 'no'):
        return False
    if value in ('true', 'on', 'yes'):
        return True
    if value.isdigit():
        return bool(int(value))
    raise ValueError(f'Invalid value for trueish: {value!r}')

def gsc_image_name(original_image_name):
    return f'gsc-{original_image_name}'

def gsc_unsigned_image_name(original_image_name):
    return f'gsc-{original_image_name}-unsigned'

def gsc_tmp_build_path(original_image_name):
    return pathlib.Path('build') / f'gsc-{original_image_name}'


def get_docker_image(docker_socket, image_name):
    try:
        docker_image = docker_socket.images.get(image_name)
        return docker_image
    except (docker.errors.ImageNotFound, docker.errors.APIError):
        return None


def build_docker_image(docker_api, build_path, image_name, dockerfile, **kwargs):
    build_path = str(build_path) # Docker API doesn't understand PathLib's PosixPath type
    stream = docker_api.build(path=build_path, tag=image_name, dockerfile=dockerfile,
                              decode=True, **kwargs)
    for chunk in stream:
        if 'stream' in chunk:
            for line in chunk['stream'].splitlines():
                print(line)


def extract_binary_info_from_image_config(config, env):
    entrypoint = config['Entrypoint'] or []
    num_starting_entrypoint_items = len(entrypoint)
    cmd = config['Cmd'] or []
    working_dir = config['WorkingDir'] or ''

    # Canonize working dir
    if working_dir == '':
        working_dir = '/'
    elif working_dir[-1] != '/':
        working_dir = working_dir + '/'

    # Some Docker images only use the optional CMD and have an empty entrypoint;
    # GSC has to make it explicit to prepare scripts and Intel SGX signatures
    entrypoint.extend(cmd)
    if not entrypoint:
        print('Could not find the entrypoint binary to the application image.')
        sys.exit(1)

    # Set binary to first executable in entrypoint and expand to full absolute path (if binary is
    # represented as relative path, e.g. `./my_app` or `some_dir/my_app`)
    binary = entrypoint[0]
    if not binary.startswith('/') and '/' in binary:
        binary = working_dir + binary

    # Check if we have fixed binary arguments as part of entrypoint
    if num_starting_entrypoint_items > 1:
        last_bin_arg = num_starting_entrypoint_items
        binary_arguments = entrypoint[1:last_bin_arg]
    else:
        last_bin_arg = 0
        binary_arguments = ''

    # Place the remaining optional arguments previously specified as command in the new command.
    # Necessary since the first element of the command may be the binary of the resulting image.
    cmd = entrypoint[last_bin_arg + 1:] if len(entrypoint) > last_bin_arg + 1 else ''

    env.globals.update({
        'binary': binary,
        'binary_arguments': binary_arguments,
        'binary_basename': os.path.basename(binary),
        'cmd': cmd,
        'working_dir': working_dir
    })


def extract_environment_from_image_config(config):
    env_list = config['Env'] or []
    base_image_environment = ''
    for env_var in env_list:
        # TODO: switch to loader.env_src_file = "file:file_with_serialized_envs" if
        # the need for multi-line envvars arises
        if '\n' in env_var:
            # we use TOML's basic single-line strings, can't have newlines
            print(f'Skipping environment variable `{env_var.split("=", maxsplit=1)[0]}`: '
                    'its value contains newlines.')
            continue
        escaped_env_var = env_var.translate(str.maketrans({'\\': r'\\', '"': r'\"'}))
        env_var_name = escaped_env_var.split('=', maxsplit=1)[0]
        env_var_value = escaped_env_var.split('=', maxsplit=1)[1]
        base_image_environment += f'loader.env.{env_var_name} = "{env_var_value}"\n'
    return base_image_environment

def extract_build_args(args):
    buildargs_dict = {}
    for item in args.build_arg:
        if '=' in item:
            key, value = item.split('=', maxsplit=1)
            buildargs_dict[key] = value
        else:
            # user specified --build-arg with key and without value, let's retrieve value from env
            if item in os.environ:
                buildargs_dict[item] = os.environ[item]
            else:
                print(f'Could not set build arg `{item}` from environment.')
                sys.exit(1)
    return buildargs_dict

def extract_define_args(args):
    defineargs_dict = {}
    for item in args.define:
        if '=' in item:
            key, value = item.split('=', maxsplit=1)
            defineargs_dict[key] = value
        else:
            print(f'Invalid value for argument `{item}`, expected `--define {item}=<value>`')
            sys.exit(1)
    return defineargs_dict

def extract_user_from_image_config(config, env):
    user = config['User']
    if not user:
        user = 'root'
    env.globals.update({'app_user': user})

def merge_manifests_in_order(manifest1, manifest2, manifest1_name, manifest2_name, path=[]):
    for key in manifest2:
        if key in manifest1:
            if isinstance(manifest1[key], dict) and isinstance(manifest2[key], dict):
                merge_manifests_in_order(manifest1[key], manifest2[key], manifest1_name,
                                         manifest2_name, path + [str(key)])
            elif isinstance(manifest1[key], list) and isinstance(manifest2[key], list):
                manifest1[key].extend(manifest2[key])
            elif manifest1[key] == manifest2[key]:
                pass
            else:
                # key exists in both manifests but with different values:
                # - for a special case of three below envvars must concatenate the values,
                # - in all other cases choose the value from the first manifest
                if ('.'.join(path) == 'loader.env' and
                        key in ['LD_LIBRARY_PATH', 'PATH', 'LD_PRELOAD']):
                    manifest1[key] = f'{manifest1[key]}:{manifest2[key]}'
                    print(f'Warning: Duplicate key `{".".join(path + [str(key)])}`. Concatenating'
                          f' values from `{manifest1_name}` and `{manifest2_name}`.')
                else:
                    print(f'Warning: Duplicate key `{".".join(path + [str(key)])}`. Overriding'
                          f' value from `{manifest2_name}` by the one in `{manifest1_name}`.')
        else:
            manifest1[key] = manifest2[key]
    return manifest1

def handle_redhat_repo_configs(distro, tmp_build_path):
    if not distro.startswith('redhat/'):
        return

    version_id_match = re.search(r'^redhat/ubi(\d+)(-minimal)?$', distro)
    if version_id_match:
        version_id = version_id_match.group(1)
        repo_name = f'rhel-{version_id}-for-x86_64-baseos-rpms'
    else:
        raise ValueError(f'Invalid Red Hat distro format: {distro}')

    with open('/etc/yum.repos.d/redhat.repo') as redhat_repo:
        redhat_repo_contents = redhat_repo.read()

        if not re.search(repo_name, redhat_repo_contents):
            print(f'Cannot find {repo_name} in /etc/yum.repos.d/redhat.repo. '
                  f'Register and subscribe your RHEL system to the Red Hat Customer '
                  f'Portal using Red Hat Subscription-Manager.')
            sys.exit(1)

        shutil.copyfile('/etc/yum.repos.d/redhat.repo', tmp_build_path / 'redhat.repo')
        pattern_sslclientkey = re.compile(r'(?<!#)sslclientkey\s*=\s*(.*)')
        pattern_sslcacert = re.compile(r'(?<!#)sslcacert\s*=\s*(.*)')

        match_sslclientkey = pattern_sslclientkey.search(redhat_repo_contents)
        if match_sslclientkey:
            sslclientkey_path = match_sslclientkey.group(1)
            sslclientkey_dir = os.path.dirname(sslclientkey_path)
        else:
            print(f'Cannot find SSL client key path in /etc/yum.repos.d/redhat.repo. '
                  f'Register and subscribe your RHEL system to the Red Hat Customer '
                  f'Portal using Red Hat Subscription-Manager.')
            sys.exit(1)

        match_sslcacert = pattern_sslcacert.search(redhat_repo_contents)
        if match_sslcacert:
            sslcacert_path = match_sslcacert.group(1)
        else:
            print(f'Cannot find SSL CA certificate path in /etc/yum.repos.d/redhat.repo. '
                  f'Register and subscribe your RHEL system to the Red Hat Customer '
                  f'Portal using Red Hat Subscription-Manager.')
            sys.exit(1)

        # The `redhat-uep.pem` file is used to validate the authenticity of Red Hat Update Engine
        # Proxy (UEP) server during updates and subscription management on the system.
        shutil.copyfile(sslcacert_path, tmp_build_path / 'redhat-uep.pem')

        if os.path.exists(tmp_build_path / 'pki'):
            shutil.rmtree(tmp_build_path / 'pki')

        # This directory stores the entitlement certificates for Red Hat subscriptions.
        # These files are used to authenticate and verify that a system is entitled to receive
        # software updates and support from Red Hat.
        shutil.copytree(sslclientkey_dir, tmp_build_path / 'pki/entitlement')

def handle_suse_repo_configs(distro, tmp_build_path):
    if not distro.startswith('registry.suse.com/suse/sle'):
        return

    if not os.path.exists('/etc/zypp/credentials.d/SCCcredentials'):
        print('Cannot find your SUSE Customer Center credentials file at '
                '/etc/zypp/credentials.d/SCCcredentials. Please register and subscribe your SUSE '
                'system to the SUSE Customer Center.')
        sys.exit(1)

    # This file contains the credentials for the SUSE Customer Center (SCC) account for the
    # system to authenticate and receive software updates and support from SUSE. Copy it to
    # the temporary build directory to include it in the graminized Docker image.
    shutil.copyfile('/etc/zypp/credentials.d/SCCcredentials', tmp_build_path / 'SCCcredentials')

def template_path(distro):
    if distro == 'quay.io/centos/centos':
        return 'centos/stream'

    if distro.startswith('redhat/ubi'):
        if 'minimal' in distro:
            return 'redhat/ubi-minimal'
        return 'redhat/ubi'

    if distro.startswith('registry.suse.com/suse/sle'):
        return 'suse'

    return distro

def assert_not_none(value, error_message):
    if value is None:
        raise jinja2.TemplateError(error_message)
    return value

def get_ubi_version(distro):
    match_ = re.match(r'^redhat/ubi(\d+)(-minimal)?:(\d+).(\d+)$', distro)
    return match_.group(1) if match_ else None

def get_sles_version(distro):
    match_ = re.match(r'^registry.suse.com/suse/sle(\d+):(\d+\.\d+)$', distro)
    return match_.group(2) if match_ else None

def get_image_distro(docker_socket, image_name):
    out = docker_socket.containers.run(image_name, entrypoint='cat /etc/os-release', remove=True)
    out = out.decode('UTF-8')

    os_release = dict(shlex.split(line)[0].split('=') for line in out.splitlines() if line.strip())

    if 'ID' not in os_release or 'VERSION_ID' not in os_release:
        raise DistroRetrievalError

    version_str = os_release['VERSION_ID']
    version = version_str.split('.')
    if os_release['ID'] == 'rhel':
        # RedHat specific logic to distinguish between UBI and UBI-minimal
        try:
            docker_socket.containers.run(image_name, entrypoint='ls /usr/bin/microdnf', remove=True)
        except docker.errors.ContainerError:
            distro = f'redhat/ubi{version[0]}:{version_str}'
        else:
            distro = f'redhat/ubi{version[0]}-minimal:{version_str}'
    elif os_release['ID'] == 'sles':
        distro = f'registry.suse.com/suse/sle{version[0]}:{version_str}'
    else:
        # Some OS distros (e.g. Alpine) have very precise versions (e.g. 3.17.3),
        # and to support these OS distros, we need to truncate at the 2nd dot.
        distro = os_release['ID'] + ':' + '.'.join(version[:2])

    if os_release['NAME'] == 'CentOS Stream':
        distro = f'quay.io/centos/centos:stream{version[0]}'

    return distro

def fetch_and_validate_distro_support(docker_socket, image_name, env):
    distro = env.globals['Distro']
    if distro == 'auto':
        distro = get_image_distro(docker_socket, image_name)
        env.globals['Distro'] = distro

    distro = distro.split(':')[0]

    if not os.path.exists(f'templates/{template_path(distro)}'):
        raise FileNotFoundError(f'`{distro}` distro is not supported by GSC.')

    return distro

# Command 1: Build unsigned graminized Docker image from original app Docker image.
def gsc_build(args):
    original_image_name = args.image                           # input original-app image name
    unsigned_image_name = gsc_unsigned_image_name(args.image)  # output unsigned image name
    signed_image_name = gsc_image_name(args.image)             # final signed image name (to check)
    tmp_build_path = gsc_tmp_build_path(args.image)            # pathlib obj with build artifacts

    docker_socket = docker.from_env()

    if get_docker_image(docker_socket, signed_image_name) is not None:
        print(f'Final graminized image `{signed_image_name}` already exists.')
        sys.exit(0)

    original_image = get_docker_image(docker_socket, original_image_name)
    if original_image is None:
        print(f'Cannot find original application Docker image `{original_image_name}`.')
        sys.exit(1)

    config = yaml.safe_load(args.config_file)
    if 'Image' in config['Gramine']:
        gramine_image_name = config['Gramine']['Image']
        if get_docker_image(docker_socket, gramine_image_name) is None:
            # TODO: Drop support for old style base-Gramine Docker image name with GSC v1.8 release
            if get_docker_image(docker_socket, gsc_image_name(gramine_image_name)) is None:
                print(f'Cannot find base-Gramine Docker image `{gramine_image_name}`.')
                sys.exit(1)

            config['Gramine']['Image'] = gsc_image_name(gramine_image_name)
            print(f'Warning: The base-Gramine Docker image `{gramine_image_name}` was generated by'
                  ' an older version of GSC. Please re-build this image using this GSC version.'
                  ' This warning will become an error in the future.')

    print(f'Building unsigned graminized Docker image `{unsigned_image_name}` from original '
          f'application image `{original_image_name}`...')

    # initialize Jinja env with configurations extracted from the original Docker image
    env = jinja2.Environment()
    env.filters['shlex_quote'] = shlex.quote
    env.filters['assert_not_none'] = assert_not_none
    env.globals['get_ubi_version'] = get_ubi_version
    env.globals['get_sles_version'] = get_sles_version
    env.globals['template_path'] = template_path
    env.globals.update(config)
    env.globals.update(vars(args))
    env.globals.update({'app_image': original_image_name})
    extract_user_from_image_config(original_image.attrs['Config'], env)
    extract_binary_info_from_image_config(original_image.attrs['Config'], env)

    os.makedirs(tmp_build_path, exist_ok=True)

    try:
        distro = fetch_and_validate_distro_support(docker_socket, original_image_name, env)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    env.loader = jinja2.FileSystemLoader('templates/')
    compile_template = env.get_template(f'{template_path(distro)}/Dockerfile.compile.template')
    env.globals.update({'compile_template': compile_template})

    # generate Dockerfile.build from Jinja-style templates/<distro>/Dockerfile.build.template
    # using the user-provided config file with info on OS distro, Gramine version and SGX driver
    # and other env configurations generated above
    build_template = env.get_template(f'{template_path(distro)}/Dockerfile.build.template')

    with open(tmp_build_path / 'Dockerfile.build', 'w') as dockerfile:
        dockerfile.write(build_template.render())

    # generate apploader.sh from Jinja-style templates/apploader.template
    apploader_template = env.get_template(f'{template_path(distro)}/apploader.template')
    with open(tmp_build_path / 'apploader.sh', 'w') as apploader:
        apploader.write(apploader_template.render())

    # generate entrypoint.manifest from three parts:
    #   - Jinja-style templates/entrypoint.manifest.template
    #   - base Docker image's environment variables
    #   - additional, user-provided manifest options

    entrypoint_manifest_name = f'{template_path(distro)}/entrypoint.manifest.template'
    entrypoint_manifest_render = env.get_template(entrypoint_manifest_name).render()
    try:
        entrypoint_manifest_dict = tomli.loads(entrypoint_manifest_render)
    except Exception as e:
        print(f'Failed to parse the "{distro}/entrypoint.manifest.template" file. Error:', e,
              file=sys.stderr)
        sys.exit(1)

    base_image_environment = extract_environment_from_image_config(original_image.attrs['Config'])
    base_image_env_dict = tomli.loads(base_image_environment)
    base_image_env_name = f'<{original_image_name} image env>'

    user_manifest_name = args.manifest
    user_manifest_contents = ''
    if not os.path.exists(user_manifest_name):
        print(f'Manifest file "{user_manifest_name}" does not exist.', file=sys.stderr)
        sys.exit(1)

    with open(user_manifest_name, 'r') as user_manifest_file:
        user_manifest_contents = user_manifest_file.read()

        try:
            user_manifest_dict = tomli.loads(user_manifest_contents)
        except Exception as e:
            print(f'Failed to parse the "{user_manifest_name}" file. Error:', e, file=sys.stderr)
            sys.exit(1)

    merged_manifest_dict = merge_manifests_in_order(user_manifest_dict, entrypoint_manifest_dict,
                                                    user_manifest_name, entrypoint_manifest_name)
    merged_manifest_name = (f'<merged {user_manifest_name} and {entrypoint_manifest_name}>')
    merged_manifest_dict = merge_manifests_in_order(merged_manifest_dict, base_image_env_dict,
                                                    merged_manifest_name, base_image_env_name)

    with open(tmp_build_path / 'entrypoint.manifest', 'wb') as entrypoint_manifest:
        tomli_w.dump(merged_manifest_dict, entrypoint_manifest)

    # copy helper script to finalize the manifest from within graminized Docker image
    shutil.copyfile('finalize_manifest.py', tmp_build_path / 'finalize_manifest.py')

    # Intel's SGX PGP RSA-2048 key signing the intel-sgx/sgx_repo repository. Expires 2027-03-20.
    # Available at https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key
    shutil.copyfile('keys/intel-sgx-deb.key', tmp_build_path / 'intel-sgx-deb.key')

    handle_redhat_repo_configs(distro, tmp_build_path)
    handle_suse_repo_configs(distro, tmp_build_path)

    build_docker_image(docker_socket.api, tmp_build_path, unsigned_image_name, 'Dockerfile.build',
                       rm=args.rm, nocache=args.no_cache, buildargs=extract_build_args(args))

    # Check if docker build failed
    if get_docker_image(docker_socket, unsigned_image_name) is None:
        print(f'Failed to build unsigned graminized Docker image `{unsigned_image_name}`.')
        sys.exit(1)

    print(f'Successfully built an unsigned graminized Docker image `{unsigned_image_name}` from '
          f'original application image `{original_image_name}`.')


# Command 2: Build a "base Gramine" Docker image with the compiled runtime of Gramine.
def gsc_build_gramine(args):
    gramine_image_name = args.image  # output base-Gramine image name
    tmp_build_path = gsc_tmp_build_path(args.image)  # pathlib obj with build artifacts

    docker_socket = docker.from_env()

    config = yaml.safe_load(args.config_file)
    if 'Image' in config['Gramine']:
        print('`gsc build-gramine` does not allow `Gramine.Image` to be set.')
        sys.exit(1)

    if get_docker_image(docker_socket, gramine_image_name) is not None:
        print(f'Base-Gramine Docker image `{gramine_image_name}` already exists.')
        sys.exit(0)

    print(f'Building base-Gramine Docker image `{gramine_image_name}`...')

    # initialize Jinja env with user-provided configurations
    env = jinja2.Environment()
    env.filters['assert_not_none'] = assert_not_none
    env.globals['get_ubi_version'] = get_ubi_version
    env.globals['get_sles_version'] = get_sles_version
    env.globals['template_path'] = template_path
    env.globals.update(config)
    env.globals.update(vars(args))

    os.makedirs(tmp_build_path, exist_ok=True)

    distro = env.globals['Distro']
    if distro == 'auto':
        print('`gsc build-gramine` does not allow `Distro` set to `auto` in the configuration '
              'file.')
        sys.exit(1)

    distro, _ = distro.split(':')
    if not os.path.exists(f'templates/{template_path(distro)}'):
        print(f'{distro} distro is not supported by GSC.')
        sys.exit(1)

    env.loader = jinja2.FileSystemLoader('templates/')

    # generate Dockerfile.compile from Jinja-style templates/<distro>/Dockerfile.compile.template
    # using the user-provided config file with info on OS distro, Gramine version and SGX driver
    # and other user-provided args (see argparser::gsc_build_gramine below)
    compile_template = env.get_template(f'{template_path(distro)}/Dockerfile.compile.template')
    with open(tmp_build_path / 'Dockerfile.compile', 'w') as dockerfile:
        dockerfile.write(compile_template.render())

    if args.file_only:
        print(f'Successfully created Dockerfile.compile for base-Gramine Docker image '
              f'`{gramine_image_name}` under `{tmp_build_path}`.')
        sys.exit(0)

    # Intel's SGX PGP RSA-1024 key signing the intel-sgx/sgx_repo repository. Expires 2023-05-24.
    # Available at https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key
    shutil.copyfile('keys/intel-sgx-deb.key', tmp_build_path / 'intel-sgx-deb.key')

    handle_redhat_repo_configs(distro, tmp_build_path)
    handle_suse_repo_configs(distro, tmp_build_path)

    build_docker_image(docker_socket.api, tmp_build_path, gramine_image_name, 'Dockerfile.compile',
                       rm=args.rm, nocache=args.no_cache, buildargs=extract_build_args(args))

    # Check if docker build failed
    if get_docker_image(docker_socket, gramine_image_name) is None:
        print(f'Failed to build a base-Gramine Docker image `{gramine_image_name}`.')
        sys.exit(1)

    print(f'Successfully built a base-Gramine Docker image `{gramine_image_name}`.')


# Command 3: Sign Docker image which was previously built via `gsc build`.
def gsc_sign_image(args):
    unsigned_image_name = gsc_unsigned_image_name(args.image)  # input image name
    signed_image_name = gsc_image_name(args.image)             # output image name
    tmp_build_path = gsc_tmp_build_path(args.image)            # pathlib obj with build artifacts

    docker_socket = docker.from_env()

    unsigned_image = get_docker_image(docker_socket, unsigned_image_name)
    if unsigned_image is None:
        print(f'Cannot find unsigned graminized Docker image `{unsigned_image_name}`.\n'
              f'You must first build this image via `gsc build` command.')
        sys.exit(1)

    print(f'Signing graminized Docker image `{unsigned_image_name}` -> `{signed_image_name}`...')

    # generate Dockerfile.sign from Jinja-style templates/<distro>/Dockerfile.sign.template
    # using the user-provided config file with info on OS distro, Gramine version and SGX driver
    env = jinja2.Environment()
    env.globals.update(yaml.safe_load(args.config_file))
    extract_user_from_image_config(unsigned_image.attrs['Config'], env)
    env.globals['args'] = extract_define_args(args)
    env.tests['trueish'] = test_trueish

    try:
        distro = fetch_and_validate_distro_support(docker_socket, args.image, env)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    env.loader = jinja2.FileSystemLoader('templates/')

    sign_template = env.get_template(f'{template_path(distro)}/Dockerfile.sign.template')
    os.makedirs(tmp_build_path, exist_ok=True)
    with open(tmp_build_path / 'Dockerfile.sign', 'w') as dockerfile:
        dockerfile.write(sign_template.render(image=unsigned_image_name))

    # copy user-provided signing key to our tmp build dir (to copy it later inside Docker image)
    tmp_build_key_path = tmp_build_path / 'gsc-signer-key.pem'
    shutil.copyfile(os.path.abspath(args.key), tmp_build_key_path)

    build_id = uuid.uuid4().hex
    try:
        # `forcerm` parameter forces removal of intermediate Docker images even after unsuccessful
        # builds, to not leave the signing key lingering in any Docker containers
        build_docker_image(docker_socket.api, tmp_build_path, signed_image_name, 'Dockerfile.sign',
                           forcerm=True, buildargs={'passphrase': args.passphrase,
                           'BUILD_ID': build_id})
    finally:
        os.remove(tmp_build_key_path)
        # Remove a temporary image created during multistage docker build to save disk space.
        # Please note that removing the image doesn't assure security.
        docker_socket.api.prune_images(filters={'label': 'build_id=' + build_id})

    if get_docker_image(docker_socket, signed_image_name) is None:
        print(f'Failed to build a signed graminized Docker image `{signed_image_name}`.')
        sys.exit(1)

    print(f'Successfully built a signed Docker image `{signed_image_name}` from '
          f'`{unsigned_image_name}`.')


# Simplified version of `Sigstruct.from_bytes()` from python/graminelibos/sigstruct.py
def read_sigstruct(sig):
    # Offsets for fields in SIGSTRUCT (defined by the SGX HW architecture, they never change)
    SGX_ARCH_ENCLAVE_CSS_DATE = 20
    SGX_ARCH_ENCLAVE_CSS_MODULUS = 128
    SGX_ARCH_ENCLAVE_CSS_ENCLAVE_HASH = 960
    SGX_ARCH_ENCLAVE_CSS_ISV_PROD_ID = 1024
    SGX_ARCH_ENCLAVE_CSS_ISV_SVN = 1026
    SGX_ARCH_ENCLAVE_CSS_ATTRIBUTES = 928
    SGX_ARCH_ENCLAVE_CSS_MISC_SELECT = 900
    # Field format: (offset, type, value)
    fields = {
        'date_year': (SGX_ARCH_ENCLAVE_CSS_DATE + 2, '<H'),
        'date_month': (SGX_ARCH_ENCLAVE_CSS_DATE + 1, '<B'),
        'date_day': (SGX_ARCH_ENCLAVE_CSS_DATE, '<B'),
        'modulus': (SGX_ARCH_ENCLAVE_CSS_MODULUS, '384s'),
        'enclave_hash': (SGX_ARCH_ENCLAVE_CSS_ENCLAVE_HASH, '32s'),
        'isv_prod_id': (SGX_ARCH_ENCLAVE_CSS_ISV_PROD_ID, '<H'),
        'isv_svn': (SGX_ARCH_ENCLAVE_CSS_ISV_SVN, '<H'),
        'flags': (SGX_ARCH_ENCLAVE_CSS_ATTRIBUTES, '8s'),
        'xfrms': (SGX_ARCH_ENCLAVE_CSS_ATTRIBUTES + 8, '8s'),
        'misc_select': (SGX_ARCH_ENCLAVE_CSS_MISC_SELECT, '4s'),
    }
    attr = {}
    for key, (offset, fmt) in fields.items():
        if key in ['date_year', 'date_month', 'date_day']:
            try:
                attr[key] = int(f'{struct.unpack_from(fmt, sig, offset)[0]:x}')
            except ValueError:
                print(f'Misencoded {key} in SIGSTRUCT!', file=sys.stderr)
                raise
            continue
        attr[key] = struct.unpack_from(fmt, sig, offset)[0]

    return attr

# Retrieve information about a previously built graminized Docker image
def gsc_info_image(args):
    docker_socket = docker.from_env()
    gsc_image = get_docker_image(docker_socket, args.image)
    if gsc_image is None:
        print(f'Could not find graminized Docker image {args.image}.\n'
              'Please make sure to build the graminized image first by using \'gsc build\''
              ' command.')
        sys.exit(1)

    # Create temporary directory on the host for sigstruct file
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Grant owner, group and everyone else read-write-execute permissions on temporary dir, so
        # that even non-root users in Docker images can copy `entrypoint.sig` into it
        os.chmod(tmpdirname,0o777)
        # Copy sigstruct file from Docker container into temporary directory on the host
        docker_socket.containers.run(args.image,
            '\'cp /gramine/app_files/entrypoint.sig /tmp/host/ 2>/dev/null || :\'',
            entrypoint=['sh', '-c'], remove=True,
            volumes={tmpdirname: {'bind': '/tmp/host', 'mode': 'rw'}})
        sigstruct = {}
        with open(os.path.join(tmpdirname, "entrypoint.sig"), 'rb') as sig:
            attr = read_sigstruct(sig.read())
            # calculate MRSIGNER as sha256 hash over RSA public key's modulus
            mrsigner = hashlib.sha256()
            mrsigner.update(attr['modulus'])
            sigstruct['mr_enclave'] = attr['enclave_hash'].hex()
            sigstruct['mr_signer'] = mrsigner.digest().hex()
            sigstruct['isv_prod_id'] = attr['isv_prod_id']
            sigstruct['isv_svn'] = attr['isv_svn']
            sigstruct['date'] = '%d-%02d-%02d' % (
                attr['date_year'], attr['date_month'], attr['date_day'])
            sigstruct['flags'] = attr['flags'].hex()
            sigstruct['xfrms'] = attr['xfrms'].hex()
            sigstruct['misc_select'] = attr['misc_select'].hex()
            # DEBUG attribute of the enclave is very important, so we print it also separately
            sigstruct['debug'] = bool(attr['flags'][0] & 0b10)

        if not sigstruct:
            print(f'Could not extract Intel SGX-related information from image {args.image}.')
            sys.exit(1)

        print(tomli_w.dumps(sigstruct))


argparser = argparse.ArgumentParser()
subcommands = argparser.add_subparsers(metavar='<command>')
subcommands.required = True

sub_build = subcommands.add_parser('build', help='Build graminized Docker image')
sub_build.set_defaults(command=gsc_build)
sub_build.add_argument('-b', '--buildtype', choices=['release', 'debug', 'debugoptimized'],
    default='release', help='Compile Gramine in release, debug or debugoptimized mode.')

sub_build.add_argument('--insecure-args', action='store_true',
    help='Allow to specify untrusted arguments during Docker run. '
         'Otherwise arguments are ignored.')
sub_build.add_argument('-nc', '--no-cache', action='store_true',
    help='Build graminized Docker image without any cached images.')
sub_build.add_argument('--rm', action='store_true',
    help='Remove intermediate Docker images when build is successful.')
sub_build.add_argument('--build-arg', action='append', default=[],
    help='Set build-time variables (same as "docker build --build-arg").')
sub_build.add_argument('-c', '--config_file', type=argparse.FileType('r', encoding='UTF-8'),
    default='config.yaml', help='Specify configuration file.')
sub_build.add_argument('image', help='Name of the application Docker image.')
sub_build.add_argument('manifest', help='Manifest file to use.')

sub_build_gramine = subcommands.add_parser('build-gramine',
    help='Build base-Gramine Docker image')
sub_build_gramine.set_defaults(command=gsc_build_gramine)
sub_build_gramine.add_argument('-b', '--buildtype', choices=['release', 'debug', 'debugoptimized'],
    default='release', help='Compile Gramine in release, debug or debugoptimized mode.')

sub_build_gramine.add_argument('-nc', '--no-cache', action='store_true',
    help='Build graminized Docker image without any cached images.')
sub_build_gramine.add_argument('--rm', action='store_true',
    help='Remove intermediate Docker images when build is successful.')
sub_build_gramine.add_argument('--build-arg', action='append', default=[],
    help='Set build-time variables (same as "docker build --build-arg").')
sub_build_gramine.add_argument('-c', '--config_file',
    type=argparse.FileType('r', encoding='UTF-8'),
    default='config.yaml', help='Specify configuration file.')
sub_build_gramine.add_argument('-f', '--file-only', action='store_true',
    help='Stop after Dockerfile is created and do not build the Docker image.')
sub_build_gramine.add_argument('image',
    help='Name of the output base-Gramine Docker image.')

sub_sign = subcommands.add_parser('sign-image', help='Sign graminized Docker image')
sub_sign.set_defaults(command=gsc_sign_image)
sub_sign.add_argument('-c', '--config_file', type=argparse.FileType('r', encoding='UTF-8'),
    default='config.yaml', help='Specify configuration file.')
sub_sign.add_argument('image', help='Name of the application (base) Docker image.')
sub_sign.add_argument('key', help='Key to sign the Intel SGX enclaves inside the Docker image.')
sub_sign.add_argument('-p', '--passphrase', "--password", help='Passphrase for the signing key.')
sub_sign.add_argument('-D','--define', action='append', default=[],
    help='Set image sign-time variables.')
sub_sign.add_argument('--remove-gramine-deps', action='append_const', dest='define',
    const='remove_gramine_deps=true', help='Remove Gramine dependencies that are not needed'
                                           ' at runtime.')
sub_sign.add_argument('--no-remove-gramine-deps', action='append_const', dest='define',
    const='remove_gramine_deps=false', help='Retain Gramine dependencies that are not needed'
                                            ' at runtime.')
sub_info = subcommands.add_parser('info-image', help='Retrieve information about a graminized '
                                  'Docker image')
sub_info.set_defaults(command=gsc_info_image)
sub_info.add_argument('image', help='Name of the graminized Docker image.')

def main(args):
    args = argparser.parse_args()
    return args.command(args)
