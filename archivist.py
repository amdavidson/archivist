import sys, logging, os
from pathlib import Path
import yaml
import archivist.pinboard as pinboard
import archivist.github as github
import archivist.imap as imap
import archivist.carddav as carddav
import archivist.caldav as caldav
from archivist import log, setup_logging

config_locations = []
config_locations.append(Path("./archivist.yml"))
if None != os.environ.get("XDG_CONFIG_HOME"):
    config_locations.append(
        Path(os.environ.get("XDG_CONFIG_HOME")) / "archivist/archivist.yml"
    )
config_locations.append(Path.home() / ".config/archivist/archivist.yml")
config_locations.append(Path.home() / ".archivist.yml")
config_locations.append(Path("/etc/archivist/archivist.yml"))

got_config = False
i = 0
while not got_config:
    if config_locations[i].exists():
        with open(config_locations[i]) as f:
            config = yaml.full_load(f)
            if config != None:
                got_config = True
                log.info("Loading configuration from: " + str(config_locations[i]))

    i += 1
    if i == len(config_locations):
        string = (
            "Could not load a config file.\n\nCreate one at one of these locations:\n"
        )
        for loc in config_locations:
            string = string + "\t- " + str(loc) + "\n"
        log.fatal(string)
        sys.exit(1)


setup_logging(config)


def run_backup(config):
    if config["service_type"] == "github":
        log.info("Backing up " + config["name"])
        github.backup_github(config)

    elif config["service_type"] == "pinboard":
        log.info("Backing up " + config["name"])
        pinboard.backup_pinboard(config)

    elif config["service_type"] == "imap":
        log.info("Backing up " + config["name"])
        imap.backup_imap(config)

    elif config["service_type"] == "carddav":
        log.info("Backing up " + config["name"])
        carddav.backup_carddav(config)

    elif config["service_type"] == "caldav":
        log.info("Backing up " + config["name"])
        caldav.backup_caldav(config)

    else:
        log.warning('Service type "' + config["service_type"] + '" is not enabled.')


def run_archivist(command, service):
    if command == "backup":
        if service == "":
            log.info("Backing up all services")
            log.info("---###---")

            for b in config["services"]:
                try:
                    run_backup(config["services"][b])
                except:
                    log.error(
                        "Backup of {} failed.".format(config["services"][b]["name"])
                    )
                log.info("---###---")

        elif service != None and service in config["services"]:
            run_backup(config["services"][service])

        else:
            log.error("Service %s not implemented" % service)

    else:
        log.error("Command %s not implemented" % command)


command = sys.argv[1] if len(sys.argv) > 1 else "backup"
service = sys.argv[2] if len(sys.argv) > 2 else ""

run_archivist(command, service)
