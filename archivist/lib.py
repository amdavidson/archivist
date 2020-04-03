import yaml
import sys 
from pathlib import Path

class Config():

    CONFIGFILE = Path.home() / ".archivist.yml"
    c = {}

    def init(self):
        with open(self.CONFIGFILE) as stream:
            try:
                config_dict = yaml.full_load(stream)
                for key, value in config_dict.items():
                    self.c[key] = value
            except yaml.YAMLError as exc:
                print(exc)

    def backupdir(self): 
        return Path(self.c["backup_folder"])


    def imapdir(self):
        return self.backupdir() / self.c["imap_localroot"]
    

