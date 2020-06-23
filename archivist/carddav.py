import requests, json, logging, datetime, hashlib
import urllib.parse
from pathlib import Path
from xml.etree import ElementTree

log = logging.getLogger(__name__)


def autodiscover(s, url):
    url = url.strip("/")
    if url.endswith("/.well-known/carddav"):
        discovery_url = url
    else:
        discovery_url = urllib.parse.urljoin(url, "/.well-known/carddav")

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
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:carddav"}
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
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:carddav"}

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
        if i.findall(".//C:addressbook", ns):
            s = i.find("./D:href", ns).text
            u = urllib.parse.urljoin(homeset_url, s).rstrip("/") + "/"
            log.info("Found an addressbook at: " + u)
            addressbook_urls.append(u)

    return addressbook_urls


# Get the homeset url for the user determined by the session
# Returns the same url it is provided if it cannot find a homeset url
def get_homeset_url(s, url):
    headers = {}
    headers["Depth"] = "0"
    headers["Content-Type"] = "text/xml"
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:carddav"}
    body = b"""
        <d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:carddav">
            <d:prop>
                <c:addressbook-home-set />
            </d:prop>
        </d:propfind>
    """
    response = s.request("PROPFIND", url, headers=headers, data=body)
    # print(response.text)
    root = ElementTree.fromstring(response.content)
    rv = root.find(".//C:addressbook-home-set/D:href", ns)
    if rv is not None:
        homeset_url = urllib.parse.urljoin(url, rv.text).rstrip("/") + "/"
    else:
        log.info("Homeset url could not be determined.")
        homeset_url = url

    log.info("Homeset url: " + homeset_url)
    return homeset_url


def get_addressbook_info(s, url):
    headers = {}
    headers["Depth"] = "0"
    headers["Content-Type"] = "text/xml"
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:carddav"}
    body = b"""<?xml version="1.0" encoding="utf-8" ?>
    <d:propfind xmlns:d="DAV:">
        <d:prop>
            <d:resourcetype />
            <d:getlastmodified />
            <d:getetag />
        </d:prop>
    </d:propfind>"""
    # body = ""

    response = s.request("propfind", url, headers=headers, data=body)
    tree = ElementTree.fromstring(response.content)
    # print(response.text)
    etag = tree.find(".//D:getetag", ns).text
    # print(etag)
    uuid = hashlib.sha256(url.encode("utf-8")).hexdigest()
    # print(uuid)
    date = datetime.datetime.strptime(
        tree.find(".//D:getlastmodified", ns).text, "%a, %d %b %Y %H:%M:%S %Z"
    ).timestamp()

    return {
        "short_name": uuid[:7],
        "uuid": uuid,
        "date": date,
        "url": url,
        "etag": etag,
    }


# Check the remote server for what addressbooks are available
# Return a list of books on offer from the server
def check_books(s, root_url):
    root_url = root_url.rstrip("/") + "/"

    # Get the principal url for the user
    principal_url = get_principal_url(s, root_url)

    # Get the homeset url for the user
    homeset_url = get_homeset_url(s, principal_url)

    # Find addressbooks from the homeset collection
    addressbook_urls = get_collection_urls(s, homeset_url)

    # Iterate through addressbooks getting more information about them.
    bookset = []
    for url in addressbook_urls:
        book_info = get_addressbook_info(s, url)
        # print(book_info)
        bookset.append(book_info)

    return bookset


# Compare the current bookset from the server to the old_backups on hand
# Return a list of books that need to be updated.
def compare_backups(old_backups, bookset):
    needs_update = []

    if old_backups is not None:
        for book in bookset:
            backups = [x for x in old_backups if x["short_name"] == book["short_name"]]
            if len(backups) > 0:
                latest = backups[0]
            else:
                log.info("No backups found.")
                needs_update.append(book)
                continue

            for b in backups:
                if b["date"] > latest["date"]:
                    latest = b
            if book["date"] > latest["date"]:
                log.info(book["url"] + " has been updated.")
                if "contacts" in latest:
                    book["contacts"] = latest["contacts"]
                needs_update.append(book)
            else:
                log.info(book["url"] + " has a current backup.")
    else:
        log.info("No backups found.")
        needs_update = bookset

    # print(needs_update)
    return needs_update


# Save new backups of the required books
def save_books(s, backup_folder, bookset):
    headers = {}
    headers["Depth"] = "1"
    headers["Content-Type"] = "text/xml"
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:carddav"}
    body = b"""<?xml version="1.0" encoding="utf-8" ?>
    <d:propfind xmlns:d="DAV:">
        <d:prop>
            <d:resourcetype />
            <d:getlastmodified />
            <d:getetag />
        </d:prop>
    </d:propfind>"""
    # body = ""

    for book in bookset:
        if "contacts" in book:
            log.info("Updating " + book["url"])
        else:
            log.info("Downloading " + book["url"])
            book["contacts"] = {}
        response = s.request("PROPFIND", book["url"], headers=headers, data=body)
        tree = ElementTree.fromstring(response.content)
        cards = tree.findall(".//D:response", ns)
        for card in cards:
            href = card.find(".//D:href", ns).text
            newEtag = card.find(".//D:getetag", ns).text
            if href in book["contacts"]:
                if book["contacts"][href]["etag"] == newEtag:
                    continue

            u = urllib.parse.urljoin(book["url"], href)

            response = s.get(u, headers={"Depth": "1"})

            book["contacts"][href] = {
                "href": href,
                "etag": newEtag,
                "vcf": response.text,
            }

        backup_file = book["short_name"] + "-" + str(book["date"]) + ".json"
        backup_folder.mkdir(parents=True, exist_ok=True)
        backup_path = backup_folder / backup_file

        with open(backup_path, "w+") as f:
            json.dump(book, f, sort_keys=True, default=str)


# Cleanup old backups of the books that were updated
def cleanup_books(books, old_backups):
    log.info("Cleaning up old backups")
    for book in books:
        backups = (x for x in old_backups if x["short_name"] == book["short_name"])
        for b in backups:
            log.info("Deleting " + str(b["file"]))
            b["file"].unlink()


# Run the whole backup sequence
def backup_carddav(config):
    with requests.Session() as s:
        s.auth = (config["user"], config["password"])

        root_url = autodiscover(s, config["url"])

        old_backups = get_old_backups(Path(config["backup_folder"]))

        new_bookset = check_books(s, root_url)

        needs_update = compare_backups(old_backups, new_bookset)

        save_books(s, Path(config["backup_folder"]), needs_update)

        if not config.get("keep_old", False) and len(needs_update) > 0:
            cleanup_books(needs_update, old_backups)
