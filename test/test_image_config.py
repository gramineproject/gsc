"""Unit tests for Docker image config extraction functions in gsc.py.

These tests cover the Docker 29.x compatibility fix where empty/nil fields
(Entrypoint, Cmd, Env, User, WorkingDir) are omitted from docker image inspect
responses instead of being returned as null.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock

# gsc.py lives one directory up from this test file
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gsc import (  # pylint: disable=wrong-import-position
    extract_binary_info_from_image_config,
    extract_environment_from_image_config,
    extract_user_from_image_config,
)


class _FakeEnv:
    """Minimal stand-in for a Jinja2 Environment (only .globals is used)."""
    def __init__(self):
        self.globals = {}


def make_env():
    return _FakeEnv()


# ---------------------------------------------------------------------------
# extract_binary_info_from_image_config
# ---------------------------------------------------------------------------

class TestExtractBinaryInfo:

    # --- Docker 29.x: fields absent from config dict ---

    def test_cmd_only_no_entrypoint_key(self):
        """Docker 29.x: Entrypoint key absent, Cmd present → binary taken from Cmd."""
        config = {'Cmd': ['/usr/bin/python3', 'app.py']}
        env = make_env()
        extract_binary_info_from_image_config(config, env)
        assert env.globals['binary'] == '/usr/bin/python3'
        assert env.globals['cmd'] == ['app.py']

    def test_entrypoint_only_no_cmd_key(self):
        """Docker 29.x: Cmd key absent, Entrypoint present → binary taken from Entrypoint."""
        config = {'Entrypoint': ['/bin/bash']}
        env = make_env()
        extract_binary_info_from_image_config(config, env)
        assert env.globals['binary'] == '/bin/bash'

    def test_both_keys_absent_exits(self):
        """Docker 29.x: Both Entrypoint and Cmd keys absent → sys.exit(1)."""
        config = {}
        env = make_env()
        with pytest.raises(SystemExit) as exc_info:
            extract_binary_info_from_image_config(config, env)
        assert exc_info.value.code == 1

    def test_working_dir_absent(self):
        """Docker 29.x: WorkingDir key absent → defaults to '/'."""
        config = {'Cmd': ['/bin/ls']}
        env = make_env()
        extract_binary_info_from_image_config(config, env)
        assert env.globals['working_dir'] == '/'

    # --- Docker 28.x: fields present but null ---

    def test_entrypoint_null_cmd_present(self):
        """Docker 28.x: Entrypoint is null (None), Cmd present → binary from Cmd."""
        config = {'Entrypoint': None, 'Cmd': ['/bin/sh', '-c', 'echo hi']}
        env = make_env()
        extract_binary_info_from_image_config(config, env)
        assert env.globals['binary'] == '/bin/sh'

    def test_cmd_null_entrypoint_present(self):
        """Docker 28.x: Cmd is null, Entrypoint present → binary from Entrypoint."""
        config = {'Entrypoint': ['/usr/local/bin/app'], 'Cmd': None}
        env = make_env()
        extract_binary_info_from_image_config(config, env)
        assert env.globals['binary'] == '/usr/local/bin/app'

    def test_working_dir_null(self):
        """Docker 28.x: WorkingDir is null (None) → defaults to '/'."""
        config = {'Cmd': ['/bin/ls'], 'WorkingDir': None}
        env = make_env()
        extract_binary_info_from_image_config(config, env)
        assert env.globals['working_dir'] == '/'

    # --- Normal cases ---

    def test_entrypoint_and_cmd_both_present(self):
        """Entrypoint + Cmd: fixed entrypoint args, Cmd[0] is the implicit cmd binary."""
        config = {
            'Entrypoint': ['/app/server', '--port'],
            'Cmd': ['8080'],
            'WorkingDir': '/app',
        }
        env = make_env()
        extract_binary_info_from_image_config(config, env)
        assert env.globals['binary'] == '/app/server'
        assert env.globals['binary_arguments'] == ['--port']
        # '8080' lands at index last_bin_arg (the implicit new-binary slot);
        # nothing remains for 'cmd'
        assert env.globals['cmd'] == ''
        assert env.globals['working_dir'] == '/app/'

    def test_working_dir_no_trailing_slash(self):
        """WorkingDir without trailing slash gets one appended."""
        config = {'Cmd': ['/bin/bash'], 'WorkingDir': '/home/user'}
        env = make_env()
        extract_binary_info_from_image_config(config, env)
        assert env.globals['working_dir'] == '/home/user/'

    def test_relative_binary_expanded_with_working_dir(self):
        """Relative binary path (with /) is prepended with WorkingDir (no normalization)."""
        config = {'Entrypoint': ['./my_app'], 'WorkingDir': '/opt/app'}
        env = make_env()
        extract_binary_info_from_image_config(config, env)
        assert env.globals['binary'] == '/opt/app/./my_app'

    def test_relative_binary_no_slash_not_expanded(self):
        """Binary with no '/' is not expanded (looked up via PATH)."""
        config = {'Entrypoint': ['python3'], 'WorkingDir': '/app'}
        env = make_env()
        extract_binary_info_from_image_config(config, env)
        assert env.globals['binary'] == 'python3'


# ---------------------------------------------------------------------------
# extract_environment_from_image_config
# ---------------------------------------------------------------------------

class TestExtractEnvironment:

    def test_env_key_absent(self):
        """Docker 29.x: Env key absent → returns empty string."""
        result = extract_environment_from_image_config({})
        assert result == ''

    def test_env_null(self):
        """Docker 28.x: Env is null (None) → returns empty string."""
        result = extract_environment_from_image_config({'Env': None})
        assert result == ''

    def test_env_empty_list(self):
        """Env is an empty list → returns empty string."""
        result = extract_environment_from_image_config({'Env': []})
        assert result == ''

    def test_env_with_variables(self):
        """Env list is serialized to TOML loader.env lines."""
        config = {'Env': ['PATH=/usr/bin:/bin', 'HOME=/root']}
        result = extract_environment_from_image_config(config)
        assert 'loader.env.PATH = "/usr/bin:/bin"' in result
        assert 'loader.env.HOME = "/root"' in result

    def test_env_newline_skipped(self, capsys):
        """Env variable containing newline is skipped with a warning."""
        config = {'Env': ['GOOD=value', 'BAD=line1\nline2']}
        result = extract_environment_from_image_config(config)
        assert 'loader.env.GOOD' in result
        assert 'loader.env.BAD' not in result
        captured = capsys.readouterr()
        assert 'BAD' in captured.out


# ---------------------------------------------------------------------------
# extract_user_from_image_config
# ---------------------------------------------------------------------------

class TestExtractUser:

    def test_user_key_absent(self):
        """Docker 29.x: User key absent → defaults to 'root'."""
        env = make_env()
        extract_user_from_image_config({}, env)
        assert env.globals['app_user'] == 'root'

    def test_user_empty_string(self):
        """Docker 28.x: User is empty string → defaults to 'root'."""
        env = make_env()
        extract_user_from_image_config({'User': ''}, env)
        assert env.globals['app_user'] == 'root'

    def test_user_null(self):
        """Docker 28.x: User is null (None) → defaults to 'root'."""
        env = make_env()
        extract_user_from_image_config({'User': None}, env)
        assert env.globals['app_user'] == 'root'

    def test_user_set(self):
        """User is explicitly set → used as-is."""
        env = make_env()
        extract_user_from_image_config({'User': 'nobody'}, env)
        assert env.globals['app_user'] == 'nobody'
