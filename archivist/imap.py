import logging, email, os, gzip
from pathlib import Path
from imapclient import IMAPClient

log = logging.getLogger(__name__)


def get_remote_folders(client):
    """ Gets and parses a list of folders from the server """
    log.info("Getting remote folders")
    l = client.list_folders()
    folders = []
    for folder in l:
        folders.append(str(folder[2]))
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
            log.info("Creating " + str(lf))
            lf.mkdir(parents=True)
            cur = lf / "cur"
            cur.mkdir()
            new = lf / "new"
            new.mkdir()
            tmp = lf / "tmp"
            tmp.mkdir()
    return True


def scan_remote_folder(client, folder):
    """ Scans a remote folder for messages and retrieves message IDs in batches"""
    messages = {}
    log.info("Scanning " + folder + " on server")
    client.select_folder(folder, readonly=True)
    uids = client.search()
    if len(uids) > 0:
        UID_newest = max(uids)
    else:
        UID_newest = 0
    UID_validity = client.folder_status(folder, what=u"UIDVALIDITY")[b"UIDVALIDITY"]
    return UID_validity, UID_newest, uids


def scan_local_folder(localroot, folder):
    """ Get the last UID stored in the folder """
    UID_file = localroot / folder / ".uid"
    if UID_file.exists():
        with open(UID_file, "r") as f:
            fstr = f.read()
            ftup = fstr.split()
            return int(ftup[0]), int(ftup[1])
    else:
        return -1, 0


def get_messages(client, folder, uid_local, uid_newest):
    """ Get all messages in a folder between two UIDs """
    if uid_newest > uid_local:
        client.select_folder(folder, readonly=True)
        searchstr = "UID " + str(uid_local) + ":" + str(uid_newest)
        messages = client.search(searchstr)
    else:
        messages = []
    return messages


def store_email(client, localroot, folder, uid_validity, uids, compress):
    """ Store an email in the correct folder"""
    response = client.fetch(uids, "RFC822")

    for uid, data in response.items():
        filename = str(uid_validity) + "-" + str(uid).zfill(9)
        emailfile = localroot / folder / "cur" / filename

        rfcdata = data[b"RFC822"]

        if compress:
            rfcdata = gzip.compress(rfcdata, compresslevel=3)
            emailfile = emailfile.with_suffix(".gz")

        with open(emailfile, "wb") as f:
            f.write(data[b"RFC822"])

    return True


def update_folder_uid(localroot, folder, uid_validity, uid):
    """ Update the folder with the most recently stored UID """
    UID_file = localroot / folder / ".uid"

    with open(UID_file, "w") as f:
        fstr = str(uid_validity) + " " + str(uid)
        f.write(fstr)

    validity_check, check = scan_local_folder(localroot, folder)

    if validity_check == uid_validity and check == uid:
        return True
    else:
        return False


def cleanup_folder(localroot, folder, remote_messages):
    cull_list = []
    local_list = {}
    path = localroot / folder / "cur"

    log.info("Cleaning up old messages in " + folder)

    for p in path.glob("*"):
        uid = int(p.stem.split("-")[1].lstrip("0"))
        local_list[uid] = p

    cull_list = list(set(local_list).difference(remote_messages))

    if len(cull_list) > 0:
        log.info("Deleting " + str(len(cull_list)) + " of " + str(len(local_list)))

        for m in cull_list:
            local_list[m].unlink()

    remote_count = len(remote_messages)
    final_count = 0
    for p in path.glob("*"):
        final_count += 1

    if final_count == remote_count:
        log.info(str(final_count) + " of " + str(remote_count) + " stored in " + folder)
        return True
    else:
        log.error(
            "L"
            + str(final_count)
            + "!=R"
            + str(remote_count)
            + " | Message counts do not match in folder "
            + folder
        )
        return False


def backup_imap(config):

    compress = config.get("compress", True)
    cleanup = config.get("cleanup", False)
    backup_folder = Path(config["backup_folder"])

    with IMAPClient(host=config["server"]) as client:
        client.login(config["user"], config["password"])

        all_folders = config.get("folders", get_remote_folders(client))
        folders = []
        exclude = config.get("exclude", None)

        if exclude != None:
            for folder in all_folders:
                if folder not in exclude:
                    folders.append(folder)
        else:
            folders = all_folders

        create_folder_structure(backup_folder, folders)

        for folder in folders:
            uid_local_validity, uid_local = scan_local_folder(backup_folder, folder)
            uid_remote_validity, uid_newest, remote_messages = scan_remote_folder(
                client, folder
            )

            # if the folder does not have a recorded validity, accept the server's
            if 0 > uid_local_validity:
                uid_local_validity = uid_remote_validity

            # Check to make sure the server has not reset UIDs
            if uid_local_validity == uid_remote_validity:
                messages = get_messages(client, folder, uid_local, uid_newest)
                if len(messages) > 0:
                    log.info("Downloading " + str(len(messages)) + " to " + folder)

                    for uid in messages:
                        if store_email(
                            client,
                            backup_folder,
                            folder,
                            uid_remote_validity,
                            uid,
                            compress,
                        ):
                            if not update_folder_uid(
                                backup_folder, folder, uid_remote_validity, uid
                            ):
                                log.error(
                                    "UID " + str(uid) + " failed to update in " + folder
                                )
                        else:
                            log.error(
                                "Message " + str(uid) + " failed to save in " + folder
                            )

                if cleanup:
                    cleanup_folder(backup_folder, folder, remote_messages)

            else:
                log.error(
                    "The server has reset UID validity, for folder "
                    + folder
                    + "."
                    + "Backup must be repaired manually"
                )
