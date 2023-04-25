import os
from typing import Tuple


TIMER = 0.1
BUFSIZE = 4096
WINDOW_SIZE = 30
DROP_THRESHOLD = 50

try:
    env_window_size = int(os.environ['TFTP_WINDOW_SIZE'])
    WINDOW_SIZE = env_window_size
except (KeyError, ValueError):
    pass

Address = Tuple[str, int]
