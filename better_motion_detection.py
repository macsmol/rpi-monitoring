#!/usr/bin/python3

import config

import base64
import gnupg
import logging
import time
import smtplib

import numpy as np

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import CircularOutput2, PyavOutput

from email.message import Message
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders


def get_encrypted_email_string(email_address_recipient, file_path_attachment, email_subject, email_message=""):
    def get_gpg_cipher_text(string, recipient_email_address):
        gpg = gnupg.GPG(gnupghome=config.gpg_home_dir)
        encrypted_data = gpg.encrypt(string, recipient_email_address)
        encrypted_str = str(encrypted_data)
        return encrypted_str

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
        msg_attachment.set_payload(file.read())
    encoders.encode_base64(msg_attachment)
    msg_attachment.add_header('Content-Disposition',
                    f'attachment; filename={file_path_attachment}')

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
    pgp_msg_part2.set_payload(get_gpg_cipher_text(plaintext_msg.as_string(), email_address_recipient))

    pgp_msg.attach(pgp_msg_part1)
    pgp_msg.attach(pgp_msg_part2)

    return pgp_msg.as_string()

def get_encrypted_email_string2(email_address_recipient, file_path_attachment, email_subject, email_message=""):
    
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

    #### 2.2 load encrypted message and dump to a string
    encrypted_data = None
    with open(file_path_attachment, 'rb') as file:
        encrypted_data = file.read()
    print(type(encrypted_data))
    payload = base64.b64encode(encrypted_data)    
    
    pgp_msg_part2 = Message()
    pgp_msg_part2.add_header(_name="Content-Type", _value="application/octet-stream", name="encrypted.asc")
    pgp_msg_part2.add_header(_name="Content-Description", _value="OpenPGP encrypted message")
    pgp_msg_part2.add_header(_name="Content-Disposition", _value="inline", filename="encrypted.asc")
    pgp_msg_part2.set_payload(payload)

    pgp_msg.attach(pgp_msg_part1)
    pgp_msg.attach(pgp_msg_part2)

    return pgp_msg.as_string()


lsize = (320, 240)
picam2 = Picamera2()
main = {"size": (1280, 720), "format": "RGB888"}
lores = {"size": lsize, "format": "YUV420"}
video_config = picam2.create_video_configuration(main, lores=lores)
picam2.configure(video_config)

duration = 2
encoder = H264Encoder(bitrate=1000000, repeat=True)
output = CircularOutput2(buffer_duration_ms=duration * 1000)
picam2.start_recording(encoder, output)

FORMAT = "%(asctime)s %(name)s: %(message)s"
logdatefmt = '%m%d %H:%M:%S'
logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=logdatefmt)
logger = logging.getLogger('mon')

logger.info("opening smtp")
smtp = smtplib.SMTP_SSL(config.server_url, config.server_port)
smtp.set_debuglevel(1)
logger.info("opening smtp - Done")

w, h = lsize
prev = None
encoding = False
ltime = 0

timestr = None
filename = None

while True:
    cur = picam2.capture_array("lores")[:h, :w]
    if prev is not None:
        # Measure pixels difference between current and
        # previous frame
        mse = np.square(np.subtract(cur, prev)).mean()
        if mse > 7:
            if not encoding:
                timestr = time.strftime("%Y-%m-%d_%H%M%S%z")

                filename = f"rec_{timestr}.mp4"
                output.open_output(PyavOutput(filename))
                encoding = True
                logger.info("New Recording started: mse %s, file: %s", mse, filename)

            ltime = time.time()
        else:
            if encoding and time.time() - ltime > duration + 2.0:
                output.close_output()
                logger.info("Recording stopped")
                encoding = False

                msg = get_encrypted_email_string2(
                    config.send_to,
                    "todo.txt.gpg",
                    #filename, 
                    f"Camera {timestr}", 
                    "Motion detected"
                )
                smtp.login(config.send_from, config.password)
                smtp.sendmail(config.send_from, config.send_to, msg)

                logger.info("Sending email - Done")
    prev = cur

smtp.close()