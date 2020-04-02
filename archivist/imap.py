
###
# Heavily influenced by and borrowed from Rui Carmo's backup script
# https://github.com/rcarmo/imapbackup/blob/master/imapbackup.py
###

import imaplib, logging, re, hashlib, email
from pathlib import Path
from archivist.lib import Config

log = logging.getLogger(__name__)

MSGID_RE = re.compile("^Message\-Id\: (.+)", re.IGNORECASE + re.MULTILINE)
BLANKS_RE = re.compile(r'\s+', re.MULTILINE)

def imap_connect(imap_server, imap_port, imap_user, imap_password):
    log.info("Connecting to "+imap_server+" as "+imap_user)
    server = imaplib.IMAP4_SSL(imap_server, imap_port)
    server.login(imap_user, imap_password)
    return server
           
def parse_paren_list(row):
  """Parses the nested list of attributes at the start of a LIST response"""
  # eat starting paren
  assert(row[0] == '(')
  row = row[1:]
 
  result = []
 
  # NOTE: RFC3501 doesn't fully define the format of name attributes 
  name_attrib_re = re.compile("^\s*(\\\\[a-zA-Z0-9_]+)\s*")
 
  # eat name attributes until ending paren
  while row[0] != ')':
    # recurse
    if row[0] == '(':
      paren_list, row = parse_paren_list(row)
      result.append(paren_list)
    # consume name attribute
    else:
      match = name_attrib_re.search(row)
      assert(match != None)
      name_attrib = row[match.start():match.end()]
      row = row[match.end():]
      #print "MATCHED '%s' '%s'" % (name_attrib, row)
      name_attrib = name_attrib.strip()
      result.append(name_attrib)
 
  # eat ending paren
  assert(')' == row[0])
  row = row[1:]
 
  # done!
  return result, row
 
def parse_string_list(row):
  """Parses the quoted and unquoted strings at the end of a LIST response"""
  slist = re.compile('\s*(?:"([^"]+)")\s*|\s*(\S+)\s*').split(row)
  return [s for s in slist if s]
 
def parse_list(row):
  """Prases response of LIST command into a list"""
  row = row.strip()
  paren_list, row = parse_paren_list(row)
  string_list = parse_string_list(row)
  assert(len(string_list) == 2)
  return [paren_list] + string_list

def get_remote_folders(server):
    """ Gets and parses a list of folders from the server """
    log.info("Getting remote folders")
    typ, data = server.list()

    folders = []
    
    for row in data:
        l = parse_list(row.decode('UTF-8'))
        folders.append(l[-1])
    
    return folders

def create_folder_structure(localroot, folders):
    """ Creates a copy of the remote folder structure locally """
    if not localroot.exists():
        log.info("Creating local folder structure")
    else: 
        log.info("Updating local folder structure")
    for f in folders:
        lf = localroot / f 
        if not lf.exists():
            log.info("Creating "+str(lf))
            lf.mkdir(parents=True)
            cur = lf / "cur"
            cur.mkdir()
            new = lf / "new"
            new.mkdir()
            tmp = lf / "tmp"
            tmp.mkdir()



def scan_remote_folder(server, folder):
    """ Scans a remote folder for messages and retrieves message IDs in batches"""
    ### ToDo: Cache this data and only pull new Messages from server.
    folder = '"' + folder + '"'
    messages = {}
    log.info("Scanning "+folder)
    typ, data = server.select(folder, readonly=True)
    c = 0
    if "OK" != typ:
        log.error("Could not retrieve messages for the folder: "+folder)
    num_messages = int(data[0])
    if num_messages > 0:
        log.info("Messages in folder "+folder+": "+str(num_messages))
        jumpsize = 500 # how many messages to pull in one transaction
        jumps = (num_messages // jumpsize) + 1 # adding one to make sure we get into the loop
        mod_messages = num_messages % jumpsize
        
        for num in range(0, jumps):
            """ Pull messages in batches to move faster than single transactions per message."""
            log.info("Pulling batch#: "+str(num))
            start = str(num*jumpsize)
            if num == (jumps-1):
                end = str(num*jumpsize + mod_messages)
            else:
                end = str(num*jumpsize + jumpsize - 1)
            message_set = start + ":" + end
            log.info("Messages in this batch: " + message_set)
            typ, data = server.fetch(message_set, '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')
            if 'OK' != typ:
                log.error("Could not retrieve messages " + message_set + " from " + folder)
            for i in range(0, len(data), 2):
                msg = data[i][1]
                msg_str = email.message_from_string(msg.decode('UTF-8'))
                msg_id = msg_str.get('Message-ID')
                if msg_id not in messages.keys():
                    messages[msg_id] = num
                    c += 1
            #try: 
            #    for d in data:
            #        if isinstance(d, tuple):
            #            header = d[1].strip()
            #            header = header.decode('UTF-8')
            #            header = BLANKS_RE.sub(' ', header)
            #            msg_id = MSGID_RE.match(header).group(1)

            #            if msg_id not in messages.keys():
            #                messages[msg_id] = num
            #                c += 1
            #except (AttributeError):
            #    """ If we break down in the batch processing, process one by one."""
            #    log.warning("Bad message in batch "+str(num)+" of folder "+folder+". Running one by one...")
            #    for n in range(int(start), int(end)):
            #        typ, data = server.fetch(str(n), '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')
            #        if 'OK' != typ:
            #            log.error("Could not retrieve message " + str(n) + " from " + folder)
            #        try:
            #            header = data[0][1].strip()
            #            header = header.decode('UTF-8')
            #            header = BLANKS_RE.sub(' ', header)
            #            msg_id = MSGID_RE.match(header).group(1)
            #        except (AttributeError):
            #            """ If the Message-ID cannot be processed normally, generate one. """
            #            log.warning("Generating Message-ID for "+str(n)+" in folder "+folder)
            #            typ, data = server.fetch(str(n), '(BODY.PEEK[HEADER.FIELDS (FROM TO CC DATE SUBJECT)])')
            #            if "OK" != typ:
            #                log.error("Could not retrieve message " + str(n) + " from " + folder)
            #            header = data[0][1].strip()
            #            header = str(header).replace('\r\n', '\t')
            #            msg_id = '<' + hashlib.sha1(header.encode('UTF-8')).hexdigest() + '>'
            #       if msg_id not in messages.keys():
            #           messages[msg_id] = num
            #           c += 1




    else: 
        log.info("No messages in folder "+folder+". Skipping ahead.")

    log.info("Parsed " + str(c) + " of " + str(num_messages) + " in " + str(folder))
    #return messages

def scan_local_folder(localroot, folder):
    print("Not implemented")

def download_messages(server, new_messages):
    print("Not implemented")



def backup_imap(imap_server, imap_port, imap_user, imap_password, imap_localroot):
    server = imap_connect(imap_server, imap_port, imap_user, imap_password)

    folders = get_remote_folders(server)

    create_folder_structure(imap_localroot, folders)

    for folder in folders:
        remote_messages = scan_remote_folder(server, folder)
#        current_messages = scan_local_folder(imap_localroot, folder)
#
#        new_messages = {}
#        
#        for msg_id in remote_messages:
#            if msg_id not in current_messages:
#                new_messages[msg_id] = remote_messages[msg_id]
#        
#        download_messages(server, new_messages)

    server.logout()


