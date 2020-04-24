import requests, json, logging
import urllib.parse
from pathlib import Path
from xml.etree import ElementTree

log = logging.getLogger(__name__)

def auto_discover(url):
   
    return response.url

def backup_carddav(config):

    with requests.Session() as s:
        s.auth = (config['user'], config['password'])
        
        url = config['url'].strip("/")
        if url.endswith('/.well-known/carddav'):
            discovery_url = url 
        else:
            discovery_url = urllib.parse.urljoin(url, '/.well-known/carddav')

        response = s.request("PROPFIND", discovery_url, headers={"Depth": "0"})

        tree = ElementTree.fromstring(response.content)

        for e in tree[0]: 
            if e.tag == "{DAV:}href":
                suff = e.text

        suff = urllib.parse.urljoin(suff + '/user/', config['user'] + '/')

        addr_url = urllib.parse.urljoin(config['url'], suff)

        response = s.request("PROPFIND", addr_url, headers={"Depth": "1"})

        tree = ElementTree.fromstring(response.content)

        print(response.text)

        ns = { "D": "DAV:", "C": "urn:ietf:params:xml:ns:carddav" }

        books = []

        for i in tree.findall("././"):
            if i.findall(".//C:addressbook", ns):
                name = i.find("./D:propstat/D:prop/D:displayname", ns).text
                url = i.find("./D:href", ns).text
                
                books.append({"name": name, "url": url})

        #### get last modified date from here and compare to local date

        for book in books:
            print(book["name"])
        #    response = s.get(book_url, headers={"Depth": "1"})
        #    
        #    backupfile = str(time.time()) + ".json" 
        #    pinboard_dir.mkdir(parents=True, exist_ok=True)
        #    backuppath = pinboard_dir / backupfile

        #    with open(backuppath, "w+") as f:
        #        f.write(response.text)

