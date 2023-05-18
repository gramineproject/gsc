#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2020-2021 Intel Corp.
#                         Anjo Vahldiek-Oberwagner <anjo.lucas.vahldiek-oberwagner@intel.com>
#                         Dmitrii Kuvaiskii <dmitrii.kuvaiskii@intel.com>

import argparse
import os
import re
import subprocess
import sys

import jinja2
import tomli
import tomli_w

def is_utf8(filename_bytes):
    try:
        filename_bytes.decode('UTF-8')
        return True
    except UnicodeError:
        return False

def extract_files_from_user_manifest(manifest):
    files = []

    files.extend(manifest['sgx'].get('trusted_files', []))
    files.extend(manifest['sgx'].get('allowed_files', []))
    files.extend(manifest['sgx'].get('protected_files',[]))

    return files


def generate_trusted_files(root_dir, already_added_files, followlinks):
    excluded_paths_regex = (r'^/('
                                r'boot/.*'
                                r'|\.dockerenv'
                                r'|\.dockerinit'
                                r'|dev/.*'
                                r'|etc/gshadow.*'
                                r'|etc/mtab'
                                r'|etc/\.pwd\.lock'
                                r'|etc/rc(\d|.)\.d/.*'
                                r'|etc/security/.*'
                                r'|etc/shadow.*'
                                r'|gramine/python/.*'
                                r'|gramine/app_files/finalize_manifest\.py'
                                r'|proc/.*'
                                r'|sys/.*'
                                r'|var/.*)$')
    exclude_re = re.compile(excluded_paths_regex)

    num_trusted = 0
    trusted_files = []

    # WARNING: below loop does not remove cycles (which can happen due to symlinks), but we assume
    # that Docker images (excluding paths/files listed in `excluded_paths_regex`) don't have cycles.
    for dirpath, dirnames, files in os.walk(root_dir.encode('UTF-8'), followlinks=followlinks):
        scandirs = []
        for dirname in dirnames:
            to_be_walked_dir = os.path.join(dirpath, dirname)
            if exclude_re.match(to_be_walked_dir.decode('UTF-8')):
                # exclude special paths from list of trusted files
                continue
            scandirs.append(dirname)
        # slice assignment, to modify `dirnames` in place (so that os.walk() will recurse only
        # into the subdirs whose names remain in `dirnames`)
        dirnames[:] = scandirs

        for file in files:
            filename = os.path.join(dirpath, file)
            if not os.path.isfile(filename):
                # only regular files are added as trusted files
                continue
            if not is_utf8(filename):
                # we append filenames as TOML strings which must be in UTF-8
                print(f'\t[from inside Docker container] File {filename} is not in UTF-8!')
                sys.exit(1)

            # convert from bytes to str for further string handling
            filename = filename.decode('UTF-8')

            if exclude_re.match(filename):
                # exclude special files and paths from list of trusted files
                continue
            if '\n' in filename:
                # we use TOML's basic single-line strings, can't have newlines
                continue
            if '\\x' in filename:
                # Python TOML parser has a bug that prevents it from correctly handling `\x`
                # sequences in strings (see https://github.com/uiri/toml/issues/404). Fortunately,
                # the only files that exhibit such pattern are systemd helper files which graminized
                # apps will never access anyway.
                # FIXME: Now we switched to `tomli`, but GSC can still use Gramine v1.3 or lower
                #        which uses `toml`. When GSC removes support for v1.3, can remove this.
                print(f'\t[from inside Docker container] File {filename} contains `\\x` sequence '
                       'and will be skipped from `sgx.trusted_files`!')
                continue

            trusted_file_entry = f'file:{filename}'
            if trusted_file_entry in already_added_files:
                # user manifest already contains this file (probably as allowed or protected)
                continue

            trusted_files.append(trusted_file_entry)
            num_trusted += 1

    print(f'\t[from inside Docker container] Found {num_trusted} files in `{root_dir}`.')
    return trusted_files


def generate_library_paths():
    encoding = sys.stdout.encoding if sys.stdout.encoding is not None else 'UTF-8'
    ld_paths = subprocess.check_output('ldconfig -v -N -X', stderr=subprocess.PIPE, shell=True)
    ld_paths = ld_paths.decode(encoding).splitlines()

    # Library paths start without whitespace (in contrast to libraries found under this path)
    ld_paths = (line for line in ld_paths if not re.match(r'(^\s)', line))

    # ldconfig utility in Ubuntu 21.04 produces output lines like
    # “/usr/local/lib: (from /etc/ld.so.conf.d/libc.conf:2)” – must take only the first part
    # of this line (the actual path name)
    ld_paths = ((line.split('(from')[0]).rstrip() for line in ld_paths)
    return ''.join(ld_paths) + os.getenv('LD_LIBRARY_PATH', default='')


argparser = argparse.ArgumentParser()
argparser.add_argument('-d', '--dir', default='/',
    help='Search directory tree from this root to generate list of trusted files.')
argparser.add_argument('-l', '--links', action='store_true',
    help='Whether to traverse symbolic links, default is True.')
argparser.add_argument('-nl', '--no-links', dest='links', action='store_false')
argparser.set_defaults(links=True)

def main(args=None):
    args = argparser.parse_args(args[1:])
    if not os.path.isdir(args.dir):
        argparser.error(f'\t[from inside Docker container] Could not find directory `{args.dir}`.')

    env = jinja2.Environment(loader=jinja2.FileSystemLoader('/'))
    env.globals.update({'library_paths': generate_library_paths(), 'env_path': os.getenv('PATH')})

    manifest = '/gramine/app_files/entrypoint.manifest'
    rendered_manifest = env.get_template(manifest).render()
    rendered_manifest_dict = tomli.loads(rendered_manifest)
    already_added_files = extract_files_from_user_manifest(rendered_manifest_dict)

    if 'allow_all_but_log' not in rendered_manifest_dict['sgx'].get('file_check_policy', ''):
        trusted_files = generate_trusted_files(args.dir, already_added_files, args.links)
        rendered_manifest_dict['sgx'].setdefault('trusted_files', []).extend(trusted_files)
    else:
        print(f'\t[from inside Docker container] Skipping trusted files generation. This image must not be used in production.')

    with open(manifest, 'wb') as manifest_file:
        tomli_w.dump(rendered_manifest_dict, manifest_file)
    print(f'\t[from inside Docker container] Successfully finalized `{manifest}`.')

if __name__ == '__main__':
    main(sys.argv)
