import requests, json, logging
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

def check_books(root_url, username, s):
    log.info("Checking for out of date address books...")

    addr_url = root_url + '/user/' + username

    response = s.request("PROPFIND", addr_url, headers={"Depth": "1"})

    tree = ElementTree.fromstring(response.content)

    ns = { "D": "DAV:", "C": "urn:ietf:params:xml:ns:carddav" }

    books = []

    for i in tree.findall("././"):
        if i.findall(".//C:addressbook", ns):
            name = i.find("./D:propstat/D:prop/D:displayname", ns).text
            date = i.find("./D:propstat/D:prop/D:getlastmodified", ns).text
            url = i.find("./D:href", ns).text

            ### TODO: check dates

            books.append({"name": name, "url": url, "date": date})
    
    return books

def save_books(s, backup_path, root_url, books):
        for book in books:
            log.info("Downloading " + book["name"])
        #### TODO: Save books
        #    response = s.get(book_url, headers={"Depth": "1"})
        #    
        #    backupfile = str(time.time()) + ".json" 
        #    pinboard_dir.mkdir(parents=True, exist_ok=True)
        #    backuppath = pinboard_dir / backupfile

        #    with open(backuppath, "w+") as f:
        #        f.write(response.text)



def backup_carddav(config):

    root_url = autodiscover(config["url"])

    with requests.Session() as s:
        s.auth = (config['user'], config['password'])
        
        books = check_books(root_url, config["user"], s)
        
        save_books(s, config['backup_folder'], root_url, books)

