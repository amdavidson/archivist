import yaml
import sys 
from pathlib import Path

class Log():
    LOGLEVEL = 3
    DEST = "stdout"

    def __call__(self, logstring, loglevel=None):
        if loglevel == "error":
            loglevel = 3
        elif loglevel == "warning":
            loglevel = 2
        else:
            loglevel = 1
        if loglevel >= self.LOGLEVEL:
            if self.DEST == "stderr":
                print(logstring, file=sys.stderr)
            else:
                print(logstring)


class Config():

    CONFIGFILE = Path.home() / ".archivist.yml"

    def init(self):
        with open(self.CONFIGFILE) as stream:
            try:
                return yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    
    

