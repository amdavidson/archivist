import requests, json, logging, datetime, hashlib
import urllib.parse
from pathlib import Path
from xml.etree import ElementTree

log = logging.getLogger(__name__)


def autodiscover(s, url):
    url = url.rstrip("/")
    if url.endswith("/.well-known/caldav"):
        discovery_url = url
    else:
        discovery_url = urllib.parse.urljoin(url, "/.well-known/caldav")

    response = s.get(discovery_url)

    if response.ok:
        log.info("Autodiscovery successful: " + response.url)
        return response.url
    else:
        log.info("Autodiscovery failed, connecting to: " + url)
        return url


def get_old_backups(backup_dir):
    old_backups = []
    for b in backup_dir.glob("*.json"):
        with open(b) as f:
            data = json.load(f)
        old_backups.append(data)

    return old_backups


# Get the principal user url for the user provided by the session
# Returns the same url that is provided if a principal user url cannot be found
def get_principal_url(s, url):
    headers = {}
    headers["Depth"] = "0"
    headers["Content-type"] = "text/xml"
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:caldav"}
    body = b"""
        <d:propfind xmlns:d="DAV:">
            <d:prop>
                <d:current-user-principal />
            </d:prop>
        </d:propfind>
        """
    response = s.request("PROPFIND", url, headers=headers, data=body)
    # print(response.text)
    root = ElementTree.fromstring(response.content)
    rv = root.find(".//{DAV:}current-user-principal/{DAV:}href")
    if rv is not None:
        principal_url = urllib.parse.urljoin(url, rv.text).rstrip("/") + "/"
    else:
        log.info("Principal URL could not be determined.")
        principal_url = url

    log.info("Principal URL: " + principal_url)
    return principal_url


# Get addressbook urls from a collection/homeset URL
def get_collection_urls(s, homeset_url):
    headers = {}
    headers["Depth"] = "1"
    headers["Content-Type"] = "text/xml"
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:caldav"}

    body = b"""<?xml version="1.0" encoding="utf-8" ?>
    <d:propfind xmlns:d="DAV:">
        <d:prop>
            <d:resourcetype />
            <d:getlastmodified />
        </d:prop>
    </d:propfind>"""

    response = s.request("PROPFIND", homeset_url, headers=headers, data=body)
    # print(response.text)
    tree = ElementTree.fromstring(response.content)

    addressbook_urls = []
    for i in tree.findall("D:response", ns):
        if i.findall(".//C:calendar", ns):
            s = i.find("./D:href", ns).text
            u = urllib.parse.urljoin(homeset_url, s).rstrip("/") + "/"
            log.info("Found an calendar at: " + u)
            addressbook_urls.append(u)

    return addressbook_urls


# Get the homeset url for the user determined by the session
# Returns the same url it is provided if it cannot find a homeset url
def get_homeset_url(s, url):
    headers = {}
    headers["Depth"] = "0"
    headers["Content-Type"] = "text/xml"
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:caldav"}
    body = b"""
        <d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
            <d:prop>
                <c:calendar-home-set />
            </d:prop>
        </d:propfind>
    """
    response = s.request("PROPFIND", url, headers=headers, data=body)
    # print(response.text)
    root = ElementTree.fromstring(response.content)
    rv = root.find(".//C:calendar-home-set/D:href", ns)
    if rv is not None:
        homeset_url = urllib.parse.urljoin(url, rv.text).rstrip("/") + "/"
    else:
        log.info("Homeset url could not be determined.")
        homeset_url = url

    log.info("Homeset url: " + homeset_url)
    return homeset_url


def get_calendar_info(s, url):
    headers = {}
    headers["Depth"] = "0"
    headers["Content-Type"] = "text/xml"
    ns = {
        "D": "DAV:",
        "C": "urn:ietf:params:xml:ns:caldav",
        "CS": "http://calendarserver.org/ns/",
    }
    body = b"""<?xml version="1.0" encoding="utf-8" ?>
    <d:propfind xmlns:d="DAV:" xmlns:cs="http://calendarserver.org/ns/">
        <d:prop>
            <d:resourcetype />
            <d:getlastmodified />
            <d:getetag />
            <d:displayname />
            <cs:getctag />
        </d:prop>
    </d:propfind>"""
    # body = ""

    response = s.request("propfind", url, headers=headers, data=body)
    tree = ElementTree.fromstring(response.content)
    # print(response.text)
    etag = tree.find(".//D:getetag", ns).text
    # print(etag)
    name = tree.find(".//D:displayname", ns).text
    ctag = tree.find(".//CS:getctag", ns).text
    # print(name, ctag)
    uuid = hashlib.sha256(url.encode("utf-8")).hexdigest()
    # print(uuid)
    lm_date = tree.find(".//D:getlastmodified", ns).text
    if lm_date is not None:
        mod_date = datetime.datetime.strptime(
            lm_date, "%a, %d %b %Y %H:%M:%S %Z"
        ).timestamp()
    else:
        mod_date = None

    return {
        "display_name": name,
        "short_name": uuid[:7],
        "uuid": uuid,
        "modified_date": mod_date,
        "backup_date": datetime.datetime.now().timestamp(),
        "url": url,
        "etag": etag,
        "ctag": ctag,
    }


# Check the remote server for what calendars are available
# Return a list of calendars on offer from the server
def check_calendars(s, root_url):
    root_url = root_url.rstrip("/") + "/"

    # Get the principal url for the user
    principal_url = get_principal_url(s, root_url)

    # Get the homeset url for the user
    homeset_url = get_homeset_url(s, principal_url)

    # get_resource_types(s, homeset_url)

    # Find addressbooks from the homeset collection
    calendar_urls = get_collection_urls(s, homeset_url)

    # Iterate through addressbooks getting more information about them.
    calset = []
    for url in calendar_urls:
        calset.append(get_calendar_info(s, url))

    return calset


# Compare the current set of calendars from the server to the old_backups on hand
# Return a list of calendars that need to be updated.
def compare_backups(old_backups, calset):
    needs_update = []

    if old_backups is not None:
        for cal in calset:
            # print(cal)
            # print(old_backups)
            backups = [x for x in old_backups if x["short_name"] == cal["short_name"]]
            if len(backups) > 0:
                latest = backups[0]
            else:
                log.info(cal["display_name"] + " not found in backups.")
                needs_update.append(cal)
                continue
            for b in backups:
                # print(b)
                if b["backup_date"] > latest["backup_date"]:
                    latest = b
            if cal["ctag"] != latest["ctag"]:
                log.info(cal["display_name"] + " has been changed.")
                cal["latest"] = latest
                needs_update.append(cal)
            else:
                log.info(cal["display_name"] + " has not been changed.")
    else:
        log.info("No backups found.")
        needs_update = calset

    # print(needs_update)
    return needs_update


# Save new backups of the required calendars
def save_calendars(s, backup_folder, calset):
    headers = {}
    headers["Depth"] = "1"
    headers["Content-Type"] = "text/xml"
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:caldav"}
    body = b"""<?xml version="1.0" encoding="utf-8" ?>
    <d:propfind xmlns:d="DAV:">
        <d:prop>
            <d:resourcetype />
            <d:getlastmodified />
            <d:getetag />
        </d:prop>
    </d:propfind>"""
    # body = ""

    for cal in calset:
        if "latest" in cal:
            cal["events"] = cal["latest"]["events"]
            cal.pop("latest")
            log.info("Updating " + cal["display_name"])
        else:
            cal["events"] = {}
            log.info("Downloading " + cal["display_name"])

        response = s.request("PROPFIND", cal["url"], headers=headers, data=body)
        tree = ElementTree.fromstring(response.content)
        cals = tree.findall(".//D:response", ns)
        for c in cals:
            href = c.find(".//D:href", ns).text
            newEtag = c.find(".//D:getetag", ns).text

            if href in cal["events"]:
                if cal["events"][href]["etag"] == newEtag:
                    continue

            u = urllib.parse.urljoin(cal["url"], href)
            response = s.get(u, headers={"Depth": "1"})
            cal["events"][href] = {
                "url": str(u),
                "etag": newEtag,
                "ics": response.text,
            }

        backup_file = cal["short_name"] + "-" + str(cal["backup_date"]) + ".json"
        backup_folder.mkdir(parents=True, exist_ok=True)
        backup_path = backup_folder / backup_file

        with open(backup_path, "w+") as f:
            json.dump(cal, f, default=str)


# Cleanup old backups of the cals that were updated
def cleanup_calendars(cals, old_backups):
    log.info("Cleaning up old backups")
    for cal in cals:
        backups = (x for x in old_backups if x["short_name"] == cal["short_name"])
        for b in backups:
            log.info("Deleting " + str(b["file"]))
            b["file"].unlink()


# Run the whole backup sequence
def backup_caldav(config):
    with requests.Session() as s:
        s.auth = (config["user"], config["password"])

        root_url = autodiscover(s, config["url"])

        old_backups = get_old_backups(Path(config["backup_folder"]))

        new_calset = check_calendars(s, root_url)

        needs_update = compare_backups(old_backups, new_calset)

        save_calendars(s, Path(config["backup_folder"]), needs_update)

        if not config.get("keep_old", False) and len(needs_update) > 0:
            cleanup_calendars(needs_update, old_backups)
