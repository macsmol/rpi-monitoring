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

buffered_duration_s = 4
min_video_duration_s = buffered_duration_s + 2

bitrate = 1000000
byterate = bitrate/8
encoder = H264Encoder(bitrate=bitrate, repeat=True)
output = CircularOutput2(buffer_duration_ms=buffered_duration_s * 1000)
picam2.start_recording(encoder, output)

max_video_duration_s = config.max_attachment_bytes/byterate

if max_video_duration_s < min_video_duration_s:
    min_attachment_size = min_video_duration_s * byterate
    logger.warning("config.max_attachment_bytes is too small. Overriding it to effectively: %s bytes", min_attachment_size)

FORMAT = "%(asctime)s %(name)s: %(message)s"
logdatefmt = '%m%d %H:%M:%S'
logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=logdatefmt)
logger = logging.getLogger('mon')

logger.info("max_video_duration_s %s", max_video_duration_s)

smtp = create_conn()

w, h = lsize
prev = None
encoding = False
ltime = 0

start_time = None
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
                start_time = time.time()
                timestr = time.strftime("%Y-%m-%d_%H%M%S%z")

                filename = f"videos/rec_{timestr}.mp4"
                output.open_output(PyavOutput(filename))
                encoding = True
                logger.info("New Recording started: mse %s, file: %s", mse, filename)
            else:
                if time.time() - start_time > max_video_duration_s:
                    output.close_output()
                    logger.info("Recording stopped - too long")
                    encoding = False
                    asyncio.run(send_mail(filename, timestr, smtp))

            ltime = time.time()
        else:
            if encoding and time.time() - ltime > min_video_duration_s:
                output.close_output()
                logger.info("Recording stopped")
                encoding = False

                asyncio.run(send_mail(filename, timestr, smtp))
               
    prev = cur

smtp.close()