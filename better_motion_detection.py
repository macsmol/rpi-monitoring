#!/usr/bin/python3

import config

import logging
import time
import smtplib

import numpy as np

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import CircularOutput2, PyavOutput

from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders

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

                msg = MIMEMultipart()
                msg.attach(MIMEText("Motion detected", _charset="utf-8"))
                
                msg['Subject'] = f"Camera {timestr}"
                msg['From']    = config.send_from
                msg['To']      = config.send_to

                #### attach video recording
                part = MIMEBase('application', "octet-stream")
                with open(filename, 'rb') as file:
                    part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition',
                                'attachment; filename={}'.format(filename))
                msg.attach(part)
                ####

                logger.info("Logging in..")
                # fails on later attempts when it does not send helo but server has timed it out
                smtp.login(config.send_from, config.password)
                
                logger.info("Sending..")
                smtp.sendmail(config.send_from, config.send_to, msg.as_string())

                logger.info("Sending email - Done")
    prev = cur

smtp.close()