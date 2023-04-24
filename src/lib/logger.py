import logging

QUIET = logging.WARNING
NORMAL = logging.INFO
VERBOSE = logging.DEBUG

logger = logging.Logger(__name__)


def create_logger(verbose: bool, quiet: bool):
    level = NORMAL
    if verbose:
        level = VERBOSE
    if quiet:
        level = QUIET

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(">> %(message)s"))
    ch.createLock()
    logger.addHandler(ch)


def verbose_log(message: str):
    logger.debug(message)


def normal_log(message: str):
    logger.info(message)


def quiet_log(message: str):
    logger.info(message)
