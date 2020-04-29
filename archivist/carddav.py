import requests, json, logging, datetime
import urllib.parse
from pathlib import Path
from xml.etree import ElementTree

log = logging.getLogger(__name__)

def autodiscover(url):
    log.info("Autodiscovering url...")
    url = url.strip("/")
    if url.endswith('/.well-known/carddav'):
        discovery_url = url 
    else:
        discovery_url = urllib.parse.urljoin(url, '/.well-known/carddav')

    response = requests.get(discovery_url)
    return response.url

def get_old_backups(backup_dir):
    old_backups = {}
    for b in backup_dir.glob("*.vcf"):
        bname, b2 = b.stem.split("##")
        bdate = datetime.datetime.fromtimestamp(float(b2))

        if bname not in old_backups:
            old_backups[bname] = {}
            old_backups[bname]["backups"] = [b]
            old_backups[bname]["latest"] = datetime.datetime.fromtimestamp(0)
        else:
            old_backups[bname]["backups"].append(b)

        if old_backups[bname]["latest"] < bdate:
            log.info("Found " + bname + " last updated on " + str(bdate))
            old_backups[bname]["latest"] = bdate


    return old_backups

def get_safe_name(name):
    safe_chars = ("_", ".", "-")
    safe_name = "".join(c for c in name if c.isalnum() or c in safe_chars).rstrip()
    return safe_name

def check_books(root_url, username, s, old_backups=None):
    log.info("Checking for out of date address books...")

    addr_url = root_url + '/user/' + username

    response = s.request("PROPFIND", addr_url, headers={"Depth": "1"})

    tree = ElementTree.fromstring(response.content)

    ns = { "D": "DAV:", "C": "urn:ietf:params:xml:ns:carddav" }

    books = []

    for i in tree.findall("././D:response", ns):
        if i.findall(".//C:addressbook", ns):
            name = i.find("./D:propstat/D:prop/D:displayname", ns).text
            date = datetime.datetime.strptime(i.find("./D:propstat/D:prop/D:getlastmodified", ns).text,
                    "%a, %d %b %Y %H:%M:%S %Z")
            url = i.find("./D:href", ns).text

            safename = get_safe_name(name)

            if safename not in old_backups or date > old_backups[safename]["latest"]:
                log.info(safename + " is out of date")
                books.append({"name": name, "url": url, "date": date})

    if len(books) == 0:
        log.info("No out of date addressbooks found.")

    return books

def save_books(s, backup_folder, root_url, books):
    for book in books:
        log.info("Downloading " + get_safe_name(book["name"]))
        full_url = urllib.parse.urljoin(root_url, book['url'])
        response = s.get(full_url, headers={"Depth": "1"})
            
        backup_file = (get_safe_name(book["name"]) + "##" + 
                str(book["date"].timestamp()) + ".vcf")
        backup_folder.mkdir(parents=True, exist_ok=True)
        backup_path = backup_folder / backup_file

        with open(backup_path, "w+") as f:
            f.write(response.text)

def cleanup_books(books, old_backups):
    log.info("Cleaning up old backups")
    for book in books:
        if book["name"] in old_backups:
            for b in old_backups[book["name"]]["backups"]:
                log.info("Deleting " + str(b))
                b.unlink()

def backup_carddav(config):

    root_url = autodiscover(config["url"])

    with requests.Session() as s:
        s.auth = (config['user'], config['password'])

        old_backups = get_old_backups(Path(config['backup_folder']))
        
        books = check_books(root_url, config["user"], s, old_backups)
        
        save_books(s, Path(config['backup_folder']), root_url, books)
      
        if config.get("keep_old", False) and len(books) > 0:
            cleanup_books(books, old_backups)

