#!/usr/bin/python3

import config
from format_mail import get_encrypted_email_string

import asyncio
import logging
import time
import smtplib

import numpy as np

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import CircularOutput2, PyavOutput

from time import sleep# workaround for pi cam not flushing in time - todo better


def create_conn():
    logger.info("opening smtp")
    smtp = smtplib.SMTP_SSL(config.server_url, config.server_port)
    #generates huge lag because it prints whole content of email (megabytes)
    #smtp.set_debuglevel(1)
    logger.info("opening smtp - Done")
    return smtp

async def send_mail(filename, timestr, smtp_conn):
    
    def test_conn_open(conn):
        try:
            status = conn.noop()[0]
        except:
            status = -1
        return True if status == 250 else False
        
    msg = get_encrypted_email_string(
        config.send_to,
        filename, 
        f"Camera {timestr}", 
        "Motion detected"
    )
    logger.info("Logging in...")
    if not test_conn_open(smtp_conn):
        smtp_conn = create_conn()
        
    smtp_conn.login(config.send_from, config.password)
    logger.info("Sendingg email..")
    smtp_conn.sendmail(config.send_from, config.send_to, msg)
    logger.info("Sendingg email - Done")


lsize = (320, 240)
picam2 = Picamera2()
main = {"size": (1280, 720), "format": "RGB888"}
lores = {"size": lsize, "format": "YUV420"}
video_config = picam2.create_video_configuration(main, lores=lores)
picam2.configure(video_config)

duration = 4
encoder = H264Encoder(bitrate=1000000, repeat=True)
output = CircularOutput2(buffer_duration_ms=duration * 1000)
picam2.start_recording(encoder, output)

FORMAT = "%(asctime)s %(name)s: %(message)s"
logdatefmt = '%m%d %H:%M:%S'
logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=logdatefmt)
logger = logging.getLogger('mon')

smtp = create_conn()

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

                filename = f"videos/rec_{timestr}.mp4"
                output.open_output(PyavOutput(filename))
                encoding = True
                logger.info("New Recording started: mse %s, file: %s", mse, filename)

            ltime = time.time()
        else:
            if encoding and time.time() - ltime > duration + 2.0:
                output.close_output()
                logger.info("Recording stopped")
                encoding = False

                asyncio.run(send_mail(filename, timestr, smtp))
               
    prev = cur

smtp.close()