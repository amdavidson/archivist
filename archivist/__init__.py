
import logging, sys

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
out_handler = logging.StreamHandler(sys.stdout)
#out_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
out_handler.setLevel(logging.INFO)
log.addHandler(out_handler)

from archivist.archivist import Archivist
