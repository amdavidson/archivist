import logging, sys

log = logging.getLogger(__name__)


def setup_logging(config):
    loglevel = config.get("loglevel", "info")
    if loglevel == "info":
        log.setLevel(logging.INFO)
    elif loglevel == "warn" or loglevel == "warning":
        log.setLevel(logging.WARNING)
    elif loglevel == "error":
        log.setLevel(logging.ERROR)
    out_handler = logging.StreamHandler(sys.stdout)
    # out_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    out_handler.setLevel(logging.INFO)
    log.addHandler(out_handler)
