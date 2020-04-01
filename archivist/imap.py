import imaplib
from pathlib import Path
from archivist.lib import Config

log = logging.getLogger(__name__)

backupdir = Path.home() / "backups/fastmail"

def imap_connect(c):
    server = imaplib.IMAP4_SSL(c['imap_server'], c['imap_port'])
    server.login(c['imap_user'], c['imap_password'])
    return server

            
def get_remote_folders(server):
    typ, data = server.list()
    print(typ)

    folders = []

    print(data)

def create_folder_structure(folders):
    print("Not implemented")

def scan_local_folder(folder):
    print("Not implemented")

def scan_remote_folder(server, folder):
    print("Not implemented")

def download_messages(server, new_messages):
    print("Not implemented")




def backup_imap():
    server = imap_connect()

    folders = get_remote_folders(server)

#    create_folder_structure(folders)
#
#    for folder in folders:
#        current_messages = scan_local_folder(folder)
#        remote_messages = scan_remote_folder(server, folder)
#
#        new_messages = {}
#        
#        for msg_id in remote_messages:
#            if msg_id not in current_messages:
#                new_messages[msg_id] = remote_messages[msg_id]
#        
#        download_messages(server, new_messages)

    server.logout()


