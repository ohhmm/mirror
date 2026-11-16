"""Exclusive file locks released when the caller closes the file."""

import errno
import os
import time
from typing import TextIO


def exclusive(file: TextIO) -> None:
  """Wait for an exclusive lock shared by processes using the same file."""
  if os.name == 'nt':
    import msvcrt

    file.seek(0)
    while True:
      try:
        msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
        return
      except OSError as error:
        if error.errno != errno.EACCES:
          raise
        time.sleep(0.05)
  else:
    import fcntl

    fcntl.flock(file, fcntl.LOCK_EX)
