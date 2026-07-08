#!/usr/bin/python3

import config

import gnupg
import logging
import time
import smtplib
import sys

from email.message import Message
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders

def get_encrypted_email_string(email_address_recipient, file_path_attachment, email_subject, email_message=""):
    def get_gpg_cipher_text(string, recipient_email_address):
        logger.info("gpg_home_dir '%s'" %config.gpg_home_dir)
        logger.info("gpg_keyring_dir '%s'" %config.gpg_keyring_dir)
        gpg = gnupg.GPG(gnupghome=config.gpg_home_dir, keyring=config.gpg_keyring_dir)
        
        # This looked like a helpful error/troubleshoot message to the user but
        # I could not ever get gpg.list_keys() to list anything.
        # even when succesfully encrypting msg to user that is not listed.
        # logger.info("listingg keys %s" %gpg.list_keys())
        # if (recipient_email_address not in gpg.list_keys()):
        #     logger.error("""Recipient email not found in gpg keyring.
        #     Did you import the public key for that email?")
        #     Does gpg_keyring_dir in config.py file point to the keyring file actually used by gpg?""")
        #     sys.exit()
        
        encrypted_data = gpg.encrypt(string, recipient_email_address, always_trust=True)
        if (encrypted_data.ok != True):
            print("Encryption to '%s' failed" %recipient_email_address)
            print("Status is %s" %encrypted_data.status)
            sys.exit(f"gpg error: {encrypted_data.status}")
        return str(encrypted_data)
    
    #### 1. plaintext message
    plaintext_msg = MIMEMultipart()
    plaintext_msg["Subject"] = email_subject
    plaintext_msg["From"]    = config.send_from
    plaintext_msg["To"]      = config.send_to
    
    #### 1.1 message text
    msg_text = MIMEText(email_message, _charset="utf-8")

    #### 1.2 video recording attachment
    msg_attachment = MIMEBase('application', "octet-stream")
    with open(file_path_attachment, 'rb') as file:
        file_content = file.read()
        msg_attachment.set_payload(file_content)
    encoders.encode_base64(msg_attachment)
    
    logger.info("file_path_attachment %s", file_path_attachment)
    filename = file_path_attachment.split('/')[-1]
    logger.info("filename %s", filename)

    msg_attachment.add_header('Content-Disposition',
                    f'attachment; filename={filename}')

    plaintext_msg.attach(msg_text)
    plaintext_msg.attach(msg_attachment)


    #### 2. pgp encrypt plaintext message
    pgp_msg = MIMEBase(_maintype="multipart", _subtype="encrypted", protocol="application/pgp-encrypted")
    pgp_msg["Subject"] = email_subject
    pgp_msg["From"]    = config.send_from
    pgp_msg["To"]      = config.send_to

    #### 2.1 create a header that says PGP/MIME was used
    pgp_msg_part1 = Message()
    pgp_msg_part1.add_header(_name="Content-Type", _value="application/pgp-encrypted")
    pgp_msg_part1.add_header(_name="Content-Description", _value="PGP/MIME version identification")
    pgp_msg_part1.set_payload("Version: 1" + "\n")

    #### 2.2 encrypt the whole content and dump to a string
    pgp_msg_part2 = Message()
    pgp_msg_part2.add_header(_name="Content-Type", _value="application/octet-stream", name="encrypted.asc")
    pgp_msg_part2.add_header(_name="Content-Description", _value="OpenPGP encrypted message")
    pgp_msg_part2.add_header(_name="Content-Disposition", _value="inline", filename="encrypted.asc")
    cipher_text = get_gpg_cipher_text(plaintext_msg.as_string(), email_address_recipient)
    pgp_msg_part2.set_payload(cipher_text)

    pgp_msg.attach(pgp_msg_part1)
    pgp_msg.attach(pgp_msg_part2)

    return pgp_msg.as_string()

FORMAT = "%(asctime)s %(name)s: %(message)s"
logdatefmt = '%m%d %H:%M:%S'
logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=logdatefmt)
logger = logging.getLogger('mon')

logger.info("openingg smtp")
smtp = smtplib.SMTP_SSL(config.server_url, config.server_port)
smtp.set_debuglevel(1)
logger.info("openingg smtp - Done")

timestr = time.strftime("%Y-%m-%d_%H%M%S%z")
filename = "testdata/0703_1255.png"

msg = get_encrypted_email_string(
    config.send_to,
    filename, 
    f"Camera {timestr}", 
    "Motion detected"
)
logger.info("Loggingg in...")
smtp.login(config.send_from, config.password)
logger.info("Sendingg...")
smtp.sendmail(config.send_from, config.send_to, msg)

logger.info("Sendingg email - Done")

smtp.close()