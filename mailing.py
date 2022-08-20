from imaplib import IMAP4_SSL
from getpass import getpass
from email import message_from_bytes
from email.message import Message
from email.header import decode_header
import typing
import os
import logging


def imapConnect(host: str, user: str, pw: typing.Optional[str] = None) -> IMAP4_SSL:
    """Connects to a mailing host via imap.

    Args:
        host (str): The host's url to connect to.
        user (str): The username to use for connection.
        pw (str | None, optional): The password to use for authentication. If None is given, user input will be used. Defaults to None.

    Returns:
        imaplib.IMAP4_SSL: _description_
    """
    imap = IMAP4_SSL(host)
    if not pw:
        pw = getpass("Input password: ")
    imap.login(user, pw)
    return imap


def imapSearch(imap: IMAP4_SSL, mailbox: typing.Optional[str] = None, *query: str) -> typing.List[int]:
    """Searches for mails via imap search criteria.

    Args:
        imap (IMAP4_SSL): A connected imaplib instance.
        mailbox (str | None, optional): The mailbox to select. Leave None if mailbox is already selected. Defaults to None.

    Returns:
        List[int]: A list of mail identifiers that match the searched criteria.
    """
    if mailbox:
        imap.select(mailbox)
    if not (result := imap.search(None, *query)[1][0]):  # No mail found?
        return list()
    else:
        return [int(i) for i in result.split()]


def imapReceive(imap: IMAP4_SSL, mailbox: typing.Optional[str] = None, n: typing.Union[typing.List[int], int] = 0) -> typing.List[Message]:
    """Receive specific or the first n mails and return them in a list of email.Message objects.

    Args:
        imap (IMAP4_SSL): A connected imaplib instance.
        mailbox (str | None, optional): The mailbox to select. Leave None if mailbox is already selected. Defaults to None.
        n (List[int] | int, optional): Either an integer indicating the n most recent mails to receive or a list of integers containing int identifiers of mails to receive. Defaults to 0 (receive all mails).

    Returns:
        List[email.Message]: List of received mails as email.Message objects.
    """
    if mailbox:
        _, msgN = imap.select(mailbox)
    else:
        msgN = imapSearch(imap, None, "ALL")
    if not msgN[0] or (msgN := int(msgN[0]) == 0):
        return list()
    if isinstance(n, int):  # Receive n most recent mails
        if n == 0 or n > msgN:
            iterate = range(msgN, 0, -1)
        else:
            iterate = range(msgN, msgN-n, -1)
    else:  # Receive specific mails denoted by id
        iterate = n
    received = list()
    for i in iterate:
        _, msg = imap.fetch(str(i), "(RFC822)")
        for res in msg:
            if isinstance(res, tuple):
                received.append(message_from_bytes(res[1]))
    return received


def mailRead(mail: Message, download="", shout=False) -> typing.Dict[str, str]:
    """Reads email.Message objects and optionally downloads their attachments.

    Args:
        mail (Message): A mail as an email.Message object.
        download (str, optional): Path to download possible attachments to. Defaults to "".
        shout (bool, optional): Set to True if text/plain content should be printed to console. Defaults to False.

    Returns:
        Dict[str, str]: A dictionary with Subject, From, To, text/plain and text/html as keys and the respective content as values.
    """
    read = dict()
    # decode Subject, From and To
    for head in ["Subject", "From", "To"]:
        content, encoding = decode_header(mail[head])[0]
        if isinstance(content, bytes) and encoding is not None:
            # if it's a bytes, decode to str
            content = content.decode(encoding)
        read[head] = content
        if shout:
            print(f"{head}: {content}")
    read.update({"text/plain": "", "text/html": ""})
    # iterate over email parts
    for part in mail.walk():
        # extract content type of email
        content_type = part.get_content_type()
        content_disposition = str(part.get("Content-Disposition"))
        try:
            # get the email body
            body = part.get_payload(decode=True).decode()
        except:
            pass
        else:
            if content_type == "text/plain" and "attachment" not in content_disposition:
                read["text/plain"] += body
                if shout:
                    print(body)
            elif content_type == "text/html":
                # if it's HTML, append body to HTML code
                read["text/html"] += body
                if shout:
                    logging.info("Mail also contains HTML code.")
        if "attachment" in content_disposition and download:
            # download attachment
            filename = part.get_filename()
            if filename:
                folder_name = "".join(
                    c if c.isalnum() else "_" for c in read["Subject"])
                folder_path = os.path.join(download, folder_name)
                if not os.path.isdir(folder_path):
                    # make a folder for this email (named after the subject)
                    os.mkdir(folder_path)
                filepath = os.path.join(folder_path, filename)
                # download attachment and save it
                open(filepath, "wb").write(part.get_payload(decode=True))
    return read
