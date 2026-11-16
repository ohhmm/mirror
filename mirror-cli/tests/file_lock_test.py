"""Exclusive locks serialize processes and release when their file closes."""

import pathlib
import subprocess
import sys

import pytest

from mirror import file_lock


def test_lock_serializes_processes(tmp_path: pathlib.Path) -> None:
  path = tmp_path / 'settings.lock'
  path.write_text('existing lock file')
  with path.open('a') as lock:
    file_lock.exclusive(lock)
    child = subprocess.Popen(
      [
        sys.executable,
        '-c',
        'import pathlib, sys; from mirror import file_lock; '
        "lock = pathlib.Path(sys.argv[1]).open('a'); lock.seek(3); "
        "print('ready', flush=True); file_lock.exclusive(lock); "
        "print('acquired', flush=True)",
        str(path),
      ],
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
    )
    try:
      assert child.stdout is not None
      assert child.stdout.readline() == 'ready\n'
      with pytest.raises(subprocess.TimeoutExpired):
        child.wait(timeout=0.2)
      lock.close()
      output, errors = child.communicate(timeout=10)
      assert child.returncode == 0, errors
      assert output == 'acquired\n'
    finally:
      if child.poll() is None:
        child.kill()
      child.communicate()


def test_lock_releases_after_exception(tmp_path: pathlib.Path) -> None:
  path = tmp_path / 'settings.lock'
  with pytest.raises(ValueError, match='interrupted update'):
    with path.open('a') as lock:
      file_lock.exclusive(lock)
      raise ValueError('interrupted update')
  with path.open('a') as lock:
    file_lock.exclusive(lock)


def test_lock_reports_closed_file(tmp_path: pathlib.Path) -> None:
  with (tmp_path / 'settings.lock').open('a') as lock:
    pass
  with pytest.raises(ValueError):
    file_lock.exclusive(lock)
